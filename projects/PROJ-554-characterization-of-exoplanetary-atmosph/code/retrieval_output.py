"""
Module to process retrieval results and generate the final output CSV.
Implements T020: Output generation for retrieval results.
"""

import os
import logging
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional

import numpy as np

# Import from local project modules
from config import get_config
from data_models import RetrievalResult, CensorshipStatus
from utils import setup_logging, RetrievalError

logger = logging.getLogger(__name__)


def process_retrieval_results(
    input_dir: Optional[Path] = None,
    output_path: Optional[Path] = None
) -> Path:
    """
    Load retrieval results (simulated or real from previous step),
    and save them to the specified CSV output path.

    This function implements T020:
    - Reads data from the processed retrieval stage (or simulates structure if T019/T021 ran but didn't write CSV yet).
    - Writes `data/processed/retrieval_results.csv` with columns:
      [planet_name, water_mixing_ratio, uncertainty, is_upper_limit, detection_limit, min_detectable_concentration]

    Args:
        input_dir: Directory containing intermediate retrieval data (e.g., from T019/T021).
                   If None, uses config defaults.
        output_path: Path to the output CSV file. If None, uses config defaults.

    Returns:
        Path: The path to the written CSV file.

    Raises:
        FileNotFoundError: If input data is missing and cannot be constructed.
        ValueError: If required data fields are missing.
    """
    config = get_config()
    
    # Default paths
    if input_dir is None:
        input_dir = config.get("paths", {}).get("data_raw", "data/raw")
    if output_path is None:
        output_path = Path(config.get("paths", {}).get("data_processed", "data/processed")) / "retrieval_results.csv"

    logger.info(f"Processing retrieval results from {input_dir} to {output_path}")

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # In a real pipeline, T019/T021 would have populated a list of RetrievalResult objects
    # or written an intermediate file. Since T019/T021 are marked done but the CSV is missing,
    # we must ensure we have the data.
    # We will look for an intermediate JSON or CSV if it exists, otherwise we assume the
    # retrieval logic (T019/T021) ran in memory or we need to re-run the logic.
    # However, per T020's specific role, it is the *output generator*.
    # If the data doesn't exist, we cannot fake it. We must check for the existence of
    # the data produced by T019/T021.
    
    # Attempt to load from a potential intermediate file (e.g., if T021 wrote a temp file)
    # or reconstruct from the raw data if the previous step was just a calculation.
    # Given the execution failure, it's likely the data exists in memory or a temp file
    # that wasn't persisted.
    
    # Strategy: Check for `data/processed/retrieval_intermediate.json` or similar.
    # If not found, we must assume the previous step (T019/T021) failed to persist.
    # But T020 is the one responsible for writing the final CSV.
    # If the previous step didn't write data, T020 cannot proceed without data.
    # However, T019/T021 are marked as completed in the task list.
    # We assume the data is available via a standard location or we must re-run the logic.
    # Since we cannot re-run the full retrieval (T018/T019) without the raw spectra here,
    # we will check for a standard intermediate file.
    
    intermediate_json = Path(input_dir).parent / "processed" / "retrieval_intermediate.json"
    
    results_data = []
    
    if intermediate_json.exists():
        import json
        with open(intermediate_json, 'r') as f:
            raw_results = json.load(f)
            for item in raw_results:
                # Map to expected schema
                results_data.append({
                    "planet_name": item.get("planet_name"),
                    "water_mixing_ratio": item.get("water_mixing_ratio"),
                    "uncertainty": item.get("uncertainty"),
                    "is_upper_limit": item.get("is_upper_limit", False),
                    "detection_limit": item.get("detection_limit"),
                    "min_detectable_concentration": item.get("min_detectable_concentration")
                })
    else:
        # Fallback: If the intermediate file is missing, we must assume the previous step
        # (T019/T021) did not persist its results.
        # Since T020 depends on T019, and T019 is marked done, we assume the data *should*
        # be there. If it's not, we cannot fabricate.
        # However, for the purpose of this task (T020), we must implement the *writing* logic.
        # If the data is missing, we raise an error to indicate the dependency failure.
        # But wait, the execution log says T019/T021 ran but the CSV is missing.
        # It implies the data was computed but not saved.
        # We will assume the data is available in a variable or we need to re-run the logic.
        # Since we can't re-run the full retrieval here, we will check for a CSV or JSON
        # that might have been partially written.
        
        # Check for a partial CSV
        partial_csv = Path(input_dir).parent / "processed" / "retrieval_partial.csv"
        if partial_csv.exists():
            import pandas as pd
            df = pd.read_csv(partial_csv)
            results_data = df.to_dict('records')
        else:
            # If absolutely no data, we must fail loudly.
            # However, in the context of the fix loop, we might need to simulate the
            # *structure* of the data to prove the writing logic works, but the prompt
            # says "NEVER fabricate results".
            # We will assume the data exists in the `data/processed` directory from a
            # previous run that failed to write the final CSV.
            # Let's check for any CSV in data/processed that looks like retrieval data.
            proc_dir = Path(input_dir).parent / "processed"
            for f in proc_dir.glob("*.csv"):
                if "retrieval" in f.name.lower():
                    import pandas as pd
                    df = pd.read_csv(f)
                    # Ensure required columns exist
                    required_cols = ["planet_name", "water_mixing_ratio", "uncertainty", "is_upper_limit", "detection_limit", "min_detectable_concentration"]
                    if all(c in df.columns for c in required_cols):
                        results_data = df.to_dict('records')
                        logger.info(f"Loaded retrieval data from {f}")
                        break
        
        if not results_data:
            # If we still have no data, we cannot proceed.
            # But for the sake of the task implementation, we will assume the data
            # is available via the `data_models` if we re-run the logic.
            # However, we don't have the raw spectra here.
            # We will raise an error to indicate the dependency failure.
            raise FileNotFoundError(
                "No retrieval data found. T019/T021 must have produced data before T020 can run. "
                "Please ensure T019/T021 successfully computed results and persisted them to an intermediate format."
            )

    # Write the final CSV
    fieldnames = [
        "planet_name", 
        "water_mixing_ratio", 
        "uncertainty", 
        "is_upper_limit", 
        "detection_limit", 
        "min_detectable_concentration"
    ]

    with open(output_path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for row in results_data:
            # Ensure all fields are present and formatted correctly
            # Handle None values for upper limits or missing data
            clean_row = {}
            for field in fieldnames:
                val = row.get(field)
                if val is None:
                    # For upper limits, if no value, set to NaN or specific marker
                    if field in ["water_mixing_ratio", "uncertainty", "detection_limit", "min_detectable_concentration"]:
                        clean_row[field] = np.nan
                    elif field == "is_upper_limit":
                        clean_row[field] = False
                    else:
                        clean_row[field] = ""
                else:
                    clean_row[field] = val
            writer.writerow(clean_row)

    logger.info(f"Successfully wrote retrieval results to {output_path}")
    return output_path


def main():
    """
    Main entry point for the retrieval output generation script.
    """
    setup_logging()
    logger.info("Starting retrieval output generation (T020)")
    
    try:
        output_path = process_retrieval_results()
        logger.info(f"Task T020 completed. Output written to {output_path}")
    except FileNotFoundError as e:
        logger.critical(f"Task T020 failed: {e}")
        raise
    except Exception as e:
        logger.critical(f"Task T020 failed with unexpected error: {e}")
        raise


if __name__ == "__main__":
    main()