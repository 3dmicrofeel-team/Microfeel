# Agent模式说明

## 📋 三种Agent模式

系统提供三种不同的Agent工作模式，每种模式有不同的工作方式和适用场景。

---

## 1. 标准模式（单次生成）

### 工作方式
- **单次调用LLM**：一次性生成完整的LUA脚本
- **RAG检索**：根据用户需求检索相关函数文档
- **直接生成**：基于检索结果直接生成代码

### 流程
```
用户输入 
  → 识别功能模块 
  → RAG检索函数文档 
  → 构建提示词 
  → LLM生成 
  → 输出LUA代码
```

### 特点
- ✅ **速度快**：只调用一次LLM API
- ✅ **成本低**：API调用次数少
- ✅ **适合简单需求**：需求明确、复杂度不高

### 适用场景
- 简单的地图生成需求
- 快速原型验证
- 对生成速度要求高

---

## 2. 迭代模式（多次优化）

### 工作方式
- **多次调用LLM**：根据`最大迭代次数`设置（默认3次）
- **迭代优化**：每次基于上一次的输出进行改进
- **质量验证**：每次迭代后检查代码质量

### 流程
```
用户输入 
  → 第1次生成（基于RAG检索）
  → 验证质量
  → 第2次优化（基于第1次结果）
  → 验证质量
  → 第3次优化（基于第2次结果）
  → 输出最终代码
```

### 特点
- ✅ **质量高**：多次优化，代码更完善
- ✅ **可控制**：可以设置最大迭代次数
- ⚠️ **速度慢**：需要多次API调用
- ⚠️ **成本高**：API调用次数多

### 适用场景
- 复杂的地图生成需求
- 需要高质量代码
- 对生成时间不敏感

### 配置参数
- **最大迭代次数**：1-10次（默认3次）
- 可以在界面上调整滑块

---

## 3. 多Agent协作

### 工作方式
- **三个Agent分工协作**：
  1. **规划Agent**：分析需求，制定生成计划
  2. **代码生成Agent**：根据计划生成LUA代码
  3. **验证Agent**：检查代码质量并优化

### 流程
```
用户输入
  → Agent 1: 规划（识别模块 + RAG检索 + 制定计划）
  → Agent 2: 生成（基于计划 + RAG文档 + 生成代码）
  → Agent 3: 验证（检查质量 + 优化代码）
  → 输出最终代码
```

### 特点
- ✅ **最准确**：三个Agent各司其职，分工明确
- ✅ **质量最高**：经过规划、生成、验证三个阶段
- ✅ **最智能**：每个Agent专注于自己的任务
- ⚠️ **速度最慢**：需要三次API调用
- ⚠️ **成本最高**：API调用次数最多

### 适用场景
- 非常复杂的地图生成需求
- 需要最高质量的代码
- 对准确性要求极高

---

## 🔄 模式对比

| 特性 | 标准模式 | 迭代模式 | 多Agent协作 |
|------|---------|---------|------------|
| **API调用次数** | 1次 | 3次（可配置） | 3次 |
| **生成速度** | ⚡⚡⚡ 最快 | ⚡⚡ 中等 | ⚡ 最慢 |
| **代码质量** | ⭐⭐ 良好 | ⭐⭐⭐ 优秀 | ⭐⭐⭐ 最佳 |
| **成本** | 💰 最低 | 💰💰 中等 | 💰💰💰 最高 |
| **适用场景** | 简单需求 | 复杂需求 | 非常复杂需求 |

---

## 🎯 选择建议

### 选择标准模式，如果：
- 需求简单明确
- 需要快速生成
- 预算有限

### 选择迭代模式，如果：
- 需求较复杂
- 需要高质量代码
- 可以接受较长的生成时间

### 选择多Agent协作，如果：
- 需求非常复杂
- 需要最高质量
- 对准确性要求极高

---

## ⚙️ 如何设置

### 在前端界面设置

1. 打开前端页面
2. 找到"Agent配置"面板
3. 点击"Agent模式"下拉菜单
4. 选择你需要的模式：
   - `标准模式（单次生成）`
   - `迭代模式（多次优化）`
   - `多Agent协作`

### 配置迭代次数（仅迭代模式）

如果选择了迭代模式，可以调整"最大迭代次数"滑块：
- 最小值：1次
- 最大值：10次
- 默认值：3次

---

## 💡 技术实现

### 标准模式实现
```python
def _standard_generate(self, user_input: str):
    # 1. RAG检索
    modules = kb.identify_required_modules(user_input)
    functions = kb.retrieve_functions(modules=modules, query=user_input)
    
    # 2. 构建提示词
    prompt = self._build_prompt(user_input, function_docs=functions)
    
    # 3. 单次生成
    response = self._call_llm_api(prompt)
    return self._extract_lua_code(response)
```

### 迭代模式实现
```python
def _iterative_generate(self, user_input: str):
    current_script = None
    
    for iteration in range(self.max_iterations):
        if iteration == 0:
            # 第一次生成
            prompt = self._build_prompt(user_input)
        else:
            # 后续迭代优化
            prompt = self._build_refinement_prompt(user_input, current_script)
        
        response = self._call_llm_api(prompt)
        current_script = self._extract_lua_code(response)
        
        # 验证质量，如果满意就停止
        if self._validate_script(current_script):
            break
    
    return current_script
```

### 多Agent协作实现
```python
def _multi_agent_generate(self, user_input: str):
    # Agent 1: 规划
    plan = self._planning_agent(user_input)  # 包含RAG检索
    
    # Agent 2: 生成
    code = self._code_generation_agent(user_input, plan)
    
    # Agent 3: 验证
    final_code = self._validation_agent(code)
    
    return final_code
```

---

## 📊 实际效果对比

### 示例：生成一个新手村地图

**标准模式**：
- 时间：~5秒
- API调用：1次
- 结果：基本满足需求，代码结构清晰

**迭代模式**（3次迭代）：
- 时间：~15秒
- API调用：3次
- 结果：代码更完善，细节更丰富，错误更少

**多Agent协作**：
- 时间：~20秒
- API调用：3次（规划+生成+验证）
- 结果：代码质量最高，结构最优，完全符合规范

---

## 🔍 如何查看当前模式

在前端界面：
- 查看"Agent配置"面板
- "Agent模式"下拉框显示当前选择的模式

在代码中：
- 前端：`config.agentMode`（'standard', 'iterative', 'multi-agent'）
- 后端：`config.get('agentMode', 'standard')`

---

## 💻 默认设置

- **默认模式**：标准模式（'standard'）
- **默认迭代次数**：3次（仅迭代模式）

---

**最后更新**: 2026-02-08
