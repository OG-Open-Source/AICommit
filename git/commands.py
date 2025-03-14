import subprocess
import os

class GitCommands:
	@staticmethod
	def run_command(command, cwd=None):
		"""运行 Git 命令"""
		process = subprocess.Popen(
			command,
			stdout=subprocess.PIPE,
			stderr=subprocess.PIPE,
			shell=True,
			cwd=cwd
		)
		stdout, stderr = process.communicate()

		if process.returncode != 0:
			raise Exception(f"Git 命令失败: {stderr.decode('utf-8')}")

		return stdout.decode('utf-8')

	@staticmethod
	def clone(url, path):
		"""克隆仓库"""
		return GitCommands.run_command(f"git clone {url} {path}")

	@staticmethod
	def init(path):
		"""初始化仓库"""
		if not os.path.exists(path):
			os.makedirs(path)
		return GitCommands.run_command("git init", cwd=path)