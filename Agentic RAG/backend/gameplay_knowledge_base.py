"""
奇遇（Encounter）知识库管理模块
处理gameplay_knowledge_base.md，构建向量数据库，实现RAG检索
"""

import os
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

try:
    import chromadb
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    print("警告: chromadb未安装，将使用内存存储。运行: pip install chromadb")

try:
    from sentence_transformers import SentenceTransformer
    EMBEDDING_AVAILABLE = True
except ImportError:
    EMBEDDING_AVAILABLE = False
    print("警告: sentence-transformers未安装，将使用简单文本匹配。运行: pip install sentence-transformers")


@dataclass
class GameplayFunctionDoc:
    """奇遇API函数文档数据结构"""
    module: str  # World, UI, System, Entity, Performer, Math, Time
    function_name: str  # GetByID, MoveTo, ShowDialogue等
    signature: str  # 函数签名
    description: str  # 说明
    parameters: str  # 参数说明
    example: str  # 示例代码
    return_value: str  # 返回值说明
    recommended_usage: str  # 推荐用法
    common_errors: str  # 常见错误
    tags: List[str]  # 功能标签


class GameplayKnowledgeBase:
    """奇遇知识库管理器"""
    
    # 模块映射
    MODULE_MAPPING = {
        "World": "核心玩法API",
        "UI": "交互核心",
        "System": "脚本控制",
        "Entity": "Actor基础能力",
        "Performer": "NPC行为接口",
        "Math": "随机性与涌现",
        "Time": "环境时间控制"
    }
    
    # 功能标签到模块的映射（用于检索）
    FUNCTION_TO_MODULE = {
        # World模块
        "获取对象": ["World"],
        "GetByID": ["World"],
        "Player": ["World"],
        "NPC": ["World"],
        "Wait": ["World"],
        "延迟": ["World"],
        "节奏": ["World"],
        "特效": ["World"],
        "PlayFX": ["World"],
        "音效": ["World"],
        "PlaySound": ["World"],
        "PlaySound2D": ["World"],
        "StopSound": ["World"],
        "生成敌人": ["World"],
        "SpawnEnemy": ["World"],
        "SpawnEnemyAtPlayer": ["World"],
        "销毁": ["World"],
        "Destroy": ["World"],
        "DestroyByID": ["World"],
        
        # UI模块
        "Toast": ["UI"],
        "提示": ["UI"],
        "FadeOut": ["UI"],
        "FadeIn": ["UI"],
        "对话": ["UI"],
        "ShowDialogue": ["UI"],
        "选择": ["UI"],
        "Ask": ["UI"],
        "AskMany": ["UI"],
        "小游戏": ["UI"],
        "PlayMiniGame": ["UI"],
        
        # System模块
        "退出": ["System"],
        "Exit": ["System"],
        "ExitAll": ["System"],
        "Pause": ["System"],
        "Resume": ["System"],
        
        # Entity模块
        "IsValid": ["Entity"],
        "GetPos": ["Entity"],
        "GetRot": ["Entity"],
        "Teleport": ["Entity"],
        "AddTrigger": ["Entity"],
        
        # Performer模块
        "移动": ["Performer"],
        "MoveTo": ["Performer"],
        "MoveToActor": ["Performer"],
        "跟随": ["Performer"],
        "Follow": ["Performer"],
        "StopFollow": ["Performer"],
        "朝向": ["Performer"],
        "LookAt": ["Performer"],
        "动画": ["Performer"],
        "PlayAnim": ["Performer"],
        "PlayAnimLoop": ["Performer"],
        "说话": ["Performer"],
        "ApproachAndSay": ["Performer"],
        "敌对": ["Performer"],
        "SetAsHostile": ["Performer"],
        "盟友": ["Performer"],
        "SetAsAlly": ["Performer"],
        "给予": ["Performer"],
        "GiveItem": ["Performer"],
        "GiveEquip": ["Performer"],
        "GiveWeapon": ["Performer"],
        "奖励": ["Performer"],
        
        # Math模块
        "随机": ["Math"],
        "RandInt": ["Math"],
        "概率": ["Math"],
        "Chance": ["Math"],
        "距离": ["Math"],
        "Dist": ["Math"],
        "Dir": ["Math"],
        "Normalize": ["Math"],
        "Lerp": ["Math"],
        "Clamp": ["Math"],
        "Remap": ["Math"],
        "RandPointInSphere": ["Math"],
        
        # Time模块
        "时间": ["Time"],
        "GetInfo": ["Time"],
        "IsNight": ["Time"],
        "夜晚": ["Time"]
    }
    
    def __init__(self, knowledge_file: str = "gameplay_knowledge_base.md"):
        """初始化知识库"""
        self.knowledge_file = knowledge_file
        self.reference_document = "gameplay_document.md"  # 参考文档
        self.functions: List[GameplayFunctionDoc] = []
        self.reference_examples: str = ""  # 参考文档中的示例代码
        self.vector_db = None
        self.embedding_model = None
        self.collection = None
        
        # 加载知识库文档
        self._load_knowledge_base()
        
        # 加载参考文档（gameplay_document.md）
        self._load_reference_document()
        
        # 初始化向量数据库
        if CHROMADB_AVAILABLE:
            self._init_vector_db()
        else:
            print("使用简单文本匹配模式")
    
    def _load_knowledge_base(self):
        """从Markdown文件加载知识库"""
        # 尝试多个可能的路径
        possible_paths = [
            os.path.join(os.path.dirname(__file__), self.knowledge_file),
            os.path.join(os.path.dirname(__file__), "..", self.knowledge_file),
            self.knowledge_file
        ]
        
        kb_path = None
        for path in possible_paths:
            if os.path.exists(path):
                kb_path = path
                break
        
        if not kb_path or not os.path.exists(kb_path):
            print(f"警告: 知识库文件不存在，尝试的路径: {possible_paths}")
            return
        
        # 读取文件，处理BOM和编码问题
        try:
            # 尝试UTF-8 with BOM
            with open(kb_path, 'r', encoding='utf-8-sig') as f:
                content = f.read()
        except (UnicodeDecodeError, UnicodeError):
            # 如果UTF-8失败，尝试UTF-8 without BOM
            try:
                with open(kb_path, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()
            except:
                # 最后尝试GBK（中文Windows常用编码）
                with open(kb_path, 'r', encoding='gbk', errors='replace') as f:
                    content = f.read()
        
        # 确保移除BOM标记
        if content.startswith('\ufeff'):
            content = content[1:]
        
        # 解析Markdown内容
        self._parse_markdown(content)
        
        print(f"已加载 {len(self.functions)} 个奇遇API函数文档")
    
    def _load_reference_document(self):
        """加载参考文档 gameplay_document.md，提取示例代码"""
        possible_paths = [
            os.path.join(os.path.dirname(__file__), self.reference_document),
            os.path.join(os.path.dirname(__file__), "..", self.reference_document),
            self.reference_document
        ]
        
        doc_path = None
        for path in possible_paths:
            if os.path.exists(path):
                doc_path = path
                break
        
        if not doc_path or not os.path.exists(doc_path):
            print(f"警告: 参考文档不存在，尝试的路径: {possible_paths}")
            return
        
        # 读取文件
        try:
            with open(doc_path, 'r', encoding='utf-8-sig') as f:
                content = f.read()
        except (UnicodeDecodeError, UnicodeError):
            try:
                with open(doc_path, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()
            except:
                with open(doc_path, 'r', encoding='gbk', errors='replace') as f:
                    content = f.read()
        
        # 移除BOM
        if content.startswith('\ufeff'):
            content = content[1:]
        
        # 提取关键部分：API示例和组合调用参考
        self._extract_reference_examples(content)
        
        print(f"已加载参考文档: {self.reference_document}")
    
    def _extract_reference_examples(self, content: str):
        """从参考文档中提取示例代码和关键规则"""
        examples_parts = []
        
        # 提取所有示例代码（格式：示例：`code`）
        example_pattern = r'示例[：:]\s*`([^`]+)`'
        examples = re.findall(example_pattern, content)
        
        # 提取组合调用参考部分（第5节）
        section_5_match = re.search(r'## 5\.\s*组合调用参考[^\n]*\n(.*?)(?=\n##|\Z)', content, re.DOTALL)
        if section_5_match:
            examples_parts.append("## 组合调用参考（来自gameplay_document.md）")
            examples_parts.append(section_5_match.group(1).strip())
            examples_parts.append("")
        
        # 提取关键API示例（World.SpawnEncounter相关）
        spawn_encounter_match = re.search(r'World\.SpawnEncounter[^\n]*示例[：:]\s*`([^`]+)`', content)
        if spawn_encounter_match:
            examples_parts.append("## World.SpawnEncounter 标准示例")
            examples_parts.append(f"```lua\n{spawn_encounter_match.group(1)}\n```")
            examples_parts.append("")
        
        # 提取Performer接口的关键示例
        performer_examples = []
        performer_pattern = r'### 3\.6\s*`Performer`[^#]*(?=###)'
        performer_match = re.search(performer_pattern, content, re.DOTALL)
        if performer_match:
            performer_section = performer_match.group(0)
            # 提取ApproachAndSay示例
            approach_example = re.search(r'npc:ApproachAndSay[^\n]*示例[：:]\s*`([^`]+)`', performer_section)
            if approach_example:
                performer_examples.append(f"- `npc:ApproachAndSay`: {approach_example.group(1)}")
            # 提取PlayAnim示例
            playanim_example = re.search(r'npc:PlayAnim[^\n]*示例[：:]\s*`([^`]+)`', performer_section)
            if playanim_example:
                performer_examples.append(f"- `npc:PlayAnim`: {playanim_example.group(1)}")
        
        if performer_examples:
            examples_parts.append("## Performer接口关键示例")
            examples_parts.extend(performer_examples)
            examples_parts.append("")
        
        # 提取UI接口的关键示例
        ui_examples = []
        ui_pattern = r'### 3\.3\s*`UI`[^#]*(?=###)'
        ui_match = re.search(ui_pattern, content, re.DOTALL)
        if ui_match:
            ui_section = ui_match.group(0)
            # 提取ShowDialogue示例
            dialogue_example = re.search(r'UI\.ShowDialogue[^\n]*示例[：:]\s*`([^`]+)`', ui_section)
            if dialogue_example:
                ui_examples.append(f"- `UI.ShowDialogue`: {dialogue_example.group(1)}")
            # 提取AskMany示例
            askmany_example = re.search(r'UI\.AskMany[^\n]*示例[：:]\s*`([^`]+)`', ui_section)
            if askmany_example:
                ui_examples.append(f"- `UI.AskMany`: {askmany_example.group(1)}")
        
        if ui_examples:
            examples_parts.append("## UI接口关键示例")
            examples_parts.extend(ui_examples)
            examples_parts.append("")
        
        # 提取通用约定
        convention_match = re.search(r'## 1\.\s*通用约定[^\n]*\n(.*?)(?=\n##)', content, re.DOTALL)
        if convention_match:
            examples_parts.append("## 通用约定（来自gameplay_document.md）")
            examples_parts.append(convention_match.group(1).strip())
            examples_parts.append("")
        
        # 添加完整的Few-Shot示例（基于用户提供的实际代码）
        examples_parts.append("## 完整Encounter示例（Few-Shot，基于实际项目代码）")
        examples_parts.append(self._get_few_shot_example())
        examples_parts.append("")
        
        self.reference_examples = "\n".join(examples_parts)
    
    def _get_few_shot_example(self) -> str:
        """
        返回简化的完整Encounter示例作为Few-Shot示例
        基于用户提供的实际项目代码格式
        """
        return """```lua
-- 完整Encounter示例（基于实际项目代码格式）
local function ResolveEncounterLoc()
    return { X = 12016.593860, Y = 13372.975811, Z = 4797.613441 }
end

function SpawnEncounter_FirstMeet()
    local npcData = {
        enc0_Alice = "Default"
    }

    local code = [[
if _G.enc0_done then return end
_G.enc0_done = true

local player = World.GetByID("Player")
local alice = World.GetByID("enc0_Alice")

if not player or not player:IsValid() then return end
if not alice or not alice:IsValid() then return end

if alice and player then
    alice:ApproachAndSay(player, "稍等片刻，旅行者。")
    World.Wait(1.0)
    local choice = UI.Ask("你要怎么做？", "接受", "拒绝")
    if choice == "接受" then
        alice:PlayAnimLoop("Happy", 0)
        World.Wait(1)
        alice:ApproachAndSay(player, "太好了！让我们开始这段旅程！")
        alice:SetAsCompanion()
        UI.Toast("Alice成为同伴")
    else
        alice:PlayAnimLoop("Frustrated", 0)
        World.Wait(1)
        alice:ApproachAndSay(player, "好吧，我尊重你的选择。")
    end
end
]]

    local loc = ResolveEncounterLoc()
    return World.SpawnEncounter(loc, 100.0, npcData, "EnterVolume", code)
end

SpawnEncounter_FirstMeet()

World.StartGame()
Time.Resume()
UI.Toast("游戏开始")
```

**关键格式要求（必须严格遵守）**：
1. **位置函数**：必须定义 `local function ResolveEncounterLoc()` 返回位置坐标 `{ X = 数值, Y = 数值, Z = 数值 }`
2. **Encounter函数**：必须使用 `function SpawnEncounter_XXX()` 格式包装
3. **NPC映射变量**：使用 `local npcData = { enc0_Alice = "Default" }` 格式（键名如 `enc0_Alice`，值为 `"Default"`）
4. **代码块变量**：使用 `local code = [[ ... ]]` 格式
5. **代码块内必须包含**：
   - `if _G.enc0_done then return end` 和 `_G.enc0_done = true`（防止重复触发）
   - `World.GetByID("Player")` 和 `World.GetByID("enc0_XXX")` 获取对象
   - `IsValid()` 判空检查（必须检查所有对象）
   - NPC对话、玩家选择、分支逻辑
   - `World.Wait()` 控制节奏（每个动作后）
6. **World.SpawnEncounter调用**：
   - 第1个参数：`ResolveEncounterLoc()` 返回的位置
   - 第2个参数：范围数字（如 `100.0` 或 `300.0`）
   - 第3个参数：`npcData` 变量
   - 第4个参数：`"EnterVolume"`（字符串）
   - 第5个参数：`code` 变量
7. **函数调用**：最后调用 `SpawnEncounter_XXX()`
8. **初始化代码**：最后包含 `World.StartGame()`, `Time.Resume()`, `UI.Toast("游戏开始")`
9. **对话格式**：
   - NPC对话：`npc:ApproachAndSay(player, "文本")` 或 `UI.ShowDialogue("名称", "文本")`
   - 玩家对话：`UI.ShowDialogue("Player", "文本")`（不能使用player:ApproachAndSay）
10. **选项格式**：
    - `UI.Ask("问题", "选项1", "选项2")` 返回字符串
    - `UI.AskMany("问题", {"选项1", "选项2"})` 返回数字索引（1开始）
11. **动画格式**：
    - `npc:PlayAnim("动画名称")` 或 `npc:PlayAnimLoop("动画名称", 0)`（动画名称必须来自素材库）
    - 停止动画：`npc:PlayAnim("Idle")` 或 `npc:PlayAnimLoop("Idle", 0)`
12. **代码块内不能有注释（`--`），否则引擎报错**
13. **所有对话内容不要使用方括号（正确：`"文本"`，错误：`"[文本]"`）**"""
    
    def get_reference_examples(self) -> str:
        """获取参考文档中的示例代码"""
        return self.reference_examples
    
    def _parse_markdown(self, content: str):
        """解析Markdown格式的知识库"""
        current_module = None
        current_section = None
        current_function = None
        
        lines = content.split('\n')
        i = 0
        
        while i < len(lines):
            line = lines[i]
            line_stripped = line.strip()
            original_line = line  # 保留原始行（用于代码块）
            
            # 跳过空行（除非在某个section中）
            if not line_stripped and not current_section:
                i += 1
                continue
            
            # 检测模块标题（如 "A. World 模块（核心玩法 API）"）
            module_match = re.match(r'^([A-Z])\.\s+(\w+)\s+模块', line_stripped)
            if module_match:
                # 保存上一个函数
                if current_function:
                    self.functions.append(current_function)
                
                module_name = module_match.group(2)
                current_module = module_name
                current_function = None
                current_section = None
                i += 1
                continue
            
            # 检测函数编号（如 "A1. 获取对象（Player / NPC）"）
            func_match = re.match(r'^([A-Z])(\d+)\.\s+(.+?)(?:（|$)', line_stripped)
            if func_match:
                # 保存上一个函数
                if current_function:
                    self.functions.append(current_function)
                
                # 开始新函数
                function_name = func_match.group(3).strip()
                current_function = GameplayFunctionDoc(
                    module=current_module or "Unknown",
                    function_name=function_name,
                    signature="",
                    description="",
                    parameters="",
                    example="",
                    return_value="",
                    recommended_usage="",
                    common_errors="",
                    tags=self._extract_tags(function_name, "")
                )
                current_section = None
                i += 1
                continue
            
            # 检测函数签名（支持两种格式）
            # 格式1: World.GetByID(uid) -> Actor|nil
            # 格式2: obj:GetRot() -> FRotator
            if current_function and not current_section and line_stripped:
                sig_match = re.match(r'^(\w+(?:\.|:)\w+\([^)]*\))\s*->', line_stripped)
                if sig_match:
                    current_function.signature = line_stripped
                    i += 1
                    continue
            
            # 检测说明、参数、示例等部分
            if current_function:
                # 检测section标题
                if line_stripped.startswith("说明：") or line_stripped.startswith("参数：") or line_stripped.startswith("示例：") or \
                   line_stripped.startswith("返回值：") or line_stripped.startswith("推荐用法：") or line_stripped.startswith("常见错误："):
                    current_section = line_stripped.split("：")[0]
                    content_text = line_stripped.split("：", 1)[1] if "：" in line_stripped else ""
                    if content_text:
                        self._set_function_field(current_function, current_section, content_text)
                    i += 1
                    continue
                elif current_section:
                    # 继续当前部分的内容
                    # 如果遇到新的函数编号或模块标题，停止当前部分
                    if re.match(r'^([A-Z])(\d+)\.', line_stripped) or re.match(r'^([A-Z])\.\s+\w+\s+模块', line_stripped):
                        current_section = None
                        # 不增加i，让外层循环重新处理这一行
                        continue
                    
                    # 添加内容到当前部分（包括空行，用于保持代码格式）
                    self._set_function_field(current_function, current_section, original_line)
            
            i += 1
        
        # 保存最后一个函数
        if current_function:
            self.functions.append(current_function)
    
    def _set_function_field(self, func: GameplayFunctionDoc, section: str, text: str):
        """设置函数文档字段"""
        if not text.strip() and section not in ["示例", "推荐用法", "常见错误"]:
            return
        
        if section == "说明":
            func.description += text + "\n"
        elif section == "参数":
            func.parameters += text + "\n"
        elif section == "示例":
            func.example += text + "\n"
        elif section == "返回值":
            func.return_value += text + "\n"
        elif section == "推荐用法":
            func.recommended_usage += text + "\n"
        elif section == "常见错误":
            func.common_errors += text + "\n"
    
    def _extract_tags(self, function_name: str, description: str) -> List[str]:
        """提取功能标签"""
        tags = []
        text = (function_name + " " + description).lower()
        
        # 从函数名提取关键词
        words = re.findall(r'\w+', function_name)
        tags.extend([w.lower() for w in words])
        
        # 从描述中提取关键词
        keywords = ["对话", "选择", "移动", "动画", "战斗", "奖励", "敌人", "NPC", "玩家", 
                   "音效", "特效", "随机", "概率", "时间", "退出", "销毁"]
        for keyword in keywords:
            if keyword in text:
                tags.append(keyword)
        
        return list(set(tags))
    
    def _init_vector_db(self):
        """初始化向量数据库"""
        if not CHROMADB_AVAILABLE:
            return
        
        try:
            # 创建持久化客户端
            db_path = os.path.join(os.path.dirname(__file__), "chroma_db_gameplay")
            self.vector_db = chromadb.PersistentClient(path=db_path)
            
            # 创建或获取集合
            collection_name = "gameplay_functions"
            try:
                self.collection = self.vector_db.get_collection(name=collection_name)
                # 检查集合中是否有文档
                count = self.collection.count()
                if count == 0 and len(self.functions) > 0:
                    # 如果集合存在但为空，且已加载函数，则重新索引
                    print(f"集合 {collection_name} 存在但为空，重新索引...")
                    self._index_functions()
                else:
                    print(f"已加载现有知识库集合: {collection_name}，包含 {count} 个文档")
            except:
                self.collection = self.vector_db.create_collection(name=collection_name)
                print(f"创建新知识库集合: {collection_name}")
                # 索引函数文档
                if len(self.functions) > 0:
                    self._index_functions()
            
            # 初始化嵌入模型
            if EMBEDDING_AVAILABLE:
                self.embedding_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
                print("嵌入模型已加载")
        except Exception as e:
            print(f"初始化向量数据库时出错: {e}")
            self.vector_db = None
    
    def _index_functions(self):
        """将函数文档索引到向量数据库"""
        if not self.collection or not self.functions:
            return
        
        print("开始索引奇遇API函数文档...")
        
        documents = []
        metadatas = []
        ids = []
        
        for idx, func in enumerate(self.functions):
            # 构建文档文本
            doc_text = f"""
模块: {func.module}
函数: {func.function_name}
签名: {func.signature}
说明: {func.description}
参数: {func.parameters}
返回值: {func.return_value}
示例: {func.example}
推荐用法: {func.recommended_usage}
标签: {', '.join(func.tags)}
"""
            documents.append(doc_text.strip())
            metadatas.append({
                "module": func.module,
                "function_name": func.function_name,
                "signature": func.signature,
                "category": func.module
            })
            ids.append(f"func_{idx}")
        
        # 批量添加
        if EMBEDDING_AVAILABLE and self.embedding_model:
            # 使用嵌入模型生成向量
            embeddings = self.embedding_model.encode(documents).tolist()
            self.collection.add(
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
        else:
            # 使用文本匹配
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
        
        print(f"已索引 {len(self.functions)} 个函数文档")
    
    def identify_required_modules(self, user_input: str, npc_tags: List[str] = None) -> List[str]:
        """
        识别用户需求中需要的功能模块
        返回模块列表，如 ["World", "UI", "Performer"]
        """
        modules = set()
        text = user_input.lower()
        
        # 根据关键词识别模块
        for keyword, module_list in self.FUNCTION_TO_MODULE.items():
            if keyword.lower() in text:
                modules.update(module_list)
        
        # 如果提到NPC，通常需要Performer和World
        if npc_tags or "npc" in text or "角色" in text:
            modules.add("Performer")
            modules.add("World")
        
        # 如果提到选择、对话，需要UI
        if any(kw in text for kw in ["选择", "对话", "询问", "选择", "ask", "dialogue"]):
            modules.add("UI")
        
        # 如果提到战斗、敌人，需要World
        if any(kw in text for kw in ["战斗", "敌人", "攻击", "combat", "enemy"]):
            modules.add("World")
        
        # 如果提到奖励，需要Performer
        if any(kw in text for kw in ["奖励", "物品", "装备", "reward", "item"]):
            modules.add("Performer")
        
        # 默认包含System（用于Exit）
        modules.add("System")
        
        return list(modules) if modules else ["World", "UI", "Performer", "System"]
    
    def retrieve_functions(self, modules: List[str] = None, query: str = "", top_k: int = 30) -> List[GameplayFunctionDoc]:
        """
        检索相关函数文档
        """
        if not self.functions:
            return []
        
        # 如果使用向量数据库
        if self.collection and EMBEDDING_AVAILABLE and self.embedding_model:
            try:
                # 生成查询向量
                query_embedding = self.embedding_model.encode([query]).tolist()[0]
                
                # 构建过滤条件
                where = None
                if modules:
                    where = {"module": {"$in": modules}}
                
                # 检索
                results = self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=min(top_k, len(self.functions)),
                    where=where
                )
                
                # 转换为函数文档
                retrieved_functions = []
                if results['ids'] and len(results['ids'][0]) > 0:
                    for idx_str in results['ids'][0]:
                        func_idx = int(idx_str.split('_')[1])
                        if func_idx < len(self.functions):
                            retrieved_functions.append(self.functions[func_idx])
                
                return retrieved_functions
            except Exception as e:
                print(f"向量检索出错，使用文本匹配: {e}")
        
        # 文本匹配回退
        return self._text_search(modules, query, top_k)
    
    def _text_search(self, modules: List[str] = None, query: str = "", top_k: int = 30) -> List[GameplayFunctionDoc]:
        """文本匹配搜索"""
        scored_functions = []
        query_lower = query.lower()
        
        for func in self.functions:
            # 模块过滤
            if modules and func.module not in modules:
                continue
            
            score = 0
            text = (func.function_name + " " + func.description + " " + func.signature).lower()
            
            # 关键词匹配
            for keyword in query_lower.split():
                if keyword in text:
                    score += 1
            
            if score > 0:
                scored_functions.append((score, func))
        
        # 按分数排序
        scored_functions.sort(key=lambda x: x[0], reverse=True)
        return [f for _, f in scored_functions[:top_k]]
    
    def get_function_docs_text(self, functions: List[GameplayFunctionDoc]) -> str:
        """将函数文档列表转换为文本格式（用于LLM提示词）"""
        if not functions:
            return "未找到相关API函数文档。"
        
        docs_text = ""
        current_module = None
        
        for func in functions:
            # 添加模块标题
            if func.module != current_module:
                docs_text += f"\n## {func.module} 模块\n"
                current_module = func.module
            
            docs_text += f"""
### {func.function_name}
签名: {func.signature}
说明: {func.description}
参数: {func.parameters}
返回值: {func.return_value}
示例:
{func.example}
推荐用法:
{func.recommended_usage}
"""
            if func.common_errors:
                docs_text += f"常见错误: {func.common_errors}\n"
        
        # 如果涉及Performer模块（包含PlayAnim），添加动画素材库信息
        has_performer = any(func.module == "Performer" for func in functions)
        has_playanim = any("PlayAnim" in func.function_name for func in functions)
        
        if has_performer or has_playanim:
            docs_text += "\n## 动画素材库（Animation Library）\n"
            docs_text += "**重要：PlayAnim必须使用以下动画名称，禁止使用素材库之外的动画名称**\n\n"
            docs_text += "### 基础动作\n"
            docs_text += "- Idle（待机）, Walk（行走）, Run（奔跑）\n\n"
            docs_text += "### 跳跃动作\n"
            docs_text += "- Jump_01（起跳_01）, Jump_02（凌空_02）, Jump_03（落地_03）\n\n"
            docs_text += "### 战斗动作\n"
            docs_text += "- Melee Attack_01/02/03（近战普攻）, Ranged Attack_01/02/03（远程普攻）\n\n"
            docs_text += "### 情绪动作\n"
            docs_text += "- Happy（开心）, Admiring（崇拜）, Shy（害羞）, Frustrated（沮丧）, Scared（恐惧）\n\n"
            docs_text += "### 交互动作\n"
            docs_text += "- Pick Up（拾取）, Hide（躲藏）, Eat（吃）, Drink（喝）, Sleep（睡）\n"
            docs_text += "- Sit（坐在椅子上）, Dialogue（说话）, Give（给予）, Point To（指向目标）\n"
            docs_text += "- Wave（挥手打招呼）, Sing（唱歌）, Dance（跳舞）\n\n"
            docs_text += "**常用动画推荐**：Wave（挥手）、Happy（开心）、Shy（害羞）、Scared（恐惧）、Drink（喝）、Sleep（睡）、Dialogue（说话）\n"
        
        # 如果涉及UI模块，添加玩家对话规则
        has_ui = any(func.module == "UI" for func in functions)
        has_dialogue = any("ShowDialogue" in func.function_name or "ApproachAndSay" in func.function_name for func in functions)
        
        if has_ui or has_dialogue:
            docs_text += "\n## 对话规则（Dialogue Rules）\n"
            docs_text += "**重要：玩家对话必须使用UI.ShowDialogue，不能使用ApproachAndSay**\n\n"
            docs_text += "- NPC说话：使用 `npc:ApproachAndSay(player, \"文本\")` 或 `UI.ShowDialogue(\"NPC名称\", \"文本\")`\n"
            docs_text += "- 玩家说话：**必须使用** `UI.ShowDialogue(\"Player\", \"文本\")` 或 `UI.ShowDialogue(\"角色名\", \"文本\")`\n"
            docs_text += "- **禁止**使用 `player:ApproachAndSay()`，玩家没有ApproachAndSay方法\n"
            docs_text += "- **对话内容格式**：所有对话内容直接使用引号包裹，**不要使用方括号**\n"
            docs_text += "  - 正确示例：`npcA:ApproachAndSay(player, \"你好\")`\n"
            docs_text += "  - 错误示例：`npcA:ApproachAndSay(player, \"[你好]\")`\n"
        
        return docs_text


# 全局知识库实例
_gameplay_kb_instance = None

def get_gameplay_knowledge_base() -> GameplayKnowledgeBase:
    """获取全局奇遇知识库实例（单例模式）"""
    global _gameplay_kb_instance
    if _gameplay_kb_instance is None:
        _gameplay_kb_instance = GameplayKnowledgeBase()
    return _gameplay_kb_instance
