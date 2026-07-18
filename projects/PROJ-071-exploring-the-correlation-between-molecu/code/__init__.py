"""
llmXive Pipeline - Code Package.
"""
from code.logging_config import setup_logging, get_logger, PipelineError, DataIngestionError
from code.config import PROJECT_ROOT, DATA_DIR, ensure_directories

__version__ = "0.1.0"
__all__ = [
    "setup_logging",
    "get_logger",
    "PipelineError",
    "DataIngestionError",
    "PROJECT_ROOT",
    "DATA_DIR",
    "ensure_directories"
]