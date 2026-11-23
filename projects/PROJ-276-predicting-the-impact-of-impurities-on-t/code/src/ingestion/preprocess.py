"""
Preprocessing module for MgB2 impurity data.

This module handles:
- Merging datasets from Materials Project and SuperCon
- Unit conversion (weight% to atomic%)
- Handling synthesis ranges (midpoint imputation)
- Attaching provenance metadata
"""
import os
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

import pandas as pd
import numpy as np

# Import from project utilities
from code.src.utils.constants import get_atomic_weight
from code.src.utils.data_provenance import generate_provenance_header
from code.src.utils.logging import get_ingestion_logger

logger = get_ingestion_logger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"

# Expected output file
OUTPUT_FILE = DATA_PROCESSED_DIR / "mgb2_clean.csv"

# Input files from T012 and T013
MATERIALS_PROJECT_FILE = DATA_RAW_DIR / "materials_project_mgb2.json"
SUPERCON_FILE = DATA_RAW_DIR / "supercon_mgb2.csv"

def clean_column_name(name: str) -> str:
    """Clean column names by removing special characters and converting to lowercase."""
    name = str(name).lower().strip()
    name = name.replace(" ", "_").replace("-", "_")
    name = "".join(c for c in name if c.isalnum() or c == "_")
    return name

def weight_pct_to_atomic_pct(weight_pct: float, impurity_element: str, host_elements: List[Tuple[str, float]]) -> float:
    """
    Convert weight percentage to atomic percentage.
    
    Args:
        weight_pct: Weight percentage of impurity
        impurity_element: Element symbol of impurity
        host_elements: List of (element, weight_pct) tuples for host material
    
    Returns:
        Atomic percentage of impurity
    """
    if pd.isna(weight_pct) or weight_pct == 0:
        return 0.0
    
    impurity_weight = get_atomic_weight(impurity_element)
    if impurity_weight is None:
        logger.warning(f"Unknown atomic weight for {impurity_element}, returning 0")
        return 0.0
    
    # Calculate moles of impurity
    moles_impurity = weight_pct / impurity_weight
    
    # Calculate moles of host elements
    moles_host = 0.0
    for element, w_pct in host_elements:
        if w_pct > 0:
            atomic_weight = get_atomic_weight(element)
            if atomic_weight:
                moles_host += w_pct / atomic_weight
    
    if moles_host == 0:
        return 0.0
    
    # Atomic percentage = moles_impurity / (moles_impurity + moles_host) * 100
    atomic_pct = (moles_impurity / (moles_impurity + moles_host)) * 100
    return atomic_pct

def handle_synthesis_range(value: Any) -> Optional[float]:
    """
    Handle synthesis range values by extracting midpoint.
    
    Args:
        value: Can be a single number, a string range "min-max", or NaN
    
    Returns:
        Midpoint value or None if not parseable
    """
    if pd.isna(value):
        return None
    
    value_str = str(value).strip()
    
    # Check if it's a range
    if "-" in value_str:
        try:
            parts = value_str.split("-")
            if len(parts) == 2:
                min_val = float(parts[0].strip())
                max_val = float(parts[1].strip())
                return (min_val + max_val) / 2
        except (ValueError, TypeError):
            logger.warning(f"Could not parse range: {value_str}")
            return None
    
    # Try to parse as single value
    try:
        return float(value_str)
    except (ValueError, TypeError):
        logger.warning(f"Could not parse value: {value_str}")
        return None

def convert_impurity_units(df: pd.DataFrame, weight_columns: List[str]) -> pd.DataFrame:
    """
    Convert impurity columns from weight% to atomic%.
    
    Args:
        df: DataFrame with impurity columns
        weight_columns: List of column names containing weight percentages
    
    Returns:
        DataFrame with converted atomic percentages
    """
    df = df.copy()
    
    # MgB2 host composition: Mg (1 atom) and B (2 atoms)
    # Atomic weights: Mg=24.305, B=10.81
    # Weight percentages in pure MgB2:
    # Mg: 24.305 / (24.305 + 2*10.81) * 100 = 52.9%
    # B: 2*10.81 / (24.305 + 2*10.81) * 100 = 47.1%
    host_composition = [("Mg", 52.9), ("B", 47.1)]
    
    for col in weight_columns:
        if col in df.columns:
            # Convert to atomic%
            df[col + "_atomic"] = df[col].apply(
                lambda x: weight_pct_to_atomic_pct(x, col.replace("impurity_", "").replace("_weight", "").replace("_wt", ""), host_composition)
            )
            # Drop original weight column
            df = df.drop(columns=[col])
    
    return df

def merge_datasets(mp_df: pd.DataFrame, supercon_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge Materials Project and SuperCon datasets.
    
    Args:
        mp_df: Materials Project DataFrame
        supercon_df: SuperCon DataFrame
    
    Returns:
        Merged DataFrame
    """
    logger.info(f"Merging datasets: MP ({len(mp_df)} rows), SuperCon ({len(supercon_df)} rows)")
    
    # Standardize column names
    mp_df = mp_df.rename(columns=lambda x: clean_column_name(x))
    supercon_df = supercon_df.rename(columns=lambda x: clean_column_name(x))
    
    # Add source column
    mp_df["source"] = "materials_project"
    supercon_df["source"] = "supercon"
    
    # Identify common columns for merging
    common_cols = set(mp_df.columns) & set(supercon_df.columns)
    
    # Standardize target column names
    target_mapping = {
        "tc": "Tc",
        "critical_temperature": "Tc",
        "superconducting_temperature": "Tc",
        "impurity_c": "impurity_C",
        "carbon_impurity": "impurity_C",
        "impurity_o": "impurity_O",
        "oxygen_impurity": "impurity_O",
        "temp_k": "temp_K",
        "temperature_k": "temp_K",
        "pressure_gpa": "pressure_GPa",
        "pressure": "pressure_GPa"
    }
    
    for df in [mp_df, supercon_df]:
        for old_name, new_name in target_mapping.items():
            if old_name in df.columns and new_name not in df.columns:
                df[new_name] = df[old_name]
                df = df.drop(columns=[old_name])
    
    # Select standard columns
    standard_cols = ["Tc", "impurity_C", "impurity_O", "temp_K", "pressure_GPa", "source"]
    
    # Add impurity atomic columns if they exist
    atomic_cols = [col for col in mp_df.columns if col.endswith("_atomic") or col.endswith("atomic_pct")]
    standard_cols.extend([c for c in atomic_cols if c not in standard_cols])
    
    # Ensure all standard columns exist (fill with NaN if missing)
    for df in [mp_df, supercon_df]:
        for col in standard_cols:
            if col not in df.columns:
                df[col] = np.nan
    
    # Select only standard columns
    mp_df = mp_df[standard_cols]
    supercon_df = supercon_df[standard_cols]
    
    # Concatenate
    merged = pd.concat([mp_df, supercon_df], ignore_index=True)
    
    logger.info(f"Merged dataset: {len(merged)} rows")
    return merged

def filter_valid_entries(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter out entries with missing Tc or impurity data.
    
    Args:
        df: DataFrame to filter
    
    Returns:
        Filtered DataFrame
    """
    logger.info(f"Filtering entries: {len(df)} before filtering")
    
    # Drop rows where Tc is missing
    df = df.dropna(subset=["Tc"])
    
    # Drop rows where all impurity columns are missing
    impurity_cols = [col for col in df.columns if "impurity" in col.lower()]
    if impurity_cols:
        df = df.dropna(subset=impurity_cols, how="all")
    
    logger.info(f"Filtered dataset: {len(df)} rows after filtering")
    return df

def attach_provenance(df: pd.DataFrame, raw_file_headers: List[str]) -> pd.DataFrame:
    """
    Attach provenance metadata to the DataFrame.
    
    Args:
        df: DataFrame to attach provenance to
        raw_file_headers: List of provenance headers from raw files
    
    Returns:
        DataFrame with provenance attached (as metadata attribute)
    """
    timestamp = datetime.utcnow().isoformat() + "Z"
    
    provenance_data = {
        "timestamp": timestamp,
        "version": "1.0",
        "sources": raw_file_headers,
        "processing_steps": [
            "merge_datasets",
            "convert_impurity_units",
            "handle_synthesis_ranges",
            "filter_valid_entries"
        ]
    }
    
    # Create minified JSON header
    provenance_json = generate_provenance_header(
        source=json.dumps(provenance_data["sources"]),
        timestamp=timestamp,
        version=provenance_data["version"]
    )
    
    # Store provenance as DataFrame attribute
    df.attrs["provenance"] = provenance_data
    df.attrs["provenance_header"] = provenance_json
    
    logger.info("Provenance metadata attached")
    return df

def preprocess_datasets() -> pd.DataFrame:
    """
    Main preprocessing function that orchestrates the entire pipeline.
    
    Returns:
        Cleaned and processed DataFrame
    """
    logger.info("Starting preprocessing pipeline")
    
    # Load raw data
    if not MATERIALS_PROJECT_FILE.exists():
        raise FileNotFoundError(f"Materials Project file not found: {MATERIALS_PROJECT_FILE}")
    
    if not SUPERCON_FILE.exists():
        raise FileNotFoundError(f"SuperCon file not found: {SUPERCON_FILE}")
    
    # Load Materials Project data (JSON)
    with open(MATERIALS_PROJECT_FILE, 'r') as f:
        mp_data = json.load(f)
    mp_df = pd.DataFrame(mp_data)
    logger.info(f"Loaded Materials Project data: {len(mp_df)} entries")
    
    # Load SuperCon data (CSV)
    supercon_df = pd.read_csv(SUPERCON_FILE)
    logger.info(f"Loaded SuperCon data: {len(supercon_df)} entries")
    
    # Extract provenance headers from raw files
    raw_file_headers = []
    
    # Check for provenance in Materials Project file
    if hasattr(mp_df, 'attrs') and 'provenance_header' in mp_df.attrs:
        raw_file_headers.append(mp_df.attrs['provenance_header'])
    else:
        # Generate basic provenance for MP
        mp_provenance = generate_provenance_header(
            source=str(MATERIALS_PROJECT_FILE.name),
            timestamp=datetime.utcnow().isoformat() + "Z",
            version="1.0"
        )
        raw_file_headers.append(mp_provenance)
    
    # Check for provenance in SuperCon file
    if hasattr(supercon_df, 'attrs') and 'provenance_header' in supercon_df.attrs:
        raw_file_headers.append(supercon_df.attrs['provenance_header'])
    else:
        # Generate basic provenance for SuperCon
        supercon_provenance = generate_provenance_header(
            source=str(SUPERCON_FILE.name),
            timestamp=datetime.utcnow().isoformat() + "Z",
            version="1.0"
        )
        raw_file_headers.append(supercon_provenance)
    
    # Merge datasets
    merged_df = merge_datasets(mp_df, supercon_df)
    
    # Handle synthesis ranges (midpoint imputation)
    numeric_cols = merged_df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        if "range" in col.lower() or merged_df[col].apply(lambda x: isinstance(x, str) and "-" in str(x)).any():
            merged_df[col] = merged_df[col].apply(handle_synthesis_range)
    
    # Convert impurity units (weight% to atomic%)
    impurity_weight_cols = [col for col in merged_df.columns if "impurity" in col.lower() and ("weight" in col.lower() or "wt" in col.lower())]
    if impurity_weight_cols:
        merged_df = convert_impurity_units(merged_df, impurity_weight_cols)
    
    # Filter valid entries
    cleaned_df = filter_valid_entries(merged_df)
    
    # Attach provenance metadata
    cleaned_df = attach_provenance(cleaned_df, raw_file_headers)
    
    logger.info(f"Preprocessing complete: {len(cleaned_df)} entries in final dataset")
    return cleaned_df

def main():
    """Main entry point for preprocessing."""
    try:
        # Ensure output directory exists
        OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        # Run preprocessing
        df = preprocess_datasets()
        
        # Save to CSV with provenance header
        provenance_header = df.attrs.get("provenance_header", "")
        
        with open(OUTPUT_FILE, 'w') as f:
            if provenance_header:
                f.write(provenance_header + "\n")
            df.to_csv(f, index=False)
        
        logger.info(f"Saved cleaned dataset to {OUTPUT_FILE}")
        print(f"Preprocessing complete. Output: {OUTPUT_FILE}")
        print(f"Total entries: {len(df)}")
        
    except Exception as e:
        logger.error(f"Preprocessing failed: {e}")
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
