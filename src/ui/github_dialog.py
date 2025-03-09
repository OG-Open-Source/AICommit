import os
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
							QListWidget, QListWidgetItem, QLabel, QLineEdit,
							QFileDialog, QMessageBox, QProgressDialog)
from PyQt5.QtCore import Qt, QSettings
from src.github.github_api import GitHubAPI
class GitHubRepoDialog(QDialog):
	def __init__(self, parent=None):
		super().__init__(parent)
		self.setWindowTitle("GitHub 倉庫")
		self.setMinimumSize(600, 400)
		self.github_api = GitHubAPI()
		self.settings = QSettings("OG-Open-Source", "CommitLogAssistant")
		self.selected_repo = None
		self.init_ui()
		self.load_repos()
	def init_ui(self):
		layout = QVBoxLayout(self)
		self.repo_list = QListWidget()
		self.repo_list.itemDoubleClicked.connect(self.on_repo_double_clicked)
		layout.addWidget(QLabel("選擇一個 GitHub 倉庫:"))
		layout.addWidget(self.repo_list)
		path_layout = QHBoxLayout()
		path_layout.addWidget(QLabel("本地路徑:"))
		self.local_path = QLineEdit()
		self.local_path.setText(os.path.expanduser("~/git"))
		path_layout.addWidget(self.local_path)
		browse_button = QPushButton("瀏覽")
		browse_button.clicked.connect(self.browse_local_path)
		path_layout.addWidget(browse_button)
		layout.addLayout(path_layout)
		buttons_layout = QHBoxLayout()
		refresh_button = QPushButton("刷新")
		refresh_button.clicked.connect(self.load_repos)
		buttons_layout.addWidget(refresh_button)
		buttons_layout.addStretch()
		self.clone_button = QPushButton("克隆")
		self.clone_button.clicked.connect(self.clone_selected_repo)
		self.clone_button.setEnabled(False)
		buttons_layout.addWidget(self.clone_button)
		cancel_button = QPushButton("取消")
		cancel_button.clicked.connect(self.reject)
		buttons_layout.addWidget(cancel_button)
		layout.addLayout(buttons_layout)
	def load_repos(self):
		self.repo_list.clear()
		token = self.settings.value("github/token", "")
		if not token:
			QMessageBox.warning(self, "未設置令牌", "請先在設定中添加 GitHub 個人訪問令牌")
			return
		progress = QProgressDialog("正在獲取 GitHub 倉庫...", "取消", 0, 0, self)
		progress.setWindowModality(Qt.WindowModal)
		progress.show()
		repos = self.github_api.get_user_repos()
		progress.close()
		if isinstance(repos, dict) and "error" in repos:
			QMessageBox.critical(self, "錯誤", repos["error"])
			return
		for repo in repos:
			item = QListWidgetItem(f"{repo['full_name']} ({repo['default_branch']})")
			item.setData(Qt.UserRole, repo)
			self.repo_list.addItem(item)
		if self.repo_list.count() > 0:
			self.repo_list.setCurrentRow(0)
			self.clone_button.setEnabled(True)
	def on_repo_double_clicked(self, item):
		self.clone_selected_repo()
	def browse_local_path(self):
		path = QFileDialog.getExistingDirectory(
			self,
			"選擇本地路徑",
			self.local_path.text()
		)
		if path:
			self.local_path.setText(path)
	def clone_selected_repo(self):
		if self.repo_list.currentItem() is None:
			return
		repo = self.repo_list.currentItem().data(Qt.UserRole)
		base_path = self.local_path.text()
		repo_name = repo["name"]
		local_path = os.path.join(base_path, repo_name)
		if os.path.exists(local_path):
			response = QMessageBox.question(
				self,
				"路徑已存在",
				f"路徑 {local_path} 已存在。是否使用現有倉庫?",
				QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
			)
			if response == QMessageBox.Cancel:
				return
			elif response == QMessageBox.Yes:
				self.selected_repo = local_path
				self.accept()
				return
		progress = QProgressDialog("正在克隆倉庫...", "取消", 0, 0, self)
		progress.setWindowModality(Qt.WindowModal)
		progress.show()
		clone_url = repo["clone_url"]
		result = self.github_api.clone_repo(clone_url, local_path)
		progress.close()
		if "error" in result:
			QMessageBox.critical(self, "克隆失敗", result["error"])
			return
		self.selected_repo = local_path
		self.accept()