#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
知识库初始化脚本
用于构建和初始化向量数据库
"""

import os
import sys
import io

# 设置UTF-8编码输出（Windows兼容）
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from knowledge_base import KnowledgeBase

def main():
    """初始化知识库"""
    print("=" * 60)
    print("Agentic RAG Knowledge Base Initialization")
    print("=" * 60)
    
    # 检查规则文件
    rule_file = os.path.join(os.path.dirname(__file__), "..", "rule_extracted.json")
    if not os.path.exists(rule_file):
        print(f"\n[ERROR] Rule file not found: {rule_file}")
        print("Please run extract_rule.py first to extract rule document")
        return 1
    
    print(f"\n[OK] Found rule file: {rule_file}")
    
    # 初始化知识库
    print("\nInitializing knowledge base...")
    try:
        kb = KnowledgeBase(rule_file="rule_extracted.json")
        
        print(f"\n[OK] Successfully loaded {len(kb.functions)} function documents")
        
        # 检查向量数据库
        if kb.vector_db:
            print(f"[OK] Vector database initialized with {kb.vector_db.count()} documents")
        else:
            print("[WARNING] Vector database not initialized (will use text matching)")
            print("  Install chromadb and sentence-transformers to enable vector search:")
            print("  pip install chromadb sentence-transformers")
        
        # 测试检索
        print("\nTesting retrieval function...")
        test_query = "创建一个有村庄和森林的地图"
        modules = kb.identify_required_modules(test_query)
        print(f"  Query: {test_query}")
        print(f"  Identified modules: {modules}")
        
        functions = kb.retrieve_functions(modules=modules, query=test_query, top_k=5)
        print(f"  Retrieved {len(functions)} relevant functions:")
        for func in functions[:5]:
            print(f"    - {func.lua_signature}")
        
        print("\n" + "=" * 60)
        print("Knowledge base initialization completed!")
        print("=" * 60)
        return 0
        
    except Exception as e:
        print(f"\n[ERROR] Initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
