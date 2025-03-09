import git
import mimetypes

class GitRepository:
	def __init__(self, repo_path=None):
		"""初始化Git倉庫對象"""
		self.repo = None
		if repo_path:
			self.open(repo_path)

	def open(self, path):
		"""打開指定路徑的Git倉庫"""
		try:
			self.repo = git.Repo(path)
			return True
		except git.InvalidGitRepositoryError:
			return False

	def get_staged_files(self):
		"""獲取已暫存的文件列表"""
		if not self.repo:
			return []

		try:
			# 獲取已暫存的文件
			staged_files = []
			# 獲取已暫存但未提交的文件
			diff_index = self.repo.index.diff("HEAD")
			for diff_item in diff_index:
				staged_files.append(diff_item.a_path)

			# 獲取新添加但尚未提交的文件
			for untracked in self.repo.git.diff("--cached", "--name-only").splitlines():
				if untracked and untracked not in staged_files:
					staged_files.append(untracked)

			return staged_files
		except Exception as e:
			print(f"獲取已暫存文件錯誤: {str(e)}")
			return []

	def get_unstaged_files(self):
		"""獲取未暫存的文件列表"""
		if not self.repo:
			return []

		try:
			# 獲取未暫存的修改文件
			unstaged_files = []
			for item in self.repo.index.diff(None):
				unstaged_files.append(item.a_path)

			# 獲取未跟踪的文件
			for item in self.repo.untracked_files:
				unstaged_files.append(item)

			return unstaged_files
		except Exception as e:
			print(f"獲取未暫存文件錯誤: {str(e)}")
			return []

	def get_file_diff(self, file_path):
		"""獲取指定文件的差異"""
		if not self.repo:
			return ""

		try:
			# 使用 mimetypes 檢測文件類型
			mime_type, encoding = mimetypes.guess_type(file_path)
			is_text = mime_type and mime_type.startswith('text')

			# 對於 Python 文件，強制設為文本文件
			if file_path.endswith('.py') or file_path.endswith('.md') or file_path.endswith('.txt'):
				is_text = True

			# 如果不是文本文件，直接返回提示
			if not is_text and mime_type:
				return "This is a binary file."

			# 獲取文件狀態
			file_status = self.get_file_status(file_path)

			# 獲取差異內容
			try:
				# 根據文件狀態選擇適當的命令
				if file_status == "Deleted":
					# 對於已刪除的文件，使用特殊命令獲取差異
					cmd = ["git", "diff", "--cached", "--", file_path]
				else:
					# 對於修改或新增的文件
					cmd = ["git", "diff", "--cached", file_path]

				diff = self.repo.git.execute(cmd, with_exceptions=False)

				# 檢查是否為二進制文件
				if "Binary files" in diff:
					return "This is a binary file."

				# 檢查差異是否為空（可能表示文件被刪除）
				if not diff.strip() and file_status == "Deleted":
					# 創建一個簡單的差異表示文件被刪除
					diff = f"@@ -1,1 +0,0 @@\n-File has been deleted"

				# 添加文件狀態到差異頂部
				cleaned_diff = [f"# @Status: {file_status}", ""]

				# 找到第一個 @@ 行，只保留它之後的內容
				found_diff_start = False
				for line in diff.splitlines():
					if found_diff_start:
						# 已經找到 @@ 行，保留所有後續內容
						cleaned_diff.append(line)
					elif line.startswith("@@"):
						# 找到 @@ 行，開始保留內容
						found_diff_start = True
						cleaned_diff.append(line)

				return "\n".join(cleaned_diff)
			except Exception as e:
				return f"無法獲取差異: {str(e)}"
		except Exception as e:
			return f"無法獲取差異: {str(e)}"

	def get_file_status(self, file_path):
		"""獲取文件的狀態（新增、修改或刪除）"""
		try:
			# 獲取文件狀態
			status_output = self.repo.git.status("--porcelain", file_path)

			# 解析狀態輸出
			if status_output:
				status_code = status_output[:2].strip()

				# 刪除的文件
				if status_code == "D" or status_code == "AD":
					return "Deleted"

				# 新增的文件
				elif status_code == "A" or status_code == "??" or status_code == "AM":
					return "New"

				# 修改的文件
				elif status_code == "M" or status_code == "MM" or status_code == "RM":
					return "Modified"

				# 重命名的文件
				elif status_code.startswith("R"):
					return "Changed"

			# 如果無法通過 status 確定，嘗試其他方法

			# 檢查是否為刪除的文件
			if self.is_file_deleted(file_path):
				return "Deleted"

			# 檢查是否為新文件
			try:
				# 嘗試獲取文件的 HEAD 版本，如果失敗則可能是新文件
				self.repo.git.show(f"HEAD:{file_path}")
				# 如果能獲取到 HEAD 版本，則是修改的文件
				return "Modified"
			except git.exc.GitCommandError:
				# 如果無法獲取 HEAD 版本，則是新文件
				return "New"

		except Exception as e:
			print(f"獲取文件狀態時出錯: {str(e)}")
			# 如果出錯，默認為修改
			return "Modified"

	def is_file_deleted(self, file_path):
		"""檢查文件是否已被刪除"""
		try:
			# 方法 1: 使用 git status 檢查
			status_output = self.repo.git.status("--porcelain", file_path)
			if status_output and status_output.strip().startswith("D"):
				return True

			# 方法 2: 使用 GitPython 的 diff_index
			diff_index = self.repo.index.diff(self.repo.head.commit)
			for diff_item in diff_index:
				if diff_item.a_path == file_path and diff_item.change_type == 'D':
					return True

			# 方法 3: 檢查文件是否存在於工作目錄但不在索引中
			try:
				# 檢查文件是否在索引中
				self.repo.git.ls_files("--", file_path)
				# 檢查文件是否不在工作目錄中
				import os
				full_path = os.path.join(self.repo.working_dir, file_path)
				if not os.path.exists(full_path):
					return True
			except:
				pass

			return False
		except Exception as e:
			print(f"檢查文件是否已刪除時出錯: {str(e)}")
			# 如果出錯，假設文件未被刪除
			return False

	def get_branches(self):
		"""獲取倉庫的分支列表"""
		if not self.repo:
			return {"local": [], "remote": []}

		try:
			# 獲取本地分支
			local_branches = [branch.name for branch in self.repo.heads]

			# 獲取遠端分支
			remote_branches = []
			for ref in self.repo.remote().refs:
				# 去除 'origin/' 前綴
				name = ref.name.split('/', 1)[1] if '/' in ref.name else ref.name
				remote_branches.append(name)

			# 獲取當前分支
			current_branch = self.repo.active_branch.name

			return {
				"local": local_branches,
				"remote": remote_branches,
				"current": current_branch
			}
		except Exception as e:
			return {"error": f"無法獲取分支: {str(e)}"}

	def commit(self, message):
		"""提交變更"""
		if not self.repo:
			return False

		try:
			# 檢查是否有已暫存的文件
			staged_files = self.get_staged_files()
			if not staged_files:
				return False

			# 執行提交
			self.repo.git.commit('-m', message)
			return True
		except Exception as e:
			print(f"提交錯誤: {str(e)}")
			return False

	def stage_file(self, file_path):
		"""暫存指定的文件"""
		if not self.repo:
			return False

		try:
			self.repo.git.add(file_path)
			return True
		except Exception as e:
			print(f"暫存文件錯誤: {str(e)}")
			return False

	def stage_all_files(self):
		"""暫存所有未暫存的文件"""
		if not self.repo:
			return False

		try:
			# 使用 git add -A 暫存所有變更
			self.repo.git.add('-A')
			return True
		except Exception as e:
			print(f"暫存所有文件錯誤: {str(e)}")
			return False