import sys
import os

# 添加專案根目錄到系統路徑
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

from PyQt5.QtWidgets import (QMainWindow, QApplication, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QTextEdit, QListWidget,
                            QLabel, QComboBox, QLineEdit, QSplitter)
from PyQt5.QtCore import Qt

# 使用絕對導入
from src.git.repository import GitRepository
from src.git.commit_helper import CommitHelper

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Commit Log Assistant")
        self.setMinimumSize(800, 600)
        
        self.repository = GitRepository()
        self.commit_helper = CommitHelper(self.repository)
        
        self.init_ui()
        
    def init_ui(self):
        """初始化用戶界面"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        
        # 倉庫選擇區域
        repo_layout = QHBoxLayout()
        repo_layout.addWidget(QLabel("Git Repository:"))
        self.repo_path = QLineEdit()
        repo_layout.addWidget(self.repo_path)
        browse_button = QPushButton("Browse")
        browse_button.clicked.connect(self.browse_repository)
        repo_layout.addWidget(browse_button)
        main_layout.addLayout(repo_layout)
        
        # 主要內容區域
        splitter = QSplitter(Qt.Horizontal)
        
        # 左側 - 文件列表
        files_widget = QWidget()
        files_layout = QVBoxLayout(files_widget)
        files_layout.addWidget(QLabel("Staged Files:"))
        self.staged_files = QListWidget()
        files_layout.addWidget(self.staged_files)
        files_layout.addWidget(QLabel("Unstaged Files:"))
        self.unstaged_files = QListWidget()
        files_layout.addWidget(self.unstaged_files)
        splitter.addWidget(files_widget)
        
        # 右側 - 提交信息編輯
        commit_widget = QWidget()
        commit_layout = QVBoxLayout(commit_widget)
        
        # 提交類型和範圍
        type_scope_layout = QHBoxLayout()
        type_scope_layout.addWidget(QLabel("Type:"))
        self.commit_type = QComboBox()
        self.commit_type.addItems(["feat", "fix", "docs", "style", "refactor", "test", "chore"])
        type_scope_layout.addWidget(self.commit_type)
        
        type_scope_layout.addWidget(QLabel("Scope:"))
        self.commit_scope = QLineEdit()
        type_scope_layout.addWidget(self.commit_scope)
        commit_layout.addLayout(type_scope_layout)
        
        # 提交描述
        commit_layout.addWidget(QLabel("Description:"))
        self.commit_description = QLineEdit()
        commit_layout.addWidget(self.commit_description)
        
        # 提交正文
        commit_layout.addWidget(QLabel("Body:"))
        self.commit_body = QTextEdit()
        commit_layout.addWidget(self.commit_body)
        
        # 提交頁腳
        commit_layout.addWidget(QLabel("Footer:"))
        self.commit_footer = QTextEdit()
        commit_layout.addWidget(self.commit_footer)
        
        # 建議區域
        commit_layout.addWidget(QLabel("Suggestions:"))
        self.suggestions = QListWidget()
        self.suggestions.itemClicked.connect(self.use_suggestion)
        commit_layout.addWidget(self.suggestions)
        
        # 預覽和提交按鈕
        buttons_layout = QHBoxLayout()
        self.preview_button = QPushButton("Preview")
        self.preview_button.clicked.connect(self.preview_commit)
        buttons_layout.addWidget(self.preview_button)
        
        self.commit_button = QPushButton("Commit")
        self.commit_button.clicked.connect(self.do_commit)
        buttons_layout.addWidget(self.commit_button)
        
        commit_layout.addLayout(buttons_layout)
        
        splitter.addWidget(commit_widget)
        main_layout.addWidget(splitter)
        
        # 狀態欄
        self.statusBar().showMessage("Ready")
    
    def browse_repository(self):
        """瀏覽並選擇Git倉庫"""
        # 實現倉庫選擇邏輯
        # ...
    
    def refresh_files(self):
        """刷新文件列表"""
        # 實現文件列表刷新邏輯
        # ...
    
    def use_suggestion(self, item):
        """使用選中的提交建議"""
        # 實現使用建議的邏輯
        # ...
    
    def preview_commit(self):
        """預覽提交信息"""
        # 實現預覽提交的邏輯
        # ...
    
    def do_commit(self):
        """執行提交操作"""
        # 實現提交操作的邏輯
        # ... 