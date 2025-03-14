from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
							QSplitter, QTreeView, QListWidget, QTextEdit,
							QToolBar, QAction, QStatusBar, QFileDialog, QMessageBox,
							QListWidgetItem, QFileSystemModel, QLabel, QLineEdit,
							QPushButton, QGroupBox, QFormLayout, QTabWidget, QDialog,
							QComboBox, QCheckBox, QMenu, QMenuBar)
from PyQt5.QtCore import Qt, QSize, QDir
from PyQt5.QtGui import QIcon, QColor, QTextCharFormat, QBrush, QFont

import os
import logging
from git.repository import GitRepository
from ui.commit_dialog import CommitDialog
from utils.config import Config

# 配置日志记录器
logger = logging.getLogger("ui.main_window")

class SettingsDialog(QDialog):
	def __init__(self, parent=None, current_provider="OpenAI"):
		super().__init__(parent)
		self.setWindowTitle("设置")
		self.setMinimumWidth(500)
		self.current_provider = current_provider
		self.setup_ui()

	def setup_ui(self):
		layout = QVBoxLayout(self)

		# 创建标签页
		tab_widget = QTabWidget()
		layout.addWidget(tab_widget)

		# GitHub 设置页
		github_widget = QWidget()
		github_layout = QFormLayout(github_widget)

		self.github_username = QLineEdit()
		github_layout.addRow("GitHub 用户名:", self.github_username)

		self.github_token = QLineEdit()
		self.github_token.setEchoMode(QLineEdit.Password)
		github_layout.addRow("GitHub 令牌:", self.github_token)

		tab_widget.addTab(github_widget, "GitHub")

		# AI 设置页
		ai_widget = QWidget()
		ai_layout = QVBoxLayout(ai_widget)

		# AI 提供商选择
		provider_group = QGroupBox("AI 提供商")
		provider_layout = QVBoxLayout(provider_group)

		# 提供商选择下拉框
		provider_selector_layout = QHBoxLayout()
		provider_selector_layout.addWidget(QLabel("当前提供商:"))

		self.provider_selector = QComboBox()
		self.provider_selector.addItems(["OpenAI", "Anthropic", "Google", "自定义 Web API"])
		self.provider_selector.setCurrentText(self.current_provider)
		self.provider_selector.currentTextChanged.connect(self.on_provider_changed)
		provider_selector_layout.addWidget(self.provider_selector)

		provider_layout.addLayout(provider_selector_layout)

		# 创建所有提供商的设置组，但只显示当前选择的
		self.provider_groups = {}

		# OpenAI 设置
		openai_group = QGroupBox("OpenAI 设置")
		openai_layout = QFormLayout(openai_group)

		self.openai_api_key = QLineEdit()
		self.openai_api_key.setEchoMode(QLineEdit.Password)
		openai_layout.addRow("API 密钥:", self.openai_api_key)

		self.openai_model = QComboBox()
		self.openai_model.addItems(["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"])
		openai_layout.addRow("模型:", self.openai_model)

		self.provider_groups["OpenAI"] = openai_group
		provider_layout.addWidget(openai_group)
		openai_group.setVisible(self.current_provider == "OpenAI")

		# Anthropic 设置
		anthropic_group = QGroupBox("Anthropic 设置")
		anthropic_layout = QFormLayout(anthropic_group)

		self.anthropic_api_key = QLineEdit()
		self.anthropic_api_key.setEchoMode(QLineEdit.Password)
		anthropic_layout.addRow("API 密钥:", self.anthropic_api_key)

		self.anthropic_model = QComboBox()
		self.anthropic_model.addItems(["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"])
		anthropic_layout.addRow("模型:", self.anthropic_model)

		self.provider_groups["Anthropic"] = anthropic_group
		provider_layout.addWidget(anthropic_group)
		anthropic_group.setVisible(self.current_provider == "Anthropic")

		# Google 设置
		google_group = QGroupBox("Google 设置")
		google_layout = QFormLayout(google_group)

		self.google_api_key = QLineEdit()
		self.google_api_key.setEchoMode(QLineEdit.Password)
		google_layout.addRow("API 密钥:", self.google_api_key)

		self.google_model = QComboBox()
		self.google_model.addItems(["gemini-pro", "gemini-ultra"])
		google_layout.addRow("模型:", self.google_model)

		self.provider_groups["Google"] = google_group
		provider_layout.addWidget(google_group)
		google_group.setVisible(self.current_provider == "Google")

		# 自定义 Web API 设置
		web_group = QGroupBox("自定义 Web API 设置")
		web_layout = QFormLayout(web_group)

		self.web_api_url = QLineEdit()
		self.web_api_url.setPlaceholderText("https://your-api-endpoint.com/v1/chat/completions")
		web_layout.addRow("API URL:", self.web_api_url)

		self.web_api_key = QLineEdit()
		self.web_api_key.setEchoMode(QLineEdit.Password)
		web_layout.addRow("API 密钥:", self.web_api_key)

		self.web_api_model = QLineEdit()
		self.web_api_model.setPlaceholderText("模型名称")
		web_layout.addRow("模型:", self.web_api_model)

		self.provider_groups["自定义 Web API"] = web_group
		provider_layout.addWidget(web_group)
		web_group.setVisible(self.current_provider == "自定义 Web API")

		ai_layout.addWidget(provider_group)

		# AI 提示设置
		prompt_group = QGroupBox("提示设置")
		prompt_layout = QVBoxLayout(prompt_group)

		self.system_prompt = QTextEdit()
		self.system_prompt.setPlaceholderText("输入系统提示，指导 AI 如何生成提交信息")
		self.system_prompt.setMaximumHeight(100)
		prompt_layout.addWidget(self.system_prompt)

		ai_layout.addWidget(prompt_group)

		tab_widget.addTab(ai_widget, "AI 设置")

		# 按钮
		button_layout = QHBoxLayout()

		self.cancel_button = QPushButton("取消")
		self.cancel_button.clicked.connect(self.reject)
		button_layout.addWidget(self.cancel_button)

		self.save_button = QPushButton("保存")
		self.save_button.clicked.connect(self.accept)
		self.save_button.setDefault(True)
		button_layout.addWidget(self.save_button)

		layout.addLayout(button_layout)

	def on_provider_changed(self, provider):
		"""当 AI 提供商选择改变时更新界面"""
		# 隐藏所有提供商设置
		for p, group in self.provider_groups.items():
			group.setVisible(False)

		# 显示当前选择的提供商设置
		if provider in self.provider_groups:
			self.provider_groups[provider].setVisible(True)

		self.current_provider = provider

# 创建自定义的文件项组件
class FileItemWidget(QWidget):
	def __init__(self, file_path, file_status, parent=None, on_checkbox_changed=None):
		super().__init__(parent)
		self.file_path = file_path
		self.file_status = file_status
		self.on_checkbox_changed = on_checkbox_changed

		layout = QHBoxLayout(self)
		layout.setContentsMargins(2, 2, 2, 2)

		# 复选框 - 默认选中
		self.checkbox = QCheckBox()
		self.checkbox.setChecked(True)  # 默认选中所有文件
		if self.on_checkbox_changed:
			self.checkbox.stateChanged.connect(self.checkbox_state_changed)
		layout.addWidget(self.checkbox)

		# 文件路径 - 使用默认颜色
		path_label = QLabel(file_path)
		layout.addWidget(path_label)

		# 设置伸缩因子，使路径标签占据剩余空间
		layout.setStretchFactor(path_label, 1)

	def checkbox_state_changed(self, state):
		"""当复选框状态改变时调用回调函数"""
		if self.on_checkbox_changed:
			self.on_checkbox_changed()

class MainWindow(QMainWindow):
	def __init__(self):
		super().__init__()

		# 初始化仓库和 AI 提供商
		self.current_repo = None

		# 从配置文件加载当前 AI 提供商
		config_manager = Config()
		self.current_ai_provider = config_manager.get("ai_provider", "OpenAI")

		self.setWindowTitle("AICommit")
		self.setMinimumSize(1000, 600)

		self.setup_menu()  # 添加菜单设置
		self.setup_ui()
		self.setup_statusbar()
		self.setup_connections()

		logger.debug("主窗口初始化完成")

	def setup_menu(self):
		"""设置菜单栏"""
		menubar = self.menuBar()

		# 文件菜单
		file_menu = menubar.addMenu("文件")

		open_action = QAction("打开仓库", self)
		open_action.setIcon(QIcon.fromTheme("document-open"))
		open_action.setShortcut("Ctrl+O")
		open_action.triggered.connect(self.open_repository)
		file_menu.addAction(open_action)

		clone_action = QAction("克隆仓库", self)
		clone_action.setIcon(QIcon.fromTheme("document-new"))
		clone_action.triggered.connect(self.clone_repository)
		file_menu.addAction(clone_action)

		file_menu.addSeparator()

		exit_action = QAction("退出", self)
		exit_action.setIcon(QIcon.fromTheme("application-exit"))
		exit_action.setShortcut("Ctrl+Q")
		exit_action.triggered.connect(self.close)
		file_menu.addAction(exit_action)

		# 分支菜单
		branch_menu = menubar.addMenu("分支")

		refresh_branches_action = QAction("刷新分支列表", self)
		refresh_branches_action.setIcon(QIcon.fromTheme("view-refresh"))
		refresh_branches_action.triggered.connect(self.refresh_branches)
		branch_menu.addAction(refresh_branches_action)

		new_branch_action = QAction("新建分支", self)
		new_branch_action.setIcon(QIcon.fromTheme("list-add"))
		new_branch_action.triggered.connect(self.create_new_branch)
		branch_menu.addAction(new_branch_action)

		branch_menu.addSeparator()

		pull_action = QAction("拉取更改", self)
		pull_action.setIcon(QIcon.fromTheme("go-down"))
		pull_action.triggered.connect(self.pull_repository)
		branch_menu.addAction(pull_action)

		push_action = QAction("推送更改", self)
		push_action.setIcon(QIcon.fromTheme("go-up"))
		push_action.triggered.connect(self.push_repository)
		branch_menu.addAction(push_action)

		# 设置菜单（替换原来的 AI 菜单）
		settings_menu = menubar.addMenu("设置")

		# AI 提供商子菜单
		provider_menu = QMenu("选择 AI 提供商", self)

		# 创建提供商选择动作组
		self.provider_actions = {}

		openai_action = QAction("OpenAI", self)
		openai_action.setCheckable(True)
		openai_action.setChecked(self.current_ai_provider == "OpenAI")
		openai_action.triggered.connect(lambda: self.set_ai_provider("OpenAI"))
		provider_menu.addAction(openai_action)
		self.provider_actions["OpenAI"] = openai_action

		anthropic_action = QAction("Anthropic", self)
		anthropic_action.setCheckable(True)
		anthropic_action.setChecked(self.current_ai_provider == "Anthropic")
		anthropic_action.triggered.connect(lambda: self.set_ai_provider("Anthropic"))
		provider_menu.addAction(anthropic_action)
		self.provider_actions["Anthropic"] = anthropic_action

		google_action = QAction("Google", self)
		google_action.setCheckable(True)
		google_action.setChecked(self.current_ai_provider == "Google")
		google_action.triggered.connect(lambda: self.set_ai_provider("Google"))
		provider_menu.addAction(google_action)
		self.provider_actions["Google"] = google_action

		web_action = QAction("自定义 Web API", self)
		web_action.setCheckable(True)
		web_action.setChecked(self.current_ai_provider == "自定义 Web API")
		web_action.triggered.connect(lambda: self.set_ai_provider("自定义 Web API"))
		provider_menu.addAction(web_action)
		self.provider_actions["自定义 Web API"] = web_action

		settings_menu.addMenu(provider_menu)

		settings_menu.addSeparator()

		generate_action = QAction("生成提交信息", self)
		generate_action.setIcon(QIcon.fromTheme("edit-redo"))
		generate_action.setShortcut("Ctrl+G")
		generate_action.triggered.connect(self.generate_commit_message)
		settings_menu.addAction(generate_action)

		settings_menu.addSeparator()

		settings_action = QAction("设置", self)
		settings_action.setIcon(QIcon.fromTheme("preferences-system"))
		settings_action.triggered.connect(self.show_settings)
		settings_menu.addAction(settings_action)

		# 帮助菜单
		help_menu = menubar.addMenu("帮助")

		about_action = QAction("关于", self)
		about_action.setIcon(QIcon.fromTheme("help-about"))
		about_action.triggered.connect(self.show_about)
		help_menu.addAction(about_action)

	def set_ai_provider(self, provider):
		"""设置当前 AI 提供商"""
		if provider == self.current_ai_provider:
			return

		# 更新当前提供商
		self.current_ai_provider = provider
		logger.info(f"切换 AI 提供商: {provider}")

		# 更新菜单选中状态
		for p, action in self.provider_actions.items():
			action.setChecked(p == provider)

		# 更新状态栏
		self.statusBar.showMessage(f"已切换 AI 提供商: {provider}")

	def show_settings(self):
		"""显示设置对话框"""
		dialog = SettingsDialog(self, current_provider=self.current_ai_provider)

		# 从配置文件加载当前设置并填充对话框
		config_manager = Config()

		# 加载 GitHub 设置
		dialog.github_username.setText(config_manager.get("github_username", ""))
		dialog.github_token.setText(config_manager.get("github_token", ""))

		# 加载 AI 设置
		dialog.system_prompt.setPlainText(config_manager.get("system_prompt", ""))

		# 加载 OpenAI 设置
		dialog.openai_api_key.setText(config_manager.get("openai_api_key", ""))
		index = dialog.openai_model.findText(config_manager.get("openai_model", "gpt-3.5-turbo"))
		if index >= 0:
			dialog.openai_model.setCurrentIndex(index)

		# 加载 Anthropic 设置
		dialog.anthropic_api_key.setText(config_manager.get("anthropic_api_key", ""))
		index = dialog.anthropic_model.findText(config_manager.get("anthropic_model", "claude-3-haiku"))
		if index >= 0:
			dialog.anthropic_model.setCurrentIndex(index)

		# 加载 Google 设置
		dialog.google_api_key.setText(config_manager.get("google_api_key", ""))
		index = dialog.google_model.findText(config_manager.get("google_model", "gemini-pro"))
		if index >= 0:
			dialog.google_model.setCurrentIndex(index)

		# 加载 Web API 设置
		dialog.web_api_url.setText(config_manager.get("web_api_url", ""))
		dialog.web_api_key.setText(config_manager.get("web_api_key", ""))
		dialog.web_api_model.setText(config_manager.get("web_api_model", ""))

		if dialog.exec_():
			# 保存设置
			logger.info("保存设置")

			# 更新当前 AI 提供商
			new_provider = dialog.provider_selector.currentText()
			if new_provider != self.current_ai_provider:
				self.set_ai_provider(new_provider)

			# 保存 API 密钥和其他设置到配置文件
			# GitHub 设置
			config_manager.set("github_username", dialog.github_username.text())
			config_manager.set("github_token", dialog.github_token.text())

			# AI 设置
			config_manager.set("ai_provider", new_provider)
			config_manager.set("system_prompt", dialog.system_prompt.toPlainText())

			# OpenAI 设置
			config_manager.set("openai_api_key", dialog.openai_api_key.text())
			config_manager.set("openai_model", dialog.openai_model.currentText())

			# Anthropic 设置
			config_manager.set("anthropic_api_key", dialog.anthropic_api_key.text())
			config_manager.set("anthropic_model", dialog.anthropic_model.currentText())

			# Google 设置
			config_manager.set("google_api_key", dialog.google_api_key.text())
			config_manager.set("google_model", dialog.google_model.currentText())

			# Web API 设置
			config_manager.set("web_api_url", dialog.web_api_url.text())
			config_manager.set("web_api_key", dialog.web_api_key.text())
			config_manager.set("web_api_model", dialog.web_api_model.text())

			self.statusBar.showMessage("设置已保存")

	def show_about(self):
		"""显示关于对话框"""
		QMessageBox.about(
			self,
			"关于 AICommit",
			"AICommit 是一个使用 AI 生成 Git 提交信息的工具。\n\n"
			"版本: 1.0.0\n"
			"作者: OG-Open-Source\n"
			"许可: MIT"
		)

	def setup_ui(self):
		# 主布局
		central_widget = QWidget()
		self.setCentralWidget(central_widget)
		main_layout = QVBoxLayout(central_widget)

		# 创建分割器
		splitter = QSplitter(Qt.Horizontal)
		main_layout.addWidget(splitter)

		# 左侧面板 - 提交信息区域
		left_panel = QWidget()
		left_layout = QVBoxLayout(left_panel)

		# 分支选择
		branch_group = QGroupBox("分支")
		branch_layout = QHBoxLayout(branch_group)

		self.branch_combo = QComboBox()
		self.branch_combo.setMinimumWidth(150)
		branch_layout.addWidget(self.branch_combo)

		self.refresh_branch_button = QPushButton("刷新")
		self.refresh_branch_button.clicked.connect(self.refresh_branches)
		branch_layout.addWidget(self.refresh_branch_button)

		self.new_branch_button = QPushButton("新建分支")
		self.new_branch_button.clicked.connect(self.create_new_branch)
		branch_layout.addWidget(self.new_branch_button)

		left_layout.addWidget(branch_group)

		# Summary 输入
		summary_group = QGroupBox("提交摘要")
		summary_layout = QVBoxLayout(summary_group)
		self.summary_edit = QLineEdit()
		self.summary_edit.setPlaceholderText("简短描述您的更改（必填）")
		summary_layout.addWidget(self.summary_edit)
		left_layout.addWidget(summary_group)

		# Description 输入
		description_group = QGroupBox("详细描述")
		description_layout = QVBoxLayout(description_group)
		self.description_edit = QTextEdit()
		self.description_edit.setPlaceholderText("详细描述您的更改（可选）")
		description_layout.addWidget(self.description_edit)
		left_layout.addWidget(description_group)

		# AI 生成按钮
		ai_button_layout = QHBoxLayout()
		self.ai_generate_button = QPushButton("AI 生成提交信息")
		self.ai_generate_button.clicked.connect(self.generate_commit_message)
		ai_button_layout.addWidget(self.ai_generate_button)
		left_layout.addLayout(ai_button_layout)

		# 提交按钮
		commit_button_layout = QHBoxLayout()
		self.commit_button = QPushButton("提交更改")
		self.commit_button.clicked.connect(self.commit_with_message)
		commit_button_layout.addWidget(self.commit_button)
		left_layout.addLayout(commit_button_layout)

		# 添加弹性空间
		left_layout.addStretch()

		splitter.addWidget(left_panel)

		# 右侧面板
		right_panel = QWidget()
		right_layout = QVBoxLayout(right_panel)
		right_layout.setContentsMargins(0, 0, 0, 0)
		splitter.addWidget(right_panel)

		# 变更列表
		changes_group = QGroupBox("变更文件")
		changes_layout = QVBoxLayout(changes_group)

		# 添加全选复选框
		self.select_all_checkbox = QCheckBox("全选")
		self.select_all_checkbox.setChecked(True)  # 默认选中
		self.select_all_checkbox.setTristate(True)  # 允许部分选中状态
		self.select_all_checkbox.stateChanged.connect(self.toggle_select_all)
		changes_layout.addWidget(self.select_all_checkbox)

		self.changes_list = QListWidget()
		self.changes_list.setSelectionMode(QListWidget.SingleSelection)
		changes_layout.addWidget(self.changes_list)
		right_layout.addWidget(changes_group)

		# 差异查看器
		diff_group = QGroupBox("差异")
		diff_layout = QVBoxLayout(diff_group)
		self.diff_viewer = QTextEdit()
		self.diff_viewer.setReadOnly(True)

		# 使用等宽字体
		fixed_font = QFont("Consolas")  # 或者使用 "Courier New"
		if not fixed_font.exactMatch():  # 如果 Consolas 不可用
			fixed_font = QFont("Courier New")
		fixed_font.setStyleHint(QFont.Monospace)  # 确保使用等宽字体
		fixed_font.setPointSize(10)  # 设置字体大小
		self.diff_viewer.setFont(fixed_font)

		diff_layout.addWidget(self.diff_viewer)
		right_layout.addWidget(diff_group)

		# 设置分割比例
		splitter.setSizes([300, 700])

		logger.debug("UI 组件设置完成")

	def setup_statusbar(self):
		self.statusBar = QStatusBar()
		self.setStatusBar(self.statusBar)
		self.statusBar.showMessage("准备就绪")

		logger.debug("状态栏设置完成")

	def setup_connections(self):
		self.changes_list.itemSelectionChanged.connect(self.show_selected_diff)

		logger.debug("信号连接设置完成")

	def open_repository(self):
		logger.info("尝试打开仓库")
		repo_path = QFileDialog.getExistingDirectory(self, "选择仓库目录")
		if repo_path:
			try:
				self.current_repo = GitRepository(repo_path)
				self.refresh_ui()
				self.statusBar.showMessage(f"已打开仓库: {repo_path}")
				logger.info(f"成功打开仓库: {repo_path}")
			except Exception as e:
				QMessageBox.critical(self, "错误", f"无法打开仓库: {str(e)}")
				logger.error(f"打开仓库失败: {str(e)}")

	def clone_repository(self):
		# 这里将实现克隆仓库的功能
		logger.info("尝试克隆仓库")
		QMessageBox.information(self, "提示", "克隆仓库功能尚未实现")

	def pull_repository(self):
		if self.current_repo:
			try:
				logger.info("尝试拉取更改")
				self.current_repo.pull()
				self.refresh_ui()
				self.statusBar.showMessage("拉取成功")
				logger.info("拉取成功")
			except Exception as e:
				QMessageBox.critical(self, "错误", f"拉取失败: {str(e)}")
				logger.error(f"拉取失败: {str(e)}")
		else:
			QMessageBox.warning(self, "警告", "请先打开一个仓库")
			logger.warning("尝试拉取但没有打开仓库")

	def push_repository(self):
		if self.current_repo:
			try:
				logger.info("尝试推送更改")
				self.current_repo.push()
				self.statusBar.showMessage("推送成功")
				logger.info("推送成功")
			except Exception as e:
				QMessageBox.critical(self, "错误", f"推送失败: {str(e)}")
				logger.error(f"推送失败: {str(e)}")
		else:
			QMessageBox.warning(self, "警告", "请先打开一个仓库")
			logger.warning("尝试推送但没有打开仓库")

	def generate_commit_message(self):
		"""使用 AI 生成提交信息"""
		if not self.current_repo:
			QMessageBox.warning(self, "警告", "请先打开一个仓库")
			return

		try:
			# 获取选中的文件
			selected_files = []
			for i in range(self.changes_list.count()):
				item = self.changes_list.item(i)
				widget = self.changes_list.itemWidget(item)
				if widget and widget.checkbox.isChecked():
					selected_files.append(widget.file_path)

			if not selected_files:
				QMessageBox.information(self, "提示", "请选择要提交的文件")
				return

			# 获取文件差异
			diffs = []
			for file_path in selected_files:
				diff = self.current_repo.get_diff(file_path)
				diffs.append(f"File: {file_path}\n{diff}\n")

			# 合并所有差异
			all_diffs = "\n".join(diffs)

			# 显示正在生成的提示
			self.statusBar.showMessage(f"正在使用 {self.current_ai_provider} 生成提交信息...")

			# 根据不同的 AI 提供商调用不同的 API
			if self.current_ai_provider == "OpenAI":
				commit_message = self.generate_with_openai(all_diffs)
			elif self.current_ai_provider == "Anthropic":
				commit_message = self.generate_with_anthropic(all_diffs)
			elif self.current_ai_provider == "Google":
				commit_message = self.generate_with_google(all_diffs)
			elif self.current_ai_provider == "自定义 Web API":
				commit_message = self.generate_with_web_api(all_diffs)
			else:
				raise ValueError(f"未知的 AI 提供商: {self.current_ai_provider}")

			# 分割提交信息为摘要和描述
			lines = commit_message.strip().split("\n")
			summary = lines[0]
			description = "\n".join(lines[1:]).strip()

			# 更新 UI
			self.summary_edit.setText(summary)
			self.description_edit.setText(description)

			self.statusBar.showMessage("提交信息生成完成")
			logger.info("提交信息生成完成")
		except Exception as e:
			QMessageBox.critical(self, "错误", f"生成提交信息失败: {str(e)}")
			logger.error(f"生成提交信息失败: {str(e)}")
			self.statusBar.showMessage("生成提交信息失败")

	def generate_with_openai(self, diffs):
		"""使用 OpenAI API 生成提交信息"""
		logger.info("使用 OpenAI 生成提交信息")
		# TODO: 实现 OpenAI API 调用
		# 这里暂时返回模拟数据
		return "feat: 添加用户认证功能\n\n实现了基于 JWT 的用户认证系统，包括：\n- 登录接口\n- 注册接口\n- 令牌验证中间件"

	def generate_with_anthropic(self, diffs):
		"""使用 Anthropic API 生成提交信息"""
		logger.info("使用 Anthropic 生成提交信息")
		# TODO: 实现 Anthropic API 调用
		# 这里暂时返回模拟数据
		return "fix: 修复用户注册时的数据验证问题\n\n- 添加了邮箱格式验证\n- 修复了密码强度检查的逻辑错误\n- 优化了错误提示信息"

	def generate_with_google(self, diffs):
		"""使用 Google API 生成提交信息"""
		logger.info("使用 Google 生成提交信息")
		# TODO: 实现 Google API 调用
		# 这里暂时返回模拟数据
		return "refactor: 重构数据库连接模块\n\n- 使用连接池优化性能\n- 添加重试机制\n- 改进错误处理逻辑"

	def generate_with_web_api(self, diffs):
		"""使用自定义 Web API 生成提交信息"""
		logger.info("使用自定义 Web API 生成提交信息")
		# TODO: 实现自定义 Web API 调用
		# 这里暂时返回模拟数据
		return "docs: 更新 API 文档\n\n- 添加新接口说明\n- 修正参数描述\n- 增加使用示例"

	def commit_with_message(self):
		if not self.current_repo:
			QMessageBox.warning(self, "警告", "请先打开一个仓库")
			logger.warning("尝试提交但没有打开仓库")
			return

		try:
			# 获取选中的文件
			selected_files = []
			for i in range(self.changes_list.count()):
				item = self.changes_list.item(i)
				widget = self.changes_list.itemWidget(item)
				if widget and widget.checkbox.isChecked():
					selected_files.append(widget.file_path)

			if not selected_files:
				QMessageBox.information(self, "提示", "没有选择要提交的文件")
				logger.info("尝试提交但没有选择文件")
				return

			# 暂存选中的文件
			for file_path in selected_files:
				logger.info(f"暂存文件: {file_path}")
				self.current_repo.stage_file(file_path)

			# 获取提交信息
			summary = self.summary_edit.text().strip()
			if not summary:
				QMessageBox.warning(self, "警告", "提交摘要不能为空")
				logger.warning("提交摘要为空")
				return

			description = self.description_edit.toPlainText().strip()

			# 组合提交信息
			commit_message = summary
			if description:
				commit_message += "\n\n" + description

			# 提交更改
			logger.info(f"提交更改，信息: {commit_message}")
			self.current_repo.commit(commit_message)
			self.refresh_ui()

			# 清空提交信息
			self.summary_edit.clear()
			self.description_edit.clear()

			self.statusBar.showMessage("提交成功")
			logger.info("提交成功")
		except Exception as e:
			QMessageBox.critical(self, "错误", f"提交失败: {str(e)}")
			logger.error(f"提交失败: {str(e)}")

	def toggle_select_all(self, state):
		"""切换全选状态"""
		# 只处理完全选中和完全未选中的状态
		if state == Qt.Checked or state == Qt.Unchecked:
			is_checked = state == Qt.Checked
			for i in range(self.changes_list.count()):
				item = self.changes_list.item(i)
				widget = self.changes_list.itemWidget(item)
				if widget:
					# 阻止触发 update_select_all_state
					widget.checkbox.blockSignals(True)
					widget.checkbox.setChecked(is_checked)
					widget.checkbox.blockSignals(False)

	def update_select_all_state(self):
		"""根据文件选中状态更新全选复选框状态"""
		if self.changes_list.count() == 0:
			self.select_all_checkbox.setCheckState(Qt.Unchecked)
			return

		checked_count = 0
		for i in range(self.changes_list.count()):
			item = self.changes_list.item(i)
			widget = self.changes_list.itemWidget(item)
			if widget and widget.checkbox.isChecked():
				checked_count += 1

		# 设置全选复选框状态
		if checked_count == 0:
			self.select_all_checkbox.setCheckState(Qt.Unchecked)
		elif checked_count == self.changes_list.count():
			self.select_all_checkbox.setCheckState(Qt.Checked)
		else:
			self.select_all_checkbox.setCheckState(Qt.PartiallyChecked)

	def show_selected_diff(self):
		if not self.current_repo:
			return

		selected_items = self.changes_list.selectedItems()
		if not selected_items:
			self.diff_viewer.clear()
			return

		try:
			item = selected_items[0]
			widget = self.changes_list.itemWidget(item)
			if widget:
				file_path = widget.file_path
				diff_text = self.current_repo.get_diff(file_path)

				# 设置差异文本并添加语法高亮
				self.diff_viewer.clear()

				# 简单的语法高亮
				cursor = self.diff_viewer.textCursor()

				# 添加行格式
				format_add = QTextCharFormat()
				format_add.setForeground(QBrush(QColor("green")))
				format_add.setBackground(QBrush(QColor(232, 255, 232)))  # 浅绿色背景

				format_remove = QTextCharFormat()
				format_remove.setForeground(QBrush(QColor("red")))
				format_remove.setBackground(QBrush(QColor(255, 232, 232)))  # 浅红色背景

				format_header = QTextCharFormat()
				format_header.setForeground(QBrush(QColor("blue")))
				format_header.setBackground(QBrush(QColor(232, 232, 255)))  # 浅蓝色背景

				format_normal = QTextCharFormat()

				# 处理每一行
				for line in diff_text.splitlines():
					if not line:  # 空行
						cursor.insertText('\n')
						continue

					# 检查行的第一个字符
					first_char = line[0] if line else ''

					if first_char == '+':
						cursor.insertText(line + '\n', format_add)
					elif first_char == '-':
						cursor.insertText(line + '\n', format_remove)
					elif line.startswith('@@') or line.startswith('diff'):
						cursor.insertText(line + '\n', format_header)
					else:
						cursor.insertText(line + '\n', format_normal)

				logger.debug(f"显示文件差异: {file_path}")
		except Exception as e:
			self.diff_viewer.setPlainText(f"无法显示差异: {str(e)}")
			logger.error(f"显示差异失败: {str(e)}")

	def refresh_branches(self):
		"""刷新分支列表"""
		if not self.current_repo:
			return

		try:
			logger.info("刷新分支列表")
			current_text = self.branch_combo.currentText()

			self.branch_combo.clear()
			branches = self.current_repo.get_branches()

			# 获取当前分支
			status = self.current_repo.get_status()
			current_branch = status['branch']

			# 添加分支到下拉框
			for branch in branches:
				self.branch_combo.addItem(branch)

			# 设置当前分支为选中项
			index = self.branch_combo.findText(current_branch)
			if index >= 0:
				self.branch_combo.setCurrentIndex(index)

			# 连接信号
			self.branch_combo.currentIndexChanged.connect(self.branch_changed)

			logger.debug(f"分支列表刷新完成，当前分支: {current_branch}")
		except Exception as e:
			QMessageBox.critical(self, "错误", f"刷新分支列表失败: {str(e)}")
			logger.error(f"刷新分支列表失败: {str(e)}")

	def branch_changed(self, index):
		"""当用户选择不同的分支时触发"""
		if not self.current_repo or index < 0:
			return

		selected_branch = self.branch_combo.currentText()
		current_status = self.current_repo.get_status()

		# 如果选择的是当前分支，不做任何操作
		if selected_branch == current_status['branch']:
			return

		try:
			# 检查是否有未提交的更改
			if current_status['modified'] or current_status['staged']:
				reply = QMessageBox.question(
					self,
					"未提交的更改",
					"您有未提交的更改，切换分支可能会丢失这些更改。是否继续？",
					QMessageBox.Yes | QMessageBox.No,
					QMessageBox.No
				)

				if reply == QMessageBox.No:
					# 恢复选择
					index = self.branch_combo.findText(current_status['branch'])
					if index >= 0:
						self.branch_combo.blockSignals(True)
						self.branch_combo.setCurrentIndex(index)
						self.branch_combo.blockSignals(False)
					return

			logger.info(f"切换到分支: {selected_branch}")
			self.current_repo.checkout_branch(selected_branch)
			self.refresh_ui()
			self.statusBar.showMessage(f"已切换到分支: {selected_branch}")
		except Exception as e:
			QMessageBox.critical(self, "错误", f"切换分支失败: {str(e)}")
			logger.error(f"切换分支失败: {str(e)}")

			# 恢复选择
			index = self.branch_combo.findText(current_status['branch'])
			if index >= 0:
				self.branch_combo.blockSignals(True)
				self.branch_combo.setCurrentIndex(index)
				self.branch_combo.blockSignals(False)

	def create_new_branch(self):
		"""创建新分支"""
		if not self.current_repo:
			QMessageBox.warning(self, "警告", "请先打开一个仓库")
			return

		branch_name, ok = QFileDialog.getSaveFileName(
			self,
			"新建分支",
			"",
			"分支名称 (*)"
		)

		if ok and branch_name:
			try:
				# 移除可能的文件扩展名
				branch_name = os.path.basename(branch_name)
				if '.' in branch_name:
					branch_name = branch_name.split('.')[0]

				logger.info(f"创建新分支: {branch_name}")
				self.current_repo.create_branch(branch_name)

				# 询问是否切换到新分支
				reply = QMessageBox.question(
					self,
					"切换分支",
					f"分支 '{branch_name}' 已创建。是否切换到新分支？",
					QMessageBox.Yes | QMessageBox.No,
					QMessageBox.Yes
				)

				if reply == QMessageBox.Yes:
					self.current_repo.checkout_branch(branch_name)

				self.refresh_branches()
				self.refresh_ui()
				self.statusBar.showMessage(f"分支 '{branch_name}' 已创建")
			except Exception as e:
				QMessageBox.critical(self, "错误", f"创建分支失败: {str(e)}")
				logger.error(f"创建分支失败: {str(e)}")

	def refresh_ui(self):
		# 刷新 UI 显示
		if self.current_repo:
			logger.debug("刷新 UI")

			# 刷新分支列表
			self.refresh_branches()

			# 更新变更列表
			self.changes_list.clear()

			try:
				status = self.current_repo.get_status()

				# 合并所有文件列表，不再区分暂存状态
				all_files = []

				# 添加已暂存的文件
				for file_path in status['staged']:
					if file_path not in all_files:
						all_files.append((file_path, "staged"))

				# 添加已修改但未暂存的文件
				for file_path in status['modified']:
					if file_path not in [f[0] for f in all_files]:
						all_files.append((file_path, "modified"))

				# 添加已删除但未暂存的文件
				for file_path in status['deleted']:
					if file_path not in [f[0] for f in all_files]:
						all_files.append((file_path, "deleted"))

				# 添加未跟踪的文件
				for file_path in status['untracked']:
					if file_path not in [f[0] for f in all_files]:
						all_files.append((file_path, "untracked"))

				# 添加所有文件到列表
				for file_path, file_status in all_files:
					item = QListWidgetItem()
					item.setSizeHint(QSize(0, 30))
					self.changes_list.addItem(item)

					# 创建文件项组件，并传递回调函数
					widget = FileItemWidget(
						file_path,
						file_status,
						on_checkbox_changed=self.update_select_all_state
					)
					self.changes_list.setItemWidget(item, widget)

				# 更新全选复选框状态
				self.update_select_all_state()

				# 更新窗口标题，显示当前分支
				self.setWindowTitle(f"AICommit - {os.path.basename(self.current_repo.path)} ({status['branch']})")

				logger.debug("UI 刷新完成")
			except Exception as e:
				QMessageBox.critical(self, "错误", f"刷新 UI 失败: {str(e)}")
				logger.error(f"刷新 UI 失败: {str(e)}")