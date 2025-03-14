from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
							QLineEdit, QPushButton, QFileDialog, QFormLayout)
from PyQt5.QtCore import Qt

class CloneDialog(QDialog):
	def __init__(self, parent=None):
		super().__init__(parent)

		self.setWindowTitle("克隆仓库")
		self.setMinimumWidth(500)

		self.setup_ui()

	def setup_ui(self):
		layout = QVBoxLayout(self)

		form_layout = QFormLayout()

		# 仓库 URL
		self.url_edit = QLineEdit()
		form_layout.addRow("仓库 URL:", self.url_edit)

		# 本地路径
		path_layout = QHBoxLayout()
		self.path_edit = QLineEdit()
		path_layout.addWidget(self.path_edit)

		self.browse_button = QPushButton("浏览...")
		self.browse_button.clicked.connect(self.browse_directory)
		path_layout.addWidget(self.browse_button)

		form_layout.addRow("本地路径:", path_layout)

		layout.addLayout(form_layout)

		# 按钮
		button_layout = QHBoxLayout()

		self.cancel_button = QPushButton("取消")
		self.cancel_button.clicked.connect(self.reject)
		button_layout.addWidget(self.cancel_button)

		self.clone_button = QPushButton("克隆")
		self.clone_button.clicked.connect(self.accept)
		self.clone_button.setDefault(True)
		button_layout.addWidget(self.clone_button)

		layout.addLayout(button_layout)

	def browse_directory(self):
		directory = QFileDialog.getExistingDirectory(self, "选择目录")
		if directory:
			self.path_edit.setText(directory)

	def get_clone_info(self):
		return {
			'url': self.url_edit.text(),
			'path': self.path_edit.text()
		}