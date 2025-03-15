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
			"system_prompt": self.get_default_system_prompt(),
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

	def get_default_system_prompt(self):
		"""获取默认的系统提示词"""
		return """You are a helpful assistant that generates concise and informative git commit messages based on code diffs.

INSTRUCTIONS:
1. Analyze the provided code diffs carefully.
2. Generate a clear and descriptive commit message that explains WHAT changes were made and WHY.
3. Format your response in two distinct parts:
   - SUMMARY: A single line (50-72 characters) that summarizes the change
   - DESCRIPTION: A more detailed explanation of the changes (if needed)

4. Use present tense (e.g., "Add feature" not "Added feature").
5. Focus on the purpose and impact of the changes, not just listing what files were modified.
6. Be specific about what was changed and why it matters.
7. If the diff includes multiple unrelated changes, organize them with bullet points in the description.

RESPONSE FORMAT:
SUMMARY: [concise summary of changes]

DESCRIPTION:
[detailed explanation if needed]
[can be multiple paragraphs]

Example:
SUMMARY: Add user authentication with JWT tokens

DESCRIPTION:
Implement user login/signup functionality using JWT for authentication.
- Add login and signup API endpoints
- Create JWT token generation and validation
- Add middleware for protected routes
- Update user model with password hashing

This change provides secure authentication for the application and lays the groundwork for user-specific features.
"""