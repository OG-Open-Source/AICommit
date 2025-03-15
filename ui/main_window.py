from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
							QSplitter, QTreeView, QListWidget, QTextEdit,
							QToolBar, QAction, QStatusBar, QFileDialog, QMessageBox,
							QListWidgetItem, QFileSystemModel, QLabel, QLineEdit,
							QPushButton, QGroupBox, QFormLayout, QTabWidget, QDialog,
							QComboBox, QCheckBox, QMenu, QMenuBar, QApplication)
from PyQt5.QtCore import Qt, QSize, QDir, QTimer, QPropertyAnimation, QEasingCurve, QRect, QThread, pyqtSignal, QEvent
from PyQt5.QtGui import QIcon, QColor, QTextCharFormat, QBrush, QFont, QPainter, QPen

import os
import logging
import time
import sys
import threading
import tempfile

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from git.repository import GitRepository
from ui.commit_dialog import CommitDialog
from utils.config import Config

# 配置日志记录器
logger = logging.getLogger("ui.main_window")

class LoadingOverlay(QWidget):
	"""加载遮罩，显示加载状态"""
	def __init__(self, parent=None):
		super().__init__(parent)
		# 首先设置所有可能使用的属性，确保它们存在
		self.parent = parent
		self.angle = 0
		self.timer = None
		self.message = "加载中..."
		self.opacity = 0.0
		self.fade_animation = None
		
		# 然后进行其他初始化
		self.setAttribute(Qt.WA_TranslucentBackground)
		
		# 增加动画流畅度，更新频率提高到每30毫秒
		try:
			self.timer = QTimer(self)
			self.timer.timeout.connect(self.rotate)
			self.timer.start(30)  # 每30毫秒更新一次
			logger.debug("成功初始化旋转计时器")
		except Exception as e:
			logger.error(f"初始化旋转计时器失败: {str(e)}", exc_info=True)
		
		self.hide()
		
		# 设置鼠标追踪，以便捕获所有鼠标事件
		self.setMouseTracking(True)
		
		# 添加淡入淡出效果
		try:
			self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
			self.fade_animation.setDuration(200)  # 200毫秒的动画时间
			logger.debug("成功初始化淡入淡出动画")
		except Exception as e:
			logger.error(f"初始化淡入淡出动画失败: {str(e)}", exc_info=True)
	
	def paintEvent(self, event):
		try:
			painter = QPainter(self)
			painter.setRenderHint(QPainter.Antialiasing)
			
			# 使用更轻量级的绘制方式
			painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
			
			# 绘制半透明背景
			painter.fillRect(self.rect(), QColor(0, 0, 0, 80))  # 降低背景不透明度
			
			# 绘制加载文本
			painter.setPen(QColor(255, 255, 255))
			font = QFont()
			font.setPointSize(12)
			painter.setFont(font)
			
			# 计算文本位置，放在中心偏下的位置
			text_rect = self.rect()
			text_rect.setTop(text_rect.top() + self.height() // 2 - 30)
			painter.drawText(text_rect, Qt.AlignHCenter, self.message)
			
			# 绘制旋转的加载图标，放在文本下方
			icon_x = self.width() // 2
			icon_y = self.height() // 2 + 30
			painter.translate(icon_x, icon_y)
			painter.rotate(self.angle)
			
			pen = QPen(QColor(255, 255, 255))
			pen.setWidth(3)
			painter.setPen(pen)
			
			# 绘制一个不完整的圆
			rect = QRect(-15, -15, 30, 30)
			painter.drawArc(rect, 0, 270 * 16)  # 角度以1/16度为单位
		except Exception as e:
			logger.error(f"绘制加载遮罩失败: {str(e)}", exc_info=True)
	
	def rotate(self):
		try:
			# 更平滑的旋转
			self.angle = (self.angle + 6) % 360
			self.update()
		except Exception as e:
			logger.error(f"旋转加载图标失败: {str(e)}", exc_info=True)
	
	def showEvent(self, event):
		"""显示事件处理"""
		try:
			# 调整大小并确保在最上层
			self.resize(self.parent.size())
			self.raise_()
			
			# 淡入效果
			if hasattr(self, 'fade_animation') and self.fade_animation is not None:
				try:
					self.fade_animation.setStartValue(0.0)
					self.fade_animation.setEndValue(1.0)
					self.fade_animation.start()
					logger.debug("开始淡入动画")
				except Exception as e:
					logger.error(f"启动淡入动画失败: {str(e)}", exc_info=True)
		except Exception as e:
			logger.error(f"显示加载遮罩失败: {str(e)}", exc_info=True)
	
	def show_with_message(self, message="加载中..."):
		try:
			self.message = message
			logger.debug(f"显示加载遮罩，消息: {message}")
			self.show()
		except Exception as e:
			logger.error(f"显示加载遮罩消息失败: {str(e)}", exc_info=True)
	
	def hideEvent(self, event):
		try:
			# 停止旋转计时器，减少资源占用
			self.timer.stop()
			logger.debug("停止加载遮罩计时器")
		except Exception as e:
			logger.error(f"隐藏加载遮罩事件处理失败: {str(e)}", exc_info=True)
	
	def hide(self):
		"""隐藏加载遮罩"""
		try:
			logger.debug("尝试隐藏加载遮罩")
			
			# 检查 fade_animation 是否存在且有效
			has_animation = hasattr(self, 'fade_animation') and self.fade_animation is not None
			
			# 淡出效果
			if has_animation:
				try:
					# 断开之前的连接，避免多次连接
					try:
						self.fade_animation.finished.disconnect()
					except (TypeError, AttributeError):
						# 如果没有连接或者方法不存在，会抛出异常
						pass
					
					self.fade_animation.setStartValue(1.0)
					self.fade_animation.setEndValue(0.0)
					self.fade_animation.finished.connect(self._hide_finished)
					self.fade_animation.start()
					logger.debug("开始淡出动画")
				except Exception as e:
					logger.error(f"启动淡出动画失败: {str(e)}", exc_info=True)
					# 如果动画失败，直接隐藏
					super().hide()
					# 尝试重新启动计时器
					if hasattr(self, 'timer') and self.timer is not None:
						try:
							self.timer.start()
						except:
							pass
			else:
				# 如果没有动画，直接隐藏
				logger.debug("无动画，直接隐藏")
				super().hide()
				# 尝试重新启动计时器
				if hasattr(self, 'timer') and self.timer is not None:
					try:
						self.timer.start()
					except:
						pass
		except Exception as e:
			logger.error(f"隐藏加载遮罩失败: {str(e)}", exc_info=True)
			# 确保在出错时也能隐藏
			try:
				super().hide()
			except:
				pass
	
	def _hide_finished(self):
		"""淡出动画完成后的回调"""
		try:
			logger.debug("淡出动画完成，隐藏加载遮罩")
			# 断开信号连接，避免多次调用
			if hasattr(self, 'fade_animation') and self.fade_animation is not None:
				try:
					self.fade_animation.finished.disconnect(self._hide_finished)
				except (TypeError, AttributeError):
					# 如果已经断开或方法不存在，会抛出异常
					pass
			
			# 调用真正的隐藏方法
			super().hide()
			
			# 重新启动计时器，为下次显示做准备
			if hasattr(self, 'timer') and self.timer is not None:
				try:
					self.timer.start()
				except:
					pass
		except Exception as e:
			logger.error(f"淡出动画完成后隐藏加载遮罩失败: {str(e)}", exc_info=True)
			# 确保在出错时也能隐藏
			try:
				super().hide()
			except:
				pass
	
	# 捕获所有鼠标事件，防止点击穿透
	def mousePressEvent(self, event):
		event.accept()
	
	def mouseReleaseEvent(self, event):
		event.accept()
	
	def mouseMoveEvent(self, event):
		event.accept()
	
	def mouseDoubleClickEvent(self, event):
		event.accept()

class ApiWorker(QThread):
	"""处理 API 请求的工作线程"""
	finished = pyqtSignal(object)  # 成功完成信号，传递结果
	error = pyqtSignal(str)  # 错误信号，传递错误信息
	
	def __init__(self, task_type, provider=None, api_params=None):
		super().__init__()
		self.task_type = task_type  # 'test_connection' 或 'generate_commit'
		self.provider = provider
		self.api_params = api_params or {}
		
	def run(self):
		try:
			if self.task_type == 'test_connection':
				result = self._test_connection()
				self.finished.emit(result)
			elif self.task_type == 'generate_commit':
				result = self._generate_commit()
				self.finished.emit(result)
		except Exception as e:
			self.error.emit(str(e))
	
	def _test_connection(self):
		"""测试与 AI 提供商的连接"""
		import time
		import requests
		import json
		
		provider = self.provider
		api_params = self.api_params
		test_message = "Hello, this is a test message. Please respond with a simple greeting."
		
		if provider == "OpenAI":
			import openai
			api_key = api_params.get('api_key', '')
			model = api_params.get('model', 'gpt-3.5-turbo')
			
			if not api_key:
				raise ValueError("API 密钥不能为空")
			
			# 设置 API 密钥
			client = openai.OpenAI(api_key=api_key)
			
			# 调用 API
			start_time = time.time()
			response = client.chat.completions.create(
				model=model,
				messages=[{"role": "user", "content": test_message}],
				max_tokens=50
			)
			end_time = time.time()
			
			# 获取响应文本
			result = response.choices[0].message.content.strip()
			
			return {
				'success': True,
				'provider': provider,
				'model': model,
				'response_time': end_time - start_time,
				'result': result
			}
			
		elif provider == "Anthropic":
			import anthropic
			api_key = api_params.get('api_key', '')
			model = api_params.get('model', 'claude-3-haiku')
			
			if not api_key:
				raise ValueError("API 密钥不能为空")
			
			# 设置 API 密钥
			client = anthropic.Anthropic(api_key=api_key)
			
			# 调用 API
			start_time = time.time()
			response = client.messages.create(
				model=model,
				messages=[{"role": "user", "content": test_message}],
				max_tokens=50
			)
			end_time = time.time()
			
			# 获取响应文本
			result = response.content[0].text
			
			return {
				'success': True,
				'provider': provider,
				'model': model,
				'response_time': end_time - start_time,
				'result': result
			}
			
		elif provider == "Google":
			import google.generativeai as genai
			api_key = api_params.get('api_key', '')
			model_name = api_params.get('model', 'gemini-pro')
			
			if not api_key:
				raise ValueError("API 密钥不能为空")
			
			# 设置 API 密钥
			genai.configure(api_key=api_key)
			
			# 获取模型
			model = genai.GenerativeModel(model_name)
			
			# 调用 API
			start_time = time.time()
			response = model.generate_content(test_message)
			end_time = time.time()
			
			# 获取响应文本
			result = response.text
			
			return {
				'success': True,
				'provider': provider,
				'model': model_name,
				'response_time': end_time - start_time,
				'result': result
			}
			
		elif provider == "自定义 Web API":
			api_url = api_params.get('api_url', '')
			api_key = api_params.get('api_key', '')
			model = api_params.get('model', '')
			
			if not api_url:
				raise ValueError("API URL 不能为空")
			
			# 准备请求头
			headers = {
				"Content-Type": "application/json"
			}
			
			if api_key:
				headers["Authorization"] = f"Bearer {api_key}"
			
			# 准备请求体
			payload = {
				"model": model,
				"messages": [
					{"role": "user", "content": test_message}
				]
			}
			
			# 调用 API
			start_time = time.time()
			response = requests.post(api_url, headers=headers, json=payload)
			end_time = time.time()
			
			# 检查响应状态
			response.raise_for_status()
			
			# 显示原始响应
			raw_response = response.text
			
			# 尝试解析 JSON
			try:
				response_data = response.json()
				formatted_json = json.dumps(response_data, indent=2)
				
				# 尝试提取响应文本
				result = "无法从响应中提取文本内容"
				
				if "choices" in response_data and len(response_data["choices"]) > 0:
					if "message" in response_data["choices"][0]:
						result = response_data["choices"][0]["message"]["content"]
					elif "text" in response_data["choices"][0]:
						result = response_data["choices"][0]["text"]
				elif "content" in response_data:
					result = response_data["content"]
				
				return {
					'success': True,
					'provider': provider,
					'url': api_url,
					'response_time': end_time - start_time,
					'result': result,
					'raw_json': formatted_json
				}
			except json.JSONDecodeError:
				# 如果不是 JSON，返回错误
				raise ValueError(f"API 返回了非 JSON 格式的响应。这可能是因为 API 端点不正确或者服务器返回了 HTML 错误页面。\n\n原始响应:\n{raw_response[:500]}...")
	
	def _generate_commit(self):
		"""生成提交信息"""
		import time
		import requests
		import json
		
		provider = self.api_params.get('provider', 'OpenAI')
		system_prompt = self.api_params.get('system_prompt', '')
		all_diffs = self.api_params.get('diffs', '')
		
		if provider == "OpenAI":
			import openai
			api_key = self.api_params.get('api_key', '')
			model = self.api_params.get('model', 'gpt-3.5-turbo')
			
			if not api_key:
				raise ValueError("OpenAI API 密钥未设置")
			
			# 设置 API 密钥
			client = openai.OpenAI(api_key=api_key)
			
			# 准备消息
			messages = []
			
			# 添加系统提示
			if system_prompt:
				if "{diff_content}" in system_prompt:
					system_prompt = system_prompt.replace("{diff_content}", all_diffs)
				messages.append({"role": "system", "content": system_prompt})
			
			# 如果系统提示中没有包含差异内容，则添加为用户消息
			if "{diff_content}" not in self.api_params.get('original_system_prompt', ''):
				messages.append({"role": "user", "content": all_diffs})
			
			# 调用 API
			start_time = time.time()
			response = client.chat.completions.create(
				model=model,
				messages=messages,
				temperature=0.3
			)
			end_time = time.time()
			
			# 获取响应文本
			commit_message = response.choices[0].message.content.strip()
			
			return {
				'success': True,
				'provider': provider,
				'response_time': end_time - start_time,
				'commit_message': commit_message
			}
			
		elif provider == "Anthropic":
			import anthropic
			api_key = self.api_params.get('api_key', '')
			model = self.api_params.get('model', 'claude-3-haiku')
			
			if not api_key:
				raise ValueError("Anthropic API 密钥未设置")
			
			# 设置 API 密钥
			client = anthropic.Anthropic(api_key=api_key)
			
			# 准备消息
			messages = []
			
			# 添加系统提示
			system = None
			if system_prompt:
				if "{diff_content}" in system_prompt:
					system_prompt = system_prompt.replace("{diff_content}", all_diffs)
				system = system_prompt
			
			# 如果系统提示中没有包含差异内容，则添加为用户消息
			if "{diff_content}" not in self.api_params.get('original_system_prompt', ''):
				messages.append({"role": "user", "content": all_diffs})
			else:
				messages.append({"role": "user", "content": "请根据上述代码差异生成提交信息"})
			
			# 调用 API
			start_time = time.time()
			response = client.messages.create(
				model=model,
				messages=messages,
				system=system,
				temperature=0.3
			)
			end_time = time.time()
			
			# 获取响应文本
			commit_message = response.content[0].text
			
			return {
				'success': True,
				'provider': provider,
				'response_time': end_time - start_time,
				'commit_message': commit_message
			}
			
		elif provider == "Google":
			import google.generativeai as genai
			api_key = self.api_params.get('api_key', '')
			model_name = self.api_params.get('model', 'gemini-pro')
			
			if not api_key:
				raise ValueError("Google API 密钥未设置")
			
			# 设置 API 密钥
			genai.configure(api_key=api_key)
			
			# 获取模型
			model = genai.GenerativeModel(model_name)
			
			# 准备提示
			prompt = system_prompt if "{diff_content}" in self.api_params.get('original_system_prompt', '') else all_diffs
			
			# 调用 API
			start_time = time.time()
			response = model.generate_content(prompt)
			end_time = time.time()
			
			# 获取响应文本
			commit_message = response.text
			
			return {
				'success': True,
				'provider': provider,
				'response_time': end_time - start_time,
				'commit_message': commit_message
			}
			
		elif provider == "自定义 Web API":
			api_url = self.api_params.get('api_url', '')
			api_key = self.api_params.get('api_key', '')
			model = self.api_params.get('model', '')
			
			if not api_url:
				raise ValueError("Web API URL 未设置")
			
			# 准备请求头
			headers = {
				"Content-Type": "application/json"
			}
			
			if api_key:
				headers["Authorization"] = f"Bearer {api_key}"
			
			# 准备请求体
			payload = {
				"model": model,
				"messages": [
					{"role": "system", "content": system_prompt}
				]
			}
			
			# 如果系统提示词中没有包含差异内容，则添加为用户消息
			if "{diff_content}" not in self.api_params.get('original_system_prompt', ''):
				payload["messages"].append({"role": "user", "content": all_diffs})
			
			# 调用 API
			start_time = time.time()
			response = requests.post(api_url, headers=headers, json=payload)
			end_time = time.time()
			
			# 检查响应状态
			response.raise_for_status()
			
			# 检查响应内容是否为空
			if not response.text.strip():
				raise ValueError("API 返回了空响应")
			
			# 尝试解析 JSON 响应
			try:
				response_data = response.json()
			except json.JSONDecodeError as e:
				# 如果不是 JSON 格式，抛出异常
				raise ValueError(f"API 返回了非 JSON 格式的响应。这可能是因为 API 端点不正确或者服务器返回了错误页面。\n\n原始响应:\n{response.text[:200]}...")
			
			# 尝试从不同的响应格式中提取文本
			if "choices" in response_data and len(response_data["choices"]) > 0:
				# OpenAI 格式
				if "message" in response_data["choices"][0]:
					commit_message = response_data["choices"][0]["message"]["content"]
				else:
					commit_message = response_data["choices"][0]["text"]
			elif "content" in response_data:
				# 简单格式
				commit_message = response_data["content"]
			elif isinstance(response_data, list) and len(response_data) > 0:
				# 数组格式
				if isinstance(response_data[0], dict) and "content" in response_data[0]:
					commit_message = response_data[0]["content"]
				else:
					commit_message = str(response_data[0])
			elif isinstance(response_data, dict) and "text" in response_data:
				# 另一种常见格式
				commit_message = response_data["text"]
			elif isinstance(response_data, str):
				# 直接是字符串
				commit_message = response_data
			else:
				# 未知格式，返回整个响应
				commit_message = json.dumps(response_data, indent=2)
			
			return {
				'success': True,
				'provider': provider,
				'response_time': end_time - start_time,
				'commit_message': commit_message
			}

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

		# 添加测试按钮
		test_openai_button = QPushButton("测试连接")
		test_openai_button.clicked.connect(lambda: self.test_connection("OpenAI"))
		openai_layout.addRow("", test_openai_button)

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

		# 添加测试按钮
		test_anthropic_button = QPushButton("测试连接")
		test_anthropic_button.clicked.connect(lambda: self.test_connection("Anthropic"))
		anthropic_layout.addRow("", test_anthropic_button)

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

		# 添加测试按钮
		test_google_button = QPushButton("测试连接")
		test_google_button.clicked.connect(lambda: self.test_connection("Google"))
		google_layout.addRow("", test_google_button)

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

		# 添加测试按钮
		test_web_button = QPushButton("测试连接")
		test_web_button.clicked.connect(lambda: self.test_connection("自定义 Web API"))
		web_layout.addRow("", test_web_button)

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

	def test_connection(self, provider):
		"""测试与 AI 提供商的连接"""
		try:
			# 检查是否安装了所需的库
			if provider == "OpenAI":
				try:
					import openai
				except ImportError:
					QMessageBox.critical(self, "错误", "未安装 OpenAI 库。请运行: pip install openai>=1.0.0")
					return
			elif provider == "Anthropic":
				try:
					import anthropic
				except ImportError:
					QMessageBox.critical(self, "错误", "未安装 Anthropic 库。请运行: pip install anthropic>=0.5.0")
					return
			elif provider == "Google":
				try:
					import google.generativeai as genai
				except ImportError:
					QMessageBox.critical(self, "错误", "未安装 Google Generative AI 库。请运行: pip install google-generativeai>=0.1.0")
					return
			
			# 立即创建并显示加载遮罩
			self.overlay = LoadingOverlay(self)
			self.overlay.show_with_message(f"正在测试与 {provider} 的连接...")
			
			# 立即处理所有待处理的事件，确保遮罩显示
			QApplication.processEvents()
			
			# 使用 QTimer 延迟执行后续操作，让 UI 有时间更新
			QTimer.singleShot(50, lambda: self._prepare_test_connection(provider))
			
		except Exception as e:
			logger.error(f"测试连接失败: {str(e)}", exc_info=True)
			if hasattr(self, 'overlay'):
				try:
					self._safe_hide_overlay('overlay')
				except Exception as hide_error:
					logger.error(f"隐藏加载遮罩失败: {str(hide_error)}", exc_info=True)
			QMessageBox.critical(self, "错误", f"测试连接失败: {str(e)}")

	def _prepare_test_connection(self, provider):
		"""准备测试连接的参数并启动工作线程"""
		try:
			# 再次处理事件，确保UI响应
			QApplication.processEvents()
			
			# 准备 API 参数
			api_params = {}
			if provider == "OpenAI":
				api_params = {
					'api_key': self.openai_api_key.text(),
					'model': self.openai_model.currentText()
				}
			elif provider == "Anthropic":
				api_params = {
					'api_key': self.anthropic_api_key.text(),
					'model': self.anthropic_model.currentText()
				}
			elif provider == "Google":
				api_params = {
					'api_key': self.google_api_key.text(),
					'model': self.google_model.currentText()
				}
			elif provider == "自定义 Web API":
				api_params = {
					'api_url': self.web_api_url.text(),
					'api_key': self.web_api_key.text(),
					'model': self.web_api_model.text()
				}
			
			# 再次处理事件，确保UI响应
			QApplication.processEvents()
			
			# 创建工作线程
			self.worker = ApiWorker('test_connection', provider, api_params)
			self.worker.finished.connect(self.on_test_connection_finished)
			self.worker.error.connect(self.on_test_connection_error)
			
			# 启动工作线程前再次处理事件
			QApplication.processEvents()
			
			# 启动工作线程
			self.worker.start()
			
			# 启动后立即处理事件
			QApplication.processEvents()
			
		except Exception as e:
			logger.error(f"准备测试连接失败: {str(e)}", exc_info=True)
			if hasattr(self, 'overlay'):
				try:
					self._safe_hide_overlay('overlay')
				except Exception as hide_error:
					logger.error(f"隐藏加载遮罩失败: {str(hide_error)}", exc_info=True)
			QMessageBox.critical(self, "错误", f"测试连接失败: {str(e)}")

	def on_test_connection_finished(self, result):
		"""测试连接完成的回调"""
		logger.debug("测试连接完成，准备隐藏加载遮罩")
		try:
			if hasattr(self, 'overlay') and self.overlay:
				QTimer.singleShot(100, lambda: self._safe_hide_overlay('overlay'))
			else:
				logger.warning("找不到加载遮罩对象")
		except Exception as e:
			logger.error(f"隐藏加载遮罩失败: {str(e)}", exc_info=True)
		
		provider = result.get('provider')
		
		if provider == "自定义 Web API":
			QMessageBox.information(
				self, 
				"测试成功", 
				f"成功连接到 Web API!\n\n"
				f"URL: {result.get('url')}\n"
				f"响应时间: {result.get('response_time'):.2f} 秒\n\n"
				f"提取的响应内容: {result.get('result')}\n\n"
				f"原始 JSON 响应:\n{result.get('raw_json', '')[:500]}..."  # 只显示前500个字符
			)
		else:
			QMessageBox.information(
				self, 
				"测试成功", 
				f"成功连接到 {provider}!\n\n"
				f"模型: {result.get('model')}\n"
				f"响应时间: {result.get('response_time'):.2f} 秒\n\n"
				f"响应内容: {result.get('result')}"
			)

	def on_test_connection_error(self, error_message):
		"""测试连接错误的回调"""
		logger.error(f"测试连接失败: {error_message}")
		try:
			if hasattr(self, 'overlay') and self.overlay:
				QTimer.singleShot(100, lambda: self._safe_hide_overlay('overlay'))
			else:
				logger.warning("找不到加载遮罩对象")
		except Exception as e:
			logger.error(f"隐藏加载遮罩失败: {str(e)}", exc_info=True)
		QMessageBox.critical(self, "连接失败", error_message)

# 创建自定义的文件项组件
class FileItemWidget(QWidget):
	"""文件项组件，显示文件名和复选框"""
	def __init__(self, file_path, status="modified", on_checkbox_changed=None):
		super().__init__()
		self.file_path = file_path
		self.status = status
		self.on_checkbox_changed = on_checkbox_changed
		self._is_updating = False  # 添加标志，防止重复触发
		
		layout = QHBoxLayout(self)
		layout.setContentsMargins(5, 0, 5, 0)
		
		self.checkbox = QCheckBox()
		self.checkbox.setChecked(True)  # 默认选中
		self.checkbox.stateChanged.connect(self._on_state_changed)
		
		status_label = QLabel()
		if status == "staged":
			status_label.setText("已暂存")
			status_label.setStyleSheet("color: green;")
		elif status == "modified":
			status_label.setText("已修改")
			status_label.setStyleSheet("color: blue;")
		elif status == "deleted":
			status_label.setText("已删除")
			status_label.setStyleSheet("color: red;")
		elif status == "untracked":
			status_label.setText("未跟踪")
			status_label.setStyleSheet("color: gray;")
		
		file_label = QLabel(file_path)
		file_label.setStyleSheet("text-align: left;")
		
		layout.addWidget(self.checkbox)
		layout.addWidget(status_label)
		layout.addWidget(file_label)
		layout.addStretch()
		
		self.setLayout(layout)
	
	def _on_state_changed(self, state):
		"""复选框状态改变时触发"""
		# 防止重复触发
		if self._is_updating:
			return
			
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

		# 添加心跳计时器，防止应用程序显示为"未响应"
		self.heartbeat_timer = QTimer(self)
		self.heartbeat_timer.timeout.connect(self._heartbeat)
		self.heartbeat_timer.start(100)  # 每100毫秒触发一次，提高频率

		# 添加差异缓存相关属性
		self.diff_cache_dir = os.path.join(tempfile.gettempdir(), "aicommit_diff_cache")
		if not os.path.exists(self.diff_cache_dir):
			os.makedirs(self.diff_cache_dir)
		self.diff_cache = {}  # 文件路径 -> 缓存文件路径
		self.diff_cache_timestamp = 0  # 上次缓存更新时间
		self.diff_cache_lock = threading.Lock()  # 缓存锁，防止并发问题
		
		# 添加应用焦点事件监听
		self.installEventFilter(self)

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
		self.changes_list.itemSelectionChanged.connect(self.on_changes_list_selection_changed)

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

		# 在成功打开仓库后，立即开始刷新差异缓存
		if self.current_repo:
			self.refresh_diff_cache_async()

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
			
			# 立即创建并显示加载遮罩
			self.loading_overlay = LoadingOverlay(self)
			self.loading_overlay.show_with_message(f"正在使用 {self.current_ai_provider} 生成提交信息...")
			
			# 立即处理所有待处理的事件，确保遮罩显示
			QApplication.processEvents()
			
			# 使用 QTimer 延迟执行后续操作，让 UI 有时间更新
			QTimer.singleShot(50, lambda: self._prepare_generate_commit(selected_files))
			
		except Exception as e:
			logger.error(f"生成提交信息失败: {str(e)}", exc_info=True)
			if hasattr(self, 'loading_overlay'):
				try:
					self._safe_hide_overlay('loading_overlay')
				except Exception as hide_error:
					logger.error(f"隐藏加载遮罩失败: {str(hide_error)}", exc_info=True)
			QMessageBox.critical(self, "错误", f"生成提交信息失败: {str(e)}")
			self.statusBar.showMessage("生成提交信息失败")

	def _prepare_generate_commit(self, selected_files):
		"""准备生成提交信息的参数并启动工作线程"""
		try:
			# 再次处理事件，确保UI响应
			QApplication.processEvents()
			
			# 获取文件差异
			diffs = []
			for file_path in selected_files:
				# 从缓存获取差异，而不是直接从仓库获取
				diff = self.get_cached_diff(file_path)
				
				# 每处理一个文件后处理事件，保持UI响应
				QApplication.processEvents()
				
				diffs.append(f"File: {file_path}\n{diff}\n")
				logger.debug(f"文件差异 ({file_path}):\n{diff}")
			
			# 合并所有差异
			all_diffs = "\n".join(diffs)
			logger.debug(f"合并后的差异总长度: {len(all_diffs)} 字符")
			
			# 获取系统提示词
			config_manager = Config()
			system_prompt = config_manager.get("system_prompt", "")
			
			# 准备 API 参数
			api_params = {
				'provider': self.current_ai_provider,
				'system_prompt': system_prompt,
				'original_system_prompt': config_manager.get("system_prompt", ""),
				'diffs': all_diffs
			}
			
			# 添加提供商特定的参数
			if self.current_ai_provider == "OpenAI":
				api_params.update({
					'api_key': config_manager.get("openai_api_key", ""),
					'model': config_manager.get("openai_model", "gpt-3.5-turbo")
				})
			elif self.current_ai_provider == "Anthropic":
				api_params.update({
					'api_key': config_manager.get("anthropic_api_key", ""),
					'model': config_manager.get("anthropic_model", "claude-3-haiku")
				})
			elif self.current_ai_provider == "Google":
				api_params.update({
					'api_key': config_manager.get("google_api_key", ""),
					'model': config_manager.get("google_model", "gemini-pro")
				})
			elif self.current_ai_provider == "自定义 Web API":
				api_params.update({
					'api_url': config_manager.get("web_api_url", ""),
					'api_key': config_manager.get("web_api_key", ""),
					'model': config_manager.get("web_api_model", "")
				})
			
			# 再次处理事件，确保UI响应
			QApplication.processEvents()
			
			# 创建工作线程
			self.commit_worker = ApiWorker('generate_commit', None, api_params)
			self.commit_worker.finished.connect(self.on_generate_commit_finished)
			self.commit_worker.error.connect(self.on_generate_commit_error)
			
			# 启动工作线程前再次处理事件
			QApplication.processEvents()
			
			# 启动工作线程
			self.commit_worker.start()
			
			# 启动后立即处理事件
			QApplication.processEvents()
			
		except Exception as e:
			logger.error(f"准备生成提交信息失败: {str(e)}", exc_info=True)
			if hasattr(self, 'loading_overlay'):
				try:
					self._safe_hide_overlay('loading_overlay')
				except Exception as hide_error:
					logger.error(f"隐藏加载遮罩失败: {str(hide_error)}", exc_info=True)
			QMessageBox.critical(self, "错误", f"生成提交信息失败: {str(e)}")
			self.statusBar.showMessage("生成提交信息失败")

	def on_generate_commit_finished(self, result):
		"""生成提交信息完成的回调"""
		try:
			# 获取提交信息
			commit_message = result.get('commit_message', '')
			logger.info(f"AI 生成的提交信息:\n{commit_message}")
			
			# 分割提交信息为摘要和描述
			lines = commit_message.strip().split("\n")
			summary = lines[0]
			description = "\n".join(lines[1:]).strip()

			# 更新 UI
			self.summary_edit.setText(summary)
			self.description_edit.setText(description)
			
			# 使用 QTimer 延迟隐藏加载遮罩，让 UI 有时间更新
			logger.debug("提交信息生成完成，准备隐藏加载遮罩")
			try:
				if hasattr(self, 'loading_overlay') and self.loading_overlay:
					QTimer.singleShot(100, lambda: self._safe_hide_overlay('loading_overlay'))
				else:
					logger.warning("找不到加载遮罩对象")
			except Exception as e:
				logger.error(f"隐藏加载遮罩失败: {str(e)}", exc_info=True)
			
			self.statusBar.showMessage("提交信息生成完成")
			logger.info("提交信息生成完成")
		except Exception as e:
			logger.error(f"处理生成的提交信息失败: {str(e)}", exc_info=True)
			try:
				if hasattr(self, 'loading_overlay') and self.loading_overlay:
					QTimer.singleShot(100, lambda: self._safe_hide_overlay('loading_overlay'))
			except Exception as hide_error:
				logger.error(f"错误处理中隐藏加载遮罩失败: {str(hide_error)}", exc_info=True)
			QMessageBox.critical(self, "错误", f"处理生成的提交信息失败: {str(e)}")
			self.statusBar.showMessage("生成提交信息失败")

	def on_generate_commit_error(self, error_message):
		"""生成提交信息错误的回调"""
		logger.error(f"生成提交信息失败: {error_message}")
		# 使用 QTimer 延迟隐藏加载遮罩，让 UI 有时间更新
		try:
			if hasattr(self, 'loading_overlay') and self.loading_overlay:
				QTimer.singleShot(100, lambda: self._safe_hide_overlay('loading_overlay'))
			else:
				logger.warning("找不到加载遮罩对象")
		except Exception as e:
			logger.error(f"隐藏加载遮罩失败: {str(e)}", exc_info=True)
		QMessageBox.critical(self, "错误", f"生成提交信息失败: {error_message}")
		self.statusBar.showMessage("生成提交信息失败")

	def _safe_hide_overlay(self, overlay_name):
		"""安全地隐藏遮罩，处理可能的异常"""
		try:
			overlay = getattr(self, overlay_name, None)
			if overlay:
				logger.debug(f"安全隐藏 {overlay_name}")
				overlay.hide()
			else:
				logger.warning(f"找不到遮罩对象: {overlay_name}")
		except Exception as e:
			logger.error(f"安全隐藏遮罩 {overlay_name} 失败: {str(e)}", exc_info=True)
			# 尝试使用更直接的方式隐藏
			try:
				overlay = getattr(self, overlay_name, None)
				if overlay:
					super(type(overlay), overlay).hide()
			except:
				pass

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
		"""切换全选/取消全选"""
		# 添加性能日志
		start_time = time.time()
		logger.debug(f"开始切换全选状态: {state}")
		
		# 设置标志，防止重复触发
		for i in range(self.changes_list.count()):
			item = self.changes_list.item(i)
			widget = self.changes_list.itemWidget(item)
			if widget:
				widget._is_updating = True
				widget.checkbox.setChecked(state == Qt.Checked)
				widget._is_updating = False
		
		end_time = time.time()
		logger.debug(f"切换全选状态完成，耗时: {end_time - start_time:.3f}秒")

	def update_select_all_state(self):
		"""更新全选复选框状态"""
		# 添加性能日志
		start_time = time.time()
		logger.debug("开始更新全选复选框状态")
		
		# 检查是否需要更新
		# 如果没有文件项，则不需要更新
		if self.changes_list.count() == 0:
			self.select_all_checkbox.setChecked(False)
			logger.debug("没有文件项，设置全选复选框为未选中")
			return
			
		# 统计选中的文件数量
		checked_count = 0
		total_count = self.changes_list.count()
		
		for i in range(total_count):
			item = self.changes_list.item(i)
			widget = self.changes_list.itemWidget(item)
			if widget and widget.checkbox.isChecked():
				checked_count += 1
		
		# 根据选中数量设置全选复选框状态
		if checked_count == 0:
			self.select_all_checkbox.setChecked(False)
		elif checked_count == total_count:
			self.select_all_checkbox.setChecked(True)
		else:
			self.select_all_checkbox.setCheckState(Qt.PartiallyChecked)
		
		end_time = time.time()
		logger.debug(f"更新全选复选框状态完成，选中: {checked_count}/{total_count}, 耗时: {end_time - start_time:.3f}秒")

	def on_changes_list_selection_changed(self):
		"""当变更列表选择改变时更新差异查看器，仅显示差异，不刷新文件列表"""
		# 添加性能日志
		start_time = time.time()
		logger.debug("开始处理变更列表选择改变事件")
		
		selected_items = self.changes_list.selectedItems()
		if not selected_items:
			self.diff_viewer.clear()
			logger.debug("没有选中项，清空差异查看器")
			return

		try:
			item = selected_items[0]
			widget = self.changes_list.itemWidget(item)
			if widget:
				file_path = widget.file_path
				
				# 检查是否需要重新获取差异
				# 如果当前显示的就是这个文件，则不需要重新获取
				if hasattr(self, '_current_diff_file') and self._current_diff_file == file_path:
					logger.debug(f"文件 {file_path} 已经在显示中，跳过重新获取差异")
					return
					
				# 记录当前显示的文件
				self._current_diff_file = file_path
				
				# 从缓存获取差异，而不是直接从仓库获取
				diff_text = self.get_cached_diff(file_path)

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

				end_time = time.time()
				logger.debug(f"显示文件差异: {file_path}, 耗时: {end_time - start_time:.3f}秒")
		except Exception as e:
			self.diff_viewer.setPlainText(f"无法显示差异: {str(e)}")
			logger.error(f"显示差异失败: {str(e)}", exc_info=True)

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
		"""刷新 UI 显示，包括文件列表和分支信息"""
		# 刷新 UI 显示
		if self.current_repo:
			start_time = time.time()
			logger.debug("开始刷新 UI")

			# 刷新分支列表
			self.refresh_branches()

			# 更新变更列表
			self.changes_list.clear()

			try:
				# 获取仓库状态，这是一个耗时操作
				status = self.current_repo.get_status()
				
				# 缓存当前状态，用于后续比较
				self._last_status = status
				
				# 合并所有文件列表，不再区分暂存状态
				all_files = []

				# 添加已暂存的文件
				for file_path in status['staged']:
					if file_path not in [f[0] for f in all_files]:
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

				end_time = time.time()
				logger.debug(f"UI 刷新完成，耗时: {end_time - start_time:.3f}秒")
			except Exception as e:
				QMessageBox.critical(self, "错误", f"刷新 UI 失败: {str(e)}")
				logger.error(f"刷新 UI 失败: {str(e)}", exc_info=True)

	def _heartbeat(self):
		"""心跳函数，定期处理事件，防止应用程序显示为"未响应" """
		try:
			# 只处理待处理的事件，不阻塞
			QApplication.processEvents()
			
			# 如果有加载遮罩显示，更新其位置
			if hasattr(self, 'overlay') and self.overlay and self.overlay.isVisible():
				self.overlay.resize(self.size())
			
			if hasattr(self, 'loading_overlay') and self.loading_overlay and self.loading_overlay.isVisible():
				self.loading_overlay.resize(self.size())
		except Exception as e:
			# 心跳函数不应该抛出异常
			logger.error(f"心跳函数出错: {str(e)}", exc_info=True)

	def eventFilter(self, obj, event):
		"""事件过滤器，用于捕获应用获取焦点事件"""
		if event.type() == QEvent.WindowActivate:
			# 当窗口获得焦点时，检查是否需要刷新差异缓存
			QTimer.singleShot(100, self.check_refresh_diff_cache)
		return super().eventFilter(obj, event)
	
	def check_refresh_diff_cache(self):
		"""检查是否需要刷新差异缓存"""
		if not self.current_repo:
			return
			
		# 如果距离上次更新超过30秒，则刷新缓存
		current_time = time.time()
		if current_time - self.diff_cache_timestamp > 30:
			self.refresh_diff_cache_async()
	
	def refresh_diff_cache_async(self):
		"""异步刷新差异缓存"""
		if not self.current_repo:
			return
			
		# 创建后台线程刷新缓存
		threading.Thread(
			target=self.refresh_diff_cache,
			daemon=True
		).start()
	
	def refresh_diff_cache(self):
		"""刷新所有文件的差异缓存"""
		if not self.current_repo:
			return
			
		try:
			logger.debug("开始刷新差异缓存")
			start_time = time.time()
			
			# 获取仓库状态
			status = self.current_repo.get_status()
			
			# 合并所有文件列表
			all_files = []
			for file_path in status['staged']:
				if file_path not in all_files:
					all_files.append(file_path)
			
			for file_path in status['modified']:
				if file_path not in all_files:
					all_files.append(file_path)
			
			for file_path in status['deleted']:
				if file_path not in all_files:
					all_files.append(file_path)
			
			for file_path in status['untracked']:
				if file_path not in all_files:
					all_files.append(file_path)
			
			# 清理旧缓存
			with self.diff_cache_lock:
				for cached_file in list(self.diff_cache.keys()):
					if cached_file not in all_files:
						cache_path = self.diff_cache[cached_file]
						try:
							if os.path.exists(cache_path):
								os.remove(cache_path)
						except:
							pass
						del self.diff_cache[cached_file]
			
			# 并行获取差异
			threads = []
			for file_path in all_files:
				thread = threading.Thread(
					target=self.cache_file_diff,
					args=(file_path,),
					daemon=True
				)
				threads.append(thread)
				thread.start()
			
			# 等待所有线程完成
			for thread in threads:
				thread.join()
			
			# 更新时间戳
			self.diff_cache_timestamp = time.time()
			
			end_time = time.time()
			logger.debug(f"差异缓存刷新完成，共 {len(all_files)} 个文件，耗时: {end_time - start_time:.3f}秒")
		except Exception as e:
			logger.error(f"刷新差异缓存失败: {str(e)}", exc_info=True)
	
	def cache_file_diff(self, file_path):
		"""缓存单个文件的差异"""
		try:
			# 获取文件差异
			diff_text = self.current_repo.get_file_diff(file_path)
			
			# 生成缓存文件路径
			cache_file = os.path.join(
				self.diff_cache_dir, 
				f"{hash(self.current_repo.path)}_{hash(file_path)}.diff"
			)
			
			# 写入缓存
			with open(cache_file, 'w', encoding='utf-8') as f:
				f.write(diff_text)
			
			# 更新缓存映射
			with self.diff_cache_lock:
				self.diff_cache[file_path] = cache_file
				
			logger.debug(f"已缓存文件差异: {file_path}")
		except Exception as e:
			logger.error(f"缓存文件差异失败 ({file_path}): {str(e)}")
	
	def get_cached_diff(self, file_path):
		"""获取缓存的文件差异"""
		with self.diff_cache_lock:
			if file_path in self.diff_cache:
				cache_path = self.diff_cache[file_path]
				try:
					if os.path.exists(cache_path):
						with open(cache_path, 'r', encoding='utf-8') as f:
							return f.read()
				except Exception as e:
					logger.error(f"读取缓存差异失败 ({file_path}): {str(e)}")
		
		# 如果缓存不存在或读取失败，直接获取
		return self.current_repo.get_file_diff(file_path)

# 在文件末尾添加
if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    
    # 设置日志
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 创建应用
    app = QApplication(sys.argv)
    
    # 创建主窗口
    window = MainWindow()
    window.show()
    
    # 运行应用
    sys.exit(app.exec_())