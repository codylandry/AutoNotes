import autonotes

@autonotes.hook(type='git:post-commit')
def log_commits(core, repo):
	"""
	This test hook will log commit messages to the appropriate section of the current
	note file based a flag convention:

		F => feature
		C => Change
		D => Defect fix
	"""
	# get the latest commit message
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
