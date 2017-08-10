from setuptools import setup

setup(
	name='AutoNotes',
	version='1.0',
	py_modules=['autonotes'],
	install_requires=[
		'Click',
	],
	entry_points='''
		[console_scripts]
		autonotes=autonotes:cli
	'''
)
