"""
Agentic RAG Backend API
处理自然语言输入，通过Agentic RAG系统生成LUA脚本
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from typing import Dict, Any, List
import json
from knowledge_base import get_knowledge_base, KnowledgeBase
from encounter_rag_system import EncounterRAGSystem

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 初始化知识库
kb = get_knowledge_base()
gameplay_kb = None  # 延迟初始化

# 配置
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


class AgenticRAGSystem:
    """
    Agentic RAG系统核心类
    实现多步骤推理和迭代优化
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.model = config.get('model', 'gpt-4.1')
        self.agent_mode = config.get('agentMode', 'standard')
        self.max_iterations = config.get('maxIterations', 3)
        # API Key会在调用时从config或环境变量获取
        
    def generate(self, user_input: str) -> str:
        """
        主生成方法
        根据Agent模式选择不同的生成策略
        """
        if self.agent_mode == 'standard':
            return self._standard_generate(user_input)
        elif self.agent_mode == 'iterative':
            return self._iterative_generate(user_input)
        elif self.agent_mode == 'multi-agent':
            return self._multi_agent_generate(user_input)
        else:
            return self._standard_generate(user_input)
    
    def _standard_generate(self, user_input: str) -> str:
        """
        标准模式：单次生成（集成RAG）
        """
        # 识别需要的模块
        required_modules = kb.identify_required_modules(user_input)
        
        # 检索相关函数
        relevant_functions = kb.retrieve_functions(
            modules=required_modules,
            query=user_input,
            top_k=40
        )
        
        # 获取函数文档
        function_docs = kb.get_function_docs_text(relevant_functions)
        
        # 构建提示词（包含RAG检索结果）
        prompt = self._build_prompt(user_input, function_docs=function_docs)
        
        # 调用LLM API
        response = self._call_llm_api(prompt)
        
        # 提取和验证LUA代码
        lua_script = self._extract_lua_code(response)
        
        return lua_script
    
    def _iterative_generate(self, user_input: str) -> str:
        """
        迭代模式：多次优化（集成RAG）
        """
        # 识别需要的模块（只在第一次）
        required_modules = kb.identify_required_modules(user_input)
        relevant_functions = kb.retrieve_functions(
            modules=required_modules,
            query=user_input,
            top_k=40
        )
        function_docs = kb.get_function_docs_text(relevant_functions)
        
        current_script = None
        
        for iteration in range(self.max_iterations):
            if iteration == 0:
                # 第一次生成（使用RAG）
                prompt = self._build_prompt(user_input, function_docs=function_docs)
            else:
                # 后续迭代：基于之前的输出进行优化
                prompt = self._build_refinement_prompt(user_input, current_script, function_docs)
            
            response = self._call_llm_api(prompt)
            current_script = self._extract_lua_code(response)
            
            # 验证脚本质量
            if self._validate_script(current_script):
                break
        
        return current_script
    
    def _multi_agent_generate(self, user_input: str) -> str:
        """
        多Agent协作模式
        """
        # Agent 1: 分析和规划
        planning_agent = self._planning_agent(user_input)
        
        # Agent 2: 生成代码
        code_agent = self._code_generation_agent(user_input, planning_agent)
        
        # Agent 3: 验证和优化
        validation_agent = self._validation_agent(code_agent)
        
        return validation_agent
    
    def _planning_agent(self, user_input: str) -> Dict[str, Any]:
        """
        规划Agent：分析需求，制定生成计划
        使用RAG检索识别需要的功能模块
        """
        # 使用知识库识别需要的模块
        required_modules = kb.identify_required_modules(user_input)
        
        # 检索相关函数文档
        relevant_functions = kb.retrieve_functions(
            modules=required_modules,
            query=user_input,
            top_k=30
        )
        
        # 获取函数文档文本
        function_docs = kb.get_function_docs_text(relevant_functions)
        
        prompt = f"""你是一个LUA地图生成专家。分析以下用户需求，制定详细的生成计划。

用户需求：
{user_input}

可用的API函数参考（已根据你的需求筛选）：
{function_docs}

请按照以下8个步骤制定计划：
1. 创建地图 - 确定地图尺寸和主题
2. 塑造地形 - 确定地形特征（山、湖、平原等）
3. 划分Block区域 - 确定各个功能区域
4. 填充Block内容 - 确定每个区域的建筑、NPC、敌人等
5. 建立连接 - 确定区域之间的道路连接
6. 自动化处理 - 确定需要自动化的内容（植被、装饰等）
7. 设置氛围 - 确定时间、天气、音效等
8. 验证并构建 - 确定验证规则

请以JSON格式返回计划，包括每个步骤需要使用的具体函数。"""
        
        response = self._call_llm_api(prompt)
        # 解析JSON计划（简化处理）
        return {
            "plan": response,
            "modules": required_modules,
            "functions": [f.lua_signature for f in relevant_functions[:10]]
        }
    
    def _code_generation_agent(self, user_input: str, plan: Dict[str, Any]) -> str:
        """
        代码生成Agent：根据计划生成LUA代码
        使用RAG检索的函数文档
        """
        # 从计划中获取需要的模块
        modules = plan.get("modules", [])
        
        # 检索相关函数
        relevant_functions = kb.retrieve_functions(
            modules=modules,
            query=user_input,
            top_k=40
        )
        
        # 获取函数文档
        function_docs = kb.get_function_docs_text(relevant_functions)
        
        prompt = self._build_prompt(user_input, plan, function_docs)
        response = self._call_llm_api(prompt)
        return self._extract_lua_code(response)
    
    def _validation_agent(self, lua_script: str) -> str:
        """
        验证Agent：检查代码质量并优化
        """
        prompt = f"""你是一个LUA代码验证专家。检查以下代码是否符合规范，并修复任何错误。

LUA代码：
```lua
{lua_script}
```

请检查：
1. 语法是否正确
2. API调用是否符合规范
3. 是否遵循8步生成流程
4. 代码结构是否完整

如果发现问题，请提供修复后的完整代码。"""
        
        response = self._call_llm_api(prompt)
        return self._extract_lua_code(response)
    
    def _build_prompt(self, user_input: str, plan: Dict[str, Any] = None, function_docs: str = None) -> str:
        """
        构建提示词，集成RAG检索的函数文档
        """
        base_prompt = f"""你是一个专业的LUA地图生成系统。根据用户需求生成完整的LUA脚本。

用户需求：
{user_input}

"""
        
        # 添加RAG检索的函数文档
        if function_docs:
            base_prompt += f"""可用的API函数参考（已根据你的需求智能检索）：
{function_docs}

"""
        else:
            # 如果没有RAG结果，使用默认提示
            base_prompt += """请使用以下API函数：

1. 创建地图
   - Env.CreateMap(width, height, scale)
   - Env.SetMapName(map, name)
   - Env.SetMapTheme(map, theme)

2. 塑造地形
   - Env.RaiseTerrain(map, center, radius, height, falloff)
   - Env.LowerTerrain(map, center, radius, depth, falloff)
   - Env.AddWaterBody(map, center, size, depth)
   - Env.SmoothTerrain(map, iterations)

3. 划分Block区域
   - Env.AddBlock(map, name, gridPos, gridSize)
   - Env.SetBlockType(block, type)
   - Env.SetBlockProperty(block, key, value)

4. 填充Block内容
   - Env.AddBuilding(block, localPos, size, style)
   - Env.AddNPCSpawn(block, npcID, localPos, rotation)
   - Env.AddEnemySpawn(block, enemyID, localPos, patrolRadius)
   - Env.AddProp(block, propID, localPos, rotation)
   - Env.AddSpawnPoint(block, tag, localPos)

5. 建立连接
   - Env.AddRoad(map, blockA, blockB, width, roadType)
   - 或 Env.AutoGenerateRoads(map)

6. 自动化处理
   - Env.AutoPaintTerrain(map)
   - Env.AutoAddVegetation(map, density)
   - Env.AutoDecorate(map)

7. 设置氛围
   - Env.SetTimeOfDay(map, hour)
   - Env.SetWeather(map, weather)
   - Env.SetAmbientSound(map, soundID)

8. 验证并构建
   - Env.ValidateMap(map)
   - Env.SaveMap(map, slotName)
   - Env.BuildAsync(map, callback)

"""
        
        base_prompt += """请严格按照以上8个步骤生成完整的、可直接运行的LUA代码。
代码应该包含 CreateStarterZone() 函数和 OnLevelReady() 函数。
确保所有函数调用都使用正确的参数格式和类型。"""
        
        if plan:
            plan_text = plan.get("plan", "")
            if plan_text:
                base_prompt += f"\n\n参考计划：\n{plan_text}"
        
        return base_prompt
    
    def _build_refinement_prompt(self, user_input: str, current_script: str, function_docs: str = None) -> str:
        """
        构建优化提示词（集成RAG）
        """
        prompt = f"""优化以下LUA代码，使其更符合用户需求。

用户需求：
{user_input}

当前代码：
```lua
{current_script}
```

"""
        
        if function_docs:
            prompt += f"""可用的API函数参考：
{function_docs}

"""
        
        prompt += """请检查并优化：
1. 是否完全满足用户需求
2. 代码结构是否合理
3. 是否有遗漏的功能
4. 函数调用是否正确（参数格式、类型）
5. 代码质量是否可以提升

请提供优化后的完整代码。"""
        
        return prompt
    
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
        
        model_config = API_CONFIG.get(self.model, API_CONFIG['gpt-4.1'])
        
        try:
            # 创建OpenAI客户端
            client = openai.OpenAI(
                api_key=api_key,
                base_url=model_config.get('base_url', 'https://api.openai.com/v1')
            )
            
            response = client.chat.completions.create(
                model=model_config['model'],
                messages=[
                    {"role": "system", "content": "你是一个专业的LUA代码生成专家，专门生成游戏地图脚本。"},
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
        """
        模拟LLM响应（用于测试）
        """
        return """function CreateStarterZone()
    local map = Env.CreateMap(100, 100, 100)
    Env.SetMapName(map, "新手平原")
    Env.SetMapTheme(map, "Medieval")

    Env.RaiseTerrain(map, {X=50, Y=50}, 30, 200, 0.8)
    Env.SmoothTerrain(map, 3)

    local villageBlock = Env.AddBlock(map, "新手村", {X=35, Y=30}, {X=30, 25})
    Env.SetBlockType(villageBlock, "Village")
    Env.SetBlockProperty(villageBlock, "SafeZone", "true")

    Env.FlattenTerrain(map, {X=50, Y=42}, 12, 50)

    local inn = Env.AddBuilding(villageBlock, {X=5, Y=5}, {X=5, Y=4}, "Medieval", {Pitch=0, Yaw=0, Roll=0})
    Env.SetBuildingType(inn, "Tavern")
    Env.AddBuildingFloor(inn, 300)
    Env.SetBuildingRoof(inn, "Pitched")
    Env.AutoFurnishBuilding(inn, "Tavern")

    Env.AddNPCSpawn(villageBlock, "NPC_QuestGiver", {X=1200, Y=400, Z=0}, {Pitch=0, Yaw=0, Roll=0})
    Env.AddSpawnPoint(villageBlock, "PlayerStart", {X=1000, Y=200, Z=0}, {Pitch=0, Yaw=0, Roll=0})

    local errors = Env.ValidateMap(map)
    if #errors > 0 then
        for _, err in ipairs(errors) do
            Log("[错误] " .. err)
        end
        return nil
    end

    Env.SaveMap(map, "StarterZone_v1")
    Env.BuildAsync(map, function(levelRoot)
        Log("关卡构建完成！")
        OnLevelReady(levelRoot)
    end)

    return map
end

function OnLevelReady(levelRoot)
    local spawnPos = World.GetSpawnPoint("PlayerStart")
    local player = World.SpawnPlayer(spawnPos)
end"""
    
    def _extract_lua_code(self, response: str) -> str:
        """
        从LLM响应中提取LUA代码
        """
        # 查找代码块
        if '```lua' in response:
            start = response.find('```lua') + 6
            end = response.find('```', start)
            if end != -1:
                return response[start:end].strip()
        elif '```' in response:
            start = response.find('```') + 3
            end = response.find('```', start)
            if end != -1:
                return response[start:end].strip()
        
        # 如果没有代码块标记，返回整个响应
        return response.strip()
    
    def _validate_script(self, script: str) -> bool:
        """
        验证脚本质量
        """
        # 基本验证：检查是否包含关键函数
        required_functions = ['CreateStarterZone', 'Env.CreateMap']
        return all(func in script for func in required_functions)


@app.route('/api/generate', methods=['POST'])
def generate_lua():
    """
    API端点：生成LUA脚本
    支持两种模式：
    - map: 地图生成（使用AgenticRAGSystem）
    - encounter: 奇遇生成（使用EncounterRAGSystem）
    """
    try:
        data = request.get_json()
        user_input = data.get('input', '')
        config = data.get('config', {})
        generation_mode = data.get('mode', 'map')  # 默认地图模式
        
        if not user_input:
            return jsonify({'error': '输入不能为空'}), 400
        
        # 处理API Key（优先使用前端传入的，否则使用环境变量）
        # API Key会直接传递给RAG系统，不需要修改环境变量
        
        if generation_mode == 'encounter':
            # 奇遇生成模式 - 使用奇遇知识库（GameplayKnowledgeBase）
            npc_tags = data.get('npcTags', None)  # 可选的NPC标签列表
            
            # 延迟初始化奇遇知识库（向量数据库：chroma_db_gameplay）
            global gameplay_kb
            if gameplay_kb is None:
                from gameplay_knowledge_base import get_gameplay_knowledge_base
                gameplay_kb = get_gameplay_knowledge_base()
                print(f"[INFO] 奇遇知识库已加载，包含 {len(gameplay_kb.functions)} 个API函数")
            
            # 创建奇遇RAG系统（使用奇遇知识库）
            encounter_system = EncounterRAGSystem(config)
            
            # 生成奇遇LUA脚本
            lua_script = encounter_system.generate(user_input, npc_tags)
            
            return jsonify({
                'success': True,
                'luaScript': lua_script,
                'model': config.get('model', 'gpt-4.1'),
                'agentMode': config.get('agentMode', 'standard'),
                'mode': 'encounter',
                'knowledgeBase': 'gameplay'  # 标识使用的知识库
            })
        else:
            # 地图生成模式（默认）- 使用地图知识库（KnowledgeBase）
            # 创建Agentic RAG系统（使用地图知识库，向量数据库：chroma_db）
            rag_system = AgenticRAGSystem(config)
            print(f"[INFO] 地图知识库已使用，包含 {len(kb.functions)} 个API函数")
            
            # 生成LUA脚本
            lua_script = rag_system.generate(user_input)
            
            return jsonify({
                'success': True,
                'luaScript': lua_script,
                'model': config.get('model', 'gpt-4.1'),
                'agentMode': config.get('agentMode', 'standard'),
                'mode': 'map',
                'knowledgeBase': 'map'  # 标识使用的知识库
            })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """
    健康检查端点
    """
    return jsonify({
        'status': 'healthy',
        'service': 'Agentic RAG API'
    })


if __name__ == '__main__':
    # 开发环境配置
    # 支持通过环境变量PORT指定端口，默认5000
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
