"""
Real data loader for the accessibility and usability study.

This module provides ``load_real_data`` which reads all ``*.json`` files
from a given ``data/raw`` directory, validates each session against the
relaxed schema via :func:`validator.validate_session`, and returns a
:class:`pandas.DataFrame` of the valid sessions.

The loader **fails loudly**:
  * Raises ``FileNotFoundError`` if the directory does not exist or contains
    no JSON files.
  * Raises ``FileNotFoundError`` if no JSON file validates against the
    relaxed schema (i.e., no real session data is available).

No synthetic data fallback is performed.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from utils.logger import get_logger
from analysis.validator import validate_session

logger = get_logger(__name__)

def load_real_data(input_dir: str) -> pd.DataFrame:
    """
    Load real session data from ``input_dir``.

    The function scans ``input_dir`` for ``*.json`` files, validates each
    session against the relaxed schema, and aggregates the valid sessions
    into a :class:`pandas.DataFrame`.

    Args:
        input_dir: Path to the directory containing raw session JSON files.

    Returns:
        DataFrame containing all schema‑valid session records.

    Raises:
        FileNotFoundError: If ``input_dir`` does not exist, contains no JSON
            files, or none of the JSON files validate against the schema.
    """
    input_path = Path(input_dir)

    if not input_path.exists():
        raise FileNotFoundError(f"Input directory does not exist: {input_dir}")

    json_files = list(input_path.glob("*.json"))
    if not json_files:
        raise FileNotFoundError(
            f"Real data not found in {input_dir}. Directory contains no JSON files."
        )

    valid_sessions: List[Dict[str, Any]] = []
    invalid_count = 0

    for json_file in json_files:
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                session_data = json.load(f)
        except json.JSONDecodeError as e:
            logger.warning(f"Skipping {json_file.name}: invalid JSON ({e})")
            invalid_count += 1
            continue
        except Exception as e:
            logger.error(f"Unexpected error reading {json_file.name}: {e}")
            invalid_count += 1
            continue

        if validate_session(session_data):
            valid_sessions.append(session_data)
        else:
            logger.warning(f"Session in {json_file.name} failed schema validation.")
            invalid_count += 1

    if not valid_sessions:
        raise FileNotFoundError(
            f"Real data not found in {input_dir}. "
            f"{invalid_count} file(s) were present but none passed validation."
        )

    logger.info(
        f"Loaded {len(valid_sessions)} valid sessions from {input_dir} "
        f"({invalid_count} invalid/skipped)."
    )

    # Convert list of dicts to DataFrame; let pandas infer columns.
    df = pd.DataFrame(valid_sessions)

    return df

def load_real_data_with_fallback(
    input_dir: str,
    fallback_dir: Optional[str] = None,
) -> pd.DataFrame:
    """
    Convenience wrapper that attempts to load from ``input_dir`` and,
    if that fails, tries ``fallback_dir``.

    Args:
        input_dir: Primary input directory.
        fallback_dir: Optional secondary directory.

    Returns:
        DataFrame containing all valid session records.

    Raises:
        FileNotFoundError: If neither directory yields any valid sessions.
    """
    try:
        return load_real_data(input_dir)
    except FileNotFoundError as primary_err:
        if fallback_dir:
            logger.info(
                f"Primary directory failed ({primary_err}); trying fallback {fallback_dir}"
            )
            return load_real_data(fallback_dir)
        else:
            raise

def main() -> None:
    """CLI entry point for data loading."""
    import argparse

    parser = argparse.ArgumentParser(description="Load real session data")
    parser.add_argument(
        "--input-dir",
        type=str,
        default="data/raw",
        help="Directory containing raw session JSON files",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/processed/raw_sessions.csv",
        help="Output CSV file path",
    )

    args = parser.parse_args()

    logger.info(f"Attempting to load real data from {args.input_dir}")

    df = load_real_data(args.input_dir)
    df.to_csv(args.output, index=False)
    logger.info(f"Saved {len(df)} sessions to {args.output}")

if __name__ == "__main__":
    main()