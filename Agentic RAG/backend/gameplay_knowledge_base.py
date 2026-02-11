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
        self.functions: List[GameplayFunctionDoc] = []
        self.vector_db = None
        self.embedding_model = None
        self.collection = None
        
        # 加载知识库文档
        self._load_knowledge_base()
        
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
                print(f"已加载现有知识库集合: {collection_name}")
            except:
                self.collection = self.vector_db.create_collection(name=collection_name)
                print(f"创建新知识库集合: {collection_name}")
                # 索引函数文档
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
        
        return docs_text


# 全局知识库实例
_gameplay_kb_instance = None

def get_gameplay_knowledge_base() -> GameplayKnowledgeBase:
    """获取全局奇遇知识库实例（单例模式）"""
    global _gameplay_kb_instance
    if _gameplay_kb_instance is None:
        _gameplay_kb_instance = GameplayKnowledgeBase()
    return _gameplay_kb_instance
