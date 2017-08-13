import autonotes, git, os
from core import Core

@autonotes.hook()
def test(repo):
	with Core(os.getcwd()) as core:
		latest_commit = next((c.message for c in repo.iter_commits()))
		core.add_item('features', latest_commit, checkbox=True, checked=True)
