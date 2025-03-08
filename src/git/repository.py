import git

class GitRepository:
    def __init__(self, repo_path=None):
        """初始化Git倉庫對象"""
        self.repo = None
        if repo_path:
            self.open(repo_path)
    
    def open(self, path):
        """打開指定路徑的Git倉庫"""
        try:
            self.repo = git.Repo(path)
            return True
        except git.InvalidGitRepositoryError:
            return False
    
    def get_staged_files(self):
        """獲取已暫存的文件列表"""
        if not self.repo:
            return []
        
        return [item.a_path for item in self.repo.index.diff("HEAD")]
    
    def get_unstaged_files(self):
        """獲取未暫存的文件列表"""
        if not self.repo:
            return []
        
        return [item.a_path for item in self.repo.index.diff(None)]
    
    def get_file_diff(self, file_path):
        """獲取指定文件的差異"""
        if not self.repo:
            return ""
        
        # 實現獲取文件差異的邏輯
        # ...

    def commit(self, message):
        """提交變更"""
        if not self.repo:
            return False
        
        try:
            self.repo.git.commit('-m', message)
            return True
        except:
            return False 