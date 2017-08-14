import functools
from globals import callbacks

def register_hook(type_):
	def decorator(method):
		@functools.wraps(method)
		def f(*args, **kwargs):
			method(*args, **kwargs)
		callbacks[type_].append(f)
		return f
	return decorator

class Hooks:
	@staticmethod
	def post_git_commit():
		return register_hook('git:post-commit')

	@staticmethod
	def post_git_push():
		return register_hook('git:post-push')

	@staticmethod
	def pre_rotate():
		return register_hook('hooks:pre-rotate')

	@staticmethod
	def post_rotate():
		return register_hook('hooks:post-rotate')

	@staticmethod
	def pre_add_item():
		return register_hook('hooks:pre-add-item')

	@staticmethod
	def post_add_item():
		return register_hook('hooks:post-add-item')

	@staticmethod
	def pre_command():
		return register_hook('hooks:pre-command')

