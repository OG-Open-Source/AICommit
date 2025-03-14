from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
							QTextEdit, QPushButton, QListWidget)
from PyQt5.QtCore import Qt

class CommitDialog(QDialog):
	def __init__(self, parent=None, staged_files=None):
		super().__init__(parent)
		self.staged_files = staged_files or []

		self.setWindowTitle("提交更改")
		self.setMinimumSize(500, 400)

		self.setup_ui()

	def setup_ui(self):
		layout = QVBoxLayout(self)

		# 暂存的文件列表
		layout.addWidget(QLabel("暂存的文件:"))

		self.files_list = QListWidget()
		for file in self.staged_files:
			self.files_list.addItem(file)
		layout.addWidget(self.files_list)

		# 提交信息
		layout.addWidget(QLabel("提交信息:"))

		self.commit_message = QTextEdit()
		layout.addWidget(self.commit_message)

		# 按钮
		button_layout = QHBoxLayout()

		self.cancel_button = QPushButton("取消")
		self.cancel_button.clicked.connect(self.reject)
		button_layout.addWidget(self.cancel_button)

		self.commit_button = QPushButton("提交")
		self.commit_button.clicked.connect(self.accept)
		self.commit_button.setDefault(True)
		button_layout.addWidget(self.commit_button)

		layout.addLayout(button_layout)

	def get_commit_message(self):
		return self.commit_message.toPlainText()