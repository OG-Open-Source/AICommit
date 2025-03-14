import os
import json

class Config:
	def __init__(self):
		self.config_dir = os.path.expanduser("~/.aicommit")
		self.config_file = os.path.join(self.config_dir, "config.json")
		self.default_config = {
			"recent_repositories": [],
			"github_token": "",
			"github_username": "",
			"user_name": "",
			"user_email": "",
			"ai_provider": "OpenAI",
			"system_prompt": "你是一个 Git 提交信息生成助手。请根据提供的代码差异生成简洁、清晰的提交信息。遵循 Conventional Commits 规范，使用类型前缀（如 feat:、fix:、docs:、style:、refactor:、perf:、test:、build:、ci:、chore:）。",
			"openai_api_key": "",
			"openai_model": "gpt-3.5-turbo",
			"anthropic_api_key": "",
			"anthropic_model": "claude-3-haiku",
			"google_api_key": "",
			"google_model": "gemini-pro",
			"web_api_url": "",
			"web_api_key": "",
			"web_api_model": ""
		}

		self.load_config()

	def load_config(self):
		"""加载配置"""
		if not os.path.exists(self.config_dir):
			os.makedirs(self.config_dir)

		if os.path.exists(self.config_file):
			try:
				with open(self.config_file, 'r') as f:
					self.config = json.load(f)
			except:
				self.config = self.default_config
		else:
			self.config = self.default_config
			self.save_config()

	def save_config(self):
		"""保存配置"""
		with open(self.config_file, 'w') as f:
			json.dump(self.config, f, indent=4)

	def get(self, key, default=None):
		"""获取配置项"""
		return self.config.get(key, default)

	def set(self, key, value):
		"""设置配置项"""
		self.config[key] = value
		self.save_config()

	def add_recent_repository(self, path):
		"""添加最近使用的仓库"""
		recent = self.config.get("recent_repositories", [])
		if path in recent:
			recent.remove(path)
		recent.insert(0, path)
		# 只保留最近的 10 个
		self.config["recent_repositories"] = recent[:10]
		self.save_config()