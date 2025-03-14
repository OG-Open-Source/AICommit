import os
import subprocess
import logging

# 配置日志记录器
logger = logging.getLogger("git_operations")

class GitRepository:
	def __init__(self, path):
		"""初始化 Git 仓库对象"""
		logger.info(f"初始化仓库: {path}")
		if not os.path.exists(path):
			logger.error(f"路径不存在: {path}")
			raise ValueError(f"路径不存在: {path}")

		# 检查是否是有效的 Git 仓库
		try:
			self._run_git_command("status", cwd=path)
			logger.info(f"成功打开仓库: {path}")
		except Exception as e:
			logger.error(f"无效的 Git 仓库: {path}, 错误: {str(e)}")
			raise ValueError(f"无效的 Git 仓库: {path}")

		self.path = path

	def _run_git_command(self, command, cwd=None):
		"""运行 Git 命令"""
		if cwd is None:
			cwd = self.path

		full_command = f"git {command}"
		logger.debug(f"执行命令: {full_command} (在 {cwd})")

		process = subprocess.Popen(
			full_command,
			stdout=subprocess.PIPE,
			stderr=subprocess.PIPE,
			shell=True,
			cwd=cwd
		)
		stdout, stderr = process.communicate()

		if process.returncode != 0:
			error_msg = stderr.decode('utf-8')
			logger.error(f"Git 命令失败: {error_msg}")
			raise Exception(f"Git 命令失败: {error_msg}")

		return stdout.decode('utf-8')

	def get_status(self):
		"""获取仓库状态"""
		logger.debug(f"获取仓库状态: {self.path}")
		try:
			branch = self._run_git_command("rev-parse --abbrev-ref HEAD").strip()

			# 获取修改但未暂存的文件（已追踪的文件）
			modified_output = self._run_git_command("diff --name-only")
			modified = [line.strip() for line in modified_output.splitlines() if line.strip()]

			# 获取未跟踪的文件
			untracked_output = self._run_git_command("ls-files --others --exclude-standard")
			untracked = [line.strip() for line in untracked_output.splitlines() if line.strip()]

			# 获取已暂存的文件
			staged_output = self._run_git_command("diff --name-only --cached")
			staged = [line.strip() for line in staged_output.splitlines() if line.strip()]

			# 获取已删除但未暂存的文件
			deleted_output = self._run_git_command("ls-files --deleted")
			deleted = [line.strip() for line in deleted_output.splitlines() if line.strip()]

			status = {
				'branch': branch,
				'modified': modified,
				'untracked': untracked,
				'staged': staged,
				'deleted': deleted
			}
			logger.debug(f"仓库状态: {status}")
			return status
		except Exception as e:
			logger.error(f"获取仓库状态失败: {str(e)}")
			raise

	def stage_file(self, file_path):
		"""暂存文件"""
		logger.info(f"暂存文件: {file_path}")
		self._run_git_command(f"add {file_path}")

	def unstage_file(self, file_path):
		"""取消暂存文件"""
		logger.info(f"取消暂存文件: {file_path}")
		self._run_git_command(f"reset HEAD {file_path}")

	def commit(self, message):
		"""提交更改"""
		logger.info(f"提交更改: {message}")
		self._run_git_command(f"commit -m \"{message}\"")

	def pull(self):
		"""拉取更改"""
		logger.info("拉取更改")
		self._run_git_command("pull")

	def push(self):
		"""推送更改"""
		logger.info("推送更改")
		self._run_git_command("push")

	def get_diff(self, file_path):
		"""获取文件差异"""
		logger.debug(f"获取文件差异: {file_path}")

		try:
			# 检查文件状态
			status = self.get_status()

			# 如果是未跟踪的文件，显示文件内容
			if file_path in status['untracked']:
				logger.debug(f"显示未跟踪文件内容: {file_path}")
				try:
					with open(os.path.join(self.path, file_path), 'r', encoding='utf-8') as f:
						content = f.read()
					# 格式化为类似 diff 的输出，以便高亮显示
					formatted_content = ""
					for line in content.splitlines():
						formatted_content += f"+{line}\n"
					return f"New file: {file_path}\n\n{formatted_content}"
				except UnicodeDecodeError:
					return f"New file: {file_path}\n\n[Binary file, content cannot be displayed]"
				except FileNotFoundError:
					return f"File not found: {file_path}"

			# 如果是已删除的文件，显示删除信息
			elif file_path in status['deleted']:
				logger.debug(f"显示已删除文件: {file_path}")
				# 尝试获取删除前的文件内容
				try:
					content = self._run_git_command(f"show HEAD:{file_path}")
					# 格式化为类似 diff 的输出
					formatted_content = ""
					for line in content.splitlines():
						formatted_content += f"-{line}\n"
					return f"Deleted file: {file_path}\n\n{formatted_content}"
				except Exception:
					return f"Deleted file: {file_path}\n\n[Cannot display content before deletion]"

			# 如果是已暂存的文件，使用 --cached 选项
			elif file_path in status['staged']:
				logger.debug(f"显示已暂存文件差异: {file_path}")
				diff_output = self._run_git_command(f"diff --cached -- \"{file_path}\"")
				# 如果输出为空（例如新添加的文件），则显示完整内容
				if not diff_output.strip():
					try:
						# 获取暂存区中的文件内容
						content = self._run_git_command(f"show :0:{file_path}")
						# 格式化为类似 diff 的输出
						formatted_content = ""
						for line in content.splitlines():
							formatted_content += f"+{line}\n"
						return f"Staged new file: {file_path}\n\n{formatted_content}"
					except Exception:
						return f"Staged new file: {file_path}\n\n[Cannot display content]"
				return diff_output

			# 如果是已修改但未暂存的文件，使用普通 diff
			else:
				logger.debug(f"显示未暂存文件差异: {file_path}")
				# 使用 -U10 选项显示更多上下文
				return self._run_git_command(f"diff -U10 -- \"{file_path}\"")
		except Exception as e:
			logger.error(f"获取差异失败: {str(e)}")
			raise

	def get_branches(self):
		"""获取所有分支"""
		logger.debug("获取所有分支")
		output = self._run_git_command("branch")
		branches = []
		for line in output.splitlines():
			if line.strip():
				# 移除前面的 * 和空格
				branch = line.strip()
				if branch.startswith('*'):
					branch = branch[1:].strip()
				branches.append(branch)
		logger.debug(f"分支列表: {branches}")
		return branches

	def checkout_branch(self, branch_name):
		"""切换分支"""
		logger.info(f"切换分支: {branch_name}")
		self._run_git_command(f"checkout {branch_name}")

	def create_branch(self, branch_name):
		"""创建新分支"""
		logger.info(f"创建分支: {branch_name}")
		self._run_git_command(f"branch {branch_name}")