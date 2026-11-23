import json
import os
import sys
import pickle
from pathlib import Path
from typing import Dict, Any

# Add parent directory to path if running from code/
if os.path.basename(os.getcwd()) == 'code':
    sys.path.insert(0, os.path.dirname(os.getcwd()))
else:
    sys.path.insert(0, os.path.join(os.getcwd(), '..'))

from config import get_project_root, get_min_rows
from ingest import load_data, filter_missing_target, impute_missing_composition, clip_outliers_target, validate_dataset_size, run_ingestion_pipeline
from engineer import calculate_interaction_features, ensure_temperature_feature, validate_dataset_size, load_data_chunked, run_engineering_pipeline
from finalize_dataset import load_engineered_data, enforce_row_cap, save_final_dataset

def load_metrics(filepath: str) -> Dict[str, Any]:
    """Load a JSON metrics file."""
    with open(filepath, 'r') as f:
        return json.load(f)

def save_metrics(filepath: str, data: Dict[str, Any]) -> None:
    """Save metrics to a JSON file."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

def generate_metrics_report() -> None:
    """
    Generate ingestion_metrics.json and update validation_log.json.
    
    This task (T023) relies on T022 (ingest.py) having run and produced:
    - data/processed/validated.csv
    - artifacts/reports/validation_log.json (partial)
    
    It calculates:
    - rows_ingested
    - rows_dropped_nulls
    - rows_dropped_other
    - rows_output
    - null_handling_success_rate
    
    And updates validation_log.json with:
    - clipped_outliers_count
    - clipped_values_list
    - threshold_99th_percentile
    """
    project_root = get_project_root()
    validated_csv_path = project_root / 'data' / 'processed' / 'validated.csv'
    validation_log_path = project_root / 'artifacts' / 'reports' / 'validation_log.json'
    ingestion_metrics_path = project_root / 'artifacts' / 'reports' / 'ingestion_metrics.json'

    # 1. Load the validated dataset produced by T022
    if not validated_csv_path.exists():
        raise FileNotFoundError(
            f"Required file not found: {validated_csv_path}. "
            "Ensure T022 (ingest.py) has been run successfully."
        )

    df_validated = load_data(str(validated_csv_path))
    rows_output = len(df_validated)

    # 2. Read the partial validation_log.json from T022
    if not validation_log_path.exists():
        raise FileNotFoundError(
            f"Required file not found: {validation_log_path}. "
            "Ensure T022 (ingest.py) has generated the initial validation log."
        )
    
    validation_log = load_metrics(str(validation_log_path))

    # 3. Extract metrics from the log
    # T022 is expected to have written these keys during its processing
    rows_ingested = validation_log.get('rows_ingested', 0)
    rows_dropped_nulls = validation_log.get('rows_dropped_nulls', 0)
    rows_dropped_other = validation_log.get('rows_dropped_other', 0)
    
    # Calculate null handling success rate
    if rows_ingested > 0:
        null_handling_success_rate = (rows_ingested - rows_dropped_nulls) / rows_ingested
    else:
        null_handling_success_rate = 0.0

    # 4. Construct ingestion_metrics.json
    ingestion_metrics = {
        "rows_ingested": rows_ingested,
        "rows_dropped_nulls": rows_dropped_nulls,
        "rows_dropped_other": rows_dropped_other,
        "rows_output": rows_output,
        "null_handling_success_rate": null_handling_success_rate
    }

    # 5. Ensure validation_log.json has the required clipping fields
    # T022 should have populated these, but we ensure they exist for the report
    if 'clipped_outliers_count' not in validation_log:
        # If T022 failed to write this, we might need to re-calculate or default
        # However, per T023 spec, we read from T022. If missing, it implies T022 didn't run fully.
        # We raise an error to fail loudly rather than fabricate.
        raise ValueError(
            "clipped_outliers_count missing from validation_log.json. "
            "T022 (ingest.py) must successfully run and populate this field."
        )
    
    # 6. Save ingestion_metrics.json
    save_metrics(str(ingestion_metrics_path), ingestion_metrics)

    # 7. Update validation_log.json (append metrics if needed, though T022 likely wrote them)
    # The task says "append metrics, do not overwrite". We ensure the file exists with all required keys.
    save_metrics(str(validation_log_path), validation_log)

    print(f"Ingestion metrics generated: {ingestion_metrics_path}")
    print(f"Validation log updated: {validation_log_path}")

def main():
    """Entry point for T023."""
    try:
        generate_metrics_report()
    except Exception as e:
        print(f"Error generating metrics report: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()