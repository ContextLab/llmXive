import sys
import os
import json
import logging
import argparse
from pathlib import Path
import pandas as pd
from typing import List, Tuple

logger = logging.getLogger(__name__)

DESCRIPTOR_NAMES_FILENAME = "descriptor_names.json"

def _find_descriptor_names_json(parquet_path: Path) -> Path:
    """
    Locate the descriptor_names.json file that governs the expected columns.

    Resolution order:
    1. <parquet_dir>/descriptor_names.json  (i.e. data/processed/descriptor_names.json)
    2. <parquet_dir>/../processed/descriptor_names.json (fallback for nested layouts)
    3. <project_root>/data/processed/descriptor_names.json
    """
    candidates = [
        parquet_path.parent / DESCRIPTOR_NAMES_FILENAME,
        parquet_path.parent.parent / "processed" / DESCRIPTOR_NAMES_FILENAME,
        parquet_path.parent.parent.parent / "data" / "processed" / DESCRIPTOR_NAMES_FILENAME,
    ]
    for cand in candidates:
        if cand.is_file():
            return cand
    return candidates[0]  # return default so caller can report a clear error

def _load_descriptor_names_json(json_path: Path) -> List[str]:
    """
    Load descriptor names from a JSON file.
    The JSON is expected to be a list of descriptor name strings.
    """
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list) or not all(isinstance(x, str) for x in data):
        raise ValueError(
            f"Descriptor names JSON at {json_path} must be a list of strings"
        )
    if len(data) == 0:
        raise ValueError(f"Descriptor names JSON at {json_path} is empty")
    return data

def validate_processed_descriptors(filepath: str, expected_columns: int = None) -> Tuple[bool, str]:
    """
    Validate the processed descriptors parquet file.

    The expected descriptor columns are derived dynamically from
    data/processed/descriptor_names.json (resolved relative to the parquet
    file location), NOT from a hard-coded list.

    Args:
        filepath: Path to the descriptors parquet file
        expected_columns: Expected number of columns (smiles + target + flags
            + descriptors). Optional; if None, derived from the JSON.

    Returns:
        Tuple of (success: bool, message: str)
    """
    parquet_path = Path(filepath)
    if not parquet_path.exists():
        return False, f"Descriptors parquet file not found: {parquet_path}"

    try:
        df = pd.read_parquet(parquet_path)
    except Exception as e:
        return False, f"Failed to read parquet file: {e}"

    required = {"smiles", "target", "stereochemistry_flag", "flexible_flag"}
    missing = required - set(df.columns)
    if missing:
        return False, f"Missing required columns: {sorted(missing)}"

    # Load descriptor name list to verify descriptor columns (dynamic)
    descriptor_names_path = _find_descriptor_names_json(parquet_path)
    if not descriptor_names_path.is_file():
        return False, f"Descriptor names JSON not found at {descriptor_names_path}"
    try:
        descriptor_names = _load_descriptor_names_json(descriptor_names_path)
    except ValueError as e:
        return False, str(e)

    # Expected descriptor columns are prefixed with 'desc_'
    expected_desc_cols = {f"desc_{name}" for name in descriptor_names}
    actual_desc_cols = {c for c in df.columns if c.startswith("desc_")}
    if expected_desc_cols != actual_desc_cols:
        missing_desc = sorted(expected_desc_cols - actual_desc_cols)
        extra_desc = sorted(actual_desc_cols - expected_desc_cols)
        return (
            False,
            "Descriptor columns mismatch. "
            f"Expected {len(expected_desc_cols)} descriptor columns, "
            f"got {len(actual_desc_cols)}. "
            f"Missing: {missing_desc[:10]}{'...' if len(missing_desc) > 10 else ''} "
            f"Unexpected: {extra_desc[:10]}{'...' if len(extra_desc) > 10 else ''}",
        )

    # Explicitly forbidden columns (TPSA / SMARTS-derived)
    forbidden = [c for c in df.columns if "TPSA" in c.upper()]
    if forbidden:
        return False, f"Forbidden TPSA-related columns present: {forbidden}"

    # Expected total column count: derived dynamically unless overridden
    if expected_columns is None:
        expected_columns = len(required) + len(expected_desc_cols)
    if df.shape[1] != expected_columns:
        return (
            False,
            f"Column count mismatch: expected {expected_columns}, got {df.shape[1]}",
        )

    # Basic sanity checks on the target column
    try:
        numeric_target = df["target"].astype(float)
        if numeric_target.isna().all():
            return False, "Target column is entirely NaN"
    except (TypeError, ValueError):
        return False, "Target column is not numeric"

    return True, (
        f"Descriptor file validation passed: {len(df)} rows, "
        f"{len(actual_desc_cols)} descriptor columns match "
        f"{descriptor_names_path}."
    )

def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    parser = argparse.ArgumentParser(description="Validate processed descriptors")
    parser.add_argument("filepath", help="Path to descriptors.parquet")
    parser.add_argument(
        "--expected-columns",
        type=int,
        default=None,
        help="Expected total column count (optional; derived from descriptor_names.json if omitted)",
    )
    args = parser.parse_args()
    success, msg = validate_processed_descriptors(args.filepath, args.expected_columns)
    if success:
        logger.info(msg)
        print(msg)
        sys.exit(0)
    else:
        logger.error(msg)
        print(msg, file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
