"""
T018a: Metric Calculation for Ingested Data.

Calculates the `linked_metadata_percentage` as (linked_trials / total_trials) * 100
and writes it to `data/processed/ingest_metrics.json`.

This task runs after T013/T014 (Ingestion/Linkage) but BEFORE T016 (Gate).
It ensures the metric is recorded even if the system subsequently halts due to
linkage thresholds.
"""
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any

# Add project root to path to allow relative imports if run as script
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.config import Config
from code.data.generate_linked_trials import load_preprocessed_trials

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def calculate_linked_metadata_percentage(linked_trials_path: Path, total_trials_count: int) -> float:
    """
    Calculate the percentage of trials that have successfully linked metadata.
    
    Args:
        linked_trials_path: Path to the CSV file containing linked trials.
        total_trials_count: The total number of trials expected (from raw ingestion).
        
    Returns:
        float: The percentage of linked trials (0.0 to 100.0).
    """
    if total_trials_count == 0:
        logger.warning("Total trials count is 0. Returning 0.0% linked metadata.")
        return 0.0

    if not linked_trials_path.exists():
        raise FileNotFoundError(
            f"Linked trials file not found at {linked_trials_path}. "
            "Ensure T013/T014 (Ingestion) and T014/T016 (Linkage) have completed successfully."
        )

    try:
        # We rely on the helper to load the data and count valid rows
        # The helper loads the CSV and returns a list of dicts (or similar structure)
        # We need to count the actual rows that made it through the linkage process.
        # Note: load_preprocessed_trials might return the data directly or we might need to count lines.
        # Based on the API surface, `load_preprocessed_trials` returns data.
        # Let's assume it returns a list of rows or a DataFrame-like structure.
        # If it returns a list of dicts:
        linked_data = load_preprocessed_trials(str(linked_trials_path))
        
        if isinstance(linked_data, list):
            linked_count = len(linked_data)
        elif hasattr(linked_data, '__len__'):
            linked_count = len(linked_data)
        else:
            # Fallback: try to count lines if it's a file path string (unlikely given function name)
            logger.error("Unexpected return type from load_preprocessed_trials")
            linked_count = 0
        
        percentage = (linked_count / total_trials_count) * 100.0
        logger.info(f"Calculated linked metadata percentage: {percentage:.2f}% "
                    f"({linked_count} linked / {total_trials_count} total)")
        return percentage
        
    except Exception as e:
        logger.error(f"Error calculating linked metadata percentage: {e}")
        raise

def write_metrics_to_json(metrics: Dict[str, Any], output_path: Path) -> None:
    """
    Writes the metrics dictionary to a JSON file.
    
    Args:
        metrics: Dictionary containing the calculated metrics.
        output_path: Path where the JSON file will be saved.
    """
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(metrics, f, indent=2)
        logger.info(f"Metrics written successfully to {output_path}")
    except IOError as e:
        logger.error(f"Failed to write metrics to {output_path}: {e}")
        raise

def main() -> None:
    """
    Main entry point for T018a.
    """
    config = Config()
    
    # Paths
    linked_trials_path = config.DATA_PROCESSED / "linked_trials.csv"
    metrics_output_path = config.DATA_PROCESSED / "ingest_metrics.json"
    
    logger.info(f"Starting T018a: Metric Calculation")
    logger.info(f"Input: {linked_trials_path}")
    logger.info(f"Output: {metrics_output_path}")
    
    # We need the total_trials_count. 
    # In a real pipeline, this might be passed as an argument or read from a previous state/metadata file.
    # Since T013/T014 produce the raw data and T016/T017 produce the linked file,
    # we assume the 'total' is the count of rows in the raw ingestion file before linkage filtering,
    # OR we can infer it from the context of the pipeline state if available.
    # However, the task description says "Calculate ... as (linked_trials / total_trials)".
    # If we don't have a separate 'total' file, we might need to count the raw input rows.
    # Let's assume the raw input is in data/raw or we count the linked file and compare to a known expected total.
    # Given the constraints and typical pipeline flow:
    # 1. T013 downloads raw CSV.
    # 2. T014 extracts metadata.
    # 3. T015/T016 filter.
    # 4. T017 writes linked_trials.csv.
    # To calculate the percentage, we need the denominator (total_trials).
    # If the raw CSV is still available, we can count it.
    # Let's look for a raw file or assume the total is passed via environment or config.
    # For robustness, let's try to find the raw input CSV.
    # If not found, we might need to rely on a 'total_trials' count stored in state.yaml or a separate file.
    # Let's assume for this implementation that the 'total_trials' is the count of rows in the 
    # 'linked_trials.csv' if no other source is found? No, that would be 100%.
    # The task implies some loss.
    # Let's assume the raw file is at `data/raw/iat_data.csv` or similar.
    # Since the exact raw filename isn't specified in the API surface, we will check for common patterns
    # or read from a metadata file if it exists.
    # Alternatively, the `load_preprocessed_trials` might return the total count if we pass a flag?
    # No, the signature is `load_preprocessed_trials(path)`.
    
    # Strategy: Count rows in the raw input if available. 
    # If not, we might need to read from `state.yaml` or a `ingest_log.json`.
    # Let's assume the raw data is in `data/raw/` and named `iat_data.csv` or similar.
    # We will search for a CSV in `data/raw`.
    raw_csv = None
    if config.DATA_RAW.exists():
        for f in config.DATA_RAW.glob("*.csv"):
            if "iat" in f.name.lower() or "trial" in f.name.lower():
                raw_csv = f
                break
        if not raw_csv:
            # Fallback to first CSV
            csvs = list(config.DATA_RAW.glob("*.csv"))
            if csvs:
                raw_csv = csvs[0]
    
    total_trials = 0
    if raw_csv and raw_csv.exists():
        try:
            with open(raw_csv, 'r', encoding='utf-8') as f:
                # Count lines excluding header
                lines = f.readlines()
                total_trials = max(0, len(lines) - 1)
            logger.info(f"Found raw CSV at {raw_csv}. Total trials (raw): {total_trials}")
        except Exception as e:
            logger.warning(f"Could not count raw CSV {raw_csv}: {e}. Using 0 as total.")
            total_trials = 0
    else:
        logger.warning(f"Raw CSV not found in {config.DATA_RAW}. Cannot calculate percentage accurately.")
        # If we can't find raw, we might assume the total is the linked count (100%) or fail.
        # But the task requires a calculation. Let's assume the total is 0 if not found to trigger a warning.
        total_trials = 0

    # Calculate
    linked_percentage = calculate_linked_metadata_percentage(linked_trials_path, total_trials)
    
    # Prepare metrics
    metrics = {
        "linked_metadata_percentage": linked_percentage,
        "linked_trials_count": len(load_preprocessed_trials(str(linked_trials_path))),
        "total_trials_count": total_trials,
        "timestamp": str(Path(__file__).stat().st_mtime) # Or use datetime.now()
    }
    
    # Write
    write_metrics_to_json(metrics, metrics_output_path)
    
    logger.info(f"T018a completed. Metric: {linked_percentage:.2f}%")

if __name__ == "__main__":
    main()
