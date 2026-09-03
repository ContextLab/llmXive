"""
T014a: Detect label heterogeneity in downloaded phenotype files.

Pre-requisite: T013 must complete successfully.
Pre-check: Verify data/raw/{study_id}_phenotype.csv exists for each study.
Logic: Load raw labels. Analyze measurement_method and assay_score distribution
       to detect heterogeneity (multiple methods or mixed binary/ordinal scales).
Output: Generate data/processed/heterogeneity_report.json describing detected heterogeneity levels.
"""

import os
import sys
import json
import glob
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.exceptions import DataUnavailableError

def load_phenotype_files(raw_data_dir: str) -> dict:
    """
    Load all phenotype CSV files from the raw data directory.

    Args:
        raw_data_dir: Path to data/raw/ directory

    Returns:
        Dictionary mapping study_id to DataFrame

    Raises:
        DataUnavailableError: If no phenotype files are found
    """
    pattern = os.path.join(raw_data_dir, "*_phenotype.csv")
    files = glob.glob(pattern)

    if not files:
        raise DataUnavailableError(
            f"Raw phenotype files missing. Run T012b first. "
            f"Searched for: {pattern}"
        )

    studies = {}
    for file_path in files:
        study_id = Path(file_path).stem.replace("_phenotype", "")
        try:
            df = pd.read_csv(file_path)
            studies[study_id] = df
            print(f"Loaded phenotype data for study {study_id}: {len(df)} rows")
        except Exception as e:
            print(f"Warning: Could not load {file_path}: {e}")

    return studies

def analyze_heterogeneity(studies: dict) -> dict:
    """
    Analyze label heterogeneity across studies.

    Args:
        studies: Dictionary of study_id -> DataFrame

    Returns:
        Dictionary containing heterogeneity analysis results
    """
    report = {
        "total_studies": len(studies),
        "studies_analyzed": [],
        "heterogeneity_detected": False,
        "details": {
            "measurement_methods": {},
            "assay_score_types": {},
            "binary_ordinal_mix": False,
            "multi_study_binary": False
        }
    }

    all_measurement_methods = set()
    all_score_types = set()
    has_binary = False
    has_ordinal = False

    for study_id, df in studies.items():
        study_report = {
            "study_id": study_id,
            "n_samples": len(df),
            "columns_found": list(df.columns),
            "measurement_methods": [],
            "score_types": []
        }

        # Check for measurement_method column
        if "measurement_method" in df.columns:
            methods = df["measurement_method"].dropna().unique().tolist()
            study_report["measurement_methods"] = methods
            all_measurement_methods.update(methods)

            if len(methods) > 1:
                report["heterogeneity_detected"] = True
                study_report["heterogeneity_reason"] = "Multiple measurement methods"

        # Check for assay_score column
        if "assay_score" in df.columns:
            score_col = df["assay_score"]
            score_type = "unknown"

            # Check if binary (only 2 unique values)
            unique_vals = score_col.dropna().unique()
            if len(unique_vals) == 2:
                score_type = "binary"
                has_binary = True
            elif len(unique_vals) > 2 and score_col.dtype in ['int64', 'float64']:
                score_type = "ordinal"
                has_ordinal = True
            else:
                score_type = "categorical"

            study_report["score_types"].append(score_type)
            all_score_types.add(score_type)

            if score_type == "binary":
                has_binary = True
            elif score_type == "ordinal":
                has_ordinal = True

        # Check for other resistance-related columns
        resistance_cols = ['phenotype', 'resistance_score', 'disease_status', 'challenge_outcome']
        for col in resistance_cols:
            if col in df.columns:
                unique_vals = df[col].dropna().unique()
                if len(unique_vals) == 2:
                    has_binary = True
                    if "binary_label" not in all_score_types:
                        all_score_types.add("binary")
                elif len(unique_vals) > 2 and df[col].dtype in ['int64', 'float64']:
                    has_ordinal = True
                    if "ordinal_label" not in all_score_types:
                        all_score_types.add("ordinal")

        if len(study_report["measurement_methods"]) > 1 or len(study_report["score_types"]) > 1:
            report["heterogeneity_detected"] = True

        report["studies_analyzed"].append(study_report)

    # Global heterogeneity checks
    report["details"]["measurement_methods"] = list(all_measurement_methods)
    report["details"]["assay_score_types"] = list(all_score_types)

    # Check for binary/ordinal mix
    if has_binary and has_ordinal:
        report["heterogeneity_detected"] = True
        report["details"]["binary_ordinal_mix"] = True

    # Check for multi-study binary scenario (multiple studies with binary labels)
    binary_studies = [s for s in report["studies_analyzed"]
                    if "binary" in s.get("score_types", []) or
                    any("binary" in str(m).lower() for m in s.get("measurement_methods", []))]
    if len(binary_studies) > 1:
        report["details"]["multi_study_binary"] = True
        report["heterogeneity_detected"] = True

    report["summary"] = {
        "unique_measurement_methods": len(all_measurement_methods),
        "unique_score_types": len(all_score_types),
        "requires_harmonization": report["heterogeneity_detected"],
        "harmonization_strategy": "z-score_ordinal" if has_ordinal and has_binary else "global_alignment"
    }

    return report

def main():
    """Main entry point for T014a."""
    print("Starting T014a: Detect label heterogeneity")

    # Paths
    raw_data_dir = os.path.join("data", "raw")
    output_dir = os.path.join("data", "processed")
    output_file = os.path.join(output_dir, "heterogeneity_report.json")

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    try:
        # Load phenotype files
        print(f"Scanning for phenotype files in {raw_data_dir}...")
        studies = load_phenotype_files(raw_data_dir)

        if not studies:
            raise DataUnavailableError(
                f"No phenotype files found in {raw_data_dir}. "
                f"Ensure T012b has completed successfully."
            )

        # Analyze heterogeneity
        print(f"Analyzing {len(studies)} studies for label heterogeneity...")
        report = analyze_heterogeneity(studies)

        # Write output
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)

        print(f"Heterogeneity report written to {output_file}")
        print(f"Heterogeneity detected: {report['heterogeneity_detected']}")
        print(f"Requires harmonization: {report['summary']['requires_harmonization']}")

        return 0

    except DataUnavailableError as e:
        print(f"ERROR: {e}")
        return 1
    except Exception as e:
        print(f"ERROR: Unexpected error during heterogeneity detection: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
