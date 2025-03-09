import sys
import os
import json
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)
from PyQt5.QtWidgets import (QMainWindow, QApplication, QWidget, QVBoxLayout,
							QHBoxLayout, QPushButton, QTextEdit, QListWidget,
							QLabel, QComboBox, QLineEdit, QSplitter, QFileDialog,
							QDialog, QFormLayout, QDialogButtonBox, QCheckBox,
							QGroupBox, QMessageBox, QFrame, QToolBar, QAction,
							QTreeWidget, QTreeWidgetItem, QTabWidget, QSlider,
							QSpinBox, QProgressDialog)
from PyQt5.QtCore import Qt, QSettings, QSize
from PyQt5.QtGui import QIcon, QFont, QColor
from src.git.repository import GitRepository
from src.git.commit_helper import CommitHelper
class SettingsDialog(QDialog):
	def __init__(self, parent=None):
		super().__init__(parent)
		self.setWindowTitle("設定")
		self.setMinimumWidth(500)
		self.settings = QSettings("OG-Open-Source", "CommitLogAssistant")
		self.init_ui()
		self.load_settings()
	def init_ui(self):
		layout = QVBoxLayout(self)
		github_group = QGroupBox("GitHub 帳號")
		github_layout = QFormLayout()
		self.github_username = QLineEdit()
		github_layout.addRow("使用者名稱:", self.github_username)
		self.github_token = QLineEdit()
		self.github_token.setEchoMode(QLineEdit.Password)
		github_layout.addRow("個人訪問令牌:", self.github_token)
		self.save_credentials = QCheckBox("記住我的憑證")
		github_layout.addRow("", self.save_credentials)
		token_info = QLabel("請在 GitHub 設定中創建個人訪問令牌 (PAT)，\n需要 'repo' 權限。")
		token_info.setWordWrap(True)
		github_layout.addRow("", token_info)
		github_group.setLayout(github_layout)
		layout.addWidget(github_group)
		ai_group = QGroupBox("AI 設定")
		ai_layout = QFormLayout()
		self.ai_provider = QComboBox()
		self.ai_provider.addItems([
			"OpenAI",
			"Anthropic Claude",
			"Google Gemini",
			"Mistral AI",
			"自定義"
		])
		self.ai_provider.currentIndexChanged.connect(self.on_provider_changed)
		ai_layout.addRow("AI 服務提供商:", self.ai_provider)
		api_key_layout = QHBoxLayout()
		self.ai_api_key = QLineEdit()
		self.ai_api_key.setEchoMode(QLineEdit.Password)
		api_key_layout.addWidget(self.ai_api_key)
		self.test_connection_btn = QPushButton("測試連接")
		self.test_connection_btn.clicked.connect(self.test_connection)
		api_key_layout.addWidget(self.test_connection_btn)
		ai_layout.addRow("API 金鑰:", api_key_layout)
		self.endpoint_container = QWidget()
		endpoint_layout = QFormLayout(self.endpoint_container)
		endpoint_layout.setContentsMargins(0, 0, 0, 0)
		self.ai_endpoint = QLineEdit()
		self.ai_endpoint.setPlaceholderText("可選，留空使用默認端點")
		endpoint_layout.addRow("API 端點:", self.ai_endpoint)
		ai_layout.addRow("", self.endpoint_container)
		model_layout = QHBoxLayout()
		self.ai_model = QComboBox()
		model_layout.addWidget(self.ai_model)
		self.custom_model = QLineEdit()
		self.custom_model.setPlaceholderText("輸入自定義模型名稱")
		self.custom_model.setVisible(False)
		model_layout.addWidget(self.custom_model)
		ai_layout.addRow("AI 模型:", model_layout)
		self.ai_temperature = QSlider(Qt.Horizontal)
		self.ai_temperature.setRange(0, 100)
		self.ai_temperature.setValue(70)
		self.ai_temperature_label = QLabel("0.7")
		self.ai_temperature.valueChanged.connect(self.update_temperature_label)
		temp_layout = QHBoxLayout()
		temp_layout.addWidget(self.ai_temperature)
		temp_layout.addWidget(self.ai_temperature_label)
		ai_layout.addRow("溫度:", temp_layout)
		self.ai_max_tokens = QSpinBox()
		self.ai_max_tokens.setRange(100, 8000)
		self.ai_max_tokens.setValue(1000)
		self.ai_max_tokens.setSingleStep(100)
		ai_layout.addRow("最大令牌數:", self.ai_max_tokens)
		self.compatibility_label = QLabel("")
		self.compatibility_label.setWordWrap(True)
		ai_layout.addRow("", self.compatibility_label)
		ai_group.setLayout(ai_layout)
		layout.addWidget(ai_group)
		button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
		button_box.accepted.connect(self.accept)
		button_box.rejected.connect(self.reject)
		layout.addWidget(button_box)
		self.update_model_list()
		self.on_provider_changed(self.ai_provider.currentIndex())
	def update_temperature_label(self, value):
		temperature = value / 100.0
		self.ai_temperature_label.setText(f"{temperature:.1f}")
	def on_provider_changed(self, index):
		provider = self.ai_provider.currentText()
		from src.ai.ai_service import AIService
		self.update_model_list()
		needs_endpoint = AIService.NEEDS_ENDPOINT.get(provider, True)
		self.endpoint_container.setVisible(needs_endpoint)
		is_custom = (provider == "自定義")
		self.ai_model.setVisible(not is_custom)
		self.custom_model.setVisible(is_custom)
		default_endpoint = AIService.DEFAULT_ENDPOINTS.get(provider)
		if default_endpoint:
			self.ai_endpoint.setPlaceholderText(f"可選，默認: {default_endpoint}")
		else:
			self.ai_endpoint.setPlaceholderText("請輸入 API 端點")
		is_openai_compatible = AIService.OPENAI_COMPATIBLE.get(provider, False)
		if is_openai_compatible and provider != "OpenAI":
			self.compatibility_label.setText(f"{provider} 使用 OpenAI 兼容 API，可以使用與 OpenAI 相同的格式發送請求。")
			self.compatibility_label.setVisible(True)
		else:
			self.compatibility_label.setVisible(False)
	def update_model_list(self):
		self.ai_model.clear()
		provider = self.ai_provider.currentText()
		if provider == "OpenAI":
			self.ai_model.addItems([
				"gpt-3.5-turbo",
				"gpt-4",
				"gpt-4-turbo",
				"gpt-4o"
			])
		elif provider == "Anthropic Claude":
			self.ai_model.addItems([
				"claude-3-opus-20240229",
				"claude-3-sonnet-20240229",
				"claude-3-haiku-20240307",
				"claude-2.1"
			])
		elif provider == "Google Gemini":
			self.ai_model.addItems([
				"gemini-pro",
				"gemini-1.5-pro",
				"gemini-1.5-flash"
			])
		elif provider == "Mistral AI":
			self.ai_model.addItems([
				"mistral-tiny",
				"mistral-small",
				"mistral-medium",
				"mistral-large-latest"
			])
	def load_settings(self):
		self.github_username.setText(self.settings.value("github/username", ""))
		save_credentials = self.settings.value("github/save_credentials", False, type=bool)
		self.save_credentials.setChecked(save_credentials)
		if save_credentials:
			self.github_token.setText(self.settings.value("github/token", ""))
		ai_provider = self.settings.value("ai/provider", "OpenAI")
		index = self.ai_provider.findText(ai_provider)
		if index >= 0:
			self.ai_provider.setCurrentIndex(index)
		self.ai_api_key.setText(self.settings.value("ai/api_key", ""))
		self.ai_endpoint.setText(self.settings.value("ai/endpoint", ""))
		self.custom_model.setText(self.settings.value("ai/custom_model", ""))
		self.update_model_list()
		ai_model = self.settings.value("ai/model", "")
		if ai_model:
			index = self.ai_model.findText(ai_model)
			if index >= 0:
				self.ai_model.setCurrentIndex(index)
		temperature = self.settings.value("ai/temperature", 0.7, type=float)
		self.ai_temperature.setValue(int(temperature * 100))
		max_tokens = self.settings.value("ai/max_tokens", 1000, type=int)
		self.ai_max_tokens.setValue(max_tokens)
	def save_settings(self):
		self.settings.setValue("github/username", self.github_username.text())
		self.settings.setValue("github/save_credentials", self.save_credentials.isChecked())
		if self.save_credentials.isChecked():
			self.settings.setValue("github/token", self.github_token.text())
		else:
			self.settings.setValue("github/token", "")
		self.settings.setValue("ai/provider", self.ai_provider.currentText())
		self.settings.setValue("ai/api_key", self.ai_api_key.text())
		self.settings.setValue("ai/endpoint", self.ai_endpoint.text())
		if self.ai_provider.currentText() == "自定義":
			self.settings.setValue("ai/model", self.custom_model.text())
			self.settings.setValue("ai/custom_model", self.custom_model.text())
		else:
			self.settings.setValue("ai/model", self.ai_model.currentText())
		self.settings.setValue("ai/temperature", self.ai_temperature.value() / 100.0)
		self.settings.setValue("ai/max_tokens", self.ai_max_tokens.value())
	def accept(self):
		self.save_settings()
		super().accept()
	def test_connection(self):
		provider = self.ai_provider.currentText()
		api_key = self.ai_api_key.text()
		endpoint = self.ai_endpoint.text()
		if not api_key:
			QMessageBox.warning(self, "缺少 API 金鑰", "請輸入 API 金鑰")
			return
		if provider == "自定義":
			model = self.custom_model.text()
			if not model:
				QMessageBox.warning(self, "缺少模型名稱", "請輸入自定義模型名稱")
				return
		else:
			model = self.ai_model.currentText()
			if not model:
				QMessageBox.warning(self, "缺少模型", "請選擇一個模型")
				return
		if provider == "自定義" and not endpoint:
			QMessageBox.warning(self, "缺少端點", "自定義服務需要指定 API 端點")
			return
		progress = QProgressDialog("正在測試連接...", "取消", 0, 0, self)
		progress.setWindowModality(Qt.WindowModal)
		progress.show()
		try:
			from src.ai.ai_service import AIService
			ai_service = AIService()
			ai_service.provider = provider
			ai_service.api_key = api_key
			ai_service.model = model
			if endpoint:
				ai_service.endpoint = endpoint
			elif provider in AIService.DEFAULT_ENDPOINTS:
				ai_service.endpoint = AIService.DEFAULT_ENDPOINTS[provider]
			else:
				progress.close()
				QMessageBox.warning(self, "缺少端點", "請輸入 API 端點")
				return
			result = ai_service.test_connection()
			progress.close()
			if "error" in result:
				QMessageBox.critical(self, "連接失敗", f"無法連接到 AI 服務: {result['error']}")
			else:
				response_dialog = QDialog(self)
				response_dialog.setWindowTitle("連接成功")
				response_dialog.setMinimumSize(600, 400)
				layout = QVBoxLayout(response_dialog)
				success_label = QLabel("成功連接到 AI 服務！")
				success_label.setStyleSheet("font-weight: bold; color: green;")
				layout.addWidget(success_label)
				if "response" in result:
					response_text = QTextEdit()
					response_text.setReadOnly(True)
					formatted_json = json.dumps(result["response"], indent=2, ensure_ascii=False)
					response_text.setPlainText(formatted_json)
					layout.addWidget(QLabel("API 回傳的 JSON:"))
					layout.addWidget(response_text)
				close_button = QPushButton("關閉")
				close_button.clicked.connect(response_dialog.accept)
				layout.addWidget(close_button)
				response_dialog.exec_()
		except Exception as e:
			progress.close()
			QMessageBox.critical(self, "連接失敗", f"發生錯誤: {str(e)}")
class MainWindow(QMainWindow):
	def __init__(self):
		super().__init__()
		self.setWindowTitle("提交日誌助手")
		self.setMinimumSize(1000, 700)
		self.repository = GitRepository()
		self.commit_helper = CommitHelper(self.repository)
		self.settings = QSettings("OG-Open-Source", "CommitLogAssistant")
		self.ai_request_in_progress = False
		self.init_ui()
	def init_ui(self):
		central_widget = QWidget()
		self.setCentralWidget(central_widget)
		main_layout = QVBoxLayout(central_widget)
		main_layout.setContentsMargins(0, 0, 0, 0)
		self.create_toolbar()
		content_widget = QWidget()
		content_layout = QVBoxLayout(content_widget)
		content_layout.setContentsMargins(10, 10, 10, 10)
		repo_layout = QHBoxLayout()
		repo_layout.addWidget(QLabel("當前倉庫:"))
		self.repo_path = QLineEdit()
		self.repo_path.setPlaceholderText("選擇 Git 倉庫...")
		self.repo_path.setReadOnly(True)
		repo_layout.addWidget(self.repo_path)
		browse_button = QPushButton("選擇倉庫")
		browse_button.clicked.connect(self.browse_repository)
		repo_layout.addWidget(browse_button)
		github_button = QPushButton("GitHub")
		github_button.clicked.connect(self.open_github_repos)
		repo_layout.addWidget(github_button)
		content_layout.addLayout(repo_layout)
		line = QFrame()
		line.setFrameShape(QFrame.HLine)
		line.setFrameShadow(QFrame.Sunken)
		content_layout.addWidget(line)
		main_splitter = QSplitter(Qt.Horizontal)
		branch_widget = QWidget()
		branch_layout = QVBoxLayout(branch_widget)
		branch_layout.setContentsMargins(0, 0, 0, 0)
		branch_label = QLabel("分支")
		branch_label.setFont(QFont("Arial", 10, QFont.Bold))
		branch_layout.addWidget(branch_label)
		self.branch_tree = QTreeWidget()
		self.branch_tree.setHeaderHidden(True)
		self.branch_tree.setColumnCount(1)
		branch_layout.addWidget(self.branch_tree)
		main_splitter.addWidget(branch_widget)
		changes_widget = QWidget()
		changes_layout = QVBoxLayout(changes_widget)
		changes_layout.setContentsMargins(0, 0, 0, 0)
		changes_label = QLabel("變更")
		changes_label.setFont(QFont("Arial", 10, QFont.Bold))
		changes_layout.addWidget(changes_label)
		self.staged_files = QListWidget()
		self.staged_files.setAlternatingRowColors(True)
		self.staged_files.itemClicked.connect(self.show_diff)
		changes_layout.addWidget(self.staged_files)
		stage_all_layout = QHBoxLayout()
		stage_all_layout.addStretch()
		stage_all_button = QPushButton("暫存所有變更")
		stage_all_button.clicked.connect(self.stage_all_files)
		stage_all_layout.addWidget(stage_all_button)
		changes_layout.addLayout(stage_all_layout)
		main_splitter.addWidget(changes_widget)
		diff_widget = QWidget()
		diff_layout = QVBoxLayout(diff_widget)
		diff_layout.setContentsMargins(0, 0, 0, 0)
		diff_label = QLabel("差異")
		diff_label.setFont(QFont("Arial", 10, QFont.Bold))
		diff_layout.addWidget(diff_label)
		self.diff_view = QTextEdit()
		self.diff_view.setReadOnly(True)
		self.diff_view.setFont(QFont("Courier New", 9))
		diff_layout.addWidget(self.diff_view)
		main_splitter.addWidget(diff_widget)
		main_splitter.setSizes([200, 300, 500])
		content_layout.addWidget(main_splitter)
		line2 = QFrame()
		line2.setFrameShape(QFrame.HLine)
		line2.setFrameShadow(QFrame.Sunken)
		content_layout.addWidget(line2)
		commit_widget = QWidget()
		commit_layout = QVBoxLayout(commit_widget)
		commit_layout.setContentsMargins(0, 0, 0, 0)
		commit_label = QLabel("提交信息")
		commit_label.setFont(QFont("Arial", 10, QFont.Bold))
		commit_layout.addWidget(commit_label)
		type_scope_layout = QHBoxLayout()
		type_scope_layout.addWidget(QLabel("類型:"))
		self.commit_type = QComboBox()
		self.commit_type.addItems([
			"Added",
			"Changed",
			"Deprecated",
			"Removed",
			"Fixed",
			"Security"
		])
		type_scope_layout.addWidget(self.commit_type)
		type_scope_layout.addWidget(QLabel("範圍:"))
		self.commit_scope = QLineEdit()
		self.commit_scope.setPlaceholderText("可選")
		type_scope_layout.addWidget(self.commit_scope)
		summary_layout = QHBoxLayout()
		summary_layout.addWidget(QLabel("摘要:"))
		self.commit_summary = QLineEdit()
		self.commit_summary.setPlaceholderText("簡短摘要...")
		summary_layout.addWidget(self.commit_summary)
		commit_layout.addLayout(summary_layout)
		description_layout = QHBoxLayout()
		description_layout.addWidget(QLabel("描述:"))
		self.ai_button = QPushButton("AI 生成")
		self.ai_button.setToolTip("使用 AI 生成提交信息")
		self.ai_button.clicked.connect(self.generate_ai_commit)
		description_layout.addStretch()
		description_layout.addWidget(self.ai_button)
		commit_layout.addLayout(description_layout)
		self.commit_description = QTextEdit()
		self.commit_description.setPlaceholderText("詳細描述您的變更...")
		self.commit_description.setMaximumHeight(100)
		commit_layout.addWidget(self.commit_description)
		suggestions_layout = QHBoxLayout()
		suggestions_layout.addWidget(QLabel("建議:"))
		self.suggestions = QComboBox()
		self.suggestions.setMinimumWidth(400)
		self.suggestions.currentIndexChanged.connect(self.use_suggestion_from_combo)
		suggestions_layout.addWidget(self.suggestions)
		commit_layout.addLayout(suggestions_layout)
		buttons_layout = QHBoxLayout()
		buttons_layout.addStretch()
		self.preview_button = QPushButton("預覽")
		self.preview_button.clicked.connect(self.preview_commit)
		buttons_layout.addWidget(self.preview_button)
		self.commit_button = QPushButton("提交")
		self.commit_button.setStyleSheet("background-color: #2ea44f; color: white;")
		self.commit_button.clicked.connect(self.do_commit)
		buttons_layout.addWidget(self.commit_button)
		commit_layout.addLayout(buttons_layout)
		content_layout.addWidget(commit_widget)
		main_layout.addWidget(content_widget)
		self.statusBar().showMessage("就緒")
		self.staged_files.itemClicked.connect(self.show_diff)
	def create_toolbar(self):
		toolbar = QToolBar("主工具欄")
		toolbar.setMovable(False)
		toolbar.setIconSize(QSize(16, 16))
		settings_action = QAction("設定", self)
		settings_action.triggered.connect(self.open_settings)
		toolbar.addAction(settings_action)
		refresh_action = QAction("刷新", self)
		refresh_action.triggered.connect(self.refresh_files)
		toolbar.addAction(refresh_action)
		fetch_action = QAction("獲取遠端", self)
		fetch_action.triggered.connect(self.fetch_remote)
		fetch_action.setToolTip("從遠端倉庫獲取最新變更")
		toolbar.addAction(fetch_action)
		push_action = QAction("推送變更", self)
		push_action.triggered.connect(self.push_changes)
		push_action.setToolTip("推送本地變更到遠端倉庫")
		toolbar.addAction(push_action)
		self.addToolBar(toolbar)
	def show_diff(self, item):
		file_path = item.text()
		diff = self.repository.get_file_diff(file_path)
		self.diff_view.setPlainText(diff)
	def open_settings(self):
		dialog = SettingsDialog(self)
		if dialog.exec_() == QDialog.Accepted:
			self.statusBar().showMessage("設定已保存")
	def generate_ai_commit(self):
		if self.ai_request_in_progress:
			self.statusBar().showMessage("AI 請求正在進行中，請稍候...")
			return
		if hasattr(self, 'ai_button'):
			self.ai_button.setEnabled(False)
		api_key = self.settings.value("ai/api_key", "")
		if not api_key:
			if hasattr(self, 'ai_button'):
				self.ai_button.setEnabled(True)
			QMessageBox.warning(self, "缺少 API 金鑰", "請在設定中添加 AI API 金鑰")
			return
		staged_files = self.repository.get_staged_files()
		if not staged_files:
			if hasattr(self, 'ai_button'):
				self.ai_button.setEnabled(True)
			QMessageBox.information(self, "沒有變更", "沒有已暫存的文件可供分析")
			return
		self.ai_request_in_progress = True
		progress = QProgressDialog("正在使用 AI 生成提交信息...", "取消", 0, 0, self)
		progress.setWindowModality(Qt.WindowModal)
		progress.show()
		try:
			all_diffs = []
			for file in staged_files:
				diff = self.repository.get_file_diff(file)
				if diff.startswith("無法獲取差異:"):
					self.statusBar().showMessage(f"警告: {diff}")
					continue
				if diff != "This is a binary file.":
					all_diffs.append(f"File: {file}\n{diff}\n")
			if not all_diffs:
				self.ai_request_in_progress = False
				if hasattr(self, 'ai_button'):
					self.ai_button.setEnabled(True)
				progress.close()
				QMessageBox.warning(self, "無法生成提交信息", "沒有找到有效的文件差異，可能是因為所有文件都是二進制文件或差異獲取失敗。")
				return
			diff_content = "\n".join(all_diffs)
			from src.ai.ai_service import AIService
			ai_service = AIService()
			result = ai_service.get_commit_content(diff_content)
			self.ai_request_in_progress = False
			if hasattr(self, 'ai_button'):
				self.ai_button.setEnabled(True)
			progress.close()
			if "error" in result:
				error_msg = result["error"]
				error_dialog = QMessageBox(QMessageBox.Critical, "AI 生成失敗",
										  f"發生錯誤:\n{error_msg}",
										  QMessageBox.Ok, self)
				error_dialog.setDetailedText(f"完整錯誤信息:\n{error_msg}")
				error_dialog.exec_()
				return
			try:
				commit_type = result.get("type", "Changed")
				commit_scope = result.get("scope", "")
				summary = result.get("summary", "")
				description = result.get("description", "")
				if summary.startswith(commit_type) or any(summary.startswith(t + ":") for t in ["Added", "Changed", "Deprecated", "Removed", "Fixed", "Security"]):
					parts = summary.split(":", 1)
					if len(parts) > 1:
						summary = parts[1].strip()
				index = self.commit_type.findText(commit_type, Qt.MatchFixedString)
				if index >= 0:
					self.commit_type.setCurrentIndex(index)
				self.commit_scope.setText(commit_scope)
				self.commit_summary.setText(summary)
				self.commit_description.setText(description)
				self.statusBar().showMessage("AI 提交信息已生成")
			except Exception as e:
				QMessageBox.warning(self, "填充表單失敗", f"無法將 AI 生成的內容填充到表單: {str(e)}")
		except Exception as e:
			self.ai_request_in_progress = False
			if hasattr(self, 'ai_button'):
				self.ai_button.setEnabled(True)
			progress.close()
			QMessageBox.warning(self, "AI 生成失敗", f"發生錯誤: {str(e)}")
	def use_suggestion_from_combo(self, index):
		if index <= 0:
			return
		suggestion_text = self.suggestions.currentText()
		parts = suggestion_text.split(": ", 1)
		if len(parts) == 2:
			type_part = parts[0]
			description = parts[1]
			if "(" in type_part and ")" in type_part:
				type_scope = type_part.split("(")
				commit_type = type_scope[0]
				commit_scope = type_scope[1].rstrip(")")
				index = self.commit_type.findText(commit_type)
				if index >= 0:
					self.commit_type.setCurrentIndex(index)
				self.commit_scope.setText(commit_scope)
			else:
				index = self.commit_type.findText(type_part)
				if index >= 0:
					self.commit_type.setCurrentIndex(index)
			self.commit_description.setText(description)
	def browse_repository(self):
		repo_path = QFileDialog.getExistingDirectory(
			self,
			"選擇 Git 倉庫目錄",
			os.path.expanduser("~")
		)
		if repo_path:
			self.repo_path.setText(repo_path)
			if self.repository.open(repo_path):
				self.setWindowTitle(f"提交日誌助手 - {os.path.basename(repo_path)}")
				self.statusBar().showMessage(f"成功打開倉庫: {repo_path}")
				self.repository.stage_all_files()
				self.refresh_files()
			else:
				self.statusBar().showMessage(f"錯誤: {repo_path} 不是有效的 Git 倉庫")
	def refresh_files(self):
		self.staged_files.clear()
		staged = self.repository.get_staged_files()
		print(f"已暫存文件: {staged}")
		for file in staged:
			self.staged_files.addItem(file)
		self.refresh_branches()
		suggestions = self.commit_helper.analyze_changes()
		self.suggestions.clear()
		self.suggestions.addItem("-- 選擇建議 --")
		for suggestion in suggestions:
			self.suggestions.addItem(suggestion)
	def refresh_branches(self):
		self.branch_tree.clear()
		branches = self.repository.get_branches()
		if isinstance(branches, dict) and "error" in branches:
			self.statusBar().showMessage(branches["error"])
			return
		local_branches_item = QTreeWidgetItem(self.branch_tree, ["本地分支"])
		for branch in branches.get("local", []):
			branch_item = QTreeWidgetItem(local_branches_item, [branch])
			if branch == branches.get("current", ""):
				font = branch_item.font(0)
				font.setBold(True)
				branch_item.setFont(0, font)
		if branches.get("remote", []):
			remote_branches_item = QTreeWidgetItem(self.branch_tree, ["遠端分支"])
			for branch in branches.get("remote", []):
				QTreeWidgetItem(remote_branches_item, [branch])
		self.branch_tree.expandAll()
	def preview_commit(self):
		commit_type = self.commit_type.currentText()
		commit_scope = self.commit_scope.text()
		summary = self.commit_summary.text()
		description = self.commit_description.toPlainText()
		if not summary:
			QMessageBox.warning(self, "缺少摘要", "請輸入提交摘要")
			return
		message = self.commit_helper.format_commit_message(
			commit_type, commit_scope, summary, description
		)
		preview_dialog = QDialog(self)
		preview_dialog.setWindowTitle("提交信息預覽")
		preview_dialog.setMinimumSize(600, 300)
		layout = QVBoxLayout(preview_dialog)
		info_label = QLabel("以下是將提交的信息：")
		info_label.setWordWrap(True)
		layout.addWidget(info_label)
		preview_text = QTextEdit()
		preview_text.setReadOnly(True)
		preview_text.setFont(QFont("Courier New", 10))
		preview_text.setPlainText(message)
		preview_text.setStyleSheet("""
			QTextEdit {
				background-color: #f5f5f5;
				border: 1px solid #ddd;
				padding: 8px;
			}
		""")
		layout.addWidget(preview_text)
		button_box = QDialogButtonBox()
		copy_button = QPushButton("複製到剪貼板")
		copy_button.clicked.connect(lambda: QApplication.clipboard().setText(message))
		button_box.addButton(copy_button, QDialogButtonBox.ActionRole)
		ok_button = QPushButton("確定")
		ok_button.clicked.connect(preview_dialog.accept)
		button_box.addButton(ok_button, QDialogButtonBox.AcceptRole)
		layout.addWidget(button_box)
		preview_dialog.exec_()
	def do_commit(self):
		commit_type = self.commit_type.currentText()
		commit_scope = self.commit_scope.text()
		summary = self.commit_summary.text()
		description = self.commit_description.toPlainText()
		if not summary:
			QMessageBox.warning(self, "缺少摘要", "請輸入提交摘要")
			return
		message = self.commit_helper.format_commit_message(
			commit_type, commit_scope, summary, description
		)
		if self.repository.commit(message):
			self.statusBar().showMessage("提交成功")
			response = QMessageBox.question(
				self,
				"推送變更",
				"提交成功。是否要推送變更到遠端倉庫？",
				QMessageBox.Yes | QMessageBox.No,
				QMessageBox.No
			)
			if response == QMessageBox.Yes:
				self.push_changes()
			self.commit_summary.clear()
			self.commit_description.clear()
			self.refresh_files()
		else:
			QMessageBox.critical(self, "提交失敗", "無法完成提交，請檢查倉庫狀態")
			self.statusBar().showMessage("提交失敗")
	def open_github_repos(self):
		from src.ui.github_dialog import GitHubRepoDialog
		dialog = GitHubRepoDialog(self)
		if dialog.exec_() == QDialog.Accepted and dialog.selected_repo:
			repo_path = dialog.selected_repo
			self.repo_path.setText(repo_path)
			if self.repository.open(repo_path):
				self.setWindowTitle(f"提交日誌助手 - {os.path.basename(repo_path)}")
				self.statusBar().showMessage(f"成功打開倉庫: {repo_path}")
				self.repository.stage_all_files()
				self.refresh_files()
			else:
				self.statusBar().showMessage(f"錯誤: {repo_path} 不是有效的 Git 倉庫")
	def stage_all_files(self):
		if self.repository.stage_all_files():
			self.refresh_files()
			self.statusBar().showMessage("已暫存所有文件")
		else:
			QMessageBox.warning(self, "暫存失敗", "無法暫存所有文件")
	def fetch_remote(self):
		if not self.repository.repo:
			QMessageBox.warning(self, "未打開倉庫", "請先打開一個 Git 倉庫")
			return
		progress = QProgressDialog("正在從遠端獲取最新變更...", "取消", 0, 0, self)
		progress.setWindowModality(Qt.WindowModal)
		progress.show()
		result = self.repository.fetch_remote()
		progress.close()
		if "error" in result:
			QMessageBox.warning(self, "獲取失敗", result["error"])
			return
		details = "\n".join(result.get("details", []))
		if details:
			info_dialog = QMessageBox(QMessageBox.Information, "獲取成功",
									 result["message"],
									 QMessageBox.Ok, self)
			info_dialog.setDetailedText(details)
			info_dialog.exec_()
		else:
			QMessageBox.information(self, "獲取成功", result["message"])
		self.refresh_branches()
		self.statusBar().showMessage(result["message"])
	def push_changes(self):
		if not self.repository.repo:
			QMessageBox.warning(self, "未打開倉庫", "請先打開一個 Git 倉庫")
			return
		branches = self.repository.get_branches()
		if isinstance(branches, dict) and "error" in branches:
			QMessageBox.warning(self, "獲取分支失敗", branches["error"])
			return
		current_branch = branches.get("current", "")
		if not current_branch:
			QMessageBox.warning(self, "未知分支", "無法確定當前分支")
			return
		progress = QProgressDialog(f"正在推送變更到 origin/{current_branch}...", "取消", 0, 0, self)
		progress.setWindowModality(Qt.WindowModal)
		progress.show()
		result = self.repository.push_changes(branch=current_branch)
		progress.close()
		if "error" in result:
			QMessageBox.warning(self, "推送失敗", result["error"])
			return
		if not result.get("success", False):
			details = "\n".join(result.get("details", []))
			error_dialog = QMessageBox(QMessageBox.Warning, "推送失敗",
									  result["message"],
									  QMessageBox.Ok, self)
			if details:
				error_dialog.setDetailedText(details)
			error_dialog.exec_()
			return
		details = "\n".join(result.get("details", []))
		if details:
			info_dialog = QMessageBox(QMessageBox.Information, "推送成功",
									  result["message"],
									  QMessageBox.Ok, self)
			info_dialog.setDetailedText(details)
			info_dialog.exec_()
		else:
			QMessageBox.information(self, "推送成功", result["message"])
		self.refresh_branches()
		self.statusBar().showMessage(result["message"])