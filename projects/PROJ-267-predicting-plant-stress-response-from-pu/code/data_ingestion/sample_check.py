"""
Sample Check Module for Data Ingestion Pipeline.

This module verifies that the merged dataset contains a sufficient number of
real samples per stress condition for the target species (Arabidopsis, Rice, Wheat).
If the sample count is insufficient (< 5 per condition for all species), it triggers
a "Data Unavailable" halt path and exits cleanly.

This module relies on data already present in `data/processed/` (typically generated
by `download.py`, `normalize.py`, and `merge.py`).
"""

import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

import pandas as pd

# Import local utilities
# We assume the project structure is: code/utils/config.py and code/utils/logging_config.py
try:
    from utils.logging_config import get_logger, log_warning
    from utils.config import DATA_PROCESSED_PATH, TARGET_SPECIES, TARGET_STRESS_CONDITIONS
except ImportError:
    # Fallback for direct execution or different import context
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from utils.logging_config import get_logger, log_warning
    from utils.config import DATA_PROCESSED_PATH, TARGET_SPECIES, TARGET_STRESS_CONDITIONS

# Initialize logger
logger = get_logger(__name__)

# Constants for thresholds
MIN_SAMPLES_PER_CONDITION = 5
OUTPUT_REPORT_PATH = Path("results/sample_check_report.json")

def load_processed_data(file_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load the processed dataset.
    
    Args:
        file_path: Optional specific file path. If None, looks for standard merged file.
        
    Returns:
        pd.DataFrame: The loaded dataset.
        
    Raises:
        FileNotFoundError: If the data file does not exist.
        ValueError: If the file format is unsupported or data is empty.
    """
    if file_path is None:
        # Expected output from the pipeline (T014)
        # We look for the standard merged CSV
        potential_files = [
            DATA_PROCESSED_PATH / "merged_proteomics_transcriptomics.csv",
            DATA_PROCESSED_PATH / "merged_data.csv",
            DATA_PROCESSED_PATH / "processed_data.csv"
        ]
        found_path = None
        for p in potential_files:
            if p.exists():
                found_path = p
                break
        
        if found_path is None:
            # Fallback: check if any CSV exists in data/processed
            csv_files = list(DATA_PROCESSED_PATH.glob("*.csv"))
            if csv_files:
                found_path = csv_files[0]
                log_warning(f"No standard merged file found. Using first available CSV: {found_path}")
            else:
                raise FileNotFoundError(
                    f"Could not find processed data in {DATA_PROCESSED_PATH}. "
                    "Please ensure the ingestion pipeline (T014) has run successfully."
                )
    else:
        found_path = file_path
        
    if not found_path.exists():
        raise FileNotFoundError(f"Data file not found: {found_path}")
    
    logger.info(f"Loading data from {found_path}")
    
    try:
        df = pd.read_csv(found_path)
    except Exception as e:
        raise ValueError(f"Failed to read CSV file {found_path}: {e}")
    
    if df.empty:
        raise ValueError(f"Loaded dataset from {found_path} is empty.")
        
    return df

def check_sample_counts(
    df: pd.DataFrame,
    species_column: str = "species",
    stress_column: str = "stress_condition",
    sample_id_column: str = "sample_id"
) -> Dict[str, Dict[str, int]]:
    """
    Count samples per species and stress condition.
    
    Args:
        df: The dataframe containing the data.
        species_column: Name of the column containing species names.
        stress_column: Name of the column containing stress conditions.
        sample_id_column: Name of the column containing unique sample IDs.
        
    Returns:
        A nested dictionary: {species: {stress: count}}
    """
    # Ensure required columns exist
    required_cols = [species_column, stress_column, sample_id_column]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in dataset: {missing_cols}")
    
    # Filter for target species only
    # Normalize species names to handle case sensitivity or minor variations
    df_clean = df.copy()
    df_clean[species_column] = df_clean[species_column].astype(str).str.strip().str.title()
    
    # Map common variations to standard names if necessary
    # e.g., "Arabidopsis thaliana" -> "Arabidopsis"
    def normalize_species(name: str) -> str:
        name_lower = name.lower()
        if "arabidopsis" in name_lower:
            return "Arabidopsis"
        if "rice" in name_lower or "oryza" in name_lower:
            return "Rice"
        if "wheat" in name_lower or "triticum" in name_lower:
            return "Wheat"
        return name
    
    df_clean[species_column] = df_clean[species_column].apply(normalize_species)
    
    # Filter for target species
    target_species_normalized = {normalize_species(s) for s in TARGET_SPECIES}
    mask = df_clean[species_column].isin(target_species_normalized)
    df_filtered = df_clean[mask]
    
    if df_filtered.empty:
        logger.warning("No samples found for target species after filtering.")
        return {s: {c: 0 for c in TARGET_STRESS_CONDITIONS} for s in TARGET_SPECIES}
    
    # Group by species and stress condition
    counts = {}
    for species in TARGET_SPECIES:
        species_normalized = normalize_species(species)
        counts[species] = {}
        for stress in TARGET_STRESS_CONDITIONS:
            # Count unique sample IDs
            subset = df_filtered[
                (df_filtered[species_column] == species_normalized) & 
                (df_filtered[stress_column].str.lower() == stress.lower())
            ]
            count = subset[sample_id_column].nunique()
            counts[species][stress] = count
            
    return counts

def evaluate_data_sufficiency(counts: Dict[str, Dict[str, int]]) -> Tuple[bool, List[str]]:
    """
    Evaluate if the data meets the minimum sample requirements.
    
    Args:
        counts: The sample counts dictionary.
        
    Returns:
        Tuple of (is_sufficient, list_of_issues)
    """
    issues = []
    sufficient_for_any = False
    
    for species in TARGET_SPECIES:
        species_ok = False
        for stress in TARGET_STRESS_CONDITIONS:
            count = counts.get(species, {}).get(stress, 0)
            if count < MIN_SAMPLES_PER_CONDITION:
                issues.append(
                    f"{species} under {stress} has {count} samples (min required: {MIN_SAMPLES_PER_CONDITION})"
                )
            else:
                species_ok = True
        
        if species_ok:
            sufficient_for_any = True
            
    if not sufficient_for_any:
        return False, issues
        
    return True, issues

def generate_report(counts: Dict[str, Dict[str, int]], is_sufficient: bool, issues: List[str]) -> Dict[str, Any]:
    """
    Generate a report dictionary for the sample check.
    """
    return {
        "status": "PASS" if is_sufficient else "FAIL",
        "threshold": MIN_SAMPLES_PER_CONDITION,
        "counts": counts,
        "issues": issues,
        "timestamp": pd.Timestamp.now().isoformat()
    }

def save_report(report: Dict[str, Any], output_path: Path) -> None:
    """
    Save the report to a JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)
    logger.info(f"Report saved to {output_path}")

def main():
    """
    Main entry point for the sample check task.
    
    This function:
    1. Loads the processed data.
    2. Counts samples per species and stress condition.
    3. Evaluates sufficiency.
    4. Generates and saves a report.
    5. Exits with code 0 if sufficient, 1 if data is insufficient (Data Unavailable path).
    """
    logger.info("Starting Sample Check (T037)...")
    
    try:
        # Load data
        df = load_processed_data()
        logger.info(f"Loaded {len(df)} rows.")
        
        # Check counts
        counts = check_sample_counts(df)
        logger.debug(f"Sample counts: {counts}")
        
        # Evaluate
        is_sufficient, issues = evaluate_data_sufficiency(counts)
        
        # Generate report
        report = generate_report(counts, is_sufficient, issues)
        
        # Save report
        save_report(report, OUTPUT_REPORT_PATH)
        
        if is_sufficient:
            logger.info("Data sufficiency check PASSED.")
            print(f"SUCCESS: Data sufficient. Report saved to {OUTPUT_REPORT_PATH}")
            sys.exit(0)
        else:
            logger.error("Data sufficiency check FAILED. Insufficient samples for all target species/conditions.")
            print(f"HALT: Data Unavailable. Insufficient samples.")
            print(f"Issues found: {issues}")
            print(f"Report saved to {OUTPUT_REPORT_PATH}")
            sys.exit(1)
            
    except FileNotFoundError as e:
        logger.critical(f"Data file not found: {e}")
        print(f"FATAL: Data file not found. Cannot proceed with sample check.")
        sys.exit(2)
    except ValueError as e:
        logger.critical(f"Data validation error: {e}")
        print(f"FATAL: Data validation error. {e}")
        sys.exit(2)
    except Exception as e:
        logger.exception(f"Unexpected error during sample check: {e}")
        print(f"FATAL: Unexpected error. {e}")
        sys.exit(3)

if __name__ == "__main__":
    main()