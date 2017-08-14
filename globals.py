from collections import defaultdict

callbacks = defaultdict(list)
DEFAULT_CURRENT_FILE_NAME = 'today.md'
DEFAULT_TEMPLATE_FILE_NAME = 'template.md'
DEFAULT_ARCHIVE_FILE_NAME = "archive-%Y-%m-%d-%H%M.md"
DEFAULT_COPY_SECTIONS = ('todo', 'notes', 'next')
