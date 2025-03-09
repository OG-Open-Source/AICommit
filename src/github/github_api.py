import requests
import os
import subprocess
from PyQt5.QtCore import QSettings
class GitHubAPI:
	def __init__(self):
		self.settings = QSettings("OG-Open-Source", "CommitLogAssistant")
		self.base_url = "https://api.github.com"
		self.headers = {
			"Accept": "application/vnd.github.v3+json"
		}
		token = self.settings.value("github/token", "")
		if token:
			self.headers["Authorization"] = f"token {token}"
	def get_user_repos(self):
		if "Authorization" not in self.headers:
			return {"error": "未設置 GitHub 令牌"}
		try:
			response = requests.get(f"{self.base_url}/user/repos", headers=self.headers)
			if response.status_code == 200:
				repos = response.json()
				repos.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
				return repos
			else:
				return {"error": f"API 錯誤: {response.status_code} - {response.text}"}
		except Exception as e:
			return {"error": f"請求錯誤: {str(e)}"}
	def clone_repo(self, repo_url, local_path):
		try:
			result = subprocess.run(
				["git", "clone", repo_url, local_path],
				capture_output=True,
				text=True
			)
			if result.returncode == 0:
				return {"success": True, "path": local_path}
			else:
				return {"error": f"克隆失敗: {result.stderr}"}
		except Exception as e:
			return {"error": f"克隆錯誤: {str(e)}"}