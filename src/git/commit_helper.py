import re
from collections import defaultdict
class CommitHelper:
	def __init__(self, repository):
		self.repository = repository
	def analyze_changes(self):
		staged_files = self.repository.get_staged_files()
		file_types = defaultdict(list)
		binary_files = []
		for file in staged_files:
			diff = self.repository.get_file_diff(file)
			if diff == "This is a binary file.":
				binary_files.append(file)
				continue
			ext = file.split('.')[-1] if '.' in file else 'other'
			file_types[ext].append(file)
		suggestions = []
		if binary_files:
			suggestions.append(f"Added: 更新二進制文件 ({len(binary_files)} 個檔案)")
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
		if not suggestions and staged_files:
			suggestions.append(f"Changed: 更新專案檔案 ({len(staged_files)} 個檔案)")
		return suggestions
	def format_commit_message(self, type, scope, summary, description=None, footer=None):
		if summary.startswith(type) or any(summary.startswith(t + ":") for t in ["Added", "Changed", "Deprecated", "Removed", "Fixed", "Security"]):
			parts = summary.split(":", 1)
			if len(parts) > 1:
				message = parts[1].strip()
			else:
				message = summary
		else:
			message = summary
		if description and description.strip():
			message += f"\n\n{description}"
		if footer and footer.strip():
			message += f"\n\n{footer}"
		return message