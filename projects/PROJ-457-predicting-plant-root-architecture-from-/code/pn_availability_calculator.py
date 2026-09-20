"""
T035a: Calculate P/N Availability Rate.

Calculates the 'P/N Availability Rate' (rows with P/N / total rows) 
as a redefinition of SC-001 due to ISRIC exclusion.

Writes result to `artifacts/reports/metrics.json`.

Prerequisites:
- T015 (Filtering logic)
- T035c (Original SC-001 measure)
- artifacts/sc_amendments.json (AM-001)
"""
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Import config utilities
try:
    from config import get_config, setup_logging
except ImportError:
    # Fallback for direct execution if path isn't set up correctly
    sys.path.insert(0, str(Path(__file__).parent))
    from config import get_config, setup_logging

# Import data ingestion to load the raw data
try:
    from data_ingestion import load_processed_data
except ImportError:
    from data_ingestion import load_processed_data


def load_json_file(file_path: Path) -> Dict[str, Any]:
    """Load a JSON file and return its contents."""
    if not file_path.exists():
        raise FileNotFoundError(f"Required file not found: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json_file(file_path: Path, data: Dict[str, Any]) -> None:
    """Save a dictionary to a JSON file."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


def calculate_pn_availability_rate(logger: logging.Logger) -> Dict[str, Any]:
    """
    Calculate the P/N Availability Rate.
    
    1. Read artifacts/sc_amendments.json (AM-001) to link calculation.
    2. Load raw PlantPheno data (or the pre-filtered dataset if raw is unavailable, 
       but the task specifies 'Total rows in raw PlantPheno dataset').
       Since T015 produces a filtered dataset, we assume the 'processed' data 
       loaded via load_processed_data represents the state after T015.
       
       However, the task says: "Denominator: Total rows in raw PlantPheno dataset".
       If the raw data is not persisted separately, we must rely on the 
       species_counts.json (from T015e) which logs `total_species_input` and 
       exclusion counts. 
       
       Wait, T015e logs `rows_excluded_by...` but not necessarily the *total raw rows*.
       Let's check T015e requirements: 
       `total_species_input`, `excluded_species_count`, `excluded_species_list`, 
       `rows_excluded_by_source`, `rows_excluded_by_missing_nutrients`, `rows_excluded_by_sample_size`.
       It does NOT explicitly log `total_raw_rows`.
       
       Alternative: The task description for T035a says "Denominator: Total rows in raw PlantPheno dataset".
       If we cannot access the raw dataset directly (it might be in memory or deleted), 
       we must reconstruct it or load it.
       
       Looking at T013/T015 flow: T015 filters the data. If the raw data isn't saved to `data/raw/`, 
       we might need to re-fetch or assume the 'processed' data loaded by T016/T035a 
       is the closest proxy, but the prompt is strict about "raw".
       
       Let's assume `load_processed_data` loads the data *after* T015 filtering.
       To get the raw count, we can sum:
       (Rows in processed) + (rows_excluded_by_source) + (rows_excluded_by_missing_nutrients) + (rows_excluded_by_sample_size)
       
       We need to read `artifacts/reports/species_counts.json` (T015e output) to get these counts.
       
    3. Calculate: 
       Numerator = Rows with P/N (in the filtered dataset, assuming T015c excluded missing nutrients).
       Denominator = Total Raw Rows.
       
       Actually, T015c excludes rows with missing nutrients. So the processed dataset 
       contains ONLY rows with P/N.
       Therefore, Numerator = len(processed_df).
       Denominator = len(processed_df) + sum(exclusions).
       
       Rate = Numerator / Denominator.
    
    4. Write to `artifacts/reports/metrics.json`.
    """
    config = get_config()
    
    # 1. Link to AM-001
    amendments_path = Path(config['ARTIFACTS_DIR']) / 'sc_amendments.json'
    try:
        amendments = load_json_file(amendments_path)
        logger.info(f"Linked to amendment record: {amendments_path}")
    except FileNotFoundError:
        logger.warning(f"Amendment record {amendments_path} not found. Proceeding without explicit link.")
        amendments = {}

    # 2. Load exclusion counts from T015e
    counts_path = Path(config['ARTIFACTS_DIR']) / 'reports' / 'species_counts.json'
    try:
        counts_data = load_json_file(counts_path)
    except FileNotFoundError:
        logger.error(f"Species counts file not found: {counts_path}. Cannot calculate denominator.")
        raise FileNotFoundError("Required T015e artifact missing.")

    # 3. Load the processed data (which contains rows with P/N, as T015c excluded missing)
    #    Note: T015c says "exclude rows where Phosphorus or Nitrogen values are missing".
    #    So the remaining data has P/N.
    try:
        df = load_processed_data()
        numerator = len(df)
        logger.info(f"Loaded processed data. Rows with P/N (Numerator): {numerator}")
    except Exception as e:
        logger.error(f"Failed to load processed data: {e}")
        raise

    # 4. Calculate Denominator
    #    Denominator = Numerator + Exclusions
    exclusions = (
        counts_data.get('rows_excluded_by_source', 0) +
        counts_data.get('rows_excluded_by_missing_nutrients', 0) +
        counts_data.get('rows_excluded_by_sample_size', 0)
    )
    denominator = numerator + exclusions
    
    if denominator == 0:
        rate = 0.0
        logger.warning("Denominator is zero. Setting rate to 0.0.")
    else:
        rate = numerator / denominator

    logger.info(f"Total Raw Rows (Denominator): {denominator}")
    logger.info(f"P/N Availability Rate: {rate:.4f}")

    # 5. Prepare Output
    metrics_path = Path(config['ARTIFACTS_DIR']) / 'reports' / 'metrics.json'
    
    # Load existing metrics if T035c wrote there
    existing_metrics = {}
    if metrics_path.exists():
        existing_metrics = load_json_file(metrics_path)

    new_metrics = {
        "pn_availability_rate": rate,
        "original_sc001_metric": "merge_success_rate (unavailable due to scope deviation)",
        "amendment_reference": "AM-001",
        "calculation_details": {
            "numerator_rows_with_pn": numerator,
            "denominator_total_raw_rows": denominator,
            "exclusions": {
                "source": counts_data.get('rows_excluded_by_source', 0),
                "missing_nutrients": counts_data.get('rows_excluded_by_missing_nutrients', 0),
                "sample_size": counts_data.get('rows_excluded_by_sample_size', 0)
            }
        }
    }

    # Merge with existing (in case T035c wrote something)
    # We overwrite the specific key but keep others if they exist
    updated_metrics = {**existing_metrics, **new_metrics}

    save_json_file(metrics_path, updated_metrics)
    logger.info(f"Wrote P/N Availability Rate to {metrics_path}")

    return updated_metrics


def main():
    """Main entry point for T035a."""
    logger = setup_logging()
    logger.info("Starting T035a: Calculate P/N Availability Rate")
    
    try:
        result = calculate_pn_availability_rate(logger)
        logger.info("T035a completed successfully.")
        print(f"Result: {result}")
    except Exception as e:
        logger.error(f"T035a failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
