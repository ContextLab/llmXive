"""
Very small logging helper used by several modules.

The real project may wish to emit structured logs; for the purpose
of getting the linting stage to succeed we provide minimal
wrappers that satisfy the import contracts.
"""
import logging

from llmxive_toolkit import paths

_logger = logging.getLogger(__name__)

def init_logging(level: int = logging.INFO) -> None:
    """
    Initialise the root logger with a basic configuration.

    Args:
        level: Logging level – defaults to ``INFO``.
    """
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    _logger.debug("Logging initialized at level %s", logging.getLevelName(level))

def log_error(message: str) -> None:
    """
    Log an error message using the module‑level logger.
    """
    _logger.error(message)

def get_exclusion_log_path() -> str:
    """
    Return the filesystem path (as a string) to the exclusion log CSV.
    """
    exclusion_path = paths.data("processed", "exclusion_log.csv")
    # Ensure the containing directory exists.
    exclusion_path.parent.mkdir(parents=True, exist_ok=True)
    return str(exclusion_path)

def log_exclusion(subject_id: str, reason: str, details: dict | None = None) -> None:
    """
    Record an exclusion event. In this minimal implementation we
    simply emit a log line; later tasks will append to the CSV.
    """
    if details is None:
        details = {}
    _logger.info(
        "Exclusion logged – Subject_ID: %s, Reason: %s, Details: %s",
        subject_id,
        reason,
        details,
    )
