"""
T014a: Detect label heterogeneity in plant metabolomics studies.

Pre-requisite: T012b must complete successfully.
Pre-check: Verify data/raw/{study_id}_phenotype.csv exists for each study.
Logic: Load raw labels. Analyze measurement_method and assay_score distribution.
Output: Generate data/processed/heterogeneity_report.json.
"""
import os
import sys
import json
import glob
import pandas as pd
import numpy as np
from pathlib import Path

# Import custom exceptions if they exist in the project
try:
    from utils.exceptions import DataUnavailableError
except ImportError:
    # Fallback if the exception module is not yet fully integrated or named differently
    class DataUnavailableError(Exception):
        """Raised when required data files are missing."""
        pass

from utils.constants import DATA_RAW_DIR, DATA_PROCESSED_DIR

def load_phenotype_files(raw_dir: Path) -> dict:
    """
    Load all phenotype CSV files from the raw directory.
    Returns a dictionary mapping study_id to DataFrame.
    """
    studies = {}
    pattern = str(raw_dir / "*_phenotype.csv")
    files = glob.glob(pattern)

    if not files:
        raise DataUnavailableError(
            "Raw phenotype files missing. Run T012b first."
        )

    for file_path in files:
        filename = os.path.basename(file_path)
        # Extract study_id from filename like "{study_id}_phenotype.csv"
        study_id = filename.replace("_phenotype.csv", "")
        try:
            df = pd.read_csv(file_path)
            studies[study_id] = df
        except Exception as e:
            print(f"Warning: Could not load {file_path}: {e}")
            continue

    if not studies:
        raise DataUnavailableError(
            "Raw phenotype files missing. Run T012b first."
        )

    return studies

def analyze_heterogeneity(studies: dict) -> dict:
    """
    Analyze measurement_method and assay_score distributions across studies.
    Detects:
    1. Multiple distinct measurement methods.
    2. Mixed binary/ordinal scales in assay_score.
    3. Inconsistent column presence.
    """
    report = {
        "total_studies": len(studies),
        "studies_analyzed": list(studies.keys()),
        "heterogeneity_detected": False,
        "details": {
            "measurement_methods": {},
            "assay_score_distributions": {},
            "column_presence": {},
            "issues": []
        }
    }

    all_methods = set()
    all_score_types = set()

    for study_id, df in studies.items():
        cols = df.columns.tolist()
        report["details"]["column_presence"][study_id] = cols

        # Check for measurement method
        method_col = None
        possible_method_cols = ["measurement_method", "assay_type", "method", "platform"]
        for col in possible_method_cols:
            if col in cols:
                method_col = col
                break

        if method_col:
            methods = df[method_col].dropna().unique().tolist()
            report["details"]["measurement_methods"][study_id] = methods
            all_methods.update(methods)

        # Check for assay score / resistance label
        score_col = None
        possible_score_cols = ["assay_score", "resistance_score", "phenotype", "label", "outcome"]
        for col in possible_score_cols:
            if col in cols:
                score_col = col
                break

        if score_col:
            values = df[score_col].dropna()
            # Determine type: binary (0/1), ordinal, or continuous
            unique_vals = values.unique()
            if len(unique_vals) <= 2 and set(unique_vals).issubset({0, 1, "0", "1", "Yes", "No", "Resistant", "Susceptible"}):
                score_type = "binary"
            elif len(unique_vals) <= 5:
                score_type = "ordinal"
            else:
                score_type = "continuous"
            
            report["details"]["assay_score_distributions"][study_id] = {
                "column": score_col,
                "type": score_type,
                "unique_values": len(unique_vals),
                "sample_values": list(unique_vals[:5])
            }
            all_score_types.add(score_type)

    # Analyze global heterogeneity
    if len(all_methods) > 1:
        report["heterogeneity_detected"] = True
        report["details"]["issues"].append(
            f"Multiple measurement methods detected: {list(all_methods)}"
        )
    
    if len(all_score_types) > 1:
        report["heterogeneity_detected"] = True
        report["details"]["issues"].append(
            f"Mixed label scales detected: {list(all_score_types)}"
        )

    # Check if any study is missing expected columns
    for study_id, cols in report["details"]["column_presence"].items():
        has_method = any(c in cols for c in ["measurement_method", "assay_type", "method", "platform"])
        has_score = any(c in cols for c in ["assay_score", "resistance_score", "phenotype", "label", "outcome"])
        if not has_method or not has_score:
            report["details"]["issues"].append(
                f"Study {study_id} missing expected metadata columns."
            )
            report["heterogeneity_detected"] = True

    return report

def main():
    """Main entry point for T014a."""
    raw_dir = Path(DATA_RAW_DIR)
    output_dir = Path(DATA_PROCESSED_DIR)
    output_file = output_dir / "heterogeneity_report.json"

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Scanning for phenotype files in {raw_dir}...")
    
    try:
        studies = load_phenotype_files(raw_dir)
        print(f"Loaded {len(studies)} studies.")
        
        report = analyze_heterogeneity(studies)
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"Heterogeneity report written to {output_file}")
        print(f"Heterogeneity detected: {report['heterogeneity_detected']}")
        
        if report['details']['issues']:
            print("Issues found:")
            for issue in report['details']['issues']:
                print(f"  - {issue}")
                
        return 0

    except DataUnavailableError as e:
        print(f"Error: {e}")
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
