"""
Updated merge_and_filter module – minor refactor to use the canonical
``CONFIG.MERGED_DATA_PATH`` constant for the output location.
The rest of the logic is unchanged from the original implementation.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any

import re
import pandas as pd

from config import CONFIG
from utils.logging import get_logger, log_provenance_event

logger = get_logger(__name__)

BCC_SPACE_GROUP = 229

# ----------------------------------------------------------------------
# Helper functions (parse_range_value, load_experimental_data, etc.)
# ----------------------------------------------------------------------
def parse_range_value(value: Any, column_name: str = "unknown") -> Tuple[Optional[float], bool]:
    if pd.isna(value) or value is None:
        return None, False
    if isinstance(value, (int, float)):
        return float(value), False
    str_val = str(value).strip()
    if not str_val:
        return None, False
    range_patterns = [
        r'^([\d.]+)\s*[-–—]\s*([\d.]+)$',
        r'^([\d.]+)\s+to\s+([\d.]+)$',
        r'^([\d.]+)\.\.([\d.]+)$',
    ]
    for pattern in range_patterns:
        match = re.match(pattern, str_val, re.IGNORECASE)
        if match:
            try:
                low = float(match.group(1))
                high = float(match.group(2))
                if low <= high:
                    midpoint = (low + high) / 2.0
                    logger.info(f"Parsed range '{str_val}' as {midpoint}")
                    return midpoint, True
                else:
                    logger.warning(f"Invalid range order in '{str_val}'")
                    return None, False
            except ValueError:
                logger.warning(f"Could not parse numbers from '{str_val}'")
                return None, False
    try:
        return float(str_val), False
    except ValueError:
        logger.warning(f"Unparseable value '{str_val}'")
        return None, False

def load_experimental_data(filepath: Optional[Path] = None) -> pd.DataFrame:
    if filepath is None:
        filepath = Path(CONFIG.EXPERIMENTAL_DATA_PATH)
    if not filepath.is_file():
        raise FileNotFoundError(f"Experimental data file not found: {filepath}")
    logger.info(f"Loading experimental data from {filepath}")
    if filepath.suffix.lower() == ".csv":
        return pd.read_csv(filepath)
    elif filepath.suffix.lower() == ".json":
        return pd.read_json(filepath)
    else:
        raise ValueError(f"Unsupported experimental data format: {filepath.suffix}")

def load_dft_data(filepath: Optional[Path] = None) -> pd.DataFrame:
    if filepath is None:
        filepath = Path(CONFIG.RAW_DFT_PATH)
    if not filepath.is_file():
        raise FileNotFoundError(f"DFT data file not found: {filepath}")
    logger.info(f"Loading DFT data from {filepath}")
    if filepath.suffix.lower() == ".csv":
        return pd.read_csv(filepath)
    elif filepath.suffix.lower() == ".json":
        return pd.read_json(filepath)
    else:
        raise ValueError(f"Unsupported DFT data format: {filepath.suffix}")

def filter_bcc_structure(df: pd.DataFrame, space_group_col: str = "space_group") -> pd.DataFrame:
    if space_group_col not in df.columns:
        raise ValueError(f"Space group column '{space_group_col}' missing")
    bcc_df = df[df[space_group_col] == BCC_SPACE_GROUP].copy()
    logger.info(f"Filtered BCC: {len(bcc_df)} of {len(df)} rows")
    return bcc_df

def merge_datasets(exp_df: pd.DataFrame, dft_df: pd.DataFrame,
                   on: List[str] = ["material_id", "composition"]) -> pd.DataFrame:
    for key in on:
        if key not in exp_df.columns or key not in dft_df.columns:
            raise ValueError(f"Merge key '{key}' missing from one of the datasets")
    merged = pd.merge(exp_df, dft_df, on=on, how="inner")
    logger.info(f"Merged dataset has {len(merged)} rows")
    return merged

def handle_nulls(df: pd.DataFrame, columns_to_parse: List[str] = None) -> pd.DataFrame:
    if columns_to_parse is None:
        columns_to_parse = ["yield_strength_MPa", "shear_modulus_GPa", "bulk_modulus_GPa"]
    df = df.copy()
    for col in columns_to_parse:
        if col in df.columns:
            parsed_vals = []
            flags = []
            for val in df[col]:
                parsed, is_range = parse_range_value(val, col)
                parsed_vals.append(parsed)
                flags.append(is_range)
            df[col] = parsed_vals
            flag_col = f"{col}_is_range"
            df[flag_col] = flags
    critical = ["yield_strength_MPa", "shear_modulus_GPa"]
    df = df.dropna(subset=[c for c in critical if c in df.columns])
    return df

def validate_merged_dataset(df: pd.DataFrame, min_rows: int = 20) -> bool:
    if len(df) < min_rows:
        logger.error(f"Dataset has {len(df)} rows (< {min_rows})")
        return False
    critical = ["yield_strength_MPa", "shear_modulus_GPa"]
    for col in critical:
        if col not in df.columns or df[col].isna().any():
            logger.error(f"Critical column '{col}' missing or contains nulls")
            return False
    logger.info("Merged dataset validation passed")
    return True

def save_merged_dataset(df: pd.DataFrame, output_path: Optional[Path] = None) -> Path:
    if output_path is None:
        output_path = Path(CONFIG.MERGED_DATA_PATH)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved merged dataset to {output_path}")
    log_provenance_event("dataset_saved", path=str(output_path), rows=len(df))
    return output_path

def main():
    """
    Entry point used by the ingestion pipeline.
    """
    try:
        exp_df = load_experimental_data()
        dft_df = load_dft_data()
        exp_bcc = filter_bcc_structure(exp_df)
        dft_bcc = filter_bcc_structure(dft_df)
        merged = merge_datasets(exp_bcc, dft_bcc)
        processed = handle_nulls(merged)
        if not validate_merged_dataset(processed):
            logger.error("Merged dataset failed validation – terminating.")
            sys.exit(1)
        save_merged_dataset(processed)
    except Exception as exc:
        logger.error(f"Merge and filter failed: {exc}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
