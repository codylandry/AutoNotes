import os
from datetime import datetime
from service import find_syslog, Service
import logging
from logging.handlers import SysLogHandler
from apscheduler.schedulers.background import BackgroundScheduler
import time
from utils import (
	decompose_notes_file,
	decompose_template,
	replace_section_text,
	remove_template_tags,
	is_checked,
	get_notes_sections,
	read,
	write
)
from globals import (
	DEFAULT_CURRENT_FILE_NAME,
	DEFAULT_TEMPLATE_FILE_NAME,
	DEFAULT_ARCHIVE_FILE_NAME,
	DEFAULT_COPY_SECTIONS,
)

class Core(object):
	def __init__(self, directory):
		self.directory = directory
		self.template_file_name = DEFAULT_TEMPLATE_FILE_NAME
		self.current_file_name = DEFAULT_CURRENT_FILE_NAME
		self.default_archive_file_name = DEFAULT_ARCHIVE_FILE_NAME
		self.template_path = os.path.join(directory, self.template_file_name)
		self.current_file_path = os.path.join(directory, self.current_file_name)
		self.current_file = None
		self.template = None

	def create_template_file(self):
		return open(self.template_path, 'a+')

	def create_current_file(self):
		return open(self.current_file_path, 'a+')

	def initialize(self, ):
		assert self.is_initialized()
		self.template = self.create_template_file()
		self.current_file = self.create_current_file()

	def is_initialized(self):
		return os.path.isfile(self.template_path) and os.path.isfile(self.current_file_path)

	def __enter__(self):
		self.initialize()
		return self

	def __exit__(self, exc_type, exc_val, exc_tb):
		self.current_file.close()
		self.template.close()

	def rotate(self):
		"""Copy today file to an archive file, clear today file, copy over unchecked items from sections to copy"""
		template_text = read(self.template)
		current_file_text = read(self.current_file)

		# get template/note sections
		template_sections = decompose_template(template_text)
		note_sections = decompose_notes_file(current_file_text, template_sections)

		# create a blank version of the template
		fresh_text = remove_template_tags(template_text, template_sections)

		# create an archive file with the datetime in the filename
		archive_file_name = os.path.join(self.directory, datetime.now().strftime(self.default_archive_file_name))
		with open(archive_file_name, 'w+') as archive_file:
			write(archive_file, current_file_text)

		# whitelist sections for copying non-checked items to
		section_names_to_copy = DEFAULT_COPY_SECTIONS
		sections_to_copy = {k: v for k, v in note_sections.items() if k in section_names_to_copy}

		# copy over lines from current today file to new
		for section_name, section_data in sections_to_copy.items():
			lines_to_copy = '\n'.join([line for line in section_data['text'].split('\n') if not is_checked(line)])
			fresh_text = replace_section_text(fresh_text, section_data, lines_to_copy)

		# overwrite the today file with the new data
		write(self.current_file, fresh_text)

	def add_item(self, section, item, checkbox=False, checked=False):
		"""
		Adds item to section or end of today file. Useful for hooks (ex. git post-commit hook) where you want to add a line
		to a today file section programmatically.
		"""
		# git post-commit hook notes
		#   get most recent commit message: git log -1 --format='%s'

		# get file paths
		sections = get_notes_sections(self.directory)
		section_data = sections[section]

		# add checkbox prefix to line if reqd
		new_item = item
		if checkbox:
			box = '[ ]'
			if checked:
				box = '[X]'
			new_item = "- {} {}".format(box, new_item)

		new_section_text = "{}\n{}".format(section_data['text'], new_item)
		file_text = read(self.current_file)
		file_text = replace_section_text(file_text, section_data, new_section_text)
		write(self.current_file, file_text)


class RotateService(Service):
	# https://python-service.readthedocs.io/en/stable/
	def __init__(self, name, core, *args, **kwargs):
		super(RotateService, self).__init__(name=name, pid_dir=core.directory, *args, **kwargs)
		self.logger.addHandler(SysLogHandler(address=find_syslog(),
		                                     facility=SysLogHandler.LOG_DAEMON))
		self.logger.setLevel(logging.INFO)
		self.core = core

	def rotate(self):
		with self.core as core:
			core.rotate()

	def run(self):
		sched = BackgroundScheduler()
		sched.add_job(self.rotate, 'cron', hour=0)
		sched.start()

		while not self.got_sigterm():
			time.sleep(1)

		sched.shutdown()
