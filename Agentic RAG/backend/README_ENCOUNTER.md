# 奇遇生成系统说明

## 概述

奇遇生成系统是Agentic RAG系统的一个扩展功能，专门用于生成游戏Encounter（奇遇）的LUA脚本。

## 知识库

### 知识库文件
- **源文档**：`backend/gameplay_knowledge_base.md`
- **向量数据库**：`backend/chroma_db_gameplay/`
- **集合名称**：`gameplay_functions`

### 知识库统计
- **总函数数**：46个API函数
- **模块分布**：
  - World: 10个函数（核心玩法API）
  - UI: 7个函数（交互核心）
  - System: 2个函数（脚本控制）
  - Entity: 6个函数（Actor基础能力）
  - Performer: 13个函数（NPC行为接口）
  - Math: 3个函数（随机性与涌现）
  - Time: 2个函数（环境时间控制）

### 初始化

运行初始化脚本：
```bash
cd backend
python init_gameplay_kb.py
```

这将：
1. 解析 `gameplay_knowledge_base.md` 文档
2. 提取46个API函数文档
3. 构建向量数据库（ChromaDB）
4. 索引所有函数文档到向量数据库

## 4层工作流

奇遇生成采用4层工作流：

### Layer 1: 故事扩写（Story Expansion）
- 输入：用户需求 + NPC标签列表
- 输出：150-250字的完整故事背景
- 包含：场景设定、触发原因、玩家介入点、至少1个结果分支

### Layer 2: 玩法拆解（Gameplay Breakdown）
- 输入：故事背景
- 输出：6-12个可执行的动作节点
- 每个节点对应一个API调用（MoveTo、ShowDialogue、AskMany等）

### Layer 3: 执行计划（Execution Plan）
- 输入：动作节点列表
- 输出：详细的脚本步骤链
- 包括：获取Actor、判空检查、站位计算、NPC行为、UI交互、分支逻辑、结束处理

### Layer 4: Lua代码生成（Final Lua）
- 输入：用户需求、故事、执行计划
- 输出：完整的 `World.SpawnEncounter` 代码
- 格式：严格遵循World.SpawnEncounter模板，无注释，包含判空、分支、节奏控制

## RAG检索流程

1. **模块识别**：根据用户输入和NPC标签识别需要的功能模块
   - 例如：提到"对话"→UI模块
   - 提到"NPC移动"→Performer模块
   - 提到"战斗"→World模块

2. **语义检索**：在奇遇知识库向量数据库中检索相关函数文档
   - 使用多语言嵌入模型（paraphrase-multilingual-MiniLM-L12-v2）
   - 检索top_k=50个最相关的函数文档

3. **文档注入**：将检索到的函数文档注入到LLM提示词
   - 包含函数签名、说明、参数、示例、推荐用法、常见错误

4. **代码生成**：LLM基于检索到的文档生成准确的LUA奇遇代码

## 使用示例

### 前端请求
```javascript
{
    "input": "我想要一个在酒馆发生的偷窃事件，玩家可以选择介入、旁观或离开。",
    "mode": "encounter",
    "npcTags": ["Tag_A", "Tag_B"],
    "config": {
        "model": "gpt-4.1",
        "agentMode": "standard",
        "apiKey": "sk-..."
    }
}
```

### 后端处理
1. 检测到 `mode: "encounter"`
2. 延迟加载奇遇知识库（如果未加载）
3. 创建 `EncounterRAGSystem` 实例
4. 执行4层工作流生成代码
5. 返回 `World.SpawnEncounter` 格式的LUA代码

## 输出格式

生成的代码必须严格遵循以下格式：

```lua
World.SpawnEncounter(
    {X=0, Y=0, Z=0},
    450,
    {
        ["Tag_A"] = "NPC_Base",
        ["Tag_B"] = "NPC_Base"
    },
    "EnterVolume",
    [[
        -- Lua代码（严禁包含注释）
        local player = World.GetByID("Player")
        local npcA = World.GetByID("Tag_A")
        -- ... 更多代码
        System.Exit()
    ]]
)
```

## 约束条件

1. **坐标固定**：`{X=0, Y=0, Z=0}`
2. **Type固定**：`"EnterVolume"`
3. **代码块格式**：必须使用 `[[ ... ]]`
4. **禁止注释**：代码块内不能包含 `--` 注释
5. **判空检查**：所有对象必须先 `IsValid()`
6. **分支要求**：必须包含至少2个分支（使用 `UI.AskMany`）
7. **节奏控制**：必须使用 `World.Wait` 控制节奏
8. **结束处理**：结尾必须 `System.Exit()`

## 知识库导入

系统使用延迟初始化策略：

```python
# 在需要时导入
from gameplay_knowledge_base import get_gameplay_knowledge_base

# 获取知识库实例（单例模式）
kb = get_gameplay_knowledge_base()

# 使用知识库
modules = kb.identify_required_modules(user_input, npc_tags)
functions = kb.retrieve_functions(modules=modules, query=user_input, top_k=50)
```

## 向量数据库状态

运行 `python init_gameplay_kb.py` 后，应该看到：
- ✅ 已加载 46 个奇遇API函数文档
- ✅ 向量数据库已初始化，包含 46 个文档
- ✅ 嵌入模型已加载

## 故障排除

### 问题1: 知识库未初始化
**症状**：`已加载 0 个奇遇API函数文档`

**解决**：
1. 检查 `gameplay_knowledge_base.md` 文件是否存在
2. 运行 `python init_gameplay_kb.py` 重新初始化
3. 检查文件编码是否为UTF-8

### 问题2: 向量数据库为空
**症状**：`向量数据库已初始化，包含 0 个文档`

**解决**：
1. 删除 `chroma_db_gameplay` 目录
2. 重新运行 `python init_gameplay_kb.py`
3. 确保函数文档已正确解析（46个函数）

### 问题3: 导入失败
**症状**：`ImportError: cannot import name 'get_gameplay_knowledge_base'`

**解决**：
1. 检查 `gameplay_knowledge_base.py` 文件是否存在
2. 检查文件语法是否正确
3. 确保在正确的目录下运行
