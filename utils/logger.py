import logging
import os
from datetime import datetime

class Logger:
	def __init__(self):
		self.log_dir = os.path.expanduser("~/.aicommit/logs")
		if not os.path.exists(self.log_dir):
			os.makedirs(self.log_dir)

		log_file = os.path.join(self.log_dir, f"aicommit_{datetime.now().strftime('%Y%m%d')}.log")

		# 配置日志
		self.logger = logging.getLogger("AICommit")
		self.logger.setLevel(logging.DEBUG)

		# 文件处理器
		file_handler = logging.FileHandler(log_file)
		file_handler.setLevel(logging.DEBUG)

		# 控制台处理器
		console_handler = logging.StreamHandler()
		console_handler.setLevel(logging.INFO)

		# 格式
		formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
		file_handler.setFormatter(formatter)
		console_handler.setFormatter(formatter)

		# 添加处理器
		self.logger.addHandler(file_handler)
		self.logger.addHandler(console_handler)

	def debug(self, message):
		self.logger.debug(message)

	def info(self, message):
		self.logger.info(message)

	def warning(self, message):
		self.logger.warning(message)

	def error(self, message):
		self.logger.error(message)

	def critical(self, message):
		self.logger.critical(message)