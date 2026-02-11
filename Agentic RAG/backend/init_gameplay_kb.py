"""
初始化奇遇知识库
解析gameplay_knowledge_base.md，构建向量数据库
"""

import sys
import io
import os

# Windows UTF-8支持
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from gameplay_knowledge_base import GameplayKnowledgeBase

def main():
    print("=" * 60)
    print("初始化奇遇知识库")
    print("=" * 60)
    
    try:
        # 创建知识库实例（会自动加载和索引）
        print("\n[1/2] 加载知识库文档...")
        kb = GameplayKnowledgeBase()
        
        if not kb.functions:
            print("警告: 未找到任何函数文档！")
            print("请确保 gameplay_knowledge_base.md 文件存在且格式正确。")
            return False
        
        print(f"✓ 已加载 {len(kb.functions)} 个API函数文档")
        
        # 检查向量数据库
        print("\n[2/2] 检查向量数据库...")
        if kb.collection:
            # 获取集合中的文档数量
            try:
                count = kb.collection.count()
                print(f"✓ 向量数据库已初始化，包含 {count} 个文档")
            except:
                print("✓ 向量数据库已初始化")
        else:
            print("⚠ 向量数据库未初始化（将使用文本匹配模式）")
        
        print("\n" + "=" * 60)
        print("奇遇知识库初始化完成！")
        print("=" * 60)
        
        # 显示模块统计
        print("\n模块统计：")
        module_counts = {}
        for func in kb.functions:
            module = func.module
            module_counts[module] = module_counts.get(module, 0) + 1
        
        for module, count in sorted(module_counts.items()):
            print(f"  {module}: {count} 个函数")
        
        return True
        
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
