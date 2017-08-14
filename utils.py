import os, click, git, re, imp, traceback
from collections import OrderedDict


TODAY_FILE_NAME = 'today.md'
TEMPLATE_FILE_NAME = 'template.md'
ARCHIVE_FILE_NAME_FORMAT = "archive-%Y-%m-%d-%H%M.md"

def read(file_):
	file_.seek(0)
	return file_.read()

def write(file_, text):
	file_.seek(0)
	file_.truncate()
	return file_.write(text)


def is_checkbox_line(line):
	matches = ['[ ]', '[]', '[X]', '[x]']
	return any([line.find(match) != -1 for match in matches])


def is_checked(line):
	if not is_checkbox_line(line):
		return False
	matches = ['[x]', '[X]']
	return any([line.find(match) != -1 for match in matches])



def import_(filename):
	"""imports a module by path and returns the module object"""
	(path, name) = os.path.split(filename)
	(name, ext) = os.path.splitext(name)

	(file, filename, data) = imp.find_module(name, [path])
	return imp.load_module(name, file, filename, data)

def get_git_root_path(path):
	"""returns the root git repo path"""
	git_repo = git.Repo(path, search_parent_directories=True)
	return git_repo.git.rev_parse("--show-toplevel")


def replace_section_text(text, section_data, section_text):
	"""Replace a 'section_name' of 'text' with 'section_text'"""
	start = text.index(section_data['before']) + len(section_data['before'])
	end = text.index(section_data['after'])
	return text[:start] + section_text + text[end:]


def decompose_template(template):
	"""
	Parses template text and returns a dictionary
	key: {
		before: text occurring before the {{ section_name }}
		after: text occurring after the {{ section_name }}
	}
	:param template: string
	:return: OrderedDict
	"""
	tokens = re.split(r'(\{\{.*\}\})', template)
	sections = OrderedDict()
	for i in range(0, len(tokens), 2):
		if i > len(tokens) - 2:
			break
		before = tokens[i]
		tag = tokens[i + 1]
		after = tokens[i + 2]
		section_name = re.search(r'(?<={{) *(\w*) *(?=}})', tag).group(0).strip()
		sections[section_name] = dict(before=before, after=after, tag=tag, name=section_name)
	return sections


def remove_template_tags(text, template_sections):
	"""
	Takes a template and removes all the {{ }} tags
	:param template: string
	:return: string
	"""
	out = text
	tags = [section['tag'] for section in template_sections.values()]
	for tag in tags:
		out = out.replace(tag, '')
	return out


def decompose_notes_file(note_text, template_sections):
	"""
	Takes note text and uses template sections to get text of each section
	:param note_text: string
	:param template_sections: OrderedDict (result of decompose_template)
	:return: OrderedDict (copy of template_sections but with 'text' key)
	"""
	ret = OrderedDict(template_sections)
	for section_name, match_data in template_sections.items():
		start = note_text.index(match_data['before']) + len(match_data['before'])
		end = note_text.index(match_data['after'])
		ret[section_name]['text'] = note_text[start:end]
	return ret


def get_template_sections(directory):
	"""Open the template at path and decompose it"""
	# get file paths
	template_file_path = os.path.join(directory, TEMPLATE_FILE_NAME)

	# get template text
	with open(template_file_path, 'r') as template_file:
		template_text = template_file.read()

	return decompose_template(template_text)


def get_notes_sections(directory):
	"""Open the template at path and decompose it"""
	# get file paths
	template_sections = get_template_sections(directory)
	today_file_path = os.path.join(directory, TODAY_FILE_NAME)

	# get template text
	with open(today_file_path, 'r') as today_file:
		today_text = today_file.read()

	return decompose_notes_file(today_text, template_sections)


def is_initialized(directory):
	"""
	Does path have all the right files
	:param directory: directory path
	:return:
	"""
	today_path = os.path.join(directory, TODAY_FILE_NAME)
	template_path = os.path.join(directory, TEMPLATE_FILE_NAME)
	return (os.path.exists(today_path) and os.path.exists(template_path))


def check_path(directory):
	"""Is path a valid existing directory"""
	if os.path.isdir(directory):
		return True
	else:
		click.secho('{} is not a directory!'.format(directory), fg='red')
		return False

def touchopen(filename, *args, **kwargs):
	open(filename, "a").close()  # "touch" file
	return open(filename, *args, **kwargs)


def install_git_post_commit_hook(directory):
	git_root = get_git_root_path(directory)
	hooks_directory = os.path.join(git_root, '.git', 'hooks')
	hook = "autonotes --directory={} git_hook --trigger".format(directory)
	hook_file_path = os.path.join(hooks_directory, 'post-commit')

	with touchopen(hook_file_path, 'a+') as hook_file:
		hook_file_text = hook_file.read()
		if hook in hook_file_text:
			click.secho('git post-commit hook already installed at: {}'.format(hook_file_path), fg='yellow')
			return
		else:
			hook_file_text += '\n' + hook
			hook_file.seek(0)
			hook_file.write(hook_file_text)

	click.secho('Git post-commit hook installed for {}'.format(git_root), fg='green')

def trigger_hooks(core, hook_type, context=None):
	from autonotes import callbacks
	with core:
		try:
			# import hooks, which register themselves on evaluation in hook_callbacks
			scripts_file_path = os.path.join(core.directory, 'scripts.py')
			import_(scripts_file_path)
		except ImportError:
			click.secho('scripts.py not in {}'.format(core.directory))
			return

		# call each hook passing the core and context
		for hook in callbacks[hook_type]:
			try:
				hook(core, context)
			except Exception as e:
				print traceback.format_exc()
