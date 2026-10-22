"""
Top-level utils package.

This package re-exports the project's utility modules located under the
``code`` directory so that imports like ``from utils.seed import set_seeds``
work without needing to modify ``sys.path`` manually.

The actual implementation lives in ``code/utils/seed.py``.
"""
# Export the seed module symbols at package level for convenience
from .seed import *  # noqa: F401,F403
