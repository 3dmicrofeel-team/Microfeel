"""
奇遇（Encounter）RAG系统
实现4层工作流：故事扩写、玩法拆解、执行计划、Lua生成
"""

import os
import re
from typing import Dict, Any, List, Optional
from gameplay_knowledge_base import get_gameplay_knowledge_base, GameplayKnowledgeBase

# Few-Shot示例（基于用户提供的实际项目代码）
FEW_SHOT_EXAMPLE = """```lua
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
    alice:ApproachAndSay(player, "稍等片刻，旅行者。旅途的风景纵然美丽，但是如果没有人一起分享，总是感觉少了一些什么。")
    World.Wait(1.0)
    local choice = UI.Ask("你要怎么做？", "邀请同行", "我是钢铁直男")
    if choice == "邀请同行" then
        alice:PlayAnimLoop("Happy", 0)
        World.Wait(1)
        alice:ApproachAndSay(player, "太好了！让我们怀揣着满满的期待，携手踏上这段探索世界的旅程！")
        alice:SetAsCompanion()
        UI.Toast("Alice成为同伴")
    else
        alice:PlayAnimLoop("Frustrated", 0)
        World.Wait(1)
        alice:ApproachAndSay(player, "你这个大猪蹄子！你以为我想等你？某个无聊的策划必须让我跟着你！")
        alice:SetAsCompanion()
        UI.Toast("Alice成为同伴")
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
   - `System.Exit()` 结束脚本（可选，如果代码块内没有则不需要）
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

# 动画素材库（必须严格使用这些动画名称）
ANIMATION_LIBRARY = [
    "Idle", "Walk", "Run",
    "Jump_01", "Jump_02", "Jump_03",
    "Melee Attack_01", "Melee Attack_02", "Melee Attack_03",
    "Ranged Attack_01", "Ranged Attack_02", "Ranged Attack_03",
    "Happy", "Admiring", "Shy", "Frustrated", "Scared",
    "Pick Up", "Hide", "Eat", "Drink", "Sleep", "Sit",
    "Dialogue", "Give", "Point To", "Wave", "Sing", "Dance"
]


class EncounterRAGSystem:
    """
    奇遇RAG系统核心类
    实现4层工作流生成奇遇LUA脚本
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.model = config.get('model', 'gpt-4.1')
        self.agent_mode = config.get('agentMode', 'standard')
        self.max_iterations = config.get('maxIterations', 3)
        self.kb = get_gameplay_knowledge_base()
        
    def generate(self, user_input: str, npc_tags: List[str] = None) -> str:
        """
        主生成方法
        根据Agent模式选择不同的生成策略
        """
        if self.agent_mode == 'standard':
            return self._standard_generate(user_input, npc_tags)
        elif self.agent_mode == 'iterative':
            return self._iterative_generate(user_input, npc_tags)
        elif self.agent_mode == 'multi-agent':
            return self._multi_agent_generate(user_input, npc_tags)
        else:
            return self._standard_generate(user_input, npc_tags)
    
    def _standard_generate(self, user_input: str, npc_tags: List[str] = None) -> str:
        """
        标准模式：单次生成（集成RAG）
        实现Thinking-Planning-Action工作流
        支持两种输入方式：
        1. 结构化剧本格式（【触发】【移动】等标记）
        2. 自然语言输入（如"请生成一个爱情故事"）
        """
        # Thinking阶段：深度理解需求（自动检测输入类型）
        thinking_result = self._thinking_phase(user_input, npc_tags)
        
        # 检测输入类型
        structured_input = thinking_result.get("structured_input", {})
        is_structured = structured_input.get("is_structured", False)
        
        if is_structured:
            # 结构化输入模式：直接使用用户输入，跳过故事扩写和玩法拆解
            story = user_input  # 直接使用原始输入
            execution_plan = "按照用户提供的结构化剧本格式生成代码"  # 简化执行计划
        else:
            # 自然语言输入模式：使用完整的工作流
            story = self._expand_story(user_input, npc_tags, thinking_result)
            gameplay_nodes = self._decompose_gameplay(story, npc_tags, thinking_result)
            execution_plan = self._build_execution_plan(gameplay_nodes, npc_tags, thinking_result)
        
        # Action阶段：生成和验证代码（两种模式都使用相同的生成方法）
        lua_code = self._generate_lua_code(user_input, story, execution_plan, npc_tags, thinking_result)
        
        # 最终验证和修正
        lua_code = self._final_validation_and_fix(lua_code, user_input, npc_tags)
        
        return lua_code
    
    def _iterative_generate(self, user_input: str, npc_tags: List[str] = None) -> str:
        """
        迭代模式：多次优化（使用Thinking-Planning-Action）
        支持两种输入方式：结构化输入和自然语言输入
        """
        # Thinking阶段：深度理解需求（自动检测输入类型）
        thinking_result = self._thinking_phase(user_input, npc_tags)
        
        # 检测输入类型
        structured_input = thinking_result.get("structured_input", {})
        is_structured = structured_input.get("is_structured", False)
        
        if is_structured:
            # 结构化输入模式：直接使用用户输入
            story = user_input
            execution_plan = "按照用户提供的结构化剧本格式生成代码"
        else:
            # 自然语言输入模式：使用完整的工作流
            story = self._expand_story(user_input, npc_tags, thinking_result)
            gameplay_nodes = self._decompose_gameplay(story, npc_tags, thinking_result)
            execution_plan = self._build_execution_plan(gameplay_nodes, npc_tags, thinking_result)
        
        # Action阶段：生成代码
        current_code = self._generate_lua_code(user_input, story, execution_plan, npc_tags, thinking_result)
        
        # 迭代优化
        for iteration in range(self.max_iterations - 1):
            # 验证当前代码
            if self._validate_encounter_code(current_code) and self._validate_reference_format(current_code):
                break
            
            # 优化代码
            current_code = self._refine_code(user_input, current_code, npc_tags)
            # 修正代码问题
            current_code = self._fix_code_issues(current_code)
        
        # 最终验证和修正
        current_code = self._final_validation_and_fix(current_code, user_input, npc_tags)
        
        return current_code
    
    def _multi_agent_generate(self, user_input: str, npc_tags: List[str] = None) -> str:
        """
        多Agent协作模式（使用Thinking-Planning-Action）
        支持两种输入方式：结构化输入和自然语言输入
        """
        # Thinking阶段：深度理解需求（自动检测输入类型）
        thinking_result = self._thinking_phase(user_input, npc_tags)
        
        # 检测输入类型
        structured_input = thinking_result.get("structured_input", {})
        is_structured = structured_input.get("is_structured", False)
        
        if is_structured:
            # 结构化输入模式：直接使用用户输入
            story = user_input
            gameplay_nodes = []
            execution_plan = "按照用户提供的结构化剧本格式生成代码"
        else:
            # 自然语言输入模式：使用完整的工作流
            story = self._expand_story(user_input, npc_tags, thinking_result)
            gameplay_nodes = self._decompose_gameplay(story, npc_tags, thinking_result)
            execution_plan = self._build_execution_plan(gameplay_nodes, npc_tags, thinking_result)
        
        plan = {
            "story": story,
            "gameplay_nodes": gameplay_nodes,
            "execution_plan": execution_plan,
            "thinking_result": thinking_result
        }
        
        # Action阶段：代码生成
        code = self._code_generation_agent(user_input, plan, npc_tags)
        
        # 最终验证和修正
        code = self._final_validation_and_fix(code, user_input, npc_tags)
        
        return code
    
    def _parse_structured_input(self, user_input: str) -> Dict[str, Any]:
        """
        解析结构化的用户输入（剧本格式）
        识别【触发】、【移动】、【播放】、【气泡】、【选项】等标记
        """
        parsed = {
            "is_structured": False,
            "trigger": None,
            "actions": [],
            "npc_characters": set(),
            "dialogue_lines": [],
            "branches": [],
            "raw_text": user_input
        }
        
        # 检查是否包含结构化标记
        structured_markers = ['【触发】', '【移动】', '【播放】', '【气泡】', '【选项】', '【结束】', '【如果是', '【停止播放】']
        has_markers = any(marker in user_input for marker in structured_markers)
        
        if not has_markers:
            return parsed
        
        parsed["is_structured"] = True
        
        lines = user_input.split('\n')
        current_branch = None
        branch_stack = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 解析触发条件
            if line.startswith('【触发】'):
                trigger_text = line.replace('【触发】', '').strip()
                parsed["trigger"] = trigger_text
            
            # 解析移动指令
            elif line.startswith('【移动】'):
                move_text = line.replace('【移动】', '').strip()
                # 提取NPC名称和目标位置
                match = re.search(r'\[([^\]]+)\]\s*(.+)', move_text)
                if match:
                    npc_name = match.group(1)
                    target = match.group(2).strip()
                    parsed["npc_characters"].add(npc_name)
                    parsed["actions"].append({
                        "type": "move",
                        "npc": npc_name,
                        "target": target
                    })
            
            # 解析动画播放
            elif line.startswith('【播放】'):
                anim_text = line.replace('【播放】', '').strip()
                match = re.search(r'动画\s*\[([^\]]+)\]', anim_text)
                if match:
                    anim_name = match.group(1)
                    # 检查是否有NPC名称
                    npc_match = re.search(r'\[([^\]]+)\]_', anim_name)
                    npc_name = npc_match.group(1) if npc_match else None
                    if npc_name:
                        parsed["npc_characters"].add(npc_name)
                    parsed["actions"].append({
                        "type": "play_anim",
                        "npc": npc_name or "player",
                        "anim": anim_name
                    })
            
            # 解析停止动画
            elif line.startswith('【停止播放】'):
                anim_text = line.replace('【停止播放】', '').strip()
                match = re.search(r'动画\s*\[([^\]]+)\]', anim_text)
                if match:
                    anim_name = match.group(1)
                    npc_match = re.search(r'\[([^\]]+)\]_', anim_name)
                    npc_name = npc_match.group(1) if npc_match else None
                    if npc_name:
                        parsed["npc_characters"].add(npc_name)
                    parsed["actions"].append({
                        "type": "stop_anim",
                        "npc": npc_name or "player",
                        "anim": anim_name
                    })
            
            # 解析对话（气泡）
            elif line.startswith('【气泡】'):
                dialogue_text = line.replace('【气泡】', '').strip()
                match = re.search(r'\[([^\]]+)\]\s*说\s*"([^"]+)"', dialogue_text)
                if match:
                    speaker = match.group(1)
                    content = match.group(2)
                    parsed["npc_characters"].add(speaker)
                    parsed["dialogue_lines"].append({
                        "speaker": speaker,
                        "content": content,
                        "branch": current_branch
                    })
            
            # 解析选项
            elif line.startswith('【选项】'):
                option_text = line.replace('【选项】', '').strip()
                # 提取问题和选项
                match = re.search(r'(.+?)\[(.+)\]', option_text)
                if match:
                    question = match.group(1).strip()
                    options_str = match.group(2)
                    options = [opt.strip() for opt in options_str.split('/')]
                    parsed["actions"].append({
                        "type": "choice",
                        "question": question,
                        "options": options,
                        "branch": current_branch
                    })
            
            # 解析分支条件
            elif line.startswith('【如果是'):
                branch_text = line.replace('【如果是', '').replace('】', '').strip()
                current_branch = branch_text
                branch_stack.append(branch_text)
            
            # 解析结束
            elif line.startswith('【结束】'):
                if branch_stack:
                    branch_stack.pop()
                    current_branch = branch_stack[-1] if branch_stack else None
                else:
                    current_branch = None
        
        parsed["npc_characters"] = list(parsed["npc_characters"])
        return parsed
    
    def _thinking_phase(self, user_input: str, npc_tags: List[str] = None) -> Dict[str, Any]:
        """
        Thinking阶段：深度理解用户需求、约束和上下文
        分析需求的关键要素，识别必要的API和模式
        """
        # 首先解析结构化输入
        structured_input = self._parse_structured_input(user_input)
        
        # 检索相关函数文档以理解可用API
        modules = self.kb.identify_required_modules(user_input, npc_tags)
        relevant_functions = self.kb.retrieve_functions(
            modules=modules,
            query=user_input,
            top_k=30
        )
        function_docs = self.kb.get_function_docs_text(relevant_functions)
        reference_examples = self.kb.get_reference_examples()
        
        # 如果检测到结构化输入，使用专门的解析提示
        if structured_input["is_structured"]:
            prompt = f"""你是一个LUA代码分析专家。用户提供了一个结构化的剧本格式输入，请深度分析并理解所有细节。

用户的结构化输入：
{user_input}

解析结果：
- 触发条件：{structured_input.get('trigger', '无')}
- 角色列表：{', '.join(structured_input.get('npc_characters', []))}
- 动作数量：{len(structured_input.get('actions', []))}
- 对话数量：{len(structured_input.get('dialogue_lines', []))}

可用的API函数参考：
{function_docs}

参考文档示例（gameplay_document.md）：
{reference_examples}

**重要任务**：
1. 必须严格按照用户提供的结构化输入生成代码
2. 不能使用任何模板或默认场景
3. 必须实现用户指定的所有动作、对话、选项和分支
4. 必须严格遵循gameplay_document.md中的示例格式
5. 对话内容不能使用方括号（用户输入中的方括号是格式标记，不是对话内容）
6. 动画名称必须映射到素材库中的正确名称（如"Alice_开心"→"Happy"）
7. 玩家对话必须使用UI.ShowDialogue("Player", "内容")

请输出详细的分析，包括：
- 需要实现的每个动作步骤
- 所有对话内容（移除格式标记中的方括号）
- 所有选项分支
- 需要使用的NPC标签映射"""
        else:
            prompt = f"""你是一个LUA代码分析专家。请深度分析以下用户需求，理解所有约束和要求。

用户需求：
{user_input}

NPC标签：{', '.join(npc_tags) if npc_tags else 'Tag_A'}

可用的API函数参考：
{function_docs}

参考文档示例（gameplay_document.md）：
{reference_examples}

请进行深度分析，输出JSON格式：
{{
    "required_modules": ["模块列表"],
    "key_requirements": ["关键需求1", "关键需求2"],
    "constraints": ["约束1", "约束2"],
    "required_apis": ["必须使用的API列表"],
    "story_elements": {{
        "scene": "场景设定",
        "trigger": "触发原因",
        "player_action": "玩家介入点",
        "branches": ["分支1", "分支2"]
    }},
    "code_patterns": ["必须遵循的代码模式"],
    "potential_issues": ["潜在问题列表"]
}}

**重要**：
1. 必须严格遵循gameplay_document.md中的示例格式
2. 对话内容不能使用方括号
3. 动画名称必须来自素材库
4. 玩家对话必须使用UI.ShowDialogue
5. 所有API调用必须与参考文档示例一致"""
        
        thinking_text = self._call_llm_api(prompt)
        
        # 解析JSON（简化处理，实际应该使用json.loads）
        thinking_result = {
            "raw_analysis": thinking_text,
            "modules": modules,
            "function_docs": function_docs,
            "reference_examples": reference_examples,
            "structured_input": structured_input  # 添加结构化输入解析结果
        }
        
        return thinking_result
    
    def _expand_story(self, user_input: str, npc_tags: List[str] = None, thinking_result: Dict[str, Any] = None) -> str:
        """
        Layer 1: 故事扩写
        将用户需求扩写为完整的故事背景
        """
        structured_input = thinking_result.get("structured_input", {}) if thinking_result else {}
        
        # 如果检测到结构化输入，直接使用输入内容作为故事
        if structured_input.get("is_structured", False):
            # 对于结构化输入，我们不需要扩写，直接使用原始输入
            return user_input
        
        npc_count = len(npc_tags) if npc_tags else 1
        npc_list_text = ", ".join(npc_tags) if npc_tags else "Tag_A"
        
        prompt = f"""你是一个游戏剧情设计师。请将以下用户需求扩写为一个完整的、可演出的短故事。

用户需求：
{user_input}

NPC数量：{npc_count}个
NPC标签：{npc_list_text}

请扩写一个150-250字的故事，必须包含：
1. 场景设定（酒馆/街道/教堂/商店等）
2. 触发原因（误会、偷窃、争吵、请求帮助等）
3. 玩家介入点（对话/选择/行动）
4. 至少1个结果分支

**输出要求**：只输出故事文本，不要包含"故事："、"背景："等标题，不要包含其他说明文字。"""
        
        story = self._call_llm_api(prompt)
        return story.strip()
    
    def _decompose_gameplay(self, story: str, npc_tags: List[str] = None, thinking_result: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Layer 2: 玩法拆解
        将故事拆解为可执行的动作节点
        注意：如果输入是结构化格式，此方法不会被调用
        """
        # 检查是否是结构化输入（理论上不应该到达这里，但做安全检查）
        structured_input = thinking_result.get("structured_input", {}) if thinking_result else {}
        if structured_input.get("is_structured", False):
            # 如果是结构化输入，返回空列表（因为不需要拆解）
            return []
        
        # 识别需要的功能模块
        modules = self.kb.identify_required_modules(story, npc_tags)
        
        # 检索相关函数文档
        relevant_functions = self.kb.retrieve_functions(
            modules=modules,
            query=story,
            top_k=40
        )
        
        function_docs = self.kb.get_function_docs_text(relevant_functions)
        
        # 使用thinking_result
        thinking_analysis = thinking_result.get("raw_analysis", "") if thinking_result else ""
        reference_examples = thinking_result.get("reference_examples", "") if thinking_result else self.kb.get_reference_examples()
        
        # 构建动画素材库文本
        animations_text = "\n".join([f"- {anim}" for anim in ANIMATION_LIBRARY])
        
        prompt = f"""你是一个游戏玩法设计师。请将以下故事拆解为6-12个可执行的动作节点。

深度需求分析：
{thinking_analysis}

参考文档示例（gameplay_document.md）：
{reference_examples}

故事：
{story}

NPC标签：{', '.join(npc_tags) if npc_tags else 'Tag_A'}

可用的API函数参考：
{function_docs}

**动画素材库（PlayAnim必须使用以下动画名称）**：
{animations_text}

每个动作节点必须对应一个API调用，例如：
- NPC移动到指定位置
- NPC面向玩家
- NPC播放动画（动画名称必须来自素材库）
- NPC说话：使用npc:ApproachAndSay(player, "文本")或UI.ShowDialogue("NPC名称", "文本")，**对话内容不要使用方括号**
- 玩家说话：**必须使用**UI.ShowDialogue("Player", "文本")，**对话内容不要使用方括号**
- UI Ask/AskMany让玩家选择
- 根据选择进入不同剧情路径
- 结束后清理（Destroy/Exit）

请以JSON格式返回动作节点列表，每个节点包含：
- action: 动作类型（如 "MoveTo", "ShowDialogue", "AskMany"）
- target: 目标对象（如 "Tag_A", "Player"）
- params: 参数说明
- description: 动作描述"""
        
        response = self._call_llm_api(prompt)
        # 简化处理：返回文本，后续解析
        return [{"description": response}]  # 实际应该解析JSON
    
    def _build_execution_plan(self, gameplay_nodes: List[Dict[str, Any]], npc_tags: List[str] = None, thinking_result: Dict[str, Any] = None) -> str:
        """
        Layer 3: 执行计划
        将玩法拆解转化为脚本步骤链
        注意：如果输入是结构化格式，此方法不会被调用
        """
        # 检查是否是结构化输入（理论上不应该到达这里，但做安全检查）
        structured_input = thinking_result.get("structured_input", {}) if thinking_result else {}
        if structured_input.get("is_structured", False):
            # 如果是结构化输入，返回简化的执行计划
            return "按照用户提供的结构化剧本格式生成代码"
        
        # 使用thinking_result
        thinking_analysis = thinking_result.get("raw_analysis", "") if thinking_result else ""
        reference_examples = thinking_result.get("reference_examples", "") if thinking_result else self.kb.get_reference_examples()
        
        # 构建动画素材库文本
        animations_text = "\n".join([f"- {anim}" for anim in ANIMATION_LIBRARY])
        
        prompt = f"""你是一个LUA脚本工程师。请将以下动作节点转化为详细的执行计划。

深度需求分析：
{thinking_analysis}

参考文档示例（gameplay_document.md）：
{reference_examples}

动作节点：
{gameplay_nodes}

NPC标签：{', '.join(npc_tags) if npc_tags else 'Tag_A'}

**动画素材库（PlayAnim必须使用以下动画名称）**：
{animations_text}

请制定执行计划，包括：
1. 获取player与NPC actor（使用World.GetByID）
2. 判空检查（IsValid）
3. 计算encounter中心点与站位点（基于玩家位置）
4. NPC移动、朝向、动画（MoveTo/LookAt/PlayAnim，动画名称必须来自素材库）
5. UI对话和选择：
   - NPC说话：使用npc:ApproachAndSay(player, "文本")或UI.ShowDialogue("NPC名称", "文本")
   - 玩家说话：**必须使用**UI.ShowDialogue("Player", "文本")
   - **重要**：所有对话内容直接使用引号包裹，不要使用方括号。正确：`"你好"`，错误：`"[你好]"`
6. 分支逻辑执行
7. 可选：生成敌人/播放FX/播放音效
8. 结束奇遇（System.Exit）

请输出详细的执行步骤。"""
        
        plan = self._call_llm_api(prompt)
        return plan.strip()
    
    def _generate_lua_code(self, user_input: str, story: str, execution_plan: str, npc_tags: List[str] = None, thinking_result: Dict[str, Any] = None) -> str:
        """
        Layer 4: Lua代码生成
        生成最终的World.SpawnEncounter代码
        """
        # 构建NPC映射（确保至少有一个NPC，语法必须正确）
        if not npc_tags:
            npc_tags = ["Tag_A"]
        
        # 如果检测到结构化输入，尝试从输入中提取NPC
        structured_input = thinking_result.get("structured_input", {}) if thinking_result else {}
        if structured_input.get("is_structured", False):
            npc_characters = structured_input.get("npc_characters", [])
            # 过滤掉"玩家"和"Player"
            npc_characters = [c for c in npc_characters if c not in ["玩家", "Player"]]
            # 如果提取到NPC角色，使用它们；否则使用默认标签
            if npc_characters and len(npc_characters) <= len(npc_tags):
                # 使用提取到的NPC角色
                pass  # 继续使用npc_tags
            elif npc_characters:
                # 如果NPC角色数量超过标签数量，使用默认标签
                npc_tags = ["Tag_A"] + [f"Tag_{chr(66+i)}" for i in range(min(len(npc_characters)-1, 3))]
        
        npc_map = "{\n"
        for tag in npc_tags:
            npc_map += f'        ["{tag}"] = "NPC_Base",\n'
        npc_map = npc_map.rstrip(",\n") + "\n    }"
        
        # 检索相关函数文档
        modules = self.kb.identify_required_modules(user_input + " " + story, npc_tags)
        relevant_functions = self.kb.retrieve_functions(
            modules=modules,
            query=user_input + " " + story,
            top_k=50
        )
        function_docs = self.kb.get_function_docs_text(relevant_functions)
        
        # 获取参考文档中的示例代码（gameplay_document.md）
        reference_examples = self.kb.get_reference_examples()
        
        # 构建动画素材库文本
        animations_text = "\n".join([f"- {anim}" for anim in ANIMATION_LIBRARY])
        
        # 从thinking_result获取深度分析
        thinking_analysis = thinking_result.get("raw_analysis", "") if thinking_result else ""
        reference_examples = thinking_result.get("reference_examples", reference_examples) if thinking_result else reference_examples
        structured_input = thinking_result.get("structured_input", {}) if thinking_result else {}
        
        # 如果检测到结构化输入，使用专门的生成提示
        is_structured = structured_input.get("is_structured", False)
        
        if is_structured:
            # 构建NPC映射（从用户输入的角色名到Tag）
            npc_characters = structured_input.get('npc_characters', [])
            npc_mapping = {}
            if npc_tags:
                for i, char in enumerate(npc_characters):
                    if i < len(npc_tags) and char != "玩家" and char != "Player":
                        npc_mapping[char] = npc_tags[i]
            
            # 构建结构化输入的详细描述
            structured_desc = f"""
**用户提供了结构化的剧本格式输入，必须严格按照此输入生成代码**

触发条件：{structured_input.get('trigger', '无')}
角色列表：{', '.join(npc_characters)}
NPC映射：{npc_mapping}

动作序列：
"""
            for i, action in enumerate(structured_input.get('actions', []), 1):
                structured_desc += f"{i}. {action}\n"
            
            structured_desc += "\n对话内容：\n"
            for i, dialogue in enumerate(structured_input.get('dialogue_lines', []), 1):
                structured_desc += f"{i}. {dialogue['speaker']}: {dialogue['content']}\n"
            
            prompt = f"""你是一个LUA代码生成专家。用户提供了详细的结构化剧本输入，你必须严格按照此输入生成代码。

**绝对禁止使用任何模板或默认场景！必须完全按照用户输入生成！**

用户的结构化输入（原始）：
{user_input}

结构化输入解析：
{structured_desc}

参考文档示例（gameplay_document.md）：
{reference_examples}

**Few-Shot完整示例（必须严格遵循此格式）**：
{FEW_SHOT_EXAMPLE}

可用的API函数参考：
{function_docs}

**动画素材库（PlayAnim必须使用以下动画名称）**：
{animations_text}

**关键要求（优先级从高到低）**：

**优先级1：语法正确性（最高优先级，必须严格遵守）**：
1. **必须遵循Few-Shot示例的完整格式**：
   - 定义 `local function ResolveEncounterLoc()` 返回位置坐标
   - 使用 `function SpawnEncounter_XXX()` 格式包装
   - 使用 `local npcData = {{ enc0_XXX = "Default" }}` 格式
   - 使用 `local code = [[ ... ]]` 格式
   - 代码块内必须包含 `if _G.enc0_done then return end` 和 `_G.enc0_done = true`
   - 最后调用 `SpawnEncounter_XXX()`
   - 最后包含 `World.StartGame()`, `Time.Resume()`, `UI.Toast("游戏开始")`
2. World.SpawnEncounter的5个参数必须完全正确：
   - 第1个参数：`ResolveEncounterLoc()` 返回的位置坐标
   - 第2个参数：范围，必须是数字（如100.0或300.0），不能是字符串或其他类型，不能太小（至少100）
   - 第3个参数：`npcData` 变量（必须是Lua字典格式，至少包含一个NPC，不能是空字典）
   - 第4个参数：类型，固定为 "EnterVolume"（字符串）
   - 第5个参数：`code` 变量（代码块，使用 [[ ... ]] 格式）
3. 代码块内必须包含：
   - `if _G.enc0_done then return end` 和 `_G.enc0_done = true`（防止重复触发）
   - `World.GetByID("Player")` 和 `World.GetByID("enc0_XXX")` 获取对象
   - `IsValid()` 判空检查（必须检查所有对象）
   - `World.Wait()` 控制节奏（每个动作后）
4. 如果用户输入无法实现，必须合理转换或跳过，但语法必须正确
5. 如果用户要求"玩家进入 [唱歌台旁5米范围内]"，range参数应该使用合理的数值（如100.0或300.0），不要使用5
6. npcData字典不能为空，至少需要一个NPC映射（如 {{ enc0_Alice = "Default" }}）
7. 代码块内不能有注释（`--`），否则引擎报错

**优先级2：尽量满足用户需求**：
5. **尽量**按照用户的结构化输入生成代码，但如果无法实现，可以合理转换
6. **尽量**实现用户指定的动作、对话、选项和分支
7. NPC标签映射：
   {npc_mapping}
   例如：Alice → Tag_A, 路人1 → Tag_B（如果存在）
8. 动画名称映射规则（必须映射到素材库）：
   - "Alice_开心" → "Happy"
   - "Alice_跳舞" → "Dance"  
   - "玩家_跳舞" → "Dance"
   - "Alice_沮丧" → "Frustrated"
9. 对话内容格式：用户输入中的方括号是格式标记，实际对话内容要去掉这些标记
   例如：【气泡】[Alice] 说 "[啊啊啊！！这是我最喜欢的歌！！！]"
   应该生成：npcAlice:ApproachAndSay(player, "啊啊啊！！这是我最喜欢的歌！！！")
   注意：对话内容中的方括号是格式标记，实际生成时要去掉
10. 玩家对话必须使用：UI.ShowDialogue("Player", "内容")
11. 选项使用：UI.AskMany("问题", {{"选项1", "选项2", "选项3"}})
12. 移动指令：【移动】[Alice] 跑向 唱歌台 → npcAlice:MoveToActor(player) 或 npcAlice:MoveTo(position)
13. 停止动画：【停止播放】动画 [Alice_跳舞] → 不需要特殊API，直接继续下一个动作
14. 必须严格遵循gameplay_document.md中的API调用格式
15. 尽量包含所有分支逻辑，使用if/elseif/else实现
16. 每个对话后要添加World.Wait()控制节奏
17. 结尾必须System.Exit()

**重要转换规则（语法正确性优先）**：
- 如果用户要求"玩家进入 [唱歌台旁5米范围内]"，range参数使用450（标准值），不要使用5
- 如果用户没有指定NPC，至少添加一个默认NPC：{{["Tag_A"] = "NPC_Base"}}
- 如果用户的要求无法用LUA实现，跳过该要求，但确保代码语法正确
- 如果用户的要求会导致语法错误，必须转换或跳过，优先保证语法正确
- 如果无法实现用户的某些要求，可以简化实现，但语法必须完全正确

**输出格式（语法必须完全正确，必须遵循Few-Shot示例格式）**：
local function ResolveEncounterLoc()
    return {{ X = 12016.593860, Y = 13372.975811, Z = 4797.613441 }}
end

function SpawnEncounter_XXX()
    local npcData = {{
        enc0_Alice = "Default"
    }}

    local code = [[
if _G.enc0_done then return end
_G.enc0_done = true

local player = World.GetByID("Player")
local alice = World.GetByID("enc0_Alice")

if not player or not player:IsValid() then return end
if not alice or not alice:IsValid() then return end

-- 严格按照用户输入生成的代码（如果无法实现则合理转换）
]]

    local loc = ResolveEncounterLoc()
    return World.SpawnEncounter(loc, 100.0, npcData, "EnterVolume", code)
end

SpawnEncounter_XXX()

World.StartGame()
Time.Resume()
UI.Toast("游戏开始")
"""
        else:
            prompt = f"""你是一个LUA代码生成专家。请根据以下信息生成完整的World.SpawnEncounter代码。

**重要：必须严格遵循 gameplay_document.md 中的示例格式和写法**

参考文档示例（gameplay_document.md）：
{reference_examples}

**Few-Shot完整示例（必须严格遵循此格式）**：
{FEW_SHOT_EXAMPLE}

深度需求分析：
{thinking_analysis}

用户需求：
{user_input}

故事背景：
{story}

执行计划：
{execution_plan}

NPC映射：
{npc_map}

可用的API函数参考：
{function_docs}

**动画素材库（PlayAnim必须使用以下动画名称）**：
{animations_text}

**重要约束（必须严格遵守Few-Shot示例格式）**：
1. 输出格式必须严格遵循Few-Shot示例：
local function ResolveEncounterLoc()
    return {{ X = 12016.593860, Y = 13372.975811, Z = 4797.613441 }}
end

function SpawnEncounter_XXX()
    local npcData = {{
        enc0_Alice = "Default"
    }}

    local code = [[
if _G.enc0_done then return end
_G.enc0_done = true

local player = World.GetByID("Player")
local alice = World.GetByID("enc0_Alice")

if not player or not player:IsValid() then return end
if not alice or not alice:IsValid() then return end

-- 你的代码逻辑
]]

    local loc = ResolveEncounterLoc()
    return World.SpawnEncounter(loc, 100.0, npcData, "EnterVolume", code)
end

SpawnEncounter_XXX()

World.StartGame()
Time.Resume()
UI.Toast("游戏开始")

2. 必须定义 `ResolveEncounterLoc()` 函数返回位置坐标
3. 必须使用 `function SpawnEncounter_XXX()` 格式包装
4. NPC映射使用 `local npcData = {{ enc0_XXX = "Default" }}` 格式
5. 代码块使用 `local code = [[ ... ]]` 格式
6. 代码块内必须包含 `if _G.enc0_done then return end` 和 `_G.enc0_done = true`
7. 代码块内禁止使用 -- 注释，否则引擎报错
8. 所有对象必须先判空 IsValid()（必须检查所有World.GetByID获取的对象）
9. 尽量包含至少2个分支（使用UI.AskMany或UI.Ask），但如果用户需求简单可以只有一个分支
10. 必须使用World.Wait控制节奏（每个动作、对话后）
11. 最后必须调用 `SpawnEncounter_XXX()`
12. 最后必须包含 `World.StartGame()`, `Time.Resume()`, `UI.Toast("游戏开始")`
13. World.SpawnEncounter的第1个参数使用 `ResolveEncounterLoc()` 返回的位置
14. World.SpawnEncounter的第2个参数：范围数字（如100.0或300.0），必须是数字且>=100
15. World.SpawnEncounter的第3个参数使用 `npcData` 变量
16. World.SpawnEncounter的第4个参数固定为 `"EnterVolume"`
17. World.SpawnEncounter的第5个参数使用 `code` 变量
18. npcData不能为空字典，至少需要一个NPC

**关键规则（必须严格遵守）**：
10. **严格遵循参考文档格式**：
    - **必须**完全按照 gameplay_document.md 中的示例格式编写代码
    - 所有API调用必须与参考文档中的示例格式一致
    - 参考文档中的示例是唯一正确的写法，必须严格遵循

11. **玩家对话规则**：
    - NPC说话：使用 npc:ApproachAndSay(player, "文本") 或 UI.ShowDialogue("NPC名称", "文本")
    - 玩家说话：**必须使用** UI.ShowDialogue("Player", "文本") 或 UI.ShowDialogue("角色名", "文本")
    - **禁止**使用 player:ApproachAndSay()，玩家没有ApproachAndSay方法
    - **对话内容格式**：对话内容直接使用引号包裹的字符串，**不要使用方括号**。正确示例：`npcA:ApproachAndSay(player, "你好")`，错误示例：`npcA:ApproachAndSay(player, "[你好]")`

12. **动画名称规则**：
    - PlayAnim的动画名称**必须**来自动画素材库
    - 禁止使用素材库之外的动画名称（如"Alice_Wave"、"Angry"等）
    - 常用动画：Wave（挥手）、Happy（开心）、Shy（害羞）、Scared（恐惧）、Drink（喝）、Sleep（睡）、Dialogue（说话）

13. **字符串格式规则**：
    - 所有对话内容、文本参数必须直接使用引号包裹，格式为 `"文本内容"`
    - **禁止**在字符串内容外添加方括号，如 `"[文本内容]"` 是错误的
    - 正确示例：`UI.ShowDialogue("NPC", "你好，需要帮助吗？")`
    - 错误示例：`UI.ShowDialogue("NPC", "[你好，需要帮助吗？]")`

**输出要求（严格遵循Few-Shot示例格式）**：
- 只输出完整的Encounter代码，不要任何解释、说明、注释或其他文字
- 不要包含"```lua"或"```"代码块标记
- 不要包含"优化说明"、"代码说明"、"基于用户需求"等任何说明文字
- 不要包含"###"、"##"等Markdown标题
- 直接输出代码，从 `local function ResolveEncounterLoc()` 开始，到 `UI.Toast("游戏开始")` 结束
- 输出格式必须完全遵循Few-Shot示例：
local function ResolveEncounterLoc()
    return {{ X = 12016.593860, Y = 13372.975811, Z = 4797.613441 }}
end

function SpawnEncounter_XXX()
    local npcData = {{
        enc0_Alice = "Default"
    }}

    local code = [[
if _G.enc0_done then return end
_G.enc0_done = true

local player = World.GetByID("Player")
local alice = World.GetByID("enc0_Alice")

if not player or not player:IsValid() then return end
if not alice or not alice:IsValid() then return end

-- 你的代码逻辑
]]

    local loc = ResolveEncounterLoc()
    return World.SpawnEncounter(loc, 100.0, npcData, "EnterVolume", code)
end

SpawnEncounter_XXX()

World.StartGame()
Time.Resume()
UI.Toast("游戏开始")"""
        
        lua_code = self._call_llm_api(prompt)
        
        # 提取纯LUA代码（移除可能的说明文字）
        lua_code = self._extract_lua_code(lua_code)
        
        # 清理代码：移除注释
        lua_code = self._remove_comments(lua_code)
        
        # 优先级1：修正语法错误（最高优先级）
        lua_code = self._fix_syntax_errors(lua_code, npc_tags)
        
        # 优先级2：修正其他代码问题（玩家对话、动画名称等）
        lua_code = self._fix_code_issues(lua_code)
        
        return lua_code.strip()
    
    def _extract_lua_code(self, response: str) -> str:
        """
        从LLM响应中提取纯LUA代码
        移除可能的说明文字、代码块标记等
        """
        # 移除代码块标记
        response = response.replace('```lua', '').replace('```', '').strip()
        
        # 移除常见的说明文字前缀
        prefixes_to_remove = [
            '基于用户需求，',
            '我们将优化',
            '优化说明：',
            '代码说明：',
            '以下是优化后的代码：',
            '生成的代码：',
        ]
        for prefix in prefixes_to_remove:
            if response.startswith(prefix):
                response = response[len(prefix):].strip()
        
        # 优先查找完整的Encounter格式（包含ResolveEncounterLoc函数）
        resolve_loc_marker = 'local function ResolveEncounterLoc()'
        spawn_func_marker = 'function SpawnEncounter_'
        
        if resolve_loc_marker in response or spawn_func_marker in response:
            # 找到ResolveEncounterLoc的开始位置
            if resolve_loc_marker in response:
                start_idx = response.find(resolve_loc_marker)
            elif spawn_func_marker in response:
                start_idx = response.find(spawn_func_marker)
            else:
                start_idx = 0
            
            code = response[start_idx:]
            
            # 查找结束位置：UI.Toast("游戏开始")
            end_marker = 'UI.Toast("游戏开始")'
            end_idx = code.find(end_marker)
            if end_idx != -1:
                code = code[:end_idx + len(end_marker)]
            else:
                # 如果没有找到结束标记，查找World.StartGame()
                end_marker2 = 'World.StartGame()'
                end_idx2 = code.find(end_marker2)
                if end_idx2 != -1:
                    # 查找World.StartGame()之后的Time.Resume()和UI.Toast
                    remaining = code[end_idx2:]
                    toast_idx = remaining.find('UI.Toast')
                    if toast_idx != -1:
                        # 找到UI.Toast的结束位置
                        toast_end = remaining.find('\n', toast_idx)
                        if toast_end == -1:
                            toast_end = len(remaining)
                        code = code[:end_idx2 + toast_end]
                    else:
                        code = code[:end_idx2 + len(end_marker2)]
            
            # 移除可能的后续说明文字
            stop_markers = [
                '\n###',
                '\n##',
                '\n**优化说明',
                '\n**代码说明',
                '\n优化说明',
                '\n代码说明',
                '\n注意：',
                '\n说明：',
                '\n这个脚本',
                '\n脚本',
                '\n基于用户需求',
                '\n我们将优化',
                '\n### 优化说明',
                '\n## 优化说明',
            ]
            
            for marker in stop_markers:
                marker_idx = code.find(marker)
                if marker_idx != -1:
                    code = code[:marker_idx]
                    break
            
            return code.strip()
        
        # 如果没有找到完整格式，回退到查找World.SpawnEncounter
        start_marker = 'World.SpawnEncounter'
        start_idx = response.find(start_marker)
        
        if start_idx == -1:
            # 如果没有找到，返回原响应
            return response
        
        # 从World.SpawnEncounter开始提取
        code = response[start_idx:]
        
        # 查找最后一个)的位置（World.SpawnEncounter的结束）
        # 需要匹配括号，找到最外层的)
        paren_count = 0
        last_paren_idx = -1
        
        for i, char in enumerate(code):
            if char == '(':
                paren_count += 1
            elif char == ')':
                paren_count -= 1
                if paren_count == 0:
                    last_paren_idx = i
                    break
        
        if last_paren_idx != -1:
            code = code[:last_paren_idx + 1]
        else:
            # 如果没找到匹配的)，尝试找到最后一个)
            last_paren_idx = code.rfind(')')
            if last_paren_idx != -1:
                code = code[:last_paren_idx + 1]
        
        # 移除可能的后续说明文字
        # 查找常见的说明文字标记
        stop_markers = [
            '\n###',
            '\n##',
            '\n**优化说明',
            '\n**代码说明',
            '\n优化说明',
            '\n代码说明',
            '\n注意：',
            '\n说明：',
            '\n这个脚本',
            '\n脚本',
            '\n基于用户需求',
            '\n我们将优化',
            '\n### 优化说明',
            '\n## 优化说明',
        ]
        
        for marker in stop_markers:
            marker_idx = code.find(marker)
            if marker_idx != -1:
                code = code[:marker_idx]
                break
        
        # 移除末尾可能的空白和换行
        code = code.rstrip()
        
        # 确保以)结尾
        if not code.endswith(')'):
            # 查找最后一个)
            last_paren = code.rfind(')')
            if last_paren != -1:
                code = code[:last_paren + 1]
        
        return code.strip()
    
    def _remove_comments(self, code: str) -> str:
        """移除Lua代码中的注释"""
        lines = code.split('\n')
        cleaned_lines = []
        in_multiline = False
        
        for line in lines:
            # 处理多行注释
            if '--[[' in line:
                in_multiline = True
                continue
            if ']]' in line and in_multiline:
                in_multiline = False
                continue
            if in_multiline:
                continue
            
            # 移除单行注释
            if '--' in line:
                # 检查是否是字符串中的--
                comment_pos = line.find('--')
                if comment_pos > 0:
                    # 检查前面是否有未闭合的字符串
                    before_comment = line[:comment_pos]
                    single_quotes = before_comment.count("'") - before_comment.count("\\'")
                    double_quotes = before_comment.count('"') - before_comment.count('\\"')
                    if single_quotes % 2 == 0 and double_quotes % 2 == 0:
                        line = line[:comment_pos].rstrip()
            
            cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def _fix_code_issues(self, code: str) -> str:
        """
        修正代码问题：
        1. 将玩家对话从ApproachAndSay改为UI.ShowDialogue
        2. 修正动画名称，确保使用素材库中的名称
        3. 移除对话内容中的方括号（如 "[文本]" -> "文本"）
        """
        lines = code.split('\n')
        fixed_lines = []
        
        for line in lines:
            # 修正玩家对话：player:ApproachAndSay -> UI.ShowDialogue
            # 匹配模式：player:ApproachAndSay(...) 或 player:ApproachAndSay(...)
            player_approach_pattern = r'player:ApproachAndSay\s*\(([^)]+)\)'
            match = re.search(player_approach_pattern, line)
            if match:
                # 提取参数
                params = match.group(1)
                # 解析参数（假设格式为：npc, "text"）
                params_parts = [p.strip().strip('"\'') for p in params.split(',')]
                if len(params_parts) >= 2:
                    # 转换为UI.ShowDialogue("Player", "text")
                    text = params_parts[-1].strip('"\'')
                    new_line = re.sub(
                        player_approach_pattern,
                        f'UI.ShowDialogue("Player", "{text}")',
                        line
                    )
                    line = new_line
            
            # 修正对话内容中的方括号：移除字符串中的方括号
            # 匹配模式：ApproachAndSay(..., "[文本]") 或 ShowDialogue("名称", "[文本]")
            # 处理 ApproachAndSay - 匹配第二个参数中的方括号
            approach_pattern = r'(ApproachAndSay\s*\([^,]+,\s*)"\[([^\]]+)\]"'
            line = re.sub(approach_pattern, r'\1"\2"', line)
            
            # 处理 ShowDialogue - 匹配第二个参数中的方括号
            showdialogue_pattern = r'(ShowDialogue\s*\([^,]+,\s*)"\[([^\]]+)\]"'
            line = re.sub(showdialogue_pattern, r'\1"\2"', line)
            
            # 处理更复杂的情况：可能有多层引号或嵌套
            # 匹配任何函数调用中第二个字符串参数的方括号
            # 通用模式：函数名(参数1, "[文本]")
            general_bracket_pattern = r'(\w+\([^,]+,\s*)"\[([^\]]+)\]"'
            line = re.sub(general_bracket_pattern, r'\1"\2"', line)
            
            # 处理变量名的情况（如 alice:ApproachAndSay）
            variable_approach_pattern = r'(\w+:\s*ApproachAndSay\s*\([^,]+,\s*)"\[([^\]]+)\]"'
            line = re.sub(variable_approach_pattern, r'\1"\2"', line)
            
            # 修正动画名称：检查PlayAnim中的动画名称是否在素材库中
            playanim_pattern = r'PlayAnim\s*\(\s*"([^"]+)"\s*\)'
            anim_match = re.search(playanim_pattern, line)
            if anim_match:
                anim_name = anim_match.group(1)
                # 检查是否在素材库中
                if anim_name not in ANIMATION_LIBRARY:
                    # 尝试映射常见错误
                    anim_mapping = {
                        "Alice_Wave": "Wave",
                        "Boss_Happy": "Happy",
                        "Alice_Angry": "Frustrated",
                        "Alice_Drink": "Drink",
                        "Alice_Stun": "Scared",
                        "Alice_Sleep": "Sleep",
                        "Alice_Shy": "Shy",
                        "Uncle_Happy": "Happy",
                        "Angry": "Frustrated",
                        "Sad": "Frustrated",
                        "Cry": "Frustrated",
                    }
                    
                    # 尝试直接匹配（移除前缀）
                    for wrong_anim, correct_anim in anim_mapping.items():
                        if wrong_anim in anim_name or anim_name.endswith(wrong_anim.split('_')[-1]):
                            line = line.replace(f'"{anim_name}"', f'"{correct_anim}"')
                            break
                    else:
                        # 如果无法映射，尝试从名称中提取关键词
                        anim_lower = anim_name.lower()
                        if 'wave' in anim_lower or '挥手' in anim_lower:
                            line = line.replace(f'"{anim_name}"', '"Wave"')
                        elif 'happy' in anim_lower or '开心' in anim_lower:
                            line = line.replace(f'"{anim_name}"', '"Happy"')
                        elif 'shy' in anim_lower or '害羞' in anim_lower:
                            line = line.replace(f'"{anim_name}"', '"Shy"')
                        elif 'scared' in anim_lower or '恐惧' in anim_lower or 'stun' in anim_lower:
                            line = line.replace(f'"{anim_name}"', '"Scared"')
                        elif 'drink' in anim_lower or '喝' in anim_lower:
                            line = line.replace(f'"{anim_name}"', '"Drink"')
                        elif 'sleep' in anim_lower or '睡' in anim_lower:
                            line = line.replace(f'"{anim_name}"', '"Sleep"')
                        elif 'frustrated' in anim_lower or 'angry' in anim_lower or '沮丧' in anim_lower or '生气' in anim_lower:
                            line = line.replace(f'"{anim_name}"', '"Frustrated"')
                        elif 'dialogue' in anim_lower or '说话' in anim_lower:
                            line = line.replace(f'"{anim_name}"', '"Dialogue"')
            
            fixed_lines.append(line)
        
        return '\n'.join(fixed_lines)
    
    def _planning_agent(self, user_input: str, npc_tags: List[str] = None) -> Dict[str, Any]:
        """规划Agent：分析需求，制定生成计划（已废弃，使用_standard_generate）"""
        # Thinking阶段
        thinking_result = self._thinking_phase(user_input, npc_tags)
        
        # Planning阶段
        story = self._expand_story(user_input, npc_tags, thinking_result)
        gameplay_nodes = self._decompose_gameplay(story, npc_tags, thinking_result)
        execution_plan = self._build_execution_plan(gameplay_nodes, npc_tags, thinking_result)
        
        return {
            "story": story,
            "gameplay_nodes": gameplay_nodes,
            "execution_plan": execution_plan,
            "thinking_result": thinking_result
        }
    
    def _code_generation_agent(self, user_input: str, plan: Dict[str, Any], npc_tags: List[str] = None) -> str:
        """代码生成Agent：根据计划生成Lua代码"""
        thinking_result = plan.get("thinking_result", {})
        return self._generate_lua_code(
            user_input,
            plan.get("story", ""),
            plan.get("execution_plan", ""),
            npc_tags,
            thinking_result
        )
    
    def _refine_code(self, user_input: str, current_code: str, npc_tags: List[str] = None) -> str:
        """优化代码"""
        modules = self.kb.identify_required_modules(user_input, npc_tags)
        relevant_functions = self.kb.retrieve_functions(
            modules=modules,
            query=user_input,
            top_k=30
        )
        function_docs = self.kb.get_function_docs_text(relevant_functions)
        
        # 获取参考文档中的示例代码（gameplay_document.md）
        reference_examples = self.kb.get_reference_examples()
        
        # 构建动画素材库文本
        animations_text = "\n".join([f"- {anim}" for anim in ANIMATION_LIBRARY])
        
        prompt = f"""优化以下LUA奇遇代码，使其更符合用户需求。

**重要：必须严格遵循 gameplay_document.md 中的示例格式和写法**

参考文档示例（gameplay_document.md）：
{reference_examples}

**Few-Shot完整示例（必须严格遵循此格式）**：
{FEW_SHOT_EXAMPLE}

用户需求：
{user_input}

当前代码：
```lua
{current_code}
```

可用的API函数参考：
{function_docs}

**动画素材库（PlayAnim必须使用以下动画名称）**：
{animations_text}

请检查并优化：
1. **是否严格遵循gameplay_document.md中的示例格式**（最重要！）
2. 是否完全满足用户需求
3. 代码结构是否合理
4. 是否有遗漏的功能
5. 函数调用是否正确（参数格式、类型，必须与参考文档示例一致）
6. 是否包含必要的判空检查
7. 是否包含至少2个分支
8. 是否包含System.Exit()
9. 是否移除了所有注释
10. **玩家对话是否使用了UI.ShowDialogue（不能使用player:ApproachAndSay）**
11. **动画名称是否来自素材库（不能使用自定义动画名称）**
12. **对话内容是否移除了方括号（正确格式："文本"，错误格式："[文本]"）**

**输出要求（严格遵循Few-Shot示例格式）**：
- 只输出完整的Encounter代码，不要任何解释、说明或其他文字
- 不要包含"```lua"或"```"代码块标记
- 直接输出代码，从 `local function ResolveEncounterLoc()` 开始，到 `UI.Toast("游戏开始")` 结束
- 必须包含完整的格式：ResolveEncounterLoc函数、SpawnEncounter_XXX函数、函数调用、初始化代码"""
        
        refined_code = self._call_llm_api(prompt)
        # 提取纯LUA代码
        refined_code = self._extract_lua_code(refined_code)
        refined_code = self._remove_comments(refined_code)
        # 修正代码问题
        refined_code = self._fix_code_issues(refined_code)
        return refined_code.strip()
    
    def _validate_encounter_code(self, code: str) -> bool:
        """
        验证奇遇代码质量
        优先级：语法正确性 > 功能完整性
        """
        # 优先级1：语法验证（最高优先级）
        
        # 1. 检查World.SpawnEncounter的基本结构
        if 'World.SpawnEncounter' not in code:
            return False
        
        # 2. 检查World.SpawnEncounter的参数格式
        spawn_pattern = r'World\.SpawnEncounter\s*\(\s*\{X=\d+,\s*Y=\d+,\s*Z=\d+\}\s*,\s*(\d+)\s*,\s*(\{[^}]*\})\s*,\s*"EnterVolume"'
        match = re.search(spawn_pattern, code)
        if not match:
            return False
        
        # 3. 检查range参数（第2个参数）必须是数字，且不能太小
        range_value = match.group(1)
        try:
            range_num = int(range_value)
            if range_num < 100:  # 范围不能太小，至少100
                return False
        except ValueError:
            return False
        
        # 4. 检查npcData参数（第3个参数）不能为空字典
        npc_data = match.group(2)
        # 检查是否包含至少一个NPC映射
        if not re.search(r'\["[^"]+"\]\s*=\s*"[^"]+"', npc_data):
            return False
        
        # 5. 检查代码块格式（第5个参数）必须使用 [[ ... ]]
        code_block_pattern = r'\[\[.*?\]\]'
        if not re.search(code_block_pattern, code, re.DOTALL):
            return False
        
        # 优先级2：功能验证（如果语法正确，再检查功能）
        
        # 检查必需的元素（但如果没有也不强制，因为用户可能只要求简单场景）
        if 'World.GetByID' not in code:
            return False
        
        # 检查玩家对话：不应该有player:ApproachAndSay
        if 'player:ApproachAndSay' in code or 'Player:ApproachAndSay' in code:
            return False
        
        # 检查对话内容：不应该有方括号包裹的对话内容
        bracket_patterns = [
            r'ApproachAndSay\s*\([^,]+,\s*"\[[^\]]+\]"',
            r'ShowDialogue\s*\([^,]+,\s*"\[[^\]]+\]"'
        ]
        for pattern in bracket_patterns:
            if re.search(pattern, code):
                return False
        
        # 检查动画名称：所有PlayAnim的动画名称应该在素材库中
        playanim_pattern = r'PlayAnim\s*\(\s*"([^"]+)"\s*\)'
        anim_matches = re.findall(playanim_pattern, code)
        for anim_name in anim_matches:
            if anim_name not in ANIMATION_LIBRARY:
                # 允许一些常见映射，但最好都使用素材库
                if anim_name not in ["Wave", "Happy", "Shy", "Scared", "Drink", "Sleep", "Dialogue", "Frustrated"]:
                    return False
        
        return True
    
    def _fix_syntax_errors(self, code: str, npc_tags: List[str] = None) -> str:
        """
        修正语法错误（最高优先级）
        确保World.SpawnEncounter的语法完全正确
        """
        if not npc_tags:
            npc_tags = ["Tag_A"]
        
        # 1. 修正range参数：如果太小或不是数字，改为450
        range_pattern = r'World\.SpawnEncounter\s*\(\s*\{X=\d+,\s*Y=\d+,\s*Z=\d+\}\s*,\s*(\d+)\s*,'
        match = re.search(range_pattern, code)
        if match:
            range_value = match.group(1)
            try:
                range_num = int(range_value)
                if range_num < 100:
                    # 替换为450
                    code = re.sub(
                        r'(World\.SpawnEncounter\s*\(\s*\{X=\d+,\s*Y=\d+,\s*Z=\d+\}\s*,\s*)\d+(\s*,)',
                        r'\g<1>450\2',
                        code,
                        count=1
                    )
            except ValueError:
                # 如果不是数字，替换为450
                code = re.sub(
                    r'(World\.SpawnEncounter\s*\(\s*\{X=\d+,\s*Y=\d+,\s*Z=\d+\}\s*,\s*)[^,]+(\s*,)',
                    r'\g<1>450\2',
                    code,
                    count=1
                )
        
        # 2. 修正npcData参数：如果为空字典，添加默认NPC
        empty_npc_pattern = r'World\.SpawnEncounter\s*\(\s*\{X=\d+,\s*Y=\d+,\s*Z=\d+\}\s*,\s*\d+\s*,\s*\{\}\s*,'
        if re.search(empty_npc_pattern, code):
            # 构建NPC映射
            npc_map = "{\n"
            for tag in npc_tags:
                npc_map += f'        ["{tag}"] = "NPC_Base",\n'
            npc_map = npc_map.rstrip(",\n") + "\n    }"
            
            code = re.sub(
                r'(World\.SpawnEncounter\s*\(\s*\{X=\d+,\s*Y=\d+,\s*Z=\d+\}\s*,\s*\d+\s*,\s*)\{\}(\s*,)',
                rf'\g<1>{re.escape(npc_map)}\2',
                code,
                count=1
            )
        
        # 3. 确保位置参数格式正确
        pos_pattern = r'World\.SpawnEncounter\s*\(\s*\{X=([^,]+),\s*Y=([^,]+),\s*Z=([^}]+)\}'
        if not re.search(pos_pattern, code):
            # 如果位置参数格式不对，修正为 {X=0, Y=0, Z=0}
            code = re.sub(
                r'World\.SpawnEncounter\s*\(\s*[^,]+',
                'World.SpawnEncounter(\n    {X=0, Y=0, Z=0}',
                code,
                count=1
            )
        
        # 4. 确保类型参数是 "EnterVolume"
        type_pattern = r'World\.SpawnEncounter\s*\([^,]+,[^,]+,[^,]+,\s*"([^"]+)"'
        match = re.search(type_pattern, code)
        if match and match.group(1) != "EnterVolume":
            code = re.sub(
                r'(World\.SpawnEncounter\s*\([^,]+,[^,]+,[^,]+,\s*)"[^"]+"',
                r'\1"EnterVolume"',
                code,
                count=1
            )
        
        return code
    
    def _final_validation_and_fix(self, code: str, user_input: str, npc_tags: List[str] = None) -> str:
        """
        最终验证和修正阶段
        优先级：语法正确性 > 功能完整性
        确保代码完全符合标准
        """
        max_iterations = 5  # 增加迭代次数以确保语法正确
        
        for iteration in range(max_iterations):
            # 优先级1：修正语法错误
            code = self._fix_syntax_errors(code, npc_tags)
            
            # 优先级2：修正其他代码问题
            code = self._fix_code_issues(code)
            
            # 验证语法（最高优先级）
            if self._validate_encounter_code(code):
                # 如果语法正确，再检查格式
                if self._validate_reference_format(code):
                    return code
            
            # 如果还有问题，使用LLM修正（但优先保证语法正确）
            if iteration < max_iterations - 1:
                # 在修正前，先确保语法正确
                code = self._fix_syntax_errors(code, npc_tags)
                code = self._refine_code(user_input, code, npc_tags)
                # 修正后再次确保语法正确
                code = self._fix_syntax_errors(code, npc_tags)
        
        # 最后一次确保语法正确
        code = self._fix_syntax_issues(code, npc_tags)
        return code
    
    def _fix_syntax_issues(self, code: str, npc_tags: List[str] = None) -> str:
        """修正语法问题的别名方法"""
        return self._fix_syntax_errors(code, npc_tags)
    
    def _validate_reference_format(self, code: str) -> bool:
        """
        验证代码是否严格遵循gameplay_document.md的格式
        """
        reference_examples = self.kb.get_reference_examples()
        
        # 检查关键模式
        checks = []
        
        # 1. 检查World.SpawnEncounter格式
        spawn_pattern = r'World\.SpawnEncounter\s*\(\s*\{X=\d+,\s*Y=\d+,\s*Z=\d+\}'
        checks.append(bool(re.search(spawn_pattern, code)))
        
        # 2. 检查ApproachAndSay格式（不能有方括号）
        approach_with_brackets = r'ApproachAndSay\s*\([^,]+,\s*"\[[^\]]+\]"'
        checks.append(not bool(re.search(approach_with_brackets, code)))
        
        # 3. 检查ShowDialogue格式（不能有方括号）
        dialogue_with_brackets = r'ShowDialogue\s*\([^,]+,\s*"\[[^\]]+\]"'
        checks.append(not bool(re.search(dialogue_with_brackets, code)))
        
        # 4. 检查PlayAnim是否使用素材库动画
        playanim_pattern = r'PlayAnim\s*\(\s*"([^"]+)"'
        anim_matches = re.findall(playanim_pattern, code)
        anim_checks = [anim in ANIMATION_LIBRARY for anim in anim_matches]
        checks.append(all(anim_checks) if anim_matches else True)
        
        # 5. 检查玩家对话（不能使用player:ApproachAndSay）
        player_approach = r'player:ApproachAndSay|Player:ApproachAndSay'
        checks.append(not bool(re.search(player_approach, code)))
        
        # 6. 检查代码块格式（必须使用[[ ... ]]）
        code_block_pattern = r'\[\[.*?\]\]'
        checks.append(bool(re.search(code_block_pattern, code, re.DOTALL)))
        
        # 7. 检查是否有注释（代码块内不能有注释）
        # 注意：这里只检查代码块内的注释
        code_block_match = re.search(r'\[\[(.*?)\]\]', code, re.DOTALL)
        if code_block_match:
            code_content = code_block_match.group(1)
            has_comments = '--' in code_content
            checks.append(not has_comments)
        
        return all(checks)
    
    def _call_llm_api(self, prompt: str) -> str:
        """
        调用LLM API
        支持从环境变量或配置中获取API密钥
        """
        import openai
        
        # 优先使用配置中的API Key，否则使用环境变量
        api_key = self.config.get('apiKey') or os.getenv('OPENAI_API_KEY', '')
        
        if not api_key:
            # 如果没有配置API密钥，返回模拟响应
            return self._mock_llm_response(prompt)
        
        # API配置
        API_CONFIG = {
            "gpt-4.1": {
                "model": "gpt-4-turbo-preview",
                "base_url": "https://api.openai.com/v1"
            },
            "gpt-5.1": {
                "model": "gpt-4-turbo-preview",  # 实际使用时替换为GPT-5.1的模型名
                "base_url": "https://api.openai.com/v1"
            }
        }
        
        model_config = API_CONFIG.get(self.model, API_CONFIG['gpt-4.1'])
        
        try:
            client = openai.OpenAI(
                api_key=api_key,
                base_url=model_config.get('base_url', 'https://api.openai.com/v1')
            )
            
            response = client.chat.completions.create(
                model=model_config['model'],
                messages=[
                    {"role": "system", "content": "你是一个专业的LUA奇遇脚本生成专家，专门生成游戏Encounter脚本。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.config.get('temperature', 0.7),
                max_tokens=self.config.get('maxTokens', 4000),
                top_p=self.config.get('topP', 0.9),
                frequency_penalty=self.config.get('frequencyPenalty', 0.0),
                presence_penalty=self.config.get('presencePenalty', 0.0)
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"API调用错误: {e}")
            return self._mock_llm_response(prompt)
    
    def _mock_llm_response(self, prompt: str) -> str:
        """模拟LLM响应（用于测试）"""
        return """World.SpawnEncounter(
    {X=0, Y=0, Z=0},
    450,
    {
        ["Tag_A"] = "NPC_Base"
    },
    "EnterVolume",
    [[
local player = World.GetByID("Player")
local npcA = World.GetByID("Tag_A")

if not player or not player:IsValid() then return end
if not npcA or not npcA:IsValid() then return end

local ppos = player:GetPos()
local base = {X=ppos.X + 200, Y=ppos.Y, Z=ppos.Z}

npcA:MoveTo(base)
World.Wait(0.9)

npcA:LookAt(player)
World.Wait(0.4)

UI.ShowDialogue("陌生人", "你能停一下吗？我需要你帮个忙。")
World.Wait(0.6)

local r = UI.AskMany("你要怎么回应？", {"帮忙", "拒绝"})

if r == 1 then
    UI.ShowDialogue("陌生人", "太好了！我就知道你是个可靠的人。")
    World.Wait(0.5)
    npcA:GiveItem("Money", 15)
    UI.Toast("你获得了 Money x15")
else
    UI.ShowDialogue("陌生人", "好吧……我不该期待什么。")
    World.Wait(0.5)
    UI.Toast("对方失望地离开了。")
end

World.Wait(0.8)

System.Exit()
    ]]
)"""
