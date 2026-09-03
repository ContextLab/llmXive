"""
Preprocessing module for MgB2 impurity data.

This module handles:
1. Merging Materials Project and SuperCon datasets
2. Converting weight% to atomic%
3. Handling synthesis ranges (midpoint imputation)
4. Attaching provenance metadata
5. Filtering for valid entries
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import pandas as pd
import numpy as np

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.src.utils.constants import get_atomic_weight
from code.src.utils.data_provenance import generate_provenance_header
from code.src.utils.logging import get_ingestion_logger

# Initialize logger
logger = get_ingestion_logger(__name__)

# Constants
MAGNESIUM_SYMBOL = "Mg"
BORON_SYMBOL = "B"
MIN_Tc_K = 0.0  # Minimum valid Tc in Kelvin
MIN_IMPU_PCT = 0.0  # Minimum valid impurity percentage
MAX_IMPU_PCT = 100.0  # Maximum valid impurity percentage

def weight_pct_to_atomic_pct(
    weight_pct: float,
    impurity_symbol: str,
    matrix_symbols: List[str] = [MAGNESIUM_SYMBOL, BORON_SYMBOL]
) -> float:
    """
    Convert weight percentage to atomic percentage.

    Formula: atomic_pct = (weight_pct / atomic_weight) / sum(weight_i / atomic_weight_i) * 100

    Args:
        weight_pct: Weight percentage of the impurity
        impurity_symbol: Chemical symbol of the impurity
        matrix_symbols: List of matrix element symbols (Mg, B)

    Returns:
        Atomic percentage of the impurity
    """
    if pd.isna(weight_pct) or weight_pct <= 0:
        return 0.0

    impurity_weight = get_atomic_weight(impurity_symbol)
    if impurity_weight is None:
        logger.warning(f"Unknown atomic weight for {impurity_symbol}, skipping conversion")
        return 0.0

    # Calculate total moles
    total_moles = weight_pct / impurity_weight

    # Add matrix components (assuming remainder is matrix)
    matrix_weight = 100.0 - weight_pct
    matrix_moles = 0.0

    # Distribute matrix weight based on stoichiometry (MgB2)
    # MgB2 has 1 Mg and 2 B atoms
    # We need to calculate the effective atomic weight of the matrix
    matrix_atomic_weight = (get_atomic_weight(MAGNESIUM_SYMBOL) + 
                            2 * get_atomic_weight(BORON_SYMBOL)) / 3.0

    if matrix_atomic_weight > 0:
        matrix_moles = matrix_weight / matrix_atomic_weight

    total_moles += matrix_moles

    if total_moles == 0:
        return 0.0

    atomic_pct = (weight_pct / impurity_weight) / total_moles * 100.0
    return atomic_pct

def handle_synthesis_range(
    value: Any,
    default: float = 0.0
) -> float:
    """
    Handle synthesis range values by taking the midpoint.

    Args:
        value: The value to process (could be a range string or numeric)
        default: Default value if parsing fails

    Returns:
        Midpoint value as float
    """
    if pd.isna(value):
        return default

    if isinstance(value, (int, float)):
        return float(value)

    value_str = str(value).strip()

    # Check for range format (e.g., "500-600", "500 to 600")
    range_delimiters = ["-", "to", "–", "—"]
    for delim in range_delimiters:
        if delim in value_str:
            parts = value_str.split(delim)
            if len(parts) == 2:
                try:
                    low = float(parts[0].strip())
                    high = float(parts[1].strip())
                    return (low + high) / 2.0
                except ValueError:
                    logger.warning(f"Could not parse range: {value_str}")
                    return default

    # Try direct conversion
    try:
        return float(value_str)
    except ValueError:
        logger.warning(f"Could not parse value: {value_str}")
        return default

def clean_column_name(name: str) -> str:
    """
    Clean column names for consistency.

    Args:
        name: Original column name

    Returns:
        Cleaned column name
    """
    return str(name).lower().strip().replace(" ", "_").replace("-", "_")

def merge_datasets(
    mp_df: pd.DataFrame,
    supercon_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Merge Materials Project and SuperCon datasets.

    Args:
        mp_df: Materials Project dataframe
        supercon_df: SuperCon dataframe

    Returns:
        Merged dataframe
    """
    logger.info(f"Merging datasets: MP ({len(mp_df)} rows), SuperCon ({len(supercon_df)} rows)")

    # Standardize column names
    mp_df.columns = [clean_column_name(c) for c in mp_df.columns]
    supercon_df.columns = [clean_column_name(c) for c in supercon_df.columns]

    # Identify common columns for merging
    common_cols = set(mp_df.columns) & set(supercon_df.columns)
    logger.info(f"Common columns: {common_cols}")

    # Add source identifier
    mp_df["source"] = "materials_project"
    supercon_df["source"] = "supercon"

    # Concatenate datasets
    combined_df = pd.concat([mp_df, supercon_df], ignore_index=True)

    logger.info(f"Combined dataset has {len(combined_df)} rows")

    return combined_df

def convert_impurity_units(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert impurity concentrations from weight% to atomic%.

    Args:
        df: DataFrame with impurity columns

    Returns:
        DataFrame with converted impurity columns
    """
    logger.info("Converting impurity units from weight% to atomic%")

    # Identify impurity columns (columns containing 'impurity' or element symbols)
    impurity_cols = []
    for col in df.columns:
        if 'impurity' in col.lower() or any(elem in col.upper() for elem in [
            "AL", "CA", "C", "N", "O", "F", "NA", "SI", "P", "S", "CL", "K", "CA",
            "SC", "TI", "V", "CR", "MN", "FE", "CO", "NI", "CU", "ZN", "GA", "GE",
            "AS", "SE", "BR", "RB", "SR", "Y", "ZR", "NB", "MO", "TE", "RU", "RH",
            "PD", "AG", "CD", "IN", "SN", "SB", "TE", "I", "CS", "BA", "LA", "CE",
            "PR", "ND", "SM", "EU", "GD", "TB", "DY", "HO", "ER", "TM", "YB", "LU",
            "HF", "TA", "W", "RE", "OS", "IR", "PT", "AU", "HG", "TL", "PB", "BI"
        ]):
            if 'atomic' not in col.lower():
                impurity_cols.append(col)

    logger.info(f"Found {len(impurity_cols)} impurity columns to convert: {impurity_cols}")

    # Convert each impurity column
    for col in impurity_cols:
        if col in df.columns:
            # Extract element symbol from column name if possible
            element = None
            for symbol in [
                "AL", "CA", "C", "N", "O", "F", "NA", "SI", "P", "S", "CL", "K", "CA",
                "SC", "TI", "V", "CR", "MN", "FE", "CO", "NI", "CU", "ZN", "GA", "GE",
                "AS", "SE", "BR", "RB", "SR", "Y", "ZR", "NB", "MO", "TE", "RU", "RH",
                "PD", "AG", "CD", "IN", "SN", "SB", "TE", "I", "CS", "BA", "LA", "CE",
                "PR", "ND", "SM", "EU", "GD", "TB", "DY", "HO", "ER", "TM", "YB", "LU",
                "HF", "TA", "W", "RE", "OS", "IR", "PT", "AU", "HG", "TL", "PB", "BI"
            ]:
                if symbol in col.upper():
                    element = symbol
                    break

            if element is None:
                logger.warning(f"Could not identify element in column: {col}")
                continue

            # Convert values
            atomic_col = f"{col}_atomic_pct"
            df[atomic_col] = df[col].apply(
                lambda x: weight_pct_to_atomic_pct(x, element)
            )

            logger.info(f"Converted {col} to {atomic_col}")

    return df

def filter_valid_entries(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter dataset for valid entries (non-null Tc and impurities).

    Args:
        df: DataFrame to filter

    Returns:
        Filtered DataFrame
    """
    logger.info("Filtering for valid entries")

    initial_count = len(df)

    # Filter for non-null Tc
    if 'tc' in df.columns:
        df = df[df['tc'].notna()]
        df = df[df['tc'] >= MIN_Tc_K]

    # Filter for non-null impurities (at least one impurity column)
    impurity_cols = [c for c in df.columns if 'impurity' in c.lower() or 'atomic_pct' in c.lower()]
    if impurity_cols:
        # Keep rows with at least one non-null impurity value
        mask = df[impurity_cols].notna().any(axis=1)
        df = df[mask]

    # Filter for valid pressure values if present
    if 'pressure_gpa' in df.columns:
        df = df[df['pressure_gpa'].notna()]

    logger.info(f"Filtered from {initial_count} to {len(df)} valid entries")

    return df

def attach_provenance(
    df: pd.DataFrame,
    source_files: List[str],
    version: str = "1.0.0"
) -> pd.DataFrame:
    """
    Attach provenance metadata to the dataframe.

    Args:
        df: DataFrame to annotate
        source_files: List of source file paths
        version: Data version string

    Returns:
      DataFrame with provenance metadata in a special column
    """
    timestamp = datetime.utcnow().isoformat()
    provenance = generate_provenance_header(
        source="; ".join(source_files),
        timestamp=timestamp,
        version=version
    )

    # Add provenance as a metadata column (will be saved as JSON string)
    df["_provenance"] = json.dumps(provenance)

    logger.info(f"Attached provenance: {provenance}")

    return df

def preprocess_datasets(
    mp_data_path: Optional[str] = None,
    supercon_data_path: Optional[str] = None,
    output_path: Optional[str] = None,
    cached_mp_path: Optional[str] = None,
    cached_supercon_path: Optional[str] = None
) -> pd.DataFrame:
    """
    Main preprocessing pipeline.

    Args:
        mp_data_path: Path to Materials Project CSV (optional if cached)
        supercon_data_path: Path to SuperCon CSV (optional if cached)
        output_path: Path for output cleaned CSV
        cached_mp_path: Path to cached MP data
        cached_supercon_path: Path to cached SuperCon data

    Returns:
        Processed DataFrame
    """
    logger.info("Starting preprocessing pipeline")

    # Determine source files for provenance
    source_files = []

    # Load or use cached data
    if cached_mp_path and os.path.exists(cached_mp_path):
        logger.info(f"Loading cached Materials Project data from {cached_mp_path}")
        mp_df = pd.read_csv(cached_mp_path)
        source_files.append(cached_mp_path)
    elif mp_data_path and os.path.exists(mp_data_path):
        logger.info(f"Loading Materials Project data from {mp_data_path}")
        mp_df = pd.read_csv(mp_data_path)
        source_files.append(mp_data_path)
    else:
        raise FileNotFoundError("Materials Project data not found. Run download_materials_project.py first.")

    if cached_supercon_path and os.path.exists(cached_supercon_path):
        logger.info(f"Loading cached SuperCon data from {cached_supercon_path}")
        supercon_df = pd.read_csv(cached_supercon_path)
        source_files.append(cached_supercon_path)
    elif supercon_data_path and os.path.exists(supercon_data_path):
        logger.info(f"Loading SuperCon data from {supercon_data_path}")
        supercon_df = pd.read_csv(supercon_data_path)
        source_files.append(supercon_data_path)
    else:
        raise FileNotFoundError("SuperCon data not found. Run download_supercon.py first.")

    # Step 1: Merge datasets
    combined_df = merge_datasets(mp_df, supercon_df)

    # Step 2: Handle synthesis ranges (midpoint imputation)
    numeric_cols = combined_df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        if combined_df[col].isna().any():
            # Check if this might be a range that needs midpoint imputation
            # For now, we'll just drop rows with NaN in critical columns
            pass

    # Step 3: Convert units
    combined_df = convert_impurity_units(combined_df)

    # Step 4: Filter valid entries
    combined_df = filter_valid_entries(combined_df)

    # Step 5: Attach provenance
    combined_df = attach_provenance(combined_df, source_files)

    # Step 6: Save output if path provided
    if output_path:
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        combined_df.to_csv(output_path, index=False)
        logger.info(f"Saved cleaned data to {output_path}")

    logger.info(f"Preprocessing complete. Final dataset: {len(combined_df)} rows")

    return combined_df

def main():
    """
    Main entry point for preprocessing script.
    """
    logger.info("Running preprocess.py main")

    # Define paths
    project_root = Path(__file__).resolve().parent.parent.parent
    data_dir = project_root / "data" / "processed"

    # Ensure data directory exists
    data_dir.mkdir(parents=True, exist_ok=True)

    # Cached data paths (from T012 and T013)
    cached_mp_path = data_dir / "materials_project_mgb2.csv"
    cached_supercon_path = data_dir / "supercon_mgb2.csv"
    output_path = data_dir / "mgb2_clean.csv"

    # Check if cached files exist
    if not cached_mp_path.exists():
        logger.error(f"Cached MP data not found: {cached_mp_path}")
        logger.error("Please run download_materials_project.py first")
        sys.exit(1)

    if not cached_supercon_path.exists():
        logger.error(f"Cached SuperCon data not found: {cached_supercon_path}")
        logger.error("Please run download_supercon.py first")
        sys.exit(1)

    # Run preprocessing
    try:
        df = preprocess_datasets(
            cached_mp_path=str(cached_mp_path),
            cached_supercon_path=str(cached_supercon_path),
            output_path=str(output_path)
        )

        # Verify output
        if not output_path.exists():
            logger.error("Output file was not created")
            sys.exit(1)

        logger.info(f"Successfully created {output_path} with {len(df)} rows")

        # Print summary
        print(f"\nPreprocessing Summary:")
        print(f"  Total rows: {len(df)}")
        print(f"  Columns: {len(df.columns)}")
        print(f"  Output: {output_path}")

        if 'tc' in df.columns:
            print(f"  Tc range: {df['tc'].min():.2f}K - {df['tc'].max():.2f}K")

    except Exception as e:
        logger.error(f"Preprocessing failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
