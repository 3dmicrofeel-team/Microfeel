# 快速启动指南

## 🚀 5分钟快速开始

### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 初始化知识库

```bash
# 提取规则文档（如果还没有）
python ../extract_rule.py

# 初始化知识库
cd backend
python init_kb.py
```

### 3. 启动系统

**双击运行**：
```
启动.bat
```

系统会自动启动并打开浏览器！

### 4. 开始使用

在前端页面输入地图描述，点击"生成LUA脚本"即可。

---

## 📚 详细文档

- `使用指南.md` - 完整使用说明
- `README.md` - 项目总览
- `DEPLOYMENT.md` - 详细部署文档

## ⚠️ 常见问题

### 端口被占用

启动脚本会自动查找可用端口，无需手动处理。

### 知识库未初始化

运行：`cd backend && python init_kb.py`

### API密钥（可选）

编辑 `backend/.env` 添加：`OPENAI_API_KEY=your_key`

没有API密钥时，系统会使用模拟数据（用于测试）。

---

## 📖 更多帮助

- `使用指南.md` - 详细使用说明和故障排除
- `README.md` - 完整项目文档
- `DEPLOYMENT.md` - 部署指南
