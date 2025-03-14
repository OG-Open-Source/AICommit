import sys
import os
import logging
from logging.handlers import RotatingFileHandler

# 配置日志
def setup_logging():
	# 创建日志目录
	log_dir = os.path.expanduser("~/.aicommit/logs")
	if not os.path.exists(log_dir):
		os.makedirs(log_dir)

	# 配置根日志记录器
	root_logger = logging.getLogger()
	root_logger.setLevel(logging.DEBUG)

	# 文件处理器 - 使用循环日志文件
	log_file = os.path.join(log_dir, "aicommit.log")
	file_handler = RotatingFileHandler(
		log_file, maxBytes=5*1024*1024, backupCount=5
	)
	file_handler.setLevel(logging.DEBUG)

	# 控制台处理器
	console_handler = logging.StreamHandler()
	console_handler.setLevel(logging.INFO)

	# 格式化器
	formatter = logging.Formatter(
		'%(asctime)s - %(name)s - %(levelname)s - %(message)s'
	)
	file_handler.setFormatter(formatter)
	console_handler.setFormatter(formatter)

	# 添加处理器
	root_logger.addHandler(file_handler)
	root_logger.addHandler(console_handler)

	return root_logger

# 将项目根目录添加到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 设置日志
logger = setup_logging()
logger.info("启动 AICommit 应用程序")

from PyQt5.QtWidgets import QApplication
from ui.main_window import MainWindow

def main():
	try:
		app = QApplication(sys.argv)
		app.setApplicationName("AICommit")
		app.setOrganizationName("OG-Open-Source")

		logger.info("初始化主窗口")
		window = MainWindow()
		window.show()

		logger.info("应用程序进入主循环")
		sys.exit(app.exec_())
	except Exception as e:
		logger.critical(f"应用程序崩溃: {str(e)}", exc_info=True)
		raise

if __name__ == "__main__":
	main()