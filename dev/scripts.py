import autonotes, git, os

@autonotes.hook()
def test():
	git_root = autonotes.get_git_root_path(os.getcwd())
	repo = git.Repo(git_root)
	latest_commit = next((c.message for c in repo.iter_commits()))
	autonotes.add_item(latest_commit, section='notes', checkbox=True, checked=True)

