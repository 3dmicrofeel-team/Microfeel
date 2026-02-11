"""
奇遇（Encounter）RAG系统
实现4层工作流：故事扩写、玩法拆解、执行计划、Lua生成
"""

import os
from typing import Dict, Any, List, Optional
from gameplay_knowledge_base import get_gameplay_knowledge_base, GameplayKnowledgeBase


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
        实现4层工作流
        """
        # Layer 1: 故事扩写
        story = self._expand_story(user_input, npc_tags)
        
        # Layer 2: 玩法拆解
        gameplay_nodes = self._decompose_gameplay(story, npc_tags)
        
        # Layer 3: 执行计划
        execution_plan = self._build_execution_plan(gameplay_nodes, npc_tags)
        
        # Layer 4: Lua代码生成
        lua_code = self._generate_lua_code(user_input, story, execution_plan, npc_tags)
        
        return lua_code
    
    def _iterative_generate(self, user_input: str, npc_tags: List[str] = None) -> str:
        """
        迭代模式：多次优化
        """
        current_code = self._standard_generate(user_input, npc_tags)
        
        for iteration in range(self.max_iterations - 1):
            # 验证当前代码
            if self._validate_encounter_code(current_code):
                break
            
            # 优化代码
            current_code = self._refine_code(user_input, current_code, npc_tags)
        
        return current_code
    
    def _multi_agent_generate(self, user_input: str, npc_tags: List[str] = None) -> str:
        """
        多Agent协作模式
        """
        # Agent 1: 规划Agent（故事+玩法）
        plan = self._planning_agent(user_input, npc_tags)
        
        # Agent 2: 代码生成Agent
        code = self._code_generation_agent(user_input, plan, npc_tags)
        
        # Agent 3: 验证Agent
        if not self._validate_encounter_code(code):
            code = self._refine_code(user_input, code, npc_tags)
        
        return code
    
    def _expand_story(self, user_input: str, npc_tags: List[str] = None) -> str:
        """
        Layer 1: 故事扩写
        将用户需求扩写为完整的故事背景
        """
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

请直接输出故事文本，不要包含其他说明。"""
        
        story = self._call_llm_api(prompt)
        return story.strip()
    
    def _decompose_gameplay(self, story: str, npc_tags: List[str] = None) -> List[Dict[str, Any]]:
        """
        Layer 2: 玩法拆解
        将故事拆解为可执行的动作节点
        """
        # 识别需要的功能模块
        modules = self.kb.identify_required_modules(story, npc_tags)
        
        # 检索相关函数文档
        relevant_functions = self.kb.retrieve_functions(
            modules=modules,
            query=story,
            top_k=40
        )
        
        function_docs = self.kb.get_function_docs_text(relevant_functions)
        
        prompt = f"""你是一个游戏玩法设计师。请将以下故事拆解为6-12个可执行的动作节点。

故事：
{story}

NPC标签：{', '.join(npc_tags) if npc_tags else 'Tag_A'}

可用的API函数参考：
{function_docs}

每个动作节点必须对应一个API调用，例如：
- NPC移动到指定位置
- NPC面向玩家
- NPC播放动画
- UI显示对话
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
    
    def _build_execution_plan(self, gameplay_nodes: List[Dict[str, Any]], npc_tags: List[str] = None) -> str:
        """
        Layer 3: 执行计划
        将玩法拆解转化为脚本步骤链
        """
        prompt = f"""你是一个LUA脚本工程师。请将以下动作节点转化为详细的执行计划。

动作节点：
{gameplay_nodes}

NPC标签：{', '.join(npc_tags) if npc_tags else 'Tag_A'}

请制定执行计划，包括：
1. 获取player与NPC actor（使用World.GetByID）
2. 判空检查（IsValid）
3. 计算encounter中心点与站位点（基于玩家位置）
4. NPC移动、朝向、动画（MoveTo/LookAt/PlayAnim）
5. UI对话和选择（ShowDialogue/AskMany）
6. 分支逻辑执行
7. 可选：生成敌人/播放FX/播放音效
8. 结束奇遇（System.Exit）

请输出详细的执行步骤。"""
        
        plan = self._call_llm_api(prompt)
        return plan.strip()
    
    def _generate_lua_code(self, user_input: str, story: str, execution_plan: str, npc_tags: List[str] = None) -> str:
        """
        Layer 4: Lua代码生成
        生成最终的World.SpawnEncounter代码
        """
        # 构建NPC映射
        if not npc_tags:
            npc_tags = ["Tag_A"]
        
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
        
        prompt = f"""你是一个LUA代码生成专家。请根据以下信息生成完整的World.SpawnEncounter代码。

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

**重要约束**：
1. 输出格式必须严格遵循：
World.SpawnEncounter(
    {{X=0, Y=0, Z=0}},
    450,
    {npc_map},
    "EnterVolume",
    [[
        -- Lua代码（严禁包含注释）
    ]]
)

2. 代码块内禁止使用 -- 注释，否则引擎报错
3. 所有对象必须先判空 IsValid()
4. 必须包含至少2个分支（使用UI.AskMany）
5. 必须使用World.Wait控制节奏
6. 结尾必须System.Exit()
7. 坐标固定{{X=0,Y=0,Z=0}}
8. Type固定"EnterVolume"
9. 代码块必须使用[[ ... ]]

请直接输出完整的World.SpawnEncounter代码，不要包含其他说明。"""
        
        lua_code = self._call_llm_api(prompt)
        
        # 清理代码：移除注释
        lua_code = self._remove_comments(lua_code)
        
        return lua_code.strip()
    
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
    
    def _planning_agent(self, user_input: str, npc_tags: List[str] = None) -> Dict[str, Any]:
        """规划Agent：分析需求，制定生成计划"""
        story = self._expand_story(user_input, npc_tags)
        gameplay_nodes = self._decompose_gameplay(story, npc_tags)
        execution_plan = self._build_execution_plan(gameplay_nodes, npc_tags)
        
        return {
            "story": story,
            "gameplay_nodes": gameplay_nodes,
            "execution_plan": execution_plan
        }
    
    def _code_generation_agent(self, user_input: str, plan: Dict[str, Any], npc_tags: List[str] = None) -> str:
        """代码生成Agent：根据计划生成Lua代码"""
        return self._generate_lua_code(
            user_input,
            plan.get("story", ""),
            plan.get("execution_plan", ""),
            npc_tags
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
        
        prompt = f"""优化以下LUA奇遇代码，使其更符合用户需求。

用户需求：
{user_input}

当前代码：
```lua
{current_code}
```

可用的API函数参考：
{function_docs}

请检查并优化：
1. 是否完全满足用户需求
2. 代码结构是否合理
3. 是否有遗漏的功能
4. 函数调用是否正确（参数格式、类型）
5. 是否包含必要的判空检查
6. 是否包含至少2个分支
7. 是否包含System.Exit()
8. 是否移除了所有注释

请提供优化后的完整World.SpawnEncounter代码。"""
        
        refined_code = self._call_llm_api(prompt)
        refined_code = self._remove_comments(refined_code)
        return refined_code.strip()
    
    def _validate_encounter_code(self, code: str) -> bool:
        """验证奇遇代码质量"""
        # 基本验证
        required_elements = [
            'World.SpawnEncounter',
            'World.GetByID',
            'IsValid',
            'System.Exit',
            'UI.AskMany'  # 至少一个分支选择
        ]
        
        return all(elem in code for elem in required_elements)
    
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
