import re
from collections import defaultdict

class CommitHelper:
	def __init__(self, repository):
		"""初始化提交輔助對象"""
		self.repository = repository

	def analyze_changes(self):
		"""分析變更並生成提交日誌建議"""
		staged_files = self.repository.get_staged_files()

		# 按文件類型分類
		file_types = defaultdict(list)
		binary_files = []

		for file in staged_files:
			# 檢查是否為二進制文件
			diff = self.repository.get_file_diff(file)
			if diff == "This is a binary file.":
				binary_files.append(file)
				continue

			ext = file.split('.')[-1] if '.' in file else 'other'
			file_types[ext].append(file)

		# 生成提交日誌建議 (使用 Keep a Changelog 風格)
		suggestions = []

		# 添加二進制文件的建議
		if binary_files:
			suggestions.append(f"Added: 更新二進制文件 ({len(binary_files)} 個檔案)")

		# 其他文件類型的建議
		if 'py' in file_types:
			suggestions.append(f"Added: 更新 Python 檔案 ({len(file_types['py'])} 個檔案)")

		if 'js' in file_types:
			suggestions.append(f"Added: 更新 JavaScript 檔案 ({len(file_types['js'])} 個檔案)")

		if 'html' in file_types:
			suggestions.append(f"Added: 更新 HTML 檔案 ({len(file_types['html'])} 個檔案)")

		if 'css' in file_types:
			suggestions.append(f"Changed: 更新 CSS 樣式 ({len(file_types['css'])} 個檔案)")

		if 'md' in file_types:
			suggestions.append(f"Added: 更新文檔 ({len(file_types['md'])} 個檔案)")

		if 'json' in file_types:
			suggestions.append(f"Changed: 更新配置檔案 ({len(file_types['json'])} 個檔案)")

		if 'txt' in file_types:
			suggestions.append(f"Added: 更新文本檔案 ({len(file_types['txt'])} 個檔案)")

		# 如果沒有特定類型的建議，添加一個通用建議
		if not suggestions and staged_files:
			suggestions.append(f"Changed: 更新專案檔案 ({len(staged_files)} 個檔案)")

		return suggestions

	def format_commit_message(self, type, scope, summary, description=None, footer=None):
		"""格式化提交信息，只使用純摘要"""
		# 檢查摘要是否已經包含類型前綴
		if summary.startswith(type) or any(summary.startswith(t + ":") for t in ["Added", "Changed", "Deprecated", "Removed", "Fixed", "Security"]):
			# 如果摘要已經包含類型前綴，提取純摘要部分
			parts = summary.split(":", 1)
			if len(parts) > 1:
				message = parts[1].strip()
			else:
				message = summary
		else:
			# 如果摘要不包含前綴，直接使用
			message = summary

		# 添加描述（如果有）
		if description and description.strip():
			message += f"\n\n{description}"

		# 添加頁腳（如果有）
		if footer and footer.strip():
			message += f"\n\n{footer}"

		return message