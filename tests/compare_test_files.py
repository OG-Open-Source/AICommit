import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from whatsdifferent import WhatsDifferent

def main():
	diff_tool = WhatsDifferent(format='markup')

	base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
	test1_path = os.path.join(base_dir, 'setup.py')
	test2_path = os.path.join(base_dir, 'AICommit.exe')

	changes = diff_tool.compare_files(test1_path, test2_path)

	formatted_output = diff_tool.format_changes(changes, test1_path, test2_path)
	print(formatted_output)

if __name__ == "__main__":
	main()