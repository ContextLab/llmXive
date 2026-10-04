import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

# Import logging setup from the project's standard location
try:
    from setup_logging import setup_logging, get_data_quality_logger
except ImportError:
    # Fallback if setup_logging is not in path (though task 11 should have created it)
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    def setup_logging(name):
        return logging.getLogger(name)
    def get_data_quality_logger():
        return logging.getLogger("data_quality")

from config import get_path_env_override

logger = logging.getLogger(__name__)
data_logger = get_data_quality_logger()

def ensure_directories(base_path: Path):
    """Ensure all required output directories exist."""
    dirs = [
        base_path / "results" / "logs",
        base_path / "data" / "processed"
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

def load_csv_as_dict_set(filepath: Path) -> set:
    """Load a CSV file and return a set of unique participant_ids."""
    if not filepath.exists():
        logger.warning(f"File not found: {filepath}")
        return set()
    
    import pandas as pd
    try:
        df = pd.read_csv(filepath)
        # Expect 'participant_id' column based on task descriptions
        if 'participant_id' in df.columns:
            return set(df['participant_id'].dropna().unique())
        else:
            # Fallback: assume first column is ID if 'participant_id' missing
            # Log this discrepancy
            logger.warning(f"Column 'participant_id' not found in {filepath}. Using first column.")
            return set(df.iloc[:, 0].dropna().unique())
    except Exception as e:
        logger.error(f"Error reading {filepath}: {e}")
        return set()

def validate_covariate_file(filepath: Path, expected_ids: set, covariate_name: str) -> Dict[str, Any]:
    """
    Validate a single covariate file.
    Returns a dict with validation status and details.
    """
    result = {
        "file": str(filepath),
        "covariate_name": covariate_name,
        "exists": filepath.exists(),
        "valid": False,
        "issues": []
    }

    if not result["exists"]:
        result["issues"].append("File does not exist")
        return result

    try:
        # Load the file
        if filepath.suffix == '.csv':
            df = pd.read_csv(filepath)
        elif filepath.suffix == '.parquet':
            df = pd.read_parquet(filepath)
        else:
            result["issues"].append(f"Unsupported file format: {filepath.suffix}")
            return result

        # Check for participant_id column
        if 'participant_id' not in df.columns:
            # Try to infer if the first column is the ID
            if len(df.columns) > 0:
                first_col = df.columns[0]
                # If it looks like an ID (e.g., contains 'id' or is the only non-data col)
                # For safety, we assume the task output format includes participant_id
                result["issues"].append(f"Missing 'participant_id' column. Found columns: {list(df.columns)}")
                return result
            else:
                result["issues"].append("Empty file or no columns")
                return result

        file_ids = set(df['participant_id'].dropna().unique())
        result["total_records"] = len(df)
        result["unique_participants"] = len(file_ids)

        # Check for missing rows in the file itself (NaN in participant_id)
        null_ids = df['participant_id'].isna().sum()
        if null_ids > 0:
            result["issues"].append(f"Contains {null_ids} rows with missing participant_id")

        # Check against expected set
        missing_in_file = expected_ids - file_ids
        extra_in_file = file_ids - expected_ids

        if missing_in_file:
            result["issues"].append(f"Missing {len(missing_in_file)} participants found in reference set")
            # Don't log all IDs to avoid log spam, just count
        if extra_in_file:
            result["issues"].append(f"Contains {len(extra_in_file)} participants not in reference set")

        # Determine validity
        # We require the file to exist, have no missing IDs in the participant_id column,
        # and contain exactly the set of participants (or a subset if the task allows, but T028e says "match the participant set")
        # "match the participant set" implies exact match or superset? Usually exact for integrity.
        # Let's be strict: no missing, no extra (unless extra is just noise which is bad).
        if not missing_in_file and not extra_in_file and null_ids == 0:
            result["valid"] = True
        else:
            result["valid"] = False

    except Exception as e:
        result["issues"].append(f"Error processing file: {str(e)}")
    
    return result

def main():
    parser = argparse.ArgumentParser(description="Validate covariate integrity for T028e")
    parser.add_argument("--base-path", type=str, default=None, help="Base project path. Defaults to current dir.")
    args = parser.parse_args()

    base_path = Path(args.base_path) if args.base_path else Path.cwd()
    ensure_directories(base_path)

    # Define input files based on T028a, T028b, T028c, T028d
    # T028a: data/processed/covariates.csv
    # T028b: data/processed/dilemma_choices.csv
    # T028c: data/processed/dilemma_complexity.csv
    # T028d: data/processed/time_of_day.csv
    
    covariate_files = [
        (base_path / "data" / "processed" / "covariates.csv", "covariates"),
        (base_path / "data" / "processed" / "dilemma_choices.csv", "dilemma_choices"),
        (base_path / "data" / "processed" / "dilemma_complexity.csv", "dilemma_complexity"),
        (base_path / "data" / "processed" / "time_of_day.csv", "time_of_day"),
    ]

    # We need a reference set of participants.
    # The most logical source is the merged dataset (if it exists) or the raw moral machine data.
    # Since T028e depends on T019b-finalize (merged_dataset.parquet) and T017-run (filtered data),
    # we try to load the merged dataset first. If not, we try the raw moral machine data.
    
    reference_ids = set()
    merged_path = base_path / "data" / "processed" / "merged_dataset.parquet"
    raw_path = base_path / "data" / "raw" / "moral_machine.csv.gz"

    if merged_path.exists():
        try:
            import pandas as pd
            df = pd.read_parquet(merged_path)
            if 'participant_id' in df.columns:
                reference_ids = set(df['participant_id'].dropna().unique())
                logger.info(f"Loaded {len(reference_ids)} participant IDs from merged_dataset.parquet")
            else:
                logger.warning("participant_id not found in merged_dataset.parquet. Trying raw data.")
        except Exception as e:
            logger.error(f"Failed to load merged dataset: {e}")
    
    if not reference_ids and raw_path.exists():
        try:
            import pandas as pd
            df = pd.read_csv(raw_path, compression='gzip')
            # Map column name if necessary
            if 'participant_id' in df.columns:
                reference_ids = set(df['participant_id'].dropna().unique())
            elif 'id' in df.columns:
                reference_ids = set(df['id'].dropna().unique())
            else:
                # Fallback to first column
                reference_ids = set(df.iloc[:, 0].dropna().unique())
            logger.info(f"Loaded {len(reference_ids)} participant IDs from moral_machine.csv.gz")
        except Exception as e:
            logger.error(f"Failed to load raw moral machine data: {e}")

    if not reference_ids:
        logger.error("Could not determine reference participant set. Validation cannot proceed.")
        # Create a failure log
        validation_result = {
            "status": "failed",
            "reason": "Could not determine reference participant set",
            "files_validated": []
        }
    else:
        validation_results = []
        all_valid = True

        for filepath, name in covariate_files:
            res = validate_covariate_file(filepath, reference_ids, name)
            validation_results.append(res)
            if not res["valid"]:
                all_valid = False

        validation_result = {
            "status": "passed" if all_valid else "failed",
            "reference_set_size": len(reference_ids),
            "files_validated": validation_results,
            "summary": "All covariate files match the participant set and have no missing rows." if all_valid else "One or more covariate files have integrity issues."
        }

    # Write output
    output_path = base_path / "results" / "logs" / "covariate_validation.json"
    with open(output_path, 'w') as f:
        json.dump(validation_result, f, indent=2)

    logger.info(f"Validation complete. Results written to {output_path}")
    data_logger.info(f"Covariate Validation: {'PASS' if validation_result['status'] == 'passed' else 'FAIL'}")

    if not all_valid:
        # Log specific issues to the data quality log for debugging
        for res in validation_results:
            if not res["valid"]:
                data_logger.warning(f"Issues in {res['covariate_name']}: {', '.join(res['issues'])}")

    return 0 if all_valid else 1

if __name__ == "__main__":
    sys.exit(main())
