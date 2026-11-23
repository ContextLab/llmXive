"""
Helper utilities for persisting raw backend snapshots.

The integration tests (``tests/test_integration_fetch.py``) expect two
functions:

* ``ensure_data_raw_dir`` – creates the directory that will hold raw JSON
  files.
* ``save_backend_snapshot`` – writes a single snapshot to that directory
  using the same naming convention as ``code.fetcher.fetch_and_save_snapshots``.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

def ensure_data_raw_dir(raw_dir: Path) -> Path:
    """
    Ensure that ``raw_dir`` exists.

    Args:
        raw_dir: Path object pointing to the desired raw data directory.

    Returns:
        The same ``Path`` instance (for convenience).
    """
    raw_dir.mkdir(parents=True, exist_ok=True)
    return raw_dir

def save_backend_snapshot(
    raw_dir: Path, backend_name: str, props: Any
) -> Path:
    """
    Persist a backend's calibration snapshot as JSON.

    The snapshot format matches what ``code.fetcher`` writes:
    ``data/raw/{backend_name}_{YYYYMMDD_HHMMSS}.json``.

    Args:
        raw_dir: Directory where the snapshot should be saved.
        backend_name: Identifier of the backend.
        props: Either a dictionary or an object with a ``to_dict`` method
               representing the backend properties.

    Returns:
        Path to the written JSON file.
    """
    raw_dir = ensure_data_raw_dir(raw_dir)

    now = datetime.now(timezone.utc)
    timestamp_str = now.strftime("%Y%m%d_%H%M%S")
    filename = f"{backend_name}_{timestamp_str}.json"
    filepath = raw_dir / filename

    if hasattr(props, "to_dict"):
        data = props.to_dict()
    else:
        data = props

    # Guarantee required top‑level keys for downstream code.
    if isinstance(data, dict):
        data.setdefault("device_id", backend_name)
        data.setdefault("timestamp", now.isoformat())

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
        logger.info(f"Saved snapshot for {backend_name} to {filepath}")
    except Exception as e:  # pragma: no cover
        logger.error(f"Failed to write snapshot for {backend_name}: {e}")
        raise

    return filepath