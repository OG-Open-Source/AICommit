import re
from collections import defaultdict

class CommitHelper:
    def __init__(self, repository):
        """初始化提交輔助對象"""
        self.repository = repository
    
    def analyze_changes(self):
        """分析變更並生成提交日誌建議"""
        staged_files = self.repository.get_staged_files()
        
        # 按文件類型分類
        file_types = defaultdict(list)
        for file in staged_files:
            ext = file.split('.')[-1] if '.' in file else 'other'
            file_types[ext].append(file)
        
        # 生成提交日誌建議
        suggestions = []
        
        if 'py' in file_types:
            suggestions.append(f"feat: update Python files ({len(file_types['py'])} files)")
        
        if 'js' in file_types:
            suggestions.append(f"feat: update JavaScript files ({len(file_types['js'])} files)")
        
        # 更多文件類型的處理...
        
        return suggestions
    
    def format_commit_message(self, type, scope, description, body=None, footer=None):
        """按照Conventional Commits格式化提交信息"""
        message = f"{type}"
        if scope:
            message += f"({scope})"
        message += f": {description}"
        
        if body:
            message += f"\n\n{body}"
        
        if footer:
            message += f"\n\n{footer}"
        
        return message 