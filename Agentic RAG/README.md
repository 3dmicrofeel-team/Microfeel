# Agentic RAG - LUA脚本生成系统

一个基于Agentic RAG架构的智能系统，支持两种生成模式：
- **地图生成**：将自然语言输入转换为完整的LUA地图脚本
- **奇遇生成**：将自然语言输入转换为完整的LUA奇遇脚本（World.SpawnEncounter）

## 系统架构

```
自然语言输入 → 功能识别 → RAG检索 → 函数文档注入 → LLM生成 → 完整LUA脚本
```

### Agentic RAG特点

- **智能检索**：根据用户需求自动识别功能模块，检索相关API函数文档
- **向量数据库**：使用ChromaDB存储函数文档，支持语义检索
- **动态规划**：Agent自主决定检索和生成策略
- **迭代优化**：支持多次迭代优化生成结果
- **多Agent协作**：规划Agent、代码生成Agent、验证Agent协同工作
- **自我验证**：自动检查代码质量和规范性
- **知识库驱动**：基于Rule.docx构建的知识库，确保生成的代码符合规范

## 功能特性

### 双模式支持

- ✅ **地图生成模式**：生成完整的地图LUA脚本（8步流程）
- ✅ **奇遇生成模式**：生成奇遇LUA脚本（4层工作流：故事扩写→玩法拆解→执行计划→Lua生成）
- ✅ **智能知识库切换**：根据选择的模式自动加载对应的向量数据库

### 前端界面

- ✅ 生成模式选择（地图生成/奇遇生成）
- ✅ NPC标签输入（奇遇模式）
- ✅ 模型选择（GPT-4.1 / GPT-5.1）
- ✅ API Key管理（前端输入和保存）
- ✅ 参数配置（Temperature, Max Tokens, Top P等）
- ✅ Agent模式选择（标准/迭代/多Agent协作）
- ✅ 自然语言输入
- ✅ 代码生成和显示
- ✅ 代码复制、下载、格式化

### 后端API

- ✅ RESTful API接口
- ✅ Agentic RAG核心系统
- ✅ 多模式生成支持
- ✅ 代码验证和优化

## 快速开始

### 1. 安装依赖

#### 前端
前端是纯HTML/CSS/JavaScript，无需安装，直接在浏览器中打开 `index.html` 即可。

#### 后端
```bash
cd backend
pip install -r requirements.txt
```

### 2. 初始化知识库

#### 地图知识库（必需）
首先提取规则文档（如果还没有）：
```bash
cd backend
python ../extract_rule.py
```

然后初始化地图知识库：
```bash
python init_kb.py
```

这将：
- 解析规则文档（`rule_extracted.json`）
- 构建函数文档索引
- 初始化向量数据库（`chroma_db`）

#### 奇遇知识库（必需）
初始化奇遇知识库：
```bash
python init_gameplay_kb.py
```

这将：
- 解析奇遇知识库文档（`gameplay_knowledge_base.md`）
- 构建函数文档索引
- 初始化向量数据库（`chroma_db_gameplay`）

**注意**：两个知识库都需要初始化才能使用对应的生成模式。

### 3. 配置API密钥

创建 `.env` 文件（在backend目录下）：
```
OPENAI_API_KEY=your_api_key_here
```

### 4. 启动系统

**双击运行**：
```
启动.bat
```

脚本会自动：
- ✅ 检查环境
- ✅ 智能查找可用端口
- ✅ 启动后端和前端
- ✅ 自动打开浏览器

详细说明请参考 `使用指南.md`

## 使用说明

### 1. 选择生成模式

- **🗺️ 地图生成**：生成完整的地图LUA脚本
- **⚔️ 奇遇生成**：生成奇遇LUA脚本（World.SpawnEncounter）

**奇遇模式额外配置**：
- **NPC标签**（可选）：输入NPC标签，如 `Tag_A, Tag_B, Tag_C`

### 2. 配置API Key（可选）

在前端界面输入OpenAI API Key：
- 输入API Key（格式：sk-...）
- 点击"保存"按钮
- 密钥会安全保存在浏览器本地存储中
- 如果不配置，系统会使用模拟数据（用于测试）

### 3. 选择模型和配置参数

- **模型选择**：选择GPT-4.1或GPT-5.1
- **Temperature**：控制输出的随机性（0-2）
- **Max Tokens**：生成的最大token数量（1000-8000）
- **Top P**：核采样参数（0-1）
- **Frequency/Presence Penalty**：控制重复和话题多样性

### 4. 选择Agent模式

- **标准模式**：单次生成，速度快
- **迭代模式**：多次优化，质量高
- **多Agent协作**：规划、生成、验证分离，最准确

### 5. 输入自然语言描述

**地图模式示例**：
```
创建一个新手村地图，包含：
- 中央有一个中世纪风格的村庄，有酒馆、商店和铁匠铺
- 村庄北边是一片迷雾森林，有1-5级的怪物
- 村庄东南角有一个废弃矿洞入口
- 村庄和各个区域之间有道路连接
```

**奇遇模式示例**：
```
我想要一个在酒馆发生的偷窃事件，玩家可以选择介入、旁观或离开。
```

### 6. 生成LUA脚本

点击"生成LUA脚本"按钮，系统将：
1. **地图模式**：按照8步流程生成地图脚本
2. **奇遇模式**：按照4层工作流生成奇遇脚本
   - Layer 1: 故事扩写
   - Layer 2: 玩法拆解
   - Layer 3: 执行计划
   - Layer 4: Lua代码生成

### 7. 使用生成的代码

- **复制**：点击复制按钮复制代码
- **下载**：点击下载按钮保存为.lua文件
- **格式化**：点击格式化按钮美化代码

## 生成流程

### 地图生成流程（8步）

系统按照以下8个步骤生成LUA地图脚本：

1. **创建地图** - 初始化地图对象
2. **塑造地形** - 添加地形特征（山、湖、平原）
3. **划分Block区域** - 创建功能区域
4. **填充Block内容** - 添加建筑、NPC、敌人等
5. **建立连接** - 添加道路连接
6. **自动化处理** - 自动添加植被、装饰等
7. **设置氛围** - 配置时间、天气、音效
8. **验证并构建** - 验证代码并构建地图

### 奇遇生成流程（4层工作流）

系统按照以下4层工作流生成LUA奇遇脚本：

1. **Layer 1: 故事扩写** - 将用户需求扩写为完整的故事背景（150-250字）
2. **Layer 2: 玩法拆解** - 将故事拆解为6-12个可执行的动作节点
3. **Layer 3: 执行计划** - 将动作节点转化为详细的脚本步骤链
4. **Layer 4: Lua代码生成** - 生成最终的World.SpawnEncounter代码

**奇遇输出格式**：
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
        -- Lua代码（无注释）
    ]]
)
```

## API文档

### POST /api/generate

生成LUA脚本

**请求体：**
```json
{
    "input": "用户输入的自然语言描述",
    "mode": "map",
    "npcTags": ["Tag_A", "Tag_B"],
    "config": {
        "model": "gpt-4.1",
        "temperature": 0.7,
        "maxTokens": 4000,
        "topP": 0.9,
        "frequencyPenalty": 0.0,
        "presencePenalty": 0.0,
        "agentMode": "standard",
        "maxIterations": 3,
        "apiKey": "sk-..."
    }
}
```

**参数说明**：
- `mode`: `"map"` 或 `"encounter"`（默认：`"map"`）
- `npcTags`: 奇遇模式的NPC标签列表（可选）
- `config.apiKey`: API密钥（可选，优先使用前端传入的）

**响应：**
```json
{
    "success": true,
    "luaScript": "生成的LUA代码",
    "model": "gpt-4.1",
    "agentMode": "standard",
    "mode": "map",
    "knowledgeBase": "map"
}
```

### GET /api/health

健康检查

**响应：**
```json
{
    "status": "healthy",
    "service": "Agentic RAG API"
}
```

## RAG检索流程

系统采用基于功能模块的RAG检索策略，根据生成模式自动切换知识库：

### 地图模式RAG流程

1. **功能识别**: 分析用户输入，识别需要的功能模块（P1-P8）
2. **语义检索**: 在地图知识库向量数据库（`chroma_db`）中检索相关函数文档
3. **文档注入**: 将检索到的函数文档注入到LLM提示词
4. **代码生成**: LLM基于检索到的文档生成准确的LUA地图代码

### 奇遇模式RAG流程

1. **功能识别**: 分析用户输入和NPC标签，识别需要的功能模块（World/UI/Performer/System等）
2. **语义检索**: 在奇遇知识库向量数据库（`chroma_db_gameplay`）中检索相关函数文档
3. **文档注入**: 将检索到的函数文档注入到LLM提示词
4. **4层工作流**: 故事扩写→玩法拆解→执行计划→Lua代码生成

### 知识库说明

- **地图知识库**：
  - 源文件：`rule_extracted.json`
  - 向量数据库：`backend/chroma_db`
  - 函数数量：根据Rule.docx提取的函数数量
  - 模块：P1-P8（地图创建、地形、Block管理等）

- **奇遇知识库**：
  - 源文件：`backend/gameplay_knowledge_base.md`
  - 向量数据库：`backend/chroma_db_gameplay`
  - 函数数量：46个API函数
  - 模块：World(10), UI(7), System(2), Entity(6), Performer(13), Math(3), Time(2)

详细说明请参考：
- [RAG架构文档](backend/README_RAG.md) - 地图生成RAG流程
- [奇遇生成说明](backend/README_ENCOUNTER.md) - 奇遇生成详细文档

## 项目结构

```
Agentic RAG/
├── index.html                      # 前端主页面
├── styles.css                      # 样式文件
├── app.js                          # 前端逻辑
├── extract_rule.py                 # 规则文档提取脚本
├── rule_extracted.json             # 提取的规则文档（JSON）
├── rule_extracted.txt              # 提取的规则文档（文本）
├── Rule.docx                       # 原始规则文档（地图API）
├── 启动.bat                        # 一键启动脚本
├── backend/
│   ├── app.py                      # Flask后端应用（集成RAG）
│   ├── knowledge_base.py           # 地图知识库管理模块
│   ├── gameplay_knowledge_base.py  # 奇遇知识库管理模块
│   ├── encounter_rag_system.py     # 奇遇RAG生成系统
│   ├── init_kb.py                  # 地图知识库初始化脚本
│   ├── init_gameplay_kb.py         # 奇遇知识库初始化脚本
│   ├── gameplay_knowledge_base.md  # 奇遇知识库文档
│   ├── gameplay_document.md         # 奇遇工作流文档
│   ├── requirements.txt            # Python依赖
│   ├── README_RAG.md               # RAG架构文档
│   ├── chroma_db/                  # 地图向量数据库（自动创建）
│   ├── chroma_db_gameplay/         # 奇遇向量数据库（自动创建）
│   └── .env                        # 环境变量（需创建）
└── README.md                       # 项目说明
```

## 技术栈

- **前端**：HTML5, CSS3, JavaScript (ES6+)
- **后端**：Python, Flask
- **AI模型**：OpenAI GPT-4.1 / GPT-5.1
- **架构**：Agentic RAG

## 注意事项

1. **API密钥**：
   - 可以在前端界面输入并保存（推荐）
   - 或创建 `backend/.env` 文件：`OPENAI_API_KEY=your_key`
   - 如果不配置，系统会使用模拟数据（用于测试）

2. **知识库初始化**：
   - **地图模式**：首次使用前需要运行 `python backend/init_kb.py`
   - **奇遇模式**：首次使用前需要运行 `python backend/init_gameplay_kb.py`
   - 启动脚本会自动检查并初始化（如果未初始化）

3. **向量数据库**：
   - 安装 `chromadb` 和 `sentence-transformers` 以启用语义检索
   - 地图知识库：`backend/chroma_db/`
   - 奇遇知识库：`backend/chroma_db_gameplay/`

4. **生成模式**：
   - 地图模式：使用地图知识库（`rule_extracted.json`）
   - 奇遇模式：使用奇遇知识库（`gameplay_knowledge_base.md`）
   - 系统会根据前端选择的模式自动切换知识库

5. **代码验证**：生成的代码需要在实际环境中测试

6. **网络连接**：需要网络连接以调用OpenAI API

## 知识库状态

### 地图知识库
- **状态**：✅ 已初始化
- **向量数据库**：`backend/chroma_db/`
- **函数数量**：根据Rule.docx提取的函数数量
- **模块**：P1-P8（地图创建、地形、Block管理等）

### 奇遇知识库
- **状态**：✅ 已初始化并完成向量化
- **向量数据库**：`backend/chroma_db_gameplay/`
- **函数数量**：46个API函数
- **向量文档数**：46个文档（已索引）
- **模块分布**：
  - World: 10个函数
  - UI: 7个函数
  - System: 2个函数
  - Entity: 6个函数
  - Performer: 13个函数
  - Math: 3个函数
  - Time: 2个函数
- **导入状态**：✅ 可以正常导入和使用

**验证命令**：
```bash
cd backend
python init_gameplay_kb.py  # 检查奇遇知识库状态
```

## 开发计划

- [x] 实现规则文档的RAG检索
- [x] 基于功能模块的智能检索
- [x] 向量数据库集成
- [x] 奇遇生成功能（4层工作流）
- [x] 双知识库支持（地图/奇遇）
- [x] 奇遇知识库向量化完成（46个函数）
- [x] 前端API Key管理
- [x] 生成模式切换
- [x] 智能知识库切换（根据模式自动加载）
- [ ] 支持更多LLM模型（Claude, Gemini等）
- [ ] 添加代码语法高亮
- [ ] 添加代码预览和测试功能
- [ ] 支持批量生成
- [ ] 添加历史记录功能
- [ ] 检索结果可视化
- [ ] 知识库增量更新

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！
