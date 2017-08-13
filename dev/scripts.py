import autonotes, git, os
from core import Core

@autonotes.hook()
def test(repo):
	this_dir = os.path.dirname(os.path.abspath(__file__))
	with Core(this_dir) as core:
		latest_commit = next((c.message for c in repo.iter_commits()))
		core.add_item('features', latest_commit, checkbox=True, checked=True)
