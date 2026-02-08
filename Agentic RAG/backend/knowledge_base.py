"""
知识库管理模块
处理规则文档，构建向量数据库，实现RAG检索
"""

import json
import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import re

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    print("警告: chromadb未安装，将使用内存存储。运行: pip install chromadb")

try:
    from sentence_transformers import SentenceTransformer
    EMBEDDING_AVAILABLE = True
except ImportError:
    EMBEDDING_AVAILABLE = False
    print("警告: sentence-transformers未安装，将使用简单文本匹配。运行: pip install sentence-transformers")


@dataclass
class FunctionDoc:
    """函数文档数据结构"""
    lua_signature: str
    cpp_signature: str
    description: str
    parameters: str
    example: str
    module: str  # P1-P8, R1-R6
    category: str  # 创建、地形、内容、连接等
    atomicity: str  # ★★★, ★★☆等
    llm_suitability: str  # 极高、高、中等
    tags: List[str]  # 功能标签


class KnowledgeBase:
    """知识库管理器"""
    
    # 功能模块映射
    MODULE_MAPPING = {
        "P1": "Map创建与地形",
        "P2": "Block管理",
        "P3": "Block内容填充",
        "P4": "Block连接系统",
        "P5": "自动化工具",
        "P6": "程序化生成",
        "P7": "氛围设置",
        "P8": "存储与构建",
        "R1-R6": "运行时API"
    }
    
    # 功能标签到模块的映射（用于检索）
    FUNCTION_TO_MODULE = {
        # 地图创建
        "创建地图": ["P1"],
        "CreateMap": ["P1"],
        "地图": ["P1"],
        
        # 地形
        "地形": ["P1"],
        "Terrain": ["P1"],
        "山丘": ["P1"],
        "湖泊": ["P1"],
        "水体": ["P1"],
        "RaiseTerrain": ["P1"],
        "LowerTerrain": ["P1"],
        "AddWaterBody": ["P1"],
        
        # Block
        "Block": ["P2"],
        "区域": ["P2"],
        "AddBlock": ["P2"],
        "SetBlockType": ["P2"],
        
        # 内容填充
        "建筑": ["P3"],
        "Building": ["P3"],
        "NPC": ["P3"],
        "敌人": ["P3"],
        "Enemy": ["P3"],
        "道具": ["P3"],
        "Prop": ["P3"],
        "AddBuilding": ["P3"],
        "AddNPCSpawn": ["P3"],
        "AddEnemySpawn": ["P3"],
        "AddProp": ["P3"],
        "AddSpawnPoint": ["P3"],
        
        # 连接
        "道路": ["P4"],
        "Road": ["P4"],
        "连接": ["P4"],
        "AddRoad": ["P4"],
        "AddBridge": ["P4"],
        "AddTeleport": ["P4"],
        
        # 自动化
        "自动": ["P5"],
        "Auto": ["P5"],
        "美化": ["P5"],
        "装饰": ["P5"],
        "植被": ["P5"],
        "AutoPaintTerrain": ["P5"],
        "AutoAddVegetation": ["P5"],
        "AutoDecorate": ["P5"],
        "AutoGenerateRoads": ["P5"],
        
        # 程序化生成
        "程序化": ["P6"],
        "生成": ["P6"],
        "Gen": ["P6"],
        "GenVillageBlock": ["P6"],
        "GenForestBlock": ["P6"],
        "GenDungeonBlock": ["P6"],
        
        # 氛围
        "氛围": ["P7"],
        "时间": ["P7"],
        "天气": ["P7"],
        "音效": ["P7"],
        "SetTimeOfDay": ["P7"],
        "SetWeather": ["P7"],
        "SetAmbientSound": ["P7"],
        
        # 构建
        "构建": ["P8"],
        "验证": ["P8"],
        "保存": ["P8"],
        "Build": ["P8"],
        "ValidateMap": ["P8"],
        "SaveMap": ["P8"],
        
        # 运行时
        "运行时": ["R1-R6"],
        "Runtime": ["R1-R6"],
        "Spawn": ["R1-R6"],
    }
    
    def __init__(self, rule_file: str = "rule_extracted.json"):
        """初始化知识库"""
        self.rule_file = rule_file
        self.functions: List[FunctionDoc] = []
        self.vector_db = None
        self.embedding_model = None
        
        # 加载规则文档
        self._load_rules()
        
        # 初始化向量数据库
        if CHROMADB_AVAILABLE:
            self._init_vector_db()
        else:
            print("使用简单文本匹配模式")
    
    def _load_rules(self):
        """从JSON文件加载规则"""
        # 尝试多个可能的路径
        possible_paths = [
            os.path.join(os.path.dirname(__file__), "..", self.rule_file),
            os.path.join(os.path.dirname(__file__), self.rule_file),
            self.rule_file
        ]
        
        rule_path = None
        for path in possible_paths:
            if os.path.exists(path):
                rule_path = path
                break
        
        if not rule_path or not os.path.exists(rule_path):
            print(f"警告: 规则文件不存在，尝试的路径: {possible_paths}")
            return
        
        with open(rule_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 解析表格数据
        tables = data.get('tables', [])
        
        # 模块映射（根据表格顺序）
        module_order = ["P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8", "R1-R6"]
        
        for table_idx, table in enumerate(tables):
            if table_idx >= len(module_order):
                module = "Other"
            else:
                module = module_order[table_idx]
            
            # 跳过表头
            for row_idx, row in enumerate(table[1:], start=1):
                if len(row) < 5:
                    continue
                
                try:
                    func_doc = FunctionDoc(
                        lua_signature=row[0] if len(row) > 0 else "",
                        cpp_signature=row[1] if len(row) > 1 else "",
                        description=row[2] if len(row) > 2 else "",
                        parameters=row[3] if len(row) > 3 else "",
                        example=row[4] if len(row) > 4 else "",
                        module=module,
                        category=self._extract_category(row[0]),
                        atomicity="",
                        llm_suitability="",
                        tags=self._extract_tags(row[0], row[2])
                    )
                    self.functions.append(func_doc)
                except Exception as e:
                    print(f"解析函数文档时出错 (表格{table_idx}, 行{row_idx}): {e}")
        
        print(f"已加载 {len(self.functions)} 个函数文档")
    
    def _extract_category(self, lua_sig: str) -> str:
        """从函数签名提取类别"""
        if "CreateMap" in lua_sig:
            return "创建"
        elif "Terrain" in lua_sig or "Water" in lua_sig:
            return "地形"
        elif "Block" in lua_sig:
            return "Block管理"
        elif "Building" in lua_sig or "NPC" in lua_sig or "Enemy" in lua_sig or "Prop" in lua_sig:
            return "内容填充"
        elif "Road" in lua_sig or "Bridge" in lua_sig or "Connection" in lua_sig:
            return "连接"
        elif "Auto" in lua_sig:
            return "自动化"
        elif "Gen" in lua_sig:
            return "程序化生成"
        elif "Time" in lua_sig or "Weather" in lua_sig or "Sound" in lua_sig or "Ambience" in lua_sig:
            return "氛围"
        elif "Build" in lua_sig or "Validate" in lua_sig or "Save" in lua_sig:
            return "构建"
        elif "Spawn" in lua_sig or "Runtime" in lua_sig:
            return "运行时"
        return "其他"
    
    def _extract_tags(self, lua_sig: str, description: str) -> List[str]:
        """提取功能标签"""
        tags = []
        text = (lua_sig + " " + description).lower()
        
        # 提取函数名
        match = re.search(r'Env\.(\w+)', lua_sig)
        if match:
            func_name = match.group(1)
            tags.append(func_name)
            
            # 分解驼峰命名
            words = re.findall(r'[A-Z][a-z]*', func_name)
            tags.extend([w.lower() for w in words])
        
        # 从描述中提取关键词
        keywords = ["地图", "地形", "建筑", "npc", "敌人", "道路", "自动", "生成", 
                   "氛围", "构建", "保存", "验证", "运行时", "block", "terrain", 
                   "building", "road", "auto", "spawn"]
        for keyword in keywords:
            if keyword in text:
                tags.append(keyword)
        
        return list(set(tags))
    
    def _init_vector_db(self):
        """初始化向量数据库"""
        if not CHROMADB_AVAILABLE:
            return
        
        # 初始化嵌入模型
        if EMBEDDING_AVAILABLE:
            try:
                self.embedding_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
                print("已加载多语言嵌入模型")
            except Exception as e:
                print(f"加载嵌入模型失败: {e}，使用简单文本匹配")
                self.embedding_model = None
        else:
            self.embedding_model = None
        
        # 初始化ChromaDB（使用新版本API）
        try:
            # 使用新版本的ChromaDB客户端
            client = chromadb.PersistentClient(path="./chroma_db")
            
            # 获取或创建集合
            self.vector_db = client.get_or_create_collection(
                name="lua_functions",
                metadata={"description": "LUA API function documents"}
            )
            
            # 如果集合为空，添加文档
            if self.vector_db.count() == 0:
                self._index_functions()
            
            print(f"向量数据库已初始化，包含 {self.vector_db.count()} 个文档")
            
        except Exception as e:
            print(f"初始化向量数据库失败: {e}")
            self.vector_db = None
    
    def _index_functions(self):
        """将函数文档索引到向量数据库"""
        if not self.vector_db or not self.embedding_model:
            return
        
        documents = []
        metadatas = []
        ids = []
        
        for idx, func in enumerate(self.functions):
            # 构建文档文本
            doc_text = f"""
函数: {func.lua_signature}
说明: {func.description}
参数: {func.parameters}
示例: {func.example}
模块: {func.module}
类别: {func.category}
标签: {', '.join(func.tags)}
"""
            documents.append(doc_text.strip())
            
            metadata = {
                "lua_signature": func.lua_signature,
                "module": func.module,
                "category": func.category,
                "tags": ",".join(func.tags)
            }
            metadatas.append(metadata)
            ids.append(f"func_{idx}")
        
        # 生成嵌入向量
        embeddings = self.embedding_model.encode(documents).tolist()
        
        # 添加到数据库
        self.vector_db.add(
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        
        print(f"已索引 {len(documents)} 个函数文档")
    
    def identify_required_modules(self, user_input: str) -> List[str]:
        """识别用户需求中需要的功能模块"""
        user_lower = user_input.lower()
        required_modules = set()
        
        # 基于关键词匹配
        for keyword, modules in self.FUNCTION_TO_MODULE.items():
            if keyword.lower() in user_lower:
                required_modules.update(modules)
        
        # 如果没有匹配到，返回核心模块
        if not required_modules:
            required_modules = {"P1", "P2", "P3", "P8"}
        
        return sorted(list(required_modules))
    
    def retrieve_functions(self, modules: List[str] = None, query: str = None, top_k: int = 20) -> List[FunctionDoc]:
        """检索相关函数"""
        results = []
        
        # 如果指定了模块，先按模块过滤
        if modules:
            filtered_funcs = [f for f in self.functions if f.module in modules]
        else:
            filtered_funcs = self.functions
        
        # 如果有查询词，进行语义检索
        if query and self.vector_db and self.embedding_model:
            try:
                # 生成查询向量
                query_embedding = self.embedding_model.encode([query]).tolist()[0]
                
                # 检索
                db_results = self.vector_db.query(
                    query_embeddings=[query_embedding],
                    n_results=min(top_k, len(filtered_funcs)),
                    where={"module": {"$in": modules}} if modules else None
                )
                
                # 匹配结果
                retrieved_ids = db_results['ids'][0] if db_results['ids'] else []
                retrieved_funcs = {}
                
                for func_id in retrieved_ids:
                    idx = int(func_id.split('_')[1])
                    if idx < len(self.functions):
                        retrieved_funcs[idx] = self.functions[idx]
                
                # 合并模块过滤和语义检索的结果
                for func in filtered_funcs:
                    func_idx = self.functions.index(func)
                    if func_idx in retrieved_funcs or not query:
                        results.append(func)
                
                # 去重
                seen = set()
                unique_results = []
                for func in results:
                    sig = func.lua_signature
                    if sig not in seen:
                        seen.add(sig)
                        unique_results.append(func)
                
                results = unique_results[:top_k]
                
            except Exception as e:
                print(f"向量检索失败: {e}，使用文本匹配")
                results = self._text_search(filtered_funcs, query, top_k)
        else:
            # 简单文本搜索
            results = self._text_search(filtered_funcs, query, top_k)
        
        return results
    
    def _text_search(self, funcs: List[FunctionDoc], query: str, top_k: int) -> List[FunctionDoc]:
        """简单文本搜索"""
        if not query:
            return funcs[:top_k]
        
        query_lower = query.lower()
        scored_funcs = []
        
        for func in funcs:
            score = 0
            text = (func.lua_signature + " " + func.description + " " + func.category).lower()
            
            # 关键词匹配
            for tag in func.tags:
                if tag.lower() in query_lower:
                    score += 2
            
            if query_lower in text:
                score += 1
            
            if score > 0:
                scored_funcs.append((score, func))
        
        # 按分数排序
        scored_funcs.sort(key=lambda x: x[0], reverse=True)
        
        return [f for _, f in scored_funcs[:top_k]]
    
    def get_function_docs_text(self, functions: List[FunctionDoc]) -> str:
        """将函数文档转换为文本格式，用于注入到提示词"""
        if not functions:
            return ""
        
        text_parts = []
        current_module = None
        
        for func in functions:
            if func.module != current_module:
                current_module = func.module
                module_name = self.MODULE_MAPPING.get(current_module, current_module)
                text_parts.append(f"\n## {module_name} ({current_module})\n")
            
            text_parts.append(f"### {func.lua_signature}")
            text_parts.append(f"**说明**: {func.description}")
            text_parts.append(f"**参数**: {func.parameters}")
            if func.example:
                text_parts.append(f"**示例**: {func.example}")
            text_parts.append("")
        
        return "\n".join(text_parts)


# 全局知识库实例
_kb_instance = None

def get_knowledge_base() -> KnowledgeBase:
    """获取知识库单例"""
    global _kb_instance
    if _kb_instance is None:
        _kb_instance = KnowledgeBase()
    return _kb_instance
