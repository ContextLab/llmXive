"""Pipeline utilities: logging, seeding, checksums, and cascade loading.

This module implements the shared infrastructure for the misinformation
cascade modeling pipeline, including the JSON edge-list cascade loader
(`load_cascade`) which validates required columns, normalizes timestamps
to UTC, and enforces the per-cascade node limit. Cascades exceeding the
node limit are skipped and their identifiers are appended to
`skipped_cascades.log` for later manual inspection (task T014).
"""

import hashlib
import json
import logging
import os
import random
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, List, Optional, Tuple

import pandas as pd

DEFAULT_NODE_LIMIT = 2000
REQUIRED_COLUMNS = ("node_id", "timestamp", "cascade_id")

__all__ = [
    "setup_logger",
    "set_global_seed",
    "compute_checksum",
    "normalize_timestamp",
    "load_cascade",
    "validate_all_cascades",
    "validate_features",
    "main",
]


def setup_logger(
    name: str, log_file: Optional[str] = None, level: int = logging.INFO
) -> logging.Logger:
    """Set up a logger with optional file output.

    Args:
        name: Logger name (typically ``__name__``).
        log_file: Optional path to a log file; the parent directory is
            created if it does not exist.
        level: Logging level.

    Returns:
        A configured ``logging.Logger`` instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    if logger.handlers:
        return logger
    formatter = logging.Formatter(
        "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
    )
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    if log_file is not None:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    logger.propagate = False
    return logger


def set_global_seed(seed: int) -> None:
    """Pin random seeds for reproducibility.

    Args:
        seed: The random seed to apply to the ``random`` and ``numpy``
            random number generators.
    """
    random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    try:
        import numpy as np

        np.random.seed(seed)
    except ImportError:  # pragma: no cover - numpy is a hard dependency
        pass


def compute_checksum(path: str) -> str:
    """Compute SHA-256 checksum of a file.

    Args:
        path: Path to the file.

    Returns:
        Hexadecimal SHA-256 digest of the file contents.
    """
    sha256 = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def normalize_timestamp(ts: Any) -> datetime:
    """Normalize a timestamp string/object to a UTC datetime.

    Naive timestamps are assumed to be UTC (a warning is logged).
    Timezone-aware timestamps are converted to UTC.

    Args:
        ts: A timestamp as an ISO-format string, epoch number, or
            ``datetime`` object.

    Returns:
        A timezone-aware ``datetime`` in UTC.

    Raises:
        ValueError: If the timestamp cannot be parsed.
    """
    logger = logging.getLogger(__name__)
    if isinstance(ts, datetime):
        dt = ts
    elif isinstance(ts, (int, float)):
        dt = datetime.fromtimestamp(float(ts), tz=timezone.utc)
    else:
        text = str(ts).strip()
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        try:
            dt = datetime.fromisoformat(text)
        except ValueError as exc:
            raise ValueError(f"Unparseable timestamp: {ts!r}") from exc
    if dt.tzinfo is None:
        logger.warning(
            "Timestamp %s has no timezone info; assuming UTC.", ts
        )
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _cascade_records(raw: Any) -> List[dict]:
    """Extract a list of node records from a parsed JSON cascade document."""
    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict):
        for key in ("nodes", "edges", "records", "data"):
            value = raw.get(key)
            if isinstance(value, list):
                return value
        raise ValueError(
            "JSON cascade document must be a list of records or a dict "
            "with a 'nodes'/'edges' list."
        )
    raise ValueError("Unsupported JSON cascade structure.")


def _log_skipped_cascade(
    cascade_id: str,
    file_path: str,
    node_count: int,
    node_limit: int,
    skipped_log_path: Optional[str],
    logger: logging.Logger,
) -> None:
    """Append a skipped cascade identifier to the skipped-cascades log."""
    message = (
        f"cascade_id={cascade_id} file={file_path} "
        f"nodes={node_count} limit={node_limit} "
        f"reason=node_limit_exceeded"
    )
    logger.warning("Skipping oversized cascade: %s", message)
    if skipped_log_path:
        log_path = Path(skipped_log_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(message + "\n")


def load_cascade(
    file_path: str,
    node_limit: int = DEFAULT_NODE_LIMIT,
    logger: Optional[logging.Logger] = None,
    skipped_log_path: Optional[str] = None,
) -> Optional[pd.DataFrame]:
    """Load a cascade from a JSON edge-list file.

    Validates required columns, normalizes timestamps to UTC, and
    enforces the node limit. Oversized cascades are skipped and their
    identifiers are logged to ``skipped_cascades.log``.

    Args:
        file_path: Path to the JSON file containing the cascade.
        node_limit: Maximum allowed number of unique nodes (default 2000).
        logger: Logger instance. If None, a default logger is created.
        skipped_log_path: Path to the log file for skipped cascades.

    Returns:
        A pandas DataFrame with the cascade data if valid and within
        limits, otherwise None.
    """
    if logger is None:
        logger = setup_logger(__name__)

    path = Path(file_path)
    if not path.exists():
        logger.error("Cascade file not found: %s", file_path)
        raise FileNotFoundError(f"Cascade file not found: {file_path}")

    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except json.JSONDecodeError as exc:
        logger.error("Invalid JSON in %s: %s", file_path, exc)
        raise ValueError(f"Invalid JSON in {file_path}: {exc}") from exc

    records = _cascade_records(raw)
    if not records:
        logger.error("Cascade file %s contains no records.", file_path)
        raise ValueError(f"Cascade file {file_path} contains no records.")

    df = pd.DataFrame(records)

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        logger.error(
            "Cascade file %s is missing required columns: %s",
            file_path,
            ", ".join(missing),
        )
        raise ValueError(
            f"Cascade file {file_path} is missing required columns: "
            f"{', '.join(missing)}"
        )

    cascade_id = str(df["cascade_id"].iloc[0])

    # Enforce the node limit (task T014): count unique node identifiers
    # and skip (return None) for oversized cascades, logging their IDs.
    node_count = df["node_id"].nunique()
    if node_count > node_limit:
        _log_skipped_cascade(
            cascade_id,
            str(file_path),
            int(node_count),
            node_limit,
            skipped_log_path,
            logger,
        )
        return None

    try:
        df["timestamp"] = df["timestamp"].apply(normalize_timestamp)
    except ValueError as exc:
        logger.error(
            "Timestamp validation failed for cascade %s in %s: %s",
            cascade_id,
            file_path,
            exc,
        )
        raise

    logger.info(
        "Loaded cascade %s from %s (%d unique nodes, within limit %d).",
        cascade_id,
        file_path,
        node_count,
        node_limit,
    )
    return df


def validate_all_cascades(
    data_dir: str,
    node_limit: int = DEFAULT_NODE_LIMIT,
    skipped_log_path: str = "skipped_cascades.log",
) -> Tuple[List[pd.DataFrame], int]:
    """Load and validate all JSON cascade files in a directory.

    Args:
        data_dir: Directory containing JSON cascade files.
        node_limit: Maximum allowed number of nodes per cascade.
        skipped_log_path: Path to the log recording skipped cascades.

    Returns:
        A tuple of (list of valid DataFrames, count of skipped files).
    """
    logger = setup_logger(__name__)
    valid: List[pd.DataFrame] = []
    skipped = 0
    directory = Path(data_dir)
    if not directory.exists():
        raise FileNotFoundError(f"Data directory not found: {data_dir}")

    json_files = sorted(directory.glob("*.json"))
    if not json_files:
        logger.warning("No JSON cascade files found in %s.", data_dir)
        return valid, skipped

    for json_file in json_files:
        try:
            df = load_cascade(
                str(json_file),
                node_limit=node_limit,
                logger=logger,
                skipped_log_path=skipped_log_path,
            )
        except (ValueError, FileNotFoundError) as exc:
            logger.error("Failed to load %s: %s", json_file, exc)
            skipped += 1
            continue
        if df is None:
            skipped += 1
        else:
            valid.append(df)

    logger.info(
        "Validated %d cascades, skipped %d (see %s).",
        len(valid),
        skipped,
        skipped_log_path,
    )
    return valid, skipped


def validate_features(df: pd.DataFrame) -> bool:
    """Validate that the features DataFrame has no missing values.

    Args:
        df: The features DataFrame.

    Returns:
        True if valid (no missing values), False otherwise.
    """
    logger = setup_logger(__name__)
    if df is None or df.empty:
        logger.error("Features DataFrame is empty.")
        return False
    if df.isnull().values.any():
        missing = df.columns[df.isnull().any()].tolist()
        logger.error("Features DataFrame has missing values in: %s", missing)
        return False
    return True


def main() -> int:
    """CLI entry point for utils module (example usage)."""
    logging.basicConfig(level=logging.INFO)
    logger = setup_logger(__name__)
    set_global_seed(12345)
    data_dir = sys.argv[1] if len(sys.argv) > 1 else "data/raw"
    skipped_log = (
        sys.argv[2] if len(sys.argv) > 2 else "skipped_cascades.log"
    )
    try:
        valid, skipped = validate_all_cascades(
            data_dir, skipped_log_path=skipped_log
        )
    except FileNotFoundError as exc:
        logger.error("%s", exc)
        return 1
    logger.info(
        "Loaded %d valid cascades; %d skipped. Skipped log: %s",
        len(valid),
        skipped,
        skipped_log,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
