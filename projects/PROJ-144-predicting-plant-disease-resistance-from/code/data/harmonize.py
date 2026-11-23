"""
Label Harmonization Module (FR-013)

Implements logic to harmonize disease resistance labels from multiple studies.
Handles binary mapping (0/1) and z-scoring for ordinal scales within studies.
"""
import os
import sys
import json
import glob
import logging
import pandas as pd
import numpy as np
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DataUnavailableError(Exception):
    """Raised when required input files are missing."""
    pass

def load_phenotype_files(raw_data_dir: str) -> dict:
    """
    Load all phenotype CSV files from the raw data directory.

    Args:
        raw_data_dir: Path to the directory containing raw phenotype files.

    Returns:
        Dictionary mapping study_id to DataFrame.
    """
    phenotype_files = glob.glob(os.path.join(raw_data_dir, '*_phenotype.csv'))
    if not phenotype_files:
        raise DataUnavailableError(
            f"No phenotype files found in {raw_data_dir}. "
            "Run T012b (download) first."
        )

    study_data = {}
    for f_path in phenotype_files:
        study_id = Path(f_path).stem.replace('_phenotype', '')
        try:
            df = pd.read_csv(f_path)
            study_data[study_id] = df
            logger.info(f"Loaded phenotype data for {study_id}: {len(df)} rows")
        except Exception as e:
            logger.error(f"Failed to load {f_path}: {e}")
            raise

    return study_data

def load_heterogeneity_report(report_path: str) -> dict:
    """
    Load the heterogeneity analysis report.

    Args:
        report_path: Path to heterogeneity_report.json.

    Returns:
        Dictionary containing heterogeneity flags and details per study.
    """
    if not os.path.exists(report_path):
        raise DataUnavailableError(
            f"Heterogeneity report not found at {report_path}. "
            "Run T015a-exec first."
        )

    with open(report_path, 'r') as f:
        return json.load(f)

def harmonize_labels(study_data: dict, heterogeneity_report: dict) -> pd.DataFrame:
    """
    Harmonize labels across studies based on heterogeneity report.

    Logic:
    1. If heterogeneity exists (including multi-study binary):
       - If ordinal: Z-score within study.
       - If binary: Map to 0/1 directly.
    2. If no heterogeneity (single binary method, single study):
       - Apply global alignment (0/1).

    Args:
        study_data: Dict of study_id -> DataFrame.
        heterogeneity_report: Dict from T015a.

    Returns:
        DataFrame with harmonized labels (study_id, sample_id, harmonized_label).
    """
    harmonized_records = []

    # Build a lookup for heterogeneity details by study_id
    hetero_lookup = {}
    for entry in heterogeneity_report.get('studies', []):
        hetero_lookup[entry['study_id']] = entry

    for study_id, df in study_data.items():
        logger.info(f"Processing harmonization for {study_id}")

        # Identify label column (common names)
        label_col = None
        for candidate in ['resistance_score', 'phenotype', 'disease_status', 'challenge_outcome', 'label']:
            if candidate in df.columns:
                label_col = candidate
                break

        if label_col is None:
            logger.warning(f"Could not find label column in {study_id}. Skipping.")
            continue

        # Check heterogeneity status
        hetero_info = hetero_lookup.get(study_id, {})
        is_heterogeneous = hetero_info.get('heterogeneity_detected', False)
        score_types = hetero_info.get('score_types', [])
        methods = hetero_info.get('methods', [])

        # Determine strategy
        # Strategy 1: Ordinal -> Z-score within study
        # Strategy 2: Binary -> Map to 0/1
        # Strategy 3: Mixed/Unknown -> Default to 0/1 mapping if possible, else warn

        has_ordinal = 'ordinal' in score_types
        has_binary = 'binary' in score_types

        # Extract raw labels
        raw_labels = df[label_col].dropna()

        # Mapping for binary/ordinal values to 0/1
        resistant_vals = {'resistant', 'r', 1, 'yes', 'yes', 'resistant'}
        susceptible_vals = {'susceptible', 's', 0, 'no', 'no', 'susceptible'}

        if has_ordinal and not has_binary:
            logger.info(f"{study_id}: Detected ordinal scale. Applying z-scoring within study.")
            # Z-score within study
            mean_val = raw_labels.mean()
            std_val = raw_labels.std()
            if std_val == 0:
                logger.warning(f"{study_id}: Zero variance in labels. Cannot z-score. Using raw values.")
                harmonized = raw_labels
            else:
                harmonized = (raw_labels - mean_val) / std_val
        else:
            # Binary or Mixed: Map to 0/1
            logger.info(f"{study_id}: Applying binary mapping (0/1).")
            
            def map_val(val):
                if pd.isna(val):
                    return np.nan
                val_str = str(val).lower().strip()
                if val_str in resistant_vals or val == 1 or val == '1':
                    return 1.0
                elif val_str in susceptible_vals or val == 0 or val == '0':
                    return 0.0
                else:
                    # Try to interpret as number
                    try:
                        num = float(val)
                        if num >= 0.5: return 1.0
                        return 0.0
                    except:
                        return np.nan

            harmonized = raw_labels.apply(map_val)

        # Create output rows
        for idx, val in harmonized.items():
            sample_id = df.iloc[idx].get('sample_id', f"{study_id}_{idx}")
            harmonized_records.append({
                'study_id': study_id,
                'sample_id': sample_id,
                'harmonized_label': val,
                'original_label': df.iloc[idx][label_col]
            })

    result_df = pd.DataFrame(harmonized_records)
    
    # Final check: ensure no missing values in harmonized_label
    if result_df['harmonized_label'].isna().any():
        missing_count = result_df['harmonized_label'].isna().sum()
        logger.warning(f"Final output contains {missing_count} NaN labels. Dropping them.")
        result_df = result_df.dropna(subset=['harmonized_label'])
        result_df['harmonized_label'] = result_df['harmonized_label'].astype(float)

    return result_df

def save_report(df: pd.DataFrame, output_path: str):
    """
    Save harmonized labels to CSV.

    Args:
        df: DataFrame with harmonized labels.
        output_path: Output file path.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved harmonized labels to {output_path}")

def main():
    """Main entry point for T015b."""
    # Define paths
    raw_data_dir = "data/raw"
    hetero_report_path = "data/processed/heterogeneity_report.json"
    output_path = "data/processed/harmonized_labels.csv"

    logger.info("Starting Label Harmonization (T015b)")

    try:
        # 1. Load inputs
        study_data = load_phenotype_files(raw_data_dir)
        hetero_report = load_heterogeneity_report(hetero_report_path)

        # 2. Harmonize
        harmonized_df = harmonize_labels(study_data, hetero_report)

        # 3. Save output
        save_report(harmonized_df, output_path)

        logger.info("T015b completed successfully.")
        return 0

    except DataUnavailableError as e:
        logger.error(f"Data unavailable: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during harmonization: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())