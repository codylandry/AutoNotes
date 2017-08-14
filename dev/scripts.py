from hooks import Hooks

@Hooks.post_git_commit()
def log_commits(core, context=None):
	"""
	This test hook will log commit messages to the appropriate section of the current
	note file based a flag convention:

		F => feature
		C => Change
		D => Defect fix
	"""

	# get the latest commit message
	repo = context.get('repo')
	latest_commit = next((c.message for c in repo.iter_commits()))

	# map flag to section name
	commit_type_map = dict(
		F='features',
		C='changes',
		D='defects'
	)

	section = None
	for k, v in commit_type_map.items():
		if (k + ':') in latest_commit:
			section = v
			break

	if section:
		# add the commit message to the appropriate section
		core.add_item(section, latest_commit, checkbox=True, checked=True)

@Hooks.pre_command()
def pre_command(core, context):
	print 'pre_command hook fired', core, context

@Hooks.pre_rotate()
def pre_rotate(core, context):
	print 'pre_rotate hook fired', core, context

@Hooks.post_rotate()
def post_rotate(core, context):
	print 'post_rotate hook fired', core, context

@Hooks.pre_add_item()
def pre_add_item(core, context):
	print 'pre_add_item hook fired', core, context

@Hooks.post_add_item()
def post_add_item(core, context):
	print 'post_add_item hook fired', core, context



