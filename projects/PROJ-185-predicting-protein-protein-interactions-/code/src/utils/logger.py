import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

try:
    # Python 3.8+
    from importlib import metadata as importlib_metadata
except ImportError:  # pragma: no cover
    import importlib_metadata  # type: ignore

# ----------------------------------------------------------------------
# JSON formatter for log records – emits a single line JSON object.
# ----------------------------------------------------------------------
class JSONFormatter(logging.Formatter):
    """
    Convert a logging record to a JSON string.  The formatter expects that
    ``record.msg`` is a dictionary that already contains the fields that
    should be emitted (timestamp, level, message, etc.).  If a non‑dict
    message is supplied it will be wrapped in a ``message`` field.
    """

    def format(self, record: logging.LogRecord) -> str:
        # Ensure the message is a dict; otherwise coerce.
        if isinstance(record.msg, dict):
            payload = record.msg
        else:
            payload = {
                "message": record.getMessage(),
            }

        # Add standard fields if they are missing.
        payload.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
        payload.setdefault("level", record.levelname)
        payload.setdefault("schema_version", 1)

        return json.dumps(payload, ensure_ascii=False)

# ----------------------------------------------------------------------
# Logger factory – creates (or returns) a singleton logger that writes to
# ``pipeline.log`` in the project root directory.
# ----------------------------------------------------------------------
_LOGGER: logging.Logger | None = None


def _get_log_path() -> Path:
    """
    Resolve the absolute path to ``pipeline.log`` located in the project
    root (three directories up from this file).
    """
    # logger.py lives in <project_root>/code/src/utils/logger.py
    project_root = Path(__file__).resolve().parents[3]
    return project_root / "pipeline.log"


def get_logger(name: str = "pipeline") -> logging.Logger:
    """
    Return a configured logger that writes JSON lines to ``pipeline.log``.
    The logger is created only once (singleton) to avoid duplicate
    handlers when imported multiple times.
    """
    global _LOGGER
    if _LOGGER is not None:
        return _LOGGER

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    log_path = _get_log_path()
    log_path.parent.mkdir(parents=True, exist_ok=True)

    handler = logging.FileHandler(log_path, mode="a", encoding="utf-8")
    handler.setFormatter(JSONFormatter())
    logger.addHandler(handler)

    _LOGGER = logger
    return logger

# ----------------------------------------------------------------------
# Helper to collect software version information.
# ----------------------------------------------------------------------
def _collect_versions() -> Dict[str, str]:
    """
    Return a mapping of selected package names to their installed versions.
    If a package cannot be imported or its version cannot be discovered,
    the value will be ``"unknown"``.
    """
    packages = [
        "python",
        "numpy",
        "pandas",
        "networkx",
        "scikit-learn",
        "tqdm",
        "requests",
        "goatools",
    ]
    versions: Dict[str, str] = {}
    for pkg in packages:
        if pkg == "python":
            versions["python"] = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
            continue
        try:
            versions[pkg] = importlib_metadata.version(pkg)  # type: ignore[arg-type]
        except Exception:  # pragma: no cover
            versions[pkg] = "unknown"
    return versions

# ----------------------------------------------------------------------
# Public logging helpers.
# ----------------------------------------------------------------------
def log_cli_invocation(args: Any) -> None:
    """
    Log a single entry describing the CLI invocation.

    Parameters
    ----------
    args : argparse.Namespace
        The parsed arguments from ``src.cli.run_pipeline``.  The namespace
        is expected to contain a ``seed`` attribute (int) that represents
        the global random seed used by the pipeline.
    """
    logger = get_logger()
    entry: Dict[str, Any] = {
        "message": "CLI invocation",
        "command": " ".join(sys.argv),
        "versions": _collect_versions(),
    }

    # ``seed`` may be optional – include only when present.
    seed = getattr(args, "seed", None)
    if seed is not None:
        entry["seed"] = seed

    logger.info(entry)

def log_error(message: str, exc_info: Any = None) -> None:
    """
    Log an error message to the pipeline log.  ``exc_info`` can be the
    exception tuple returned by ``sys.exc_info()`` to capture a traceback.
    """
    logger = get_logger()
    entry: Dict[str, Any] = {
        "message": message,
        "error": True,
    }
    logger.error(entry, exc_info=exc_info)