import sys
from utils import *
from core import Core, RotateService
import traceback
from globals import callbacks

def _maybe_fire_hook(ctx, hook_type, context=None):
	if ctx.obj.get('fire_hooks', False):
		trigger_hooks(ctx.obj['core'], hook_type, context)

@click.group()
@click.option('--directory',
              default=os.getcwd(),
              type=click.Path(exists=True, dir_okay=True, file_okay=False, resolve_path=True))
@click.option('--hooks/--no-hooks', 'fire_hooks', default=True, help="Fire/don't fire hook methods")
@click.pass_context
def cli(context, directory, fire_hooks):
	"""
	This script allows you to automatically generate and manage tasks/notes

	Arguments:
		- directory: defaults to current working directory
	"""
	core = Core(directory)
	if not core.is_initialized() and not context.invoked_subcommand == 'init':
		click.secho('Warning: {} is not initialized, run => autonotes init'.format(directory), fg='red')
		sys.exit(1)
	context.obj = dict(core=core, fire_hooks=fire_hooks)
	_maybe_fire_hook(context, 'hooks:pre-command')

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
	_maybe_fire_hook(ctx, 'hooks:pre-rotate')
	with ctx.obj['core'] as core:
		core.rotate()
	_maybe_fire_hook(ctx, 'hooks:post-rotate')

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
	_maybe_fire_hook(ctx, 'hooks:pre-add-item')
	with ctx.obj['core'] as core:
		core.add_item(section, item_text, checkbox=checkbox, checked=checked)
	_maybe_fire_hook(ctx, 'hooks:post-add-item')

@click.command()
@click.option('--install/--uninstall', default=True, help="Install git post-commit hook script")
@click.pass_context
def git_hooks(ctx, install):
	with ctx.obj['core'] as core:
		# install git pos-commit hook that calls this function with --trigger set
		if install:
			install_git_post_commit_hook(core.directory)

@click.command()
@click.argument('hook_type')
@click.option('--context', default='', help="Extra data passed to hook callback function")
@click.pass_context
def trigger_hook(ctx, hook_type, context):
	core = ctx.obj['core']
	if 'git:' in hook_type:
		try:
			# get git repo object to pass to hook
			git_root = get_git_root_path(os.getcwd())
			repo = git.Repo(git_root)
			trigger_hooks(core, hook_type, context=dict(repo=repo, context=context))
		except:
			click.secho('{} is not part of a git repo'.format(core.directory))
		finally:
			return

	trigger_hooks(core, hook_type, context=context)

@click.command()
@click.argument('command', type=click.Choice(['start', 'stop']))
@click.pass_context
def service(ctx, command):
	core = ctx.obj['core']
	s = RotateService('autonotes', core)
	getattr(s, command)()


cli.add_command(init)
cli.add_command(create_template)
cli.add_command(create_today)
cli.add_command(rotate)
cli.add_command(add_item)
cli.add_command(git_hooks)
cli.add_command(trigger_hook)
cli.add_command(service)
