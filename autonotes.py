from datetime import datetime
import sys
import functools
from utils import *
from core import Core
import traceback

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
	core = Core(directory)

	if not core.is_initialized() and not context.invoked_subcommand == 'init':
		click.secho('Warning: {} is not initialized, run => autonotes init'.format(directory), fg='red')
		sys.exit(1)

	context.obj = dict(core=core)

@click.command()
@click.pass_context
def init(ctx):
	"""Creates Required Files"""
	core = ctx.obj['core']
	if core.is_initialized():
		click.secho(core.directory + ' already initialized!\n', fg='green')
		return

	if not check_path(core.directory):
		return

	click.secho('\nCREATING REQUIRED FILES...', fg='blue')

	template_path = core.template_path
	if os.path.exists(template_path):
		click.secho('\t- {} already exists!'.format(template_path), fg='yellow')
	else:
		core.create_template_file()
		click.echo('\t- {}'.format(template_path))

	today_path = core.current_file_path
	if os.path.exists(today_path):
		click.secho('\t- {} already exists!'.format(today_path), fg='yellow')
	else:
		core.create_current_file()
		click.echo('\t- {}'.format(today_path))

	click.secho('Success!\n', fg='green')


@click.command()
@click.pass_context
def create_template(ctx):
	"""Recreates an empty template file"""
	core = ctx.obj['core']

	if os.path.exists(core.template_path):
		click.secho(core.template_path + ' already exists!\n', fg='yellow')
		return

	click.secho('\nCREATING TEMPLATE FILE...', fg='blue')
	core.create_template_file()
	click.echo('\t- {}'.format(core.template_path))
	click.secho('Success!\n', fg='green')


@click.command()
@click.pass_context
def create_today(ctx):
	"""Recreates an empty today note file"""
	core = ctx.obj['core']

	if os.path.exists(core.current_file_path):
		click.secho(core.current_file_path + ' already exists!\n', fg='yellow')
		return

	click.secho('\nCREATING TODAY FILE...', fg='blue')
	core.create_current_file()
	click.echo('\t- {}'.format(core.current_file_path))
	click.secho('Success!\n', fg='green')


@click.command()
@click.pass_context
def rotate(ctx):
	"""Copy today file to an archive file, clear today file, copy over unchecked items from sections to copy"""
	# get file paths
	with ctx.obj['core'] as core:
		core.rotate()

@click.command()
@click.option('--checkbox/--no-checkbox', default=False, help="Add a checkbox to the line")
@click.option('--checked/--not-checked', default=False, help='Check the checkbox if --checkbox set')
@click.option('--section', default='', type=str, help="Specify the section the line will be added to.  (Default = end of file)")
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

	with ctx.obj['core'] as core:
		core.add_item(section, item_text, checkbox=checkbox, checked=checked)

# TODO: codylandry - REFACTOR HOOK API

hook_callbacks = []

@click.command()
@click.option('--install', is_flag=True, default=False, help="Install git post-commit hook script")
@click.option('--trigger', is_flag=True, default=False, help="Fires registered post-commit callbacks")
@click.pass_context
def git_hook(ctx, install, trigger):
	with ctx.obj['core'] as core:

		if install:
			install_git_post_commit_hook(core.directory)

		elif trigger:
			scripts_file_path = os.path.join(core.directory, 'scripts.py')
			try:
				git_root = get_git_root_path(os.getcwd())
				repo = git.Repo(git_root)
				import_(scripts_file_path)
				for hook in hook_callbacks:
					try:
						hook(core, repo)
					except Exception as e:
						print traceback.format_exc()
			except ImportError:
				click.secho('scripts.py not in {}'.format(core.directory))
				return

def hook(type='post-commit'):
	def decorator(method):
		@functools.wraps(method)
		def f(*args, **kwargs):
			method(*args, **kwargs)
		hook_callbacks.append(f)
		return f
	return decorator


cli.add_command(init)
cli.add_command(create_template)
cli.add_command(create_today)
cli.add_command(rotate)
cli.add_command(add_item)
cli.add_command(git_hook)

if __name__ == '__main__':
	cli()
