import sys
import os
import logging
import argparse
from pathlib import Path
import pandas as pd
from typing import List, Tuple

logger = logging.getLogger(__name__)

def _load_descriptor_names_json(json_path: Path) -> List[str]:
    """
    Load descriptor names from a JSON file.
    The JSON is expected to be a list of descriptor name strings.
    """
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)

def validate_processed_descriptors(filepath: str, expected_columns: int = None) -> Tuple[bool, str]:
    """
    Validate the processed descriptors parquet file.

    Args:
        filepath: Path to the descriptors parquet file
        expected_columns: Expected number of columns (smiles + target + descriptors)

    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        df = pd.read_parquet(filepath)
    except Exception as e:
        return False, f"Failed to read parquet file: {e}"

    required = {"smiles", "target", "stereochemistry_flag", "flexible_flag"}
    missing = required - set(df.columns)
    if missing:
        return False, f"Missing required columns: {missing}"

    # Load descriptor name list to verify descriptor columns
    descriptor_names_path = Path(filepath).parents[1] / "descriptor_names.json"
    if not descriptor_names_path.exists():
        return False, f"Descriptor names JSON not found at {descriptor_names_path}"
    descriptor_names = _load_descriptor_names_json(descriptor_names_path)

    # Expected descriptor columns are prefixed with 'desc_'
    expected_desc_cols = {f"desc_{name}" for name in descriptor_names}
    actual_desc_cols = {c for c in df.columns if c.startswith("desc_")}
    if expected_desc_cols != actual_desc_cols:
        return (
            False,
            f"Descriptor columns mismatch. Expected {len(expected_desc_cols)}, got {len(actual_desc_cols)}",
        )

    if expected_columns is not None and df.shape[1] != expected_columns:
        return (
            False,
            f"Column count mismatch: expected {expected_columns}, got {df.shape[1]}",
        )

    return True, "Descriptor file validation passed."

def main():
    parser = argparse.ArgumentParser(description="Validate processed descriptors")
    parser.add_argument("filepath", help="Path to descriptors.parquet")
    parser.add_argument(
        "--expected-columns",
        type=int,
        default=None,
        help="Expected total column count (optional)",
    )
    args = parser.parse_args()
    success, msg = validate_processed_descriptors(args.filepath, args.expected_columns)
    if success:
        logger.info(msg)
        sys.exit(0)
    else:
        logger.error(msg)
        sys.exit(1)

if __name__ == "__main__":
    main()
