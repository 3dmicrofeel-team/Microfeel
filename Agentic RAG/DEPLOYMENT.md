# 部署指南 - 一步步实现Agentic RAG系统

## 前置要求

- Python 3.8 或更高版本
- pip 包管理器
- 网络连接（用于下载依赖和调用API）

## 第一步：检查Python环境

打开终端（PowerShell或CMD），运行：

```bash
python --version
```

**预期输出**: Python 3.8.x 或更高版本

如果未安装Python，请访问 https://www.python.org/downloads/ 下载安装。

---

## 第二步：安装Python依赖

### 2.1 进入项目目录

```bash
cd "d:\vibe coding\Microfeel\Agentic RAG"
```

### 2.2 安装基础依赖

```bash
cd backend
pip install flask flask-cors openai python-dotenv python-docx
```

**验证**: 如果看到 "Successfully installed" 表示成功。

### 2.3 安装向量数据库依赖（可选但推荐）

```bash
pip install chromadb sentence-transformers numpy
```

**注意**: 
- 如果安装失败，可以跳过这一步，系统会使用文本匹配模式
- 安装可能需要几分钟时间

**验证**:
```bash
python -c "import chromadb; print('ChromaDB installed')"
python -c "import sentence_transformers; print('SentenceTransformers installed')"
```

---

## 第三步：提取规则文档

### 3.1 返回项目根目录

```bash
cd ..
```

### 3.2 运行提取脚本

```bash
python extract_rule.py
```

**预期输出**:
```
成功提取 61 个段落和 15 个表格
内容已保存到 rule_extracted.json 和 rule_extracted.txt
```

### 3.3 验证文件生成

检查以下文件是否存在：
- `rule_extracted.json`
- `rule_extracted.txt`

```bash
dir rule_extracted.*
```

---

## 第四步：初始化知识库

### 4.1 进入backend目录

```bash
cd backend
```

### 4.2 运行初始化脚本

```bash
python init_kb.py
```

**预期输出**:
```
============================================================
Agentic RAG 知识库初始化
============================================================

✓ 找到规则文件: ...\rule_extracted.json

正在初始化知识库...
✓ 成功加载 XX 个函数文档
✓ 向量数据库已初始化，包含 XX 个文档
（或者：⚠ 向量数据库未初始化（将使用文本匹配模式））

测试检索功能...
  查询: 创建一个有村庄和森林的地图
  识别模块: ['P1', 'P2', 'P3', 'P8']
  检索到 X 个相关函数:
    - Env.CreateMap(...)
    - Env.AddBlock(...)
    ...

============================================================
知识库初始化完成！
============================================================
```

### 4.3 验证知识库

如果看到 "知识库初始化完成！" 表示成功。

---

## 第五步：配置API密钥（可选）

### 5.1 创建.env文件

在 `backend` 目录下创建 `.env` 文件：

**Windows PowerShell**:
```powershell
cd backend
New-Item -Path .env -ItemType File
```

**Windows CMD**:
```cmd
cd backend
type nul > .env
```

### 5.2 编辑.env文件

打开 `.env` 文件，添加：

```
OPENAI_API_KEY=your_api_key_here
```

**注意**: 
- 将 `your_api_key_here` 替换为你的实际API密钥
- 如果没有API密钥，系统会使用模拟数据（用于测试）

---

## 第六步：启动后端服务

### 6.1 确保在backend目录

```bash
cd backend
```

### 6.2 启动Flask服务器

```bash
python app.py
```

**预期输出**:
```
 * Running on http://0.0.0.0:5000
 * Debug mode: on
```

**重要**: 保持这个终端窗口打开，不要关闭！

### 6.3 验证后端运行

打开新的终端窗口，测试API：

```bash
curl http://localhost:5000/api/health
```

**预期输出**:
```json
{"status":"healthy","service":"Agentic RAG API"}
```

或者使用浏览器访问: http://localhost:5000/api/health

---

## 第七步：启动前端

### 7.1 打开前端页面

有两种方式：

**方式1: 直接打开文件**
- 在文件管理器中找到 `index.html`
- 双击打开（会在默认浏览器中打开）

**方式2: 使用本地服务器（推荐）**

打开新的终端窗口：

```bash
cd "d:\vibe coding\Microfeel\Agentic RAG"
python -m http.server 8080
```

然后在浏览器中访问: http://localhost:8080

### 7.2 验证前端加载

你应该看到：
- 左侧：模型配置和Agent配置面板
- 中间：自然语言输入框和输出区域
- 右侧：规则参考面板

---

## 第八步：测试完整流程

### 8.1 在前端页面测试

1. **选择模型**: 选择 GPT-4.1 或 GPT-5.1
2. **输入测试内容**:
```
创建一个新手村地图，包含：
- 中央有一个中世纪风格的村庄
- 村庄北边是一片森林
- 村庄和森林之间有道路连接
```
3. **点击"生成LUA脚本"按钮**

### 8.2 观察生成过程

- 状态栏会显示"正在生成中..."
- 进度条会逐渐填充
- 生成的LUA代码会显示在输出区域

### 8.3 验证输出

生成的代码应该包含：
- `function CreateStarterZone()`
- `Env.CreateMap(...)`
- `Env.AddBlock(...)`
- `Env.AddRoad(...)`
- `Env.BuildAsync(...)`

---

## 第九步：验证RAG功能

### 9.1 测试功能识别

打开Python交互式环境：

```bash
cd backend
python
```

然后运行：

```python
from knowledge_base import get_knowledge_base

kb = get_knowledge_base()
modules = kb.identify_required_modules("创建一个有村庄和森林的地图")
print(f"识别到的模块: {modules}")
```

**预期输出**: `识别到的模块: ['P1', 'P2', 'P3', 'P8']`

### 9.2 测试函数检索

继续在Python中运行：

```python
functions = kb.retrieve_functions(
    modules=['P1', 'P2', 'P3'],
    query="村庄",
    top_k=5
)

print(f"检索到 {len(functions)} 个函数:")
for func in functions:
    print(f"  - {func.lua_signature}")
```

**预期输出**: 应该看到相关的函数列表，如 `Env.CreateMap`, `Env.AddBlock` 等

---

## 常见问题排查

### 问题1: Python命令不存在

**解决**: 
- 确保Python已安装并添加到PATH
- 尝试使用 `python3` 或 `py` 命令

### 问题2: pip安装失败

**解决**:
```bash
python -m pip install --upgrade pip
pip install flask flask-cors openai python-dotenv python-docx
```

### 问题3: 规则文件提取失败

**解决**:
- 确保 `Rule.docx` 文件存在
- 检查是否安装了 `python-docx`: `pip install python-docx`

### 问题4: 知识库初始化失败

**解决**:
- 确保 `rule_extracted.json` 文件存在
- 检查文件路径是否正确
- 查看错误信息，可能需要安装缺失的依赖

### 问题5: 后端启动失败（端口被占用）

**解决**:
- 修改 `backend/app.py` 中的端口号：
```python
app.run(debug=True, host='0.0.0.0', port=5001)  # 改为5001或其他端口
```
- 同时更新前端 `app.js` 中的API地址

### 问题6: 前端无法连接后端

**解决**:
1. 确保后端正在运行（检查终端窗口）
2. 检查 `app.js` 中的API地址是否正确
3. 检查浏览器控制台是否有错误（F12打开开发者工具）

### 问题7: 生成失败或返回错误

**解决**:
- 如果没有配置API密钥，这是正常的（会使用模拟数据）
- 如果配置了API密钥，检查：
  - API密钥是否正确
  - 网络连接是否正常
  - API配额是否充足

---

## 部署检查清单

完成以下检查，确保系统正常运行：

- [ ] Python环境已安装（3.8+）
- [ ] 所有依赖已安装
- [ ] 规则文档已提取（rule_extracted.json存在）
- [ ] 知识库已初始化（init_kb.py运行成功）
- [ ] 后端服务已启动（http://localhost:5000可访问）
- [ ] 前端页面可正常打开
- [ ] 可以成功生成LUA代码
- [ ] RAG检索功能正常（可选）

---

## 下一步

系统部署完成后，你可以：

1. **自定义配置**: 修改模型参数、Agent模式等
2. **扩展知识库**: 添加更多函数文档或规则
3. **优化检索**: 调整检索策略和参数
4. **集成真实API**: 配置OpenAI API密钥使用真实模型

---

## 获取帮助

如果遇到问题：

1. 检查错误信息
2. 查看 `README.md` 和 `backend/README_RAG.md`
3. 验证每个步骤的输出是否符合预期
4. 检查常见问题排查部分

祝部署顺利！🎉
