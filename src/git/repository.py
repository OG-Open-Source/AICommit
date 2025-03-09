import git
import mimetypes
class GitRepository:
	def __init__(self, repo_path=None):
		self.repo = None
		if repo_path:
			self.open(repo_path)
	def open(self, path):
		try:
			self.repo = git.Repo(path)
			return True
		except git.InvalidGitRepositoryError:
			return False
	def get_staged_files(self):
		if not self.repo:
			return []
		try:
			staged_files = []
			diff_index = self.repo.index.diff("HEAD")
			for diff_item in diff_index:
				staged_files.append(diff_item.a_path)
			for untracked in self.repo.git.diff("--cached", "--name-only").splitlines():
				if untracked and untracked not in staged_files:
					staged_files.append(untracked)
			return staged_files
		except Exception as e:
			print(f"獲取已暫存文件錯誤: {str(e)}")
			return []
	def get_unstaged_files(self):
		if not self.repo:
			return []
		try:
			unstaged_files = []
			for item in self.repo.index.diff(None):
				unstaged_files.append(item.a_path)
			for item in self.repo.untracked_files:
				unstaged_files.append(item)
			return unstaged_files
		except Exception as e:
			print(f"獲取未暫存文件錯誤: {str(e)}")
			return []
	def get_file_diff(self, file_path):
		if not self.repo:
			return ""
		try:
			mime_type, encoding = mimetypes.guess_type(file_path)
			is_text = mime_type and mime_type.startswith('text')
			if file_path.endswith('.py') or file_path.endswith('.md') or file_path.endswith('.txt'):
				is_text = True
			if not is_text and mime_type:
				return "This is a binary file."
			file_status = self.get_file_status(file_path)
			try:
				if file_status == "Deleted":
					cmd = ["git", "diff", "--cached", "--", file_path]
				else:
					cmd = ["git", "diff", "--cached", file_path]
				diff = self.repo.git.execute(cmd, with_exceptions=False)
				if "Binary files" in diff:
					return "This is a binary file."
				if not diff.strip() and file_status == "Deleted":
					diff = f"@@ -1,1 +0,0 @@\n-File has been deleted"
				cleaned_diff = [f"# @Status: {file_status}", ""]
				found_diff_start = False
				for line in diff.splitlines():
					if found_diff_start:
						cleaned_diff.append(line)
					elif line.startswith("@@"):
						found_diff_start = True
						cleaned_diff.append(line)
				return "\n".join(cleaned_diff)
			except Exception as e:
				return f"無法獲取差異: {str(e)}"
		except Exception as e:
			return f"無法獲取差異: {str(e)}"
	def get_file_status(self, file_path):
		try:
			status_output = self.repo.git.status("--porcelain", file_path)
			if status_output:
				status_code = status_output[:2].strip()
				if status_code == "D" or status_code == "AD":
					return "Deleted"
				elif status_code == "A" or status_code == "??" or status_code == "AM":
					return "New"
				elif status_code == "M" or status_code == "MM" or status_code == "RM":
					return "Modified"
				elif status_code.startswith("R"):
					return "Changed"
			if self.is_file_deleted(file_path):
				return "Deleted"
			try:
				self.repo.git.show(f"HEAD:{file_path}")
				return "Modified"
			except git.exc.GitCommandError:
				return "New"
		except Exception as e:
			print(f"獲取文件狀態時出錯: {str(e)}")
			return "Modified"
	def is_file_deleted(self, file_path):
		try:
			status_output = self.repo.git.status("--porcelain", file_path)
			if status_output and status_output.strip().startswith("D"):
				return True
			diff_index = self.repo.index.diff(self.repo.head.commit)
			for diff_item in diff_index:
				if diff_item.a_path == file_path and diff_item.change_type == 'D':
					return True
			try:
				self.repo.git.ls_files("--", file_path)
				import os
				full_path = os.path.join(self.repo.working_dir, file_path)
				if not os.path.exists(full_path):
					return True
			except:
				pass
			return False
		except Exception as e:
			print(f"檢查文件是否已刪除時出錯: {str(e)}")
			return False
	def get_branches(self):
		if not self.repo:
			return {"local": [], "remote": []}
		try:
			local_branches = [branch.name for branch in self.repo.heads]

			remote_branches = []
			for ref in self.repo.remote().refs:
				name = ref.name.split('/', 1)[1] if '/' in ref.name else ref.name
				remote_branches.append(name)
			current_branch = self.repo.active_branch.name
			return {
				"local": local_branches,
				"remote": remote_branches,
				"current": current_branch
			}
		except Exception as e:
			return {"error": f"無法獲取分支: {str(e)}"}
	def commit(self, message):
		if not self.repo:
			return False
		try:
			staged_files = self.get_staged_files()
			if not staged_files:
				return False
			self.repo.git.commit('-m', message)
			return True
		except Exception as e:
			print(f"提交錯誤: {str(e)}")
			return False
	def stage_file(self, file_path):
		if not self.repo:
			return False
		try:
			self.repo.git.add(file_path)
			return True
		except Exception as e:
			print(f"暫存文件錯誤: {str(e)}")
			return False
	def stage_all_files(self):
		if not self.repo:
			return False
		try:
			self.repo.git.add('-A')
			return True
		except Exception as e:
			print(f"暫存所有文件錯誤: {str(e)}")
			return False
	def fetch_remote(self):
		if not self.repo:
			return {"error": "未打開倉庫"}
		try:
			if not self.repo.remotes:
				return {"error": "沒有設置遠端倉庫"}
			origin = self.repo.remotes.origin
			fetch_info = origin.fetch()
			result = {
				"success": True,
				"message": f"成功從 {origin.name} 獲取最新變更",
				"details": []
			}
			for info in fetch_info:
				if info.flags & info.NEW_HEAD:
					result["details"].append(f"新分支: {info.name}")
				elif info.flags & info.HEAD_UPTODATE:
					result["details"].append(f"分支已是最新: {info.name}")
				elif info.flags & info.FAST_FORWARD:
					result["details"].append(f"快進更新: {info.name}")
				elif info.flags & info.FORCED_UPDATE:
					result["details"].append(f"強制更新: {info.name}")
				else:
					result["details"].append(f"更新: {info.name}")
			return result
		except Exception as e:
			return {"error": f"獲取遠端變更時出錯: {str(e)}"}
	def push_changes(self, remote_name="origin", branch=None):
		if not self.repo:
			return {"error": "未打開倉庫"}
		try:
			if not self.repo.remotes:
				return {"error": "沒有設置遠端倉庫"}
			remote = self.repo.remote(remote_name)
			if not branch:
				branch = self.repo.active_branch.name
			push_info = remote.push(refspec=f"{branch}:{branch}")
			result = {
				"success": True,
				"message": f"成功推送到 {remote_name}/{branch}",
				"details": []
			}
			for info in push_info:
				if info.flags & info.ERROR:
					result["success"] = False
					result["message"] = f"推送到 {remote_name}/{branch} 時出錯"
					result["details"].append(f"錯誤: {info.summary}")
				elif info.flags & info.REJECTED:
					result["success"] = False
					result["message"] = f"推送到 {remote_name}/{branch} 被拒絕"
					result["details"].append(f"拒絕: {info.summary}")
				elif info.flags & info.REMOTE_REJECTED:
					result["success"] = False
					result["message"] = f"推送到 {remote_name}/{branch} 被遠端拒絕"
					result["details"].append(f"遠端拒絕: {info.summary}")
				elif info.flags & info.UP_TO_DATE:
					result["details"].append(f"分支已是最新: {info.summary}")
				elif info.flags & info.FAST_FORWARD:
					result["details"].append(f"快進更新: {info.summary}")
				elif info.flags & info.NEW_HEAD:
					result["details"].append(f"新分支: {info.summary}")
				else:
					result["details"].append(f"推送信息: {info.summary}")
			return result
		except Exception as e:
			return {"error": f"推送變更時出錯: {str(e)}"}