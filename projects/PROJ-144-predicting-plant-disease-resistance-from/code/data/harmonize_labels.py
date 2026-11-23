import os
import sys
import json
import glob
import pandas as pd
import numpy as np
from typing import Dict, Any, List
from pathlib import Path

# Import from existing project modules to maintain API surface
from utils.io import log_preprocessing_step, compute_file_hash
from utils.constants import DATA_RAW_DIR, DATA_PROCESSED_DIR

def harmonize_labels(
    raw_phenotype_files: List[Path],
    heterogeneity_report_path: Path,
    output_path: Path
) -> pd.DataFrame:
    """
    Apply label harmonization based on FR-013.

    Logic:
    1. Load raw phenotype files.
    2. Load heterogeneity report to determine strategy.
    3. If heterogeneity exists (multiple methods or mixed scales):
       - Stratify by measurement_method OR apply z-scoring within study.
    4. If no heterogeneity (single binary method):
       - Apply global alignment (0/1).
    5. Output: Standardized binary (0/1) or z-scored labels.

    Args:
        raw_phenotype_files: List of paths to raw phenotype CSVs.
        heterogeneity_report_path: Path to the heterogeneity report JSON.
        output_path: Path to save the harmonized labels CSV.

    Returns:
        DataFrame containing the harmonized labels.
    """
    if not heterogeneity_report_path.exists():
        raise FileNotFoundError(f"Heterogeneity report not found: {heterogeneity_report_path}")

    with open(heterogeneity_report_path, 'r') as f:
        heterogeneity_info = json.load(f)

    all_labels = []

    for file_path in raw_phenotype_files:
        if not file_path.exists():
            raise FileNotFoundError(f"Raw phenotype file missing: {file_path}")

        df = pd.read_csv(file_path)

        # Identify study ID from filename
        study_id = file_path.stem.replace('_phenotype', '')

        # Determine the primary label column
        # Look for common resistance label columns
        label_cols = ['phenotype', 'resistance_score', 'disease_status', 'challenge_outcome', 'binary_label']
        label_col = None
        for col in label_cols:
            if col in df.columns:
                label_col = col
                break

        if label_col is None:
            # Fallback: use the first non-numeric column if it looks like a label
            non_numeric_cols = df.select_dtypes(include=['object', 'category']).columns
            if len(non_numeric_cols) > 0:
                label_col = non_numeric_cols[0]
            else:
                raise ValueError(f"Could not identify label column in {file_path}")

        # Extract label data
        labels = df[[label_col]].copy()
        labels.columns = ['raw_label']
        labels['study_id'] = study_id

        # Determine if this study has heterogeneity
        study_hetero = heterogeneity_info.get(study_id, {})
        has_heterogeneity = study_hetero.get('has_heterogeneity', False)
        measurement_method = study_hetero.get('measurement_method', None)

        if has_heterogeneity:
            log_preprocessing_step(
                "label_harmonization",
                f"Applying z-scoring/stratification for study {study_id} due to heterogeneity"
            )

            # Strategy: Z-score within study if continuous/ordinal
            if labels['raw_label'].dtype in ['int64', 'float64']:
                # Z-score normalization
                mean_val = labels['raw_label'].mean()
                std_val = labels['raw_label'].std()
                if std_val == 0:
                    labels['harmonized_label'] = 0.0
                else:
                    labels['harmonized_label'] = (labels['raw_label'] - mean_val) / std_val
            else:
                # For categorical, map to 0/1 based on resistance vs susceptibility
                # Assume 'resistant' or 'high' maps to 1, others to 0
                # This is a simplified heuristic; in reality, we'd need domain knowledge
                labels['harmonized_label'] = labels['raw_label'].apply(
                    lambda x: 1 if str(x).lower() in ['resistant', 'high', '1', 'yes'] else 0
                )
        else:
            log_preprocessing_step(
                "label_harmonization",
                f"Applying global binary alignment for study {study_id}"
            )

            # Global binary alignment (0/1)
            # Map known resistance values to 1, susceptibility to 0
            labels['harmonized_label'] = labels['raw_label'].apply(
                lambda x: 1 if str(x).lower() in ['resistant', 'high', '1', 'yes', 'r'] else 0
            )

        all_labels.append(labels)

    # Concatenate all studies
    harmonized_df = pd.concat(all_labels, ignore_index=True)

    # Ensure no missing values in harmonized_label
    if harmonized_df['harmonized_label'].isnull().any():
        log_preprocessing_step(
            "label_harmonization",
            "Warning: Missing values detected in harmonized labels. Dropping rows."
        )
        harmonized_df = harmonized_df.dropna(subset=['harmonized_label'])

    # Save to output path
    harmonized_df.to_csv(output_path, index=False)

    # Compute and log checksum
    checksum = compute_file_hash(output_path)
    log_preprocessing_step(
        "label_harmonization",
        f"Saved harmonized labels to {output_path} (SHA256: {checksum})"
    )

    return harmonized_df


def main():
    """
    Main entry point for label harmonization.
    Reads raw phenotype files and heterogeneity report, outputs harmonized labels.
    """
    # Define paths
    raw_dir = Path(DATA_RAW_DIR)
    processed_dir = Path(DATA_PROCESSED_DIR)
    processed_dir.mkdir(parents=True, exist_ok=True)

    # Find all raw phenotype files
    phenotype_files = list(raw_dir.glob("*_phenotype.csv"))

    if not phenotype_files:
        raise FileNotFoundError(
            "No raw phenotype files found. Ensure T012b has completed successfully."
        )

    # Path to heterogeneity report (output of T014a)
    heterogeneity_report_path = processed_dir / "heterogeneity_report.json"

    if not heterogeneity_report_path.exists():
        raise FileNotFoundError(
            f"Heterogeneity report not found at {heterogeneity_report_path}. "
            "Ensure T014a has completed successfully."
        )

    # Output path
    output_path = processed_dir / "harmonized_labels.csv"

    log_preprocessing_step("label_harmonization", "Starting label harmonization process")

    try:
        harmonized_df = harmonize_labels(
            raw_phenotype_files=phenotype_files,
            heterogeneity_report_path=heterogeneity_report_path,
            output_path=output_path
        )

        log_preprocessing_step(
            "label_harmonization",
            f"Successfully harmonized {len(harmonized_df)} labels"
        )

        # Verify output
        if not output_path.exists():
            raise RuntimeError("Output file was not created.")

        if output_path.stat().st_size == 0:
            raise RuntimeError("Output file is empty.")

        print(f"Harmonized labels saved to: {output_path}")
        print(f"Total samples: {len(harmonized_df)}")
        print(f"Label distribution:\n{harmonized_df['harmonized_label'].value_counts()}")

    except Exception as e:
        log_preprocessing_step("label_harmonization", f"Error: {str(e)}")
        raise


if __name__ == "__main__":
    main()