import click
import re
from collections import OrderedDict
import os
from datetime import datetime
import sys
import git

TODAY_FILE_NAME = 'today.md'
TEMPLATE_FILE_NAME = 'template.md'
ARCHIVE_FILE_NAME_FORMAT = "archive-%Y-%m-%d-%H%M.md"


@click.group()
@click.option('--directory',
              default=os.getcwd(),
              type=click.Path(exists=True, dir_okay=True, file_okay=False, resolve_path=True))
@click.pass_context
def cli(context, directory):
	"""
	This script allows you to automatically generate and manage tasks/notes

	Arguments:
		- directory: defaults to current working directory
	"""
	if not is_initialized(directory) and not context.invoked_subcommand == 'init':
		click.secho('Warning: {} is not initialized, run => autonotes init'.format(directory), fg='red')
		sys.exit(1)

	context.obj = dict(directory=directory)


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


@click.command()
@click.pass_context
def init(ctx):
	"""Creates Required Files"""
	directory = ctx.obj['directory']
	if is_initialized(directory):
		click.secho(directory + ' already initialized!\n', fg='green')
		return

	if not check_path(directory):
		return

	click.secho('\nCREATING REQUIRED FILES...', fg='blue')

	template_path = os.path.join(directory, TEMPLATE_FILE_NAME)
	if os.path.exists(template_path):
		click.secho('\t- {} already exists!'.format(template_path), fg='yellow')
	else:
		open(template_path, 'w+')
		click.echo('\t- {}'.format(template_path))

	today_path = os.path.join(directory, TODAY_FILE_NAME)
	if os.path.exists(today_path):
		click.secho('\t- {} already exists!'.format(today_path), fg='yellow')
	else:
		open(today_path, 'w+')
		click.echo('\t- {}'.format(today_path))

	click.secho('Success!\n', fg='green')


@click.command()
@click.pass_context
def create_template(ctx):
	"""Recreates an empty template file"""
	directory = ctx.obj['directory']
	if not check_path(directory):
		return

	filepath = os.path.join(directory, TEMPLATE_FILE_NAME)
	if os.path.exists(filepath):
		click.secho(filepath + ' already exists!\n', fg='yellow')
		return

	click.secho('\nCREATING TEMPLATE FILE...', fg='blue')
	with open(filepath, 'w+') as f:
		f.write('')
	click.echo('\t- {}'.format(filepath))
	click.secho('Success!\n', fg='green')


@click.command()
@click.pass_context
def create_today(ctx):
	"""Recreates an empty today note file"""
	directory = ctx.obj['directory']
	if not check_path(directory):
		return

	filepath = os.path.join(directory, TODAY_FILE_NAME)
	if os.path.exists(filepath):
		click.secho(filepath + ' already exists!\n', fg='yellow')
		return

	click.secho('\nCREATING TODAY FILE...', fg='blue')
	with open(filepath, 'w+') as f:
		f.write('')
	click.echo('\t- {}'.format(filepath))
	click.secho('Success!\n', fg='green')


def is_checkbox_line(line):
	matches = ['[ ]', '[]', '[X]', '[x]']
	return any([line.find(match) != -1 for match in matches])


def is_checked(line):
	if not is_checkbox_line(line):
		return False
	matches = ['[x]', '[X]']
	return any([line.find(match) != -1 for match in matches])


@click.command()
@click.pass_context
def rotate(ctx):
	"""Copy today file to an archive file, clear today file, copy over unchecked items from sections to copy"""
	# get file paths
	directory = ctx.obj['directory']
	today_file_path = os.path.join(directory, TODAY_FILE_NAME)
	template_file_path = os.path.join(directory, TEMPLATE_FILE_NAME)

	# get template text
	with open(template_file_path, 'r') as template_file:
		template_text = template_file.read()

	# get note text
	with open(today_file_path, 'r') as today_file:
		today_file_text = today_file.read()

	# get template/note sections
	template_sections = decompose_template(template_text)
	note_sections = decompose_notes_file(today_file_text, template_sections)

	# create a blank version of the template
	fresh_today_text = remove_template_tags(template_text, template_sections)

	# create an archive file with the datetime in the filename
	archive_file_name = os.path.join(directory, datetime.now().strftime(ARCHIVE_FILE_NAME_FORMAT))
	with open(archive_file_name, 'w+') as archive_file:
		archive_file.write(today_file_text)

	# whitelist sections for copying non-checked items to
	section_names_to_copy = ['todo', 'notes', 'next']
	sections_to_copy = {k: v for k, v in note_sections.items() if k in section_names_to_copy}

	# copy over lines from current today file to new
	for section_name, section_data in sections_to_copy.items():
		lines_to_copy = '\n'.join([line for line in section_data['text'].split('\n') if not is_checked(line)])
		fresh_today_text = replace_section_text(fresh_today_text, section_data, lines_to_copy)

	# overwrite the today file with the new data
	with open(today_file_path, 'w') as today_file:
		today_file.write(fresh_today_text)


@click.command()
@click.option('--checkbox/--no-checkbox', default=False, help="Add a checkbox to the line")
@click.option('--checked/--not-checked', default=False, help='Check the checkbox if --checkbox set')
@click.option('--section', type=str, help="Specify the section the line will be added to.  (Default = end of file)")
@click.argument('item_text', type=str)
@click.pass_context
def add_item(ctx, checkbox, checked, section, item_text):
	"""
	Adds item to section or end of today file. Useful for hooks (ex. git post-commit hook) where you want to add a line
	to a today file section programmatically.
	"""
	# git post-commit hook notes
	#   get most recent commit message: git log -1 --format='%s'

	# get file paths
	directory = ctx.obj['directory']
	sections = get_notes_sections(directory)
	section_data = sections[section]

	new_item = item_text
	if checkbox:
		box = '[ ]'
		if checked:
			box = '[X]'
		new_item = "- {} {}".format(box, new_item)

	new_section_text = "{}\n{}".format(section_data['text'], new_item)

	today_file_path = os.path.join(directory, TODAY_FILE_NAME)
	with open(today_file_path, 'r') as today_file:
		today_text = today_file.read()

	today_text = replace_section_text(today_text, section_data, new_section_text)

	with open(today_file_path, 'w') as today_file:
		today_file.write(today_text)


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


@click.command()
@click.option('--install', is_flag=True, default=False, help="Install git post-commit hook script")
@click.option('--trigger', is_flag=True, default=False, help="Fires registered post-commit callbacks")
@click.pass_context
def git_hook(ctx, install, trigger):
	directory = ctx.obj['directory']

	if install:
		install_git_post_commit_hook(directory)

	elif trigger:
		print 'test'


cli.add_command(init)
cli.add_command(create_template)
cli.add_command(create_today)
cli.add_command(rotate)
cli.add_command(add_item)
cli.add_command(git_hook)

if __name__ == '__main__':
	cli()
