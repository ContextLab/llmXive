"""
Data Ingestion Module.

Handles fetching, validating, and cleaning ceramic data from multiple sources.
"""
import os
import sys
import json
import logging
import re
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd
import numpy as np
from chemparse import parse_formula

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import initialize_config, get_int_config
from contracts.schemas import CeramicEntry, validate_data_against_schema
from logger import setup_citation_logger

# Initialize config
initialize_config()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(project_root / 'logs' / 'ingestion.log')
    ]
)
logger = logging.getLogger(__name__)
citation_logger = setup_citation_logger()

def ensure_output_dirs():
    """Ensure all required output directories exist."""
    dirs = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "data" / "artifacts",
        project_root / "logs"
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)

def derive_primary_anion_cation_group(composition: str) -> str:
    """
    Derive the primary anion-cation group from a composition string.

    Args:
        composition: Chemical formula (e.g., 'Al2O3')

    Returns:
        String representing the group (e.g., 'O-Al')
    """
    try:
        parsed = parse_formula(composition)
        elements = list(parsed.keys())
        # Simple heuristic: last element is anion (usually), first is cation
        # This is a simplification; real logic would use periodic table groups
        if len(elements) >= 2:
            cation = elements[0]
            anion = elements[-1]
            return f"{anion}-{cation}"
        elif len(elements) == 1:
            return f"Element-{elements[0]}"
        else:
            return "Unknown"
    except Exception as e:
        logger.warning(f"Failed to parse composition '{composition}': {e}")
        return "Unknown"

def validate_entry(entry: Dict[str, Any]) -> bool:
    """Validate a single entry against the CeramicEntry schema."""
    try:
        CeramicEntry(**entry)
        return True
    except Exception as e:
        logger.debug(f"Validation failed for entry: {e}")
        return False

def validate_no_missing_primary_predictors(df: pd.DataFrame) -> bool:
    """
    Validate that essential descriptors have no missing values.

    Args:
        df: DataFrame with computed descriptors

    Returns:
        True if all primary predictors are present, False otherwise
    """
    primary_predictors = [
        'mean_atomic_radius',
        'electronegativity_std',
        'valence_electron_concentration',
        'cation_size_variance'
    ]

    missing = [col for col in primary_predictors if col not in df.columns or df[col].isna().any()]

    if missing:
        logger.error(f"Missing primary predictors: {missing}")
        return False

    return True

def flag_high_variance_ranges(df: pd.DataFrame, threshold: float = 0.5) -> pd.DataFrame:
    """
    Flag and exclude entries where range width exceeds a threshold.

    Args:
        df: DataFrame with 'weibull_modulus' and 'range_original' (if applicable)
        threshold: Maximum allowed range width as fraction of midpoint

    Returns:
        Filtered DataFrame
    """
    if 'range_original' not in df.columns:
        return df

    # Calculate range width
    df['range_width'] = df['range_original'].apply(lambda x: float(x.split('-')[1]) - float(x.split('-')[0]) if isinstance(x, str) and '-' in str(x) else 0)
    df['midpoint'] = df['weibull_modulus']

    # Flag high variance
    df['high_variance'] = (df['range_width'] / df['midpoint']) > threshold

    # Exclude flagged entries
    filtered_df = df[~df['high_variance']].copy()
    logger.info(f"Excluded {df['high_variance'].sum()} high-variance range entries.")

    return filtered_df.drop(columns=['range_width', 'midpoint', 'high_variance'], errors='ignore')

def generate_data_availability_report(count: int, output_path: str = None):
    """
    Generate a data availability report if N < 30.

    Args:
        count: Number of valid entries
        output_path: Path to save the report
    """
    if count >= 30:
        return

    report = {
        "status": "insufficient_data",
        "count": count,
        "threshold": 30,
        "message": f"Insufficient data for modeling (N={count} < 30).",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    if not output_path:
        output_path = project_root / "data" / "reports" / "data_availability_report.json"

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    logger.warning(f"Data availability report generated: {output_path}")

def validate_data_gap(count: int):
    """
    Validate data gap and halt pipeline if N < 30.

    Args:
        count: Number of valid entries
    """
    if count < 30:
        generate_data_availability_report(count)
        logger.error(f"Power Limitation: Insufficient data (N={count} < 30).")
        print("Power Limitation: Insufficient data (N < 30)", file=sys.stderr)
        sys.exit(1)
    elif count < 50:
        logger.warning(f"Small dataset (30 <= N={count} < 50). Hold-out validation will be used.")
    else:
        logger.info(f"Dataset size sufficient (N={count} >= 50). Using 5-fold CV.")

def main():
    """
    Main entry point for ingestion.

    This function orchestrates the full data ingestion pipeline:
    1. Fetch data from sources
    2. Validate and clean
    3. Compute descriptors
    4. Save processed data
    """
    logger.info("Starting data ingestion pipeline...")
    ensure_output_dirs()

    # Placeholder for actual ingestion logic
    # In a real implementation, this would call fetch_* and process_* functions
    logger.info("Ingestion pipeline completed (placeholder).")

if __name__ == "__main__":
    main()
