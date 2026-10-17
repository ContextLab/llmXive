"""
Package initializer for the `code` module.
Sets up a shared logger instance used across submodules.
"""
from llmxive_toolkit import get_logger

# Create a logger for the package; submodules can import `logger` from `code`.
logger = get_logger(__name__)
