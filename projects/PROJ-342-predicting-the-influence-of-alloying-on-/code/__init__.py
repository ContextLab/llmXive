"""
Project package initializer.
Ensures that all required top‑level directories exist and configures a
project‑wide logger that writes to ``logs/project.log`` and also streams to
stdout.  Other modules can obtain a child logger via ``get_logger``.
"""

import logging
from pathlib import Path

# ----------------------------------------------------------------------
# Determine project root (one level above the ``code`` package)
# ----------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# ----------------------------------------------------------------------
# Directories that must exist for the pipeline
# ----------------------------------------------------------------------
REQUIRED_DIRS = [
    PROJECT_ROOT / "code",
    PROJECT_ROOT / "data" / "raw",
    PROJECT_ROOT / "data" / "processed",
    PROJECT_ROOT / "artifacts" / "models",
    PROJECT_ROOT / "artifacts" / "metrics",
    PROJECT_ROOT / "artifacts" / "reports",
    PROJECT_ROOT / "figures",
    PROJECT_ROOT / "paper",
    PROJECT_ROOT / "tests",
    PROJECT_ROOT / "logs",
    PROJECT_ROOT / "specs" / "001-predicting-the-influence-of-alloying-on" / "contracts",
]

# Create any missing directories
for _dir in REQUIRED_DIRS:
    _dir.mkdir(parents=True, exist_ok=True)

# ----------------------------------------------------------------------
# Configure a project‑wide logger
# ----------------------------------------------------------------------
LOGS_DIR = PROJECT_ROOT / "logs"
LOG_FILE = LOGS_DIR / "project.log"

# Root logger for the project (named ``project``)
_project_logger = logging.getLogger("project")
_project_logger.setLevel(logging.INFO)

# Avoid adding duplicate handlers if the package is re‑imported
if not _project_logger.handlers:
    _formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    _file_handler = logging.FileHandler(LOG_FILE)
    _file_handler.setFormatter(_formatter)
    _stream_handler = logging.StreamHandler()
    _stream_handler.setFormatter(_formatter)

    _project_logger.addHandler(_file_handler)
    _project_logger.addHandler(_stream_handler)

def get_logger(name: str = __name__) -> logging.Logger:
    """
    Return a child logger that inherits the project handlers.

    Parameters
    ----------
    name : str
        Name of the logger (typically ``__name__`` of the calling module).

    Returns
    -------
    logging.Logger
        Configured logger instance.
    """
    child_logger = logging.getLogger(f"project.{name}")
    child_logger.setLevel(logging.INFO)
    return child_logger

# Expose the logger for modules that simply ``import code`` and expect
# ``code.logger`` to be usable.
logger = get_logger(__name__)