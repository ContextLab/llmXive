"""
Wrapper module that forwards configuration helpers from the real implementation
located at ``code.utils.config``. This allows legacy imports such as
``from utils.config import get_project_root`` to continue working.
"""
from code.utils.config import (
    get_project_root,
    get_data_path,
    get_results_path,
    get_log_path,
)

__all__ = [
    "get_project_root",
    "get_data_path",
    "get_results_path",
    "get_log_path",
]
