# @authors: OG-Open-Source
# @version: 1.0.1
# @description: A tool for analyzing file differences with detailed change tracking

import difflib
import os
import re
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple, Union
from collections import defaultdict

@dataclass
class ChangeLocation:
	file_path: str
	line_number: int
	char_position: Optional[int] = None

	def __str__(self) -> str:
		result = f"{self.file_path}:{self.line_number}"
		if self.char_position is not None:
			result += f":{self.char_position}"
		return result

@dataclass
class Change:
	content: str
	change_type: str
	location: ChangeLocation

	def __str__(self) -> str:
		return f"{self.change_type.upper()}: {repr(self.content)} at {self.location}"


class WhatsDifferent:
	FORMAT = 'simple'

	def __init__(self, code_extensions=None, format=None):
		self.code_extensions = code_extensions or ['.py', '.js', '.java', '.c', '.cpp', '.h', '.cs', '.php', '.rb']
		self.format = format or self.FORMAT

	@classmethod
	def set_format(cls, format_type):
		if format_type not in ['simple', 'readable', 'markup']:
			raise ValueError(f"Unsupported format type: {format_type}. Must be one of: 'simple', 'readable', 'markup'")
		cls.FORMAT = format_type

	def set_format(self, format_type):
		if format_type not in ['simple', 'readable', 'markup']:
			raise ValueError(f"Unsupported format type: {format_type}. Must be one of: 'simple', 'readable', 'markup'")
		self.format = format_type
		return self

	def _is_binary_file(self, file_path: str) -> bool:
		if not os.path.exists(file_path):
			return False

		try:
			with open(file_path, 'rb') as f:
				chunk = f.read(1024)

			if b'\x00' in chunk:
				return True

			non_text = sum(1 for b in chunk if b < 32 and b != 9 and b != 10 and b != 13)
			if non_text / len(chunk) > 0.3:
				return True

			return False
		except Exception:
			return False

	def compare_files(self, old_file_path: str, new_file_path: str) -> List[Change]:
		old_exists = os.path.exists(old_file_path)
		new_exists = os.path.exists(new_file_path)

		if not old_exists and not new_exists:
			raise FileNotFoundError(f"Both files don't exist: {old_file_path}, {new_file_path}")

		if old_exists and self._is_binary_file(old_file_path):
			location = ChangeLocation(file_path=old_file_path, line_number=1)
			return [Change("Binary file detected", "info", location)]

		if new_exists and self._is_binary_file(new_file_path):
			location = ChangeLocation(file_path=new_file_path, line_number=1)
			return [Change("Binary file detected", "info", location)]

		if not old_exists:
			with open(new_file_path, 'r', encoding='utf-8') as f:
				new_content = f.readlines()

			changes = []
			for i, line in enumerate(new_content):
				content = line.rstrip('\n\r')
				if content:
					location = ChangeLocation(file_path=new_file_path, line_number=i+1)
					changes.append(Change(content, 'added', location))

			return changes

		if not new_exists:
			with open(old_file_path, 'r', encoding='utf-8') as f:
				old_content = f.readlines()

			changes = []
			for i, line in enumerate(old_content):
				content = line.rstrip('\n\r')
				if content:
					location = ChangeLocation(file_path=old_file_path, line_number=i+1)
					changes.append(Change(content, 'removed', location))

			return changes

		try:
			with open(old_file_path, 'r', encoding='utf-8') as f:
				old_content = f.readlines()

			with open(new_file_path, 'r', encoding='utf-8') as f:
				new_content = f.readlines()

			return self._analyze_diff(old_content, new_content, new_file_path)
		except UnicodeDecodeError:
			location = ChangeLocation(file_path=new_file_path, line_number=1)
			return [Change("Unable to decode file as text - likely binary", "info", location)]

	def compare_strings(self, old_content: str, new_content: str, file_path: str = "unknown") -> List[Change]:
		old_lines = old_content.splitlines(True)
		new_lines = new_content.splitlines(True)

		return self._analyze_diff(old_lines, new_lines, file_path)

	def _analyze_diff(self, old_lines: List[str], new_lines: List[str], file_path: str) -> List[Change]:
		changes = []

		matcher = difflib.SequenceMatcher(None, old_lines, new_lines)

		for tag, i1, i2, j1, j2 in matcher.get_opcodes():
			if tag == 'replace':
				for i in range(i1, i2):
					content = old_lines[i].rstrip('\n\r')
					if content:
						location = ChangeLocation(file_path=file_path, line_number=i + 1)
						changes.append(Change(content, 'removed', location))

				for j in range(j1, j2):
					content = new_lines[j].rstrip('\n\r')
					if content:
						location = ChangeLocation(file_path=file_path, line_number=j + 1)
						changes.append(Change(content, 'added', location))

			elif tag == 'delete':
				for i in range(i1, i2):
					content = old_lines[i].rstrip('\n\r')
					if content:
						location = ChangeLocation(file_path=file_path, line_number=i + 1)
						changes.append(Change(content, 'removed', location))

			elif tag == 'insert':
				for j in range(j1, j2):
					content = new_lines[j].rstrip('\n\r')
					if content:
						location = ChangeLocation(file_path=file_path, line_number=j + 1)
						changes.append(Change(content, 'added', location))

		return changes

	def _get_location(self, file_path: str, line_number: int, code_structure: Dict) -> ChangeLocation:
		return ChangeLocation(file_path=file_path, line_number=line_number)

	def compare_long_lines(self, old_line: str, new_line: str, file_path: str = "unknown") -> List[Change]:
		changes = []
		matcher = difflib.SequenceMatcher(None, old_line, new_line)

		for tag, i1, i2, j1, j2 in matcher.get_opcodes():
			if tag == 'replace':
				old_content = old_line[i1:i2]
				new_content = new_line[j1:j2]

				if old_content:
					location = ChangeLocation(file_path, 1, None)
					location.char_position = i1
					if i1 == 0:
						location.leading_spaces = len(old_content) - len(old_content.lstrip())
					changes.append(Change(old_content, 'removed', location))

				if new_content:
					location = ChangeLocation(file_path, 1, None)
					location.char_position = j1
					if j1 == 0:
						location.leading_spaces = len(new_content) - len(new_content.lstrip())
					changes.append(Change(new_content, 'added', location))

			elif tag == 'delete':
				content = old_line[i1:i2]
				if content:
					location = ChangeLocation(file_path, 1, None)
					location.char_position = i1
					if i1 == 0:
						location.leading_spaces = len(content) - len(content.lstrip())
					changes.append(Change(content, 'removed', location))

			elif tag == 'insert':
				content = new_line[j1:j2]
				if content:
					location = ChangeLocation(file_path, 1, None)
					location.char_position = j1
					if j1 == 0:
						location.leading_spaces = len(content) - len(content.lstrip())
					changes.append(Change(content, 'added', location))

		return changes

	def format_changes(self, changes: List[Change], old_file_path: str = None, new_file_path: str = None,
					  format_type: str = None) -> str:
		if format_type is None:
			format_type = self.format

		file_status = "modified"

		if old_file_path and new_file_path:
			old_exists = os.path.exists(old_file_path)
			new_exists = os.path.exists(new_file_path)

			if not old_exists and new_exists:
				file_status = "created"
			elif old_exists and not new_exists:
				file_status = "deleted"
			elif old_exists and new_exists:
				old_empty = os.path.getsize(old_file_path) == 0
				new_empty = os.path.getsize(new_file_path) == 0

				if old_empty and not new_empty:
					file_status = "created"
				elif not old_empty and new_empty:
					file_status = "deleted"

		if not changes:
			if file_status == "modified":
				return "No differences found."
			else:
				old_name = os.path.basename(old_file_path) if old_file_path else "unknown"
				new_name = os.path.basename(new_file_path) if new_file_path else "unknown"
				return f"@@ '{old_name}' & '{new_name}' @@ {file_status}"

		binary_changes = [c for c in changes if c.change_type == "info" and "binary" in c.content.lower()]
		if binary_changes:
			old_name = os.path.basename(old_file_path) if old_file_path else "unknown"
			new_name = os.path.basename(new_file_path) if new_file_path else "unknown"
			return f"@@ '{old_name}' & '{new_name}' @@ {file_status}\nBinary file detected - cannot display differences"

		changes_by_line = defaultdict(list)
		for change in changes:
			changes_by_line[change.location.line_number].append(change)

		old_lines = []
		new_lines = []

		if old_file_path and os.path.exists(old_file_path):
			try:
				with open(old_file_path, 'r', encoding='utf-8') as f:
					old_lines = f.readlines()
			except UnicodeDecodeError:
				pass

		if new_file_path and os.path.exists(new_file_path):
			try:
				with open(new_file_path, 'r', encoding='utf-8') as f:
					new_lines = f.readlines()
			except UnicodeDecodeError:
				pass

		result = []

		if old_file_path and new_file_path:
			old_name = os.path.basename(old_file_path)
			new_name = os.path.basename(new_file_path)
			result.append(f"@@ '{old_name}' & '{new_name}' @@ {file_status}")

		added = [c for c in changes if c.change_type == 'added']
		removed = [c for c in changes if c.change_type == 'removed']

		if format_type == 'simple':
			for line_number in sorted(changes_by_line.keys()):
				line_changes = changes_by_line[line_number]

				for change in line_changes:
					if change.change_type == 'removed':
						if old_lines and line_number <= len(old_lines):
							original_line = old_lines[line_number-1].rstrip('\n\r')
							result.append(f"[{line_number},-]{original_line}")
						else:
							result.append(f"[{line_number},-]{change.content}")

				for change in line_changes:
					if change.change_type == 'added':
						if new_lines and line_number <= len(new_lines):
							original_line = new_lines[line_number-1].rstrip('\n\r')
							result.append(f"[{line_number},+]{original_line}")
						else:
							result.append(f"[{line_number},+]{change.content}")

		elif format_type == 'readable':
			result.append(f"\nChange Summary:")
			result.append(f"- Total changes: {len(changes)}")
			result.append(f"- Added content: {len(added)} lines")
			result.append(f"- Removed content: {len(removed)} lines")

			for line_number in sorted(changes_by_line.keys()):
				line_changes = changes_by_line[line_number]

				result.append(f"\nChanges at line {line_number}:")

				context_lines = 2

				if old_lines and line_number <= len(old_lines):
					result.append("Old file context:")
					start = max(0, line_number - context_lines - 1)
					end = min(len(old_lines), line_number + context_lines)

					for i in range(start, end):
						prefix = '> ' if i == line_number - 1 else '  '
						result.append(f"  {prefix}{i+1}: {old_lines[i].rstrip()}")

				if new_lines and line_number <= len(new_lines):
					result.append("New file context:")
					start = max(0, line_number - context_lines - 1)
					end = min(len(new_lines), line_number + context_lines)

					for i in range(start, end):
						prefix = '> ' if i == line_number - 1 else '  '
						result.append(f"  {prefix}{i+1}: {new_lines[i].rstrip()}")

				for change in line_changes:
					if change.change_type == 'removed':
						if old_lines and line_number <= len(old_lines):
							original_line = old_lines[line_number-1].rstrip('\n\r')
							result.append(f"[{line_number},-]{original_line}")
						else:
							result.append(f"[{line_number},-]{change.content}")

				for change in line_changes:
					if change.change_type == 'added':
						if new_lines and line_number <= len(new_lines):
							original_line = new_lines[line_number-1].rstrip('\n\r')
							result.append(f"[{line_number},+]{original_line}")
						else:
							result.append(f"[{line_number},+]{change.content}")

		elif format_type == 'markup':
			result.append(f"# Changes between '{old_name}' and '{new_name}' ({file_status})")
			result.append(f"Total changes: {len(changes)} ({len(added)} added, {len(removed)} removed)")

			semantic_groups = self._group_changes_by_semantic_unit(changes)

			for group_name, group_changes in semantic_groups.items():
				result.append(f"\n## {group_name}")

				group_by_line = defaultdict(list)
				for change in group_changes:
					group_by_line[change.location.line_number].append(change)

				for line_number in sorted(group_by_line.keys()):
					line_changes = group_by_line[line_number]

					for change in line_changes:
						if change.change_type == 'removed':
							if old_lines and line_number <= len(old_lines):
								original_line = old_lines[line_number-1].rstrip('\n\r')
								result.append(f"- `{original_line}`")
							else:
								result.append(f"- `{change.content}`")

					for change in line_changes:
						if change.change_type == 'added':
							if new_lines and line_number <= len(new_lines):
								original_line = new_lines[line_number-1].rstrip('\n\r')
								result.append(f"+ `{original_line}`")
							else:
								result.append(f"+ `{change.content}`")

			important_changes = self._identify_important_changes(changes)
			if important_changes:
				result.append("\n## Key Changes")
				for change in important_changes:
					if change.change_type == 'added':
						result.append(f"+ Added: `{change.content}`")
					else:
						result.append(f"- Removed: `{change.content}`")

		else:
			result.append(f"Error: Unknown format type '{format_type}'")

		return "\n".join(result)

	def _group_changes_by_semantic_unit(self, changes: List[Change]) -> Dict[str, List[Change]]:
		groups = defaultdict(list)

		for change in changes:
			if hasattr(change.location, 'function_name') and change.location.function_name:
				if hasattr(change.location, 'class_name') and change.location.class_name:
					group_name = f"Class: {change.location.class_name}, Method: {change.location.function_name}"
				else:
					group_name = f"Function: {change.location.function_name}"
			elif hasattr(change.location, 'class_name') and change.location.class_name:
				group_name = f"Class: {change.location.class_name}"
			else:
				group_name = "Global scope"

			groups[group_name].append(change)

		return groups

	def _identify_important_changes(self, changes: List[Change]) -> List[Change]:
		important_changes = []

		for change in changes:
			content = change.content.strip()

			if re.match(r'^def\s+\w+|^class\s+\w+', content):
				important_changes.append(change)

			elif re.match(r'^import\s+|^from\s+\w+\s+import', content):
				important_changes.append(change)

			elif re.match(r'^return\s+', content):
				important_changes.append(change)

			elif re.search(r'\w+\(.*\)', content) and not content.startswith(('#', '//', '/*')):
				important_changes.append(change)

		return important_changes

	def format_for_markup(self, changes: List[Change], old_file_path: str = None, new_file_path: str = None) -> str:
		return self.format_changes(changes, old_file_path, new_file_path, format_type='markup')