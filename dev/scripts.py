import autonotes

@autonotes.hook()
def test(core, repo):
	print core, repo
	latest_commit = next((c.message for c in repo.iter_commits()))
	commit_type_map = dict(
		F='features',
		C='changes',
		D='defects'
	)
	section = None
	for k, v in commit_type_map.items():
		if k in latest_commit:
			section = v
			break

	print 'test test, ', latest_commit
	if section:
		core.add_item(section, latest_commit, checkbox=True, checked=True)
