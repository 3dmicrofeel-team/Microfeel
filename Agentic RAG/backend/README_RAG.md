# Agentic RAG 系统架构说明

## 系统架构

```
用户输入
    ↓
功能识别Agent (识别需要的模块: P1-P8)
    ↓
RAG检索 (根据模块和查询检索相关函数)
    ↓
函数文档注入 (将检索结果注入到提示词)
    ↓
LLM生成 (基于检索到的函数文档生成代码)
    ↓
LUA脚本输出
```

## 核心组件

### 1. 知识库 (KnowledgeBase)

**位置**: `backend/knowledge_base.py`

**功能**:
- 解析规则文档 (`rule_extracted.json`)
- 按功能模块组织函数文档
- 构建向量数据库（使用ChromaDB）
- 实现语义检索和文本匹配

**关键方法**:
- `identify_required_modules(user_input)`: 识别用户需求中需要的功能模块
- `retrieve_functions(modules, query, top_k)`: 检索相关函数文档
- `get_function_docs_text(functions)`: 将函数文档转换为文本格式

### 2. 功能模块映射

系统将LUA API分为8个主要模块：

- **P1**: Map创建与地形
- **P2**: Block管理
- **P3**: Block内容填充
- **P4**: Block连接系统
- **P5**: 自动化工具
- **P6**: 程序化生成
- **P7**: 氛围设置
- **P8**: 存储与构建
- **R1-R6**: 运行时API

### 3. RAG检索流程

#### 步骤1: 功能识别
```python
modules = kb.identify_required_modules(user_input)
# 示例: ["P1", "P2", "P3", "P8"]
```

#### 步骤2: 语义检索
```python
functions = kb.retrieve_functions(
    modules=modules,
    query=user_input,
    top_k=40
)
```

#### 步骤3: 文档注入
```python
function_docs = kb.get_function_docs_text(functions)
# 注入到LLM提示词中
```

## 使用方式

### 1. 初始化知识库

```bash
cd backend
python init_kb.py
```

### 2. 在代码中使用

```python
from knowledge_base import get_knowledge_base

kb = get_knowledge_base()

# 识别模块
modules = kb.identify_required_modules("创建一个有村庄和森林的地图")

# 检索函数
functions = kb.retrieve_functions(modules=modules, query="村庄", top_k=10)

# 获取文档文本
docs = kb.get_function_docs_text(functions)
```

## 向量数据库

### 安装依赖

```bash
pip install chromadb sentence-transformers
```

### 数据库位置

向量数据库存储在 `backend/chroma_db/` 目录下。

### 嵌入模型

默认使用 `paraphrase-multilingual-MiniLM-L12-v2`，支持中英文。

## 检索策略

### 1. 关键词匹配

系统维护了一个功能标签到模块的映射表 (`FUNCTION_TO_MODULE`)，用于快速识别需要的模块。

### 2. 语义检索

如果安装了向量数据库，系统会：
1. 将用户查询转换为向量
2. 在向量数据库中搜索相似文档
3. 返回最相关的函数文档

### 3. 文本匹配

如果没有向量数据库，系统会使用简单的文本匹配：
- 匹配函数名中的关键词
- 匹配函数描述中的关键词
- 按匹配度排序

## 配置选项

### 检索参数

- `top_k`: 返回的函数数量（默认20-40）
- `modules`: 限制检索的模块范围
- `query`: 语义查询文本

### 向量数据库配置

在 `knowledge_base.py` 中可以修改：
- 嵌入模型
- 数据库路径
- 集合名称

## 性能优化

1. **模块预过滤**: 先按模块过滤，减少检索范围
2. **缓存机制**: 知识库使用单例模式，避免重复加载
3. **批量检索**: 一次性检索多个函数，减少数据库查询

## 故障排除

### 问题1: 向量数据库未初始化

**原因**: 未安装 chromadb 或 sentence-transformers

**解决**:
```bash
pip install chromadb sentence-transformers
```

### 问题2: 规则文件不存在

**原因**: 未提取规则文档

**解决**:
```bash
cd backend
python ../extract_rule.py
```

### 问题3: 检索结果不准确

**解决**:
1. 检查 `FUNCTION_TO_MODULE` 映射是否完整
2. 调整 `top_k` 参数
3. 优化用户输入的描述

## 扩展开发

### 添加新的功能标签

在 `knowledge_base.py` 的 `FUNCTION_TO_MODULE` 中添加：

```python
"新功能": ["P1", "P2"]
```

### 自定义检索策略

重写 `retrieve_functions` 方法，实现自定义检索逻辑。

### 添加新的模块

1. 在 `MODULE_MAPPING` 中添加模块定义
2. 更新规则文档解析逻辑
3. 添加功能标签映射
