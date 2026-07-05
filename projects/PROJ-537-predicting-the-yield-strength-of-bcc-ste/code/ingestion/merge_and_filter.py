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

# Constants for structure filtering (BCC = Space Group 229)
BCC_SPACE_GROUP = 229

def parse_range_value(value: Any, column_name: str = "unknown") -> Tuple[Optional[float], bool]:
    """
    Parse a value that might be a single number, a string range (e.g., "200-250"),
    or other formats. Returns (midpoint, is_range_flag).
    
    If the value is already a number, returns (value, False).
    If the value is a range string, returns (midpoint, True).
    If parsing fails, returns (None, False).
    """
    if pd.isna(value) or value is None:
        return None, False
    
    # If it's already a numeric type
    if isinstance(value, (int, float)):
        return float(value), False
    
    # Convert to string for parsing
    str_val = str(value).strip()
    if not str_val:
        return None, False
    
    # Check for range format: "200-250", "200 to 250", "200..250", etc.
    # Common patterns: "A-B", "A to B", "A..B", "A-B " (with spaces)
    range_patterns = [
        r'^([\d.]+)\s*[-–—]\s*([\d.]+)$',  # A-B (various dash types)
        r'^([\d.]+)\s+to\s+([\d.]+)$',      # A to B
        r'^([\d.]+)\.\.([\d.]+)$',          # A..B
        r'^([\d.]+)\s*\\s*\s*([\d.]+)$',    # A\B or similar
    ]
    
    for pattern in range_patterns:
        match = re.match(pattern, str_val, re.IGNORECASE)
        if match:
            try:
                low = float(match.group(1))
                high = float(match.group(2))
                if low <= high:
                    midpoint = (low + high) / 2.0
                    logger.info(f"Parsed range '{str_val}' in column '{column_name}' as midpoint {midpoint}")
                    return midpoint, True
                else:
                    logger.warning(f"Invalid range order in '{str_val}': low ({low}) > high ({high})")
                    return None, False
            except ValueError:
                logger.warning(f"Could not parse numeric values from range string '{str_val}'")
                return None, False
    
    # Try to parse as a single number
    try:
        return float(str_val), False
    except ValueError:
        logger.warning(f"Could not parse value '{str_val}' as a number or range")
        return None, False

def load_experimental_data(filepath: Optional[Path] = None) -> pd.DataFrame:
    """Load experimental data from CSV/JSON."""
    if filepath is None:
        filepath = Path(CONFIG.EXPERIMENTAL_DATA_PATH)
    
    if not filepath.exists():
        raise FileNotFoundError(f"Experimental data file not found: {filepath}")
    
    logger.info(f"Loading experimental data from {filepath}")
    
    suffix = filepath.suffix.lower()
    if suffix == '.csv':
        df = pd.read_csv(filepath)
    elif suffix == '.json':
        df = pd.read_json(filepath)
    else:
        raise ValueError(f"Unsupported file format: {suffix}")
    
    logger.info(f"Loaded {len(df)} rows of experimental data")
    return df

def load_dft_data(filepath: Optional[Path] = None) -> pd.DataFrame:
    """Load DFT data from CSV/JSON."""
    if filepath is None:
        filepath = Path(CONFIG.DFT_DATA_PATH)
    
    if not filepath.exists():
        raise FileNotFoundError(f"DFT data file not found: {filepath}")
    
    logger.info(f"Loading DFT data from {filepath}")
    
    suffix = filepath.suffix.lower()
    if suffix == '.csv':
        df = pd.read_csv(filepath)
    elif suffix == '.json':
        df = pd.read_json(filepath)
    else:
        raise ValueError(f"Unsupported file format: {suffix}")
    
    logger.info(f"Loaded {len(df)} rows of DFT data")
    return df

def filter_bcc_structure(df: pd.DataFrame, space_group_col: str = "space_group") -> pd.DataFrame:
    """Filter dataframe to keep only BCC structures (Space Group 229)."""
    logger.info(f"Filtering for BCC structure (Space Group {BCC_SPACE_GROUP})")
    
    if space_group_col not in df.columns:
        raise ValueError(f"Space group column '{space_group_col}' not found in dataframe")
    
    bcc_df = df[df[space_group_col] == BCC_SPACE_GROUP].copy()
    logger.info(f"Found {len(bcc_df)} BCC samples out of {len(df)} total")
    
    if len(bcc_df) == 0:
        logger.warning("No BCC samples found after filtering!")
    
    return bcc_df

def merge_datasets(exp_df: pd.DataFrame, dft_df: pd.DataFrame, 
                   on: List[str] = ["material_id", "composition"]) -> pd.DataFrame:
    """Merge experimental and DFT datasets on common keys."""
    logger.info(f"Merging datasets on keys: {on}")
    
    # Ensure common columns exist
    for key in on:
        if key not in exp_df.columns or key not in dft_df.columns:
            raise ValueError(f"Merge key '{key}' not found in both datasets")
    
    merged = pd.merge(exp_df, dft_df, on=on, how='inner')
    logger.info(f"Merged dataset has {len(merged)} rows")
    
    return merged

def handle_nulls(df: pd.DataFrame, columns_to_parse: List[str] = None) -> pd.DataFrame:
    """
    Handle null values and parse range values in specified columns.
    Adds '_is_range' flags for columns that had range values parsed.
    """
    if columns_to_parse is None:
        # Default columns that might contain ranges
        columns_to_parse = ["yield_strength_MPa", "shear_modulus_GPa", "bulk_modulus_GPa"]
    
    df = df.copy()
    range_flags_added = []
    
    for col in columns_to_parse:
        if col in df.columns:
            # Parse ranges and create flags
            new_values = []
            is_range_flags = []
            
            for val in df[col]:
                parsed_val, is_range = parse_range_value(val, col)
                new_values.append(parsed_val)
                is_range_flags.append(is_range)
            
            df[col] = new_values
            
            # Add flag column if any ranges were found
            if any(is_range_flags):
                flag_col = f"{col}_is_range"
                df[flag_col] = is_range_flags
                range_flags_added.append(flag_col)
                logger.info(f"Added range flag column: {flag_col} ({sum(is_range_flags)} ranges found)")
            else:
                # Ensure the flag column exists even if all False, for consistency
                flag_col = f"{col}_is_range"
                df[flag_col] = False
                range_flags_added.append(flag_col)
    
    # Drop rows where critical columns are still null after parsing
    critical_cols = ["yield_strength_MPa", "shear_modulus_GPa"]
    existing_critical = [c for c in critical_cols if c in df.columns]
    
    if existing_critical:
        initial_count = len(df)
        df = df.dropna(subset=existing_critical)
        dropped_count = initial_count - len(df)
        if dropped_count > 0:
            logger.warning(f"Dropped {dropped_count} rows due to null values in critical columns: {existing_critical}")
    
    return df

def validate_merged_dataset(df: pd.DataFrame, min_rows: int = 20) -> bool:
    """Validate that merged dataset meets minimum requirements."""
    logger.info(f"Validating merged dataset (min_rows={min_rows})")
    
    if len(df) < min_rows:
        logger.error(f"Dataset has {len(df)} rows, which is less than required {min_rows}")
        return False
    
    # Check for critical columns
    critical_cols = ["yield_strength_MPa", "shear_modulus_GPa"]
    for col in critical_cols:
        if col not in df.columns:
            logger.error(f"Critical column '{col}' missing from dataset")
            return False
        if df[col].isna().any():
            logger.error(f"Critical column '{col}' contains null values")
            return False
    
    logger.info(f"Validation passed: {len(df)} rows, all critical columns present and non-null")
    return True

def save_merged_dataset(df: pd.DataFrame, output_path: Optional[Path] = None) -> Path:
    """Save merged dataset to CSV and log provenance."""
    if output_path is None:
        output_path = Path(CONFIG.INTERMEDIATE_DATA_PATH) / "merged.csv"
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Saving merged dataset to {output_path}")
    df.to_csv(output_path, index=False)
    
    # Log provenance
    log_provenance_event(
        event_type="dataset_saved",
        details={
            "path": str(output_path),
            "rows": len(df),
            "columns": list(df.columns),
            "range_flags": [col for col in df.columns if col.endswith("_is_range")]
        }
    )
    
    return output_path

def main():
    """Main entry point for the merge and filter pipeline."""
    try:
        # Load data
        exp_df = load_experimental_data()
        dft_df = load_dft_data()
        
        # Filter for BCC
        exp_bcc = filter_bcc_structure(exp_df)
        dft_bcc = filter_bcc_structure(dft_df)
        
        # Merge
        merged = merge_datasets(exp_bcc, dft_bcc)
        
        # Handle nulls and parse ranges
        processed = handle_nulls(merged)
        
        # Validate
        if not validate_merged_dataset(processed):
            logger.error("Dataset validation failed. Halting pipeline.")
            sys.exit(1)
        
        # Save
        output_path = save_merged_dataset(processed)
        logger.info(f"Pipeline complete. Output saved to {output_path}")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()