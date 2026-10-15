"""
Utility functions for the project.

This module provides minimal logging utilities required by the pipeline
without pulling in heavy dependencies (e.g., pyarrow) that caused import
conflicts in earlier runs.
"""

import logging
from pathlib import Path
from llmxive_toolkit import get_logger as llm_get_logger

# ----------------------------------------------------------------------
# Logging helpers
# ----------------------------------------------------------------------
def setup_logging(level: int = logging.INFO) -> None:
    """
    Configure a basic root logger. This is called at the start of the
    pipeline (e.g., in ``code/main.py``) to ensure that log messages are
    emitted to stdout.

    Args:
        level: Logging level for the root logger (default: INFO).
    """
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

def get_logger(name: str) -> logging.Logger:
    """
    Return a logger instance. Internally we delegate to the
    ``llmxive_toolkit.get_logger`` implementation so that log files are
    created in the standard ``logs/`` directory if the toolkit is
    configured to do so.

    Args:
        name: Name of the logger (typically ``__name__``).

    Returns:
        A configured ``logging.Logger`` instance.
    """
    return llm_get_logger(name)

# ----------------------------------------------------------------------
# Placeholder helpers used by other modules (no‑op implementations)
# ----------------------------------------------------------------------
def write_parquet(df, path: Path) -> None:
    """
    Write a DataFrame to Parquet. This thin wrapper isolates the
    ``pandas`` call and keeps the signature stable for modules that
    expect it.

    Args:
        df: pandas.DataFrame to write.
        path: Destination pathlib.Path (the parent directory is created
              automatically).
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)

def compute_sha256(path: Path) -> str:
    """
    Compute the SHA‑256 checksum of a file.

    Args:
        path: Path to the file.

    Returns:
        Hex‑encoded SHA‑256 digest.
    """
    import hashlib

    sha256 = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def update_state_yaml(file_path: Path, checksum: str) -> None:
    """
    Update ``state.yaml`` with a new artifact entry.  The function is a
    very small wrapper around the project's ``state_manager`` utilities
    (which are not required for the thin pipeline).  If the state file
    does not exist it is created.

    Args:
        file_path: Path to the artifact that was just written.
        checksum: SHA‑256 checksum of the artifact.
    """
    import yaml
    from datetime import datetime

    state_path = Path(__file__).parents[2] / "state.yaml"
    state = {}
    if state_path.exists():
        with state_path.open("r") as f:
            state = yaml.safe_load(f) or {}

    artifact_entry = {
        "path": str(file_path.relative_to(state_path.parent)),
        "checksum": checksum,
        "updated_at": datetime.utcnow().isoformat() + "Z",
    }

    state.setdefault("artifact_hashes", {})
    state["artifact_hashes"][artifact_entry["path"]] = artifact_entry

    with state_path.open("w") as f:
        yaml.safe_dump(state, f)
