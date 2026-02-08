# Agentic RAG - LUA地图脚本生成系统

一个基于Agentic RAG架构的智能系统，将自然语言输入转换为完整的LUA地图脚本。

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

### 前端界面

- ✅ 模型选择（GPT-4.1 / GPT-5.1）
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

首先提取规则文档（如果还没有）：
```bash
cd backend
python ../extract_rule.py
```

然后初始化知识库：
```bash
python init_kb.py
```

这将：
- 解析规则文档
- 构建函数文档索引
- 初始化向量数据库（如果安装了chromadb）

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

### 1. 选择模型和配置参数

- **模型选择**：选择GPT-4.1或GPT-5.1
- **Temperature**：控制输出的随机性（0-2）
- **Max Tokens**：生成的最大token数量（1000-8000）
- **Top P**：核采样参数（0-1）
- **Frequency/Presence Penalty**：控制重复和话题多样性

### 2. 选择Agent模式

- **标准模式**：单次生成，速度快
- **迭代模式**：多次优化，质量高
- **多Agent协作**：规划、生成、验证分离，最准确

### 3. 输入自然语言描述

详细描述你想要创建的地图，例如：

```
创建一个新手村地图，包含：
- 中央有一个中世纪风格的村庄，有酒馆、商店和铁匠铺
- 村庄北边是一片迷雾森林，有1-5级的怪物
- 村庄东南角有一个废弃矿洞入口
- 村庄和各个区域之间有道路连接
```

### 4. 生成LUA脚本

点击"生成LUA脚本"按钮，系统将：
1. 分析你的需求
2. 规划生成步骤
3. 生成LUA代码
4. 验证和优化代码

### 5. 使用生成的代码

- **复制**：点击复制按钮复制代码
- **下载**：点击下载按钮保存为.lua文件
- **格式化**：点击格式化按钮美化代码

## 生成流程

系统按照以下8个步骤生成LUA脚本：

1. **创建地图** - 初始化地图对象
2. **塑造地形** - 添加地形特征（山、湖、平原）
3. **划分Block区域** - 创建功能区域
4. **填充Block内容** - 添加建筑、NPC、敌人等
5. **建立连接** - 添加道路连接
6. **自动化处理** - 自动添加植被、装饰等
7. **设置氛围** - 配置时间、天气、音效
8. **验证并构建** - 验证代码并构建地图

## API文档

### POST /api/generate

生成LUA脚本

**请求体：**
```json
{
    "input": "用户输入的自然语言描述",
    "config": {
        "model": "gpt-4.1",
        "temperature": 0.7,
        "maxTokens": 4000,
        "topP": 0.9,
        "frequencyPenalty": 0.0,
        "presencePenalty": 0.0,
        "agentMode": "standard",
        "maxIterations": 3
    }
}
```

**响应：**
```json
{
    "success": true,
    "luaScript": "生成的LUA代码",
    "model": "gpt-4.1",
    "agentMode": "standard"
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

系统采用基于功能模块的RAG检索策略：

1. **功能识别**: 分析用户输入，识别需要的功能模块（P1-P8）
2. **语义检索**: 在向量数据库中检索相关函数文档
3. **文档注入**: 将检索到的函数文档注入到LLM提示词
4. **代码生成**: LLM基于检索到的文档生成准确的LUA代码

详细说明请参考 [RAG架构文档](backend/README_RAG.md)

## 项目结构

```
Agentic RAG/
├── index.html              # 前端主页面
├── styles.css              # 样式文件
├── app.js                  # 前端逻辑
├── extract_rule.py         # 规则文档提取脚本
├── rule_extracted.json     # 提取的规则文档（JSON）
├── rule_extracted.txt      # 提取的规则文档（文本）
├── Rule.docx               # 原始规则文档
├── backend/
│   ├── app.py              # Flask后端应用（集成RAG）
│   ├── knowledge_base.py   # 知识库管理模块
│   ├── init_kb.py         # 知识库初始化脚本
│   ├── requirements.txt   # Python依赖
│   ├── README_RAG.md      # RAG架构文档
│   ├── chroma_db/         # 向量数据库（自动创建）
│   └── .env               # 环境变量（需创建）
└── README.md              # 项目说明
```

## 技术栈

- **前端**：HTML5, CSS3, JavaScript (ES6+)
- **后端**：Python, Flask
- **AI模型**：OpenAI GPT-4.1 / GPT-5.1
- **架构**：Agentic RAG

## 注意事项

1. **API密钥**：需要配置OpenAI API密钥才能使用真实模型
2. **规则文档**：系统会自动从 `Rule.docx` 提取规则并构建知识库
3. **向量数据库**：安装 `chromadb` 和 `sentence-transformers` 以启用语义检索
4. **代码验证**：生成的代码需要在实际环境中测试
5. **网络连接**：需要网络连接以调用OpenAI API
6. **知识库初始化**：首次使用前需要运行 `init_kb.py` 初始化知识库

## 开发计划

- [x] 实现规则文档的RAG检索
- [x] 基于功能模块的智能检索
- [x] 向量数据库集成
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
