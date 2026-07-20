"""
Main orchestrator for the energy consumption pipeline.

This module coordinates the aggregation of raw inference results into a clean,
analysis-ready dataset. It enforces data integrity by filtering out invalid
entries (null energy, zero tokens) before downstream statistical analysis.
"""
import os
import csv
import logging
from code.config import DATA_PROCESSED_DIR

# Configure logging for the orchestrator
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def aggregate_results():
    """
    Reads energy_results_raw.csv, filters rows where energy_kwh is null or tokens_generated is 0,
    and writes the clean dataset to energy_results_aggregated.csv.
    
    Filters:
    - Removes rows where energy_kwh is None, empty string, "None", or non-numeric.
    - Removes rows where tokens_generated is None, empty string, "0", or non-numeric.
    - Removes rows where values are <= 0 (sanity check).
    
    Output columns: model_id, problem_id, tokens_generated, energy_kwh, runtime_seconds, pass_fail_status
    
    Side Effects:
    - Writes filtered rows to data/processed/filtered_rows.csv
    - Writes clean rows to data/processed/energy_results_aggregated.csv
    """
    raw_path = os.path.join(DATA_PROCESSED_DIR, "energy_results_raw.csv")
    agg_path = os.path.join(DATA_PROCESSED_DIR, "energy_results_aggregated.csv")
    filtered_path = os.path.join(DATA_PROCESSED_DIR, "filtered_rows.csv")

    logger.info(f"Starting aggregation from {raw_path}")

    if not os.path.exists(raw_path):
        logger.error(f"Raw results not found at {raw_path}. Run inference first.")
        raise FileNotFoundError(f"Raw results not found at {raw_path}. Run inference first.")

    valid_rows = []
    filtered_rows = []

    try:
        with open(raw_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames:
                logger.warning("Raw file appears empty or has no headers.")
                rows = []
            else:
                rows = list(reader)
        
        total_rows = len(rows)
        logger.info(f"Found {total_rows} rows in raw data.")

        for row in rows:
            # Filter out rows where energy_kwh is null or tokens_generated is 0
            energy = row.get("energy_kwh")
            tokens = row.get("tokens_generated")
            
            # Check for null/None string or empty
            energy_is_null = (
                energy is None or 
                energy == "" or 
                energy == "None" or 
                energy.lower() == "nan"
            )
            
            tokens_is_zero_or_null = (
                tokens is None or 
                tokens == "" or 
                tokens == "0" or 
                tokens.lower() == "nan"
            )

            if energy_is_null or tokens_is_zero_or_null:
                filtered_rows.append(row)
                continue
            
            # Convert to float for safety to ensure numeric validity
            try:
                energy_val = float(energy)
                tokens_val = float(tokens)
            except ValueError:
                filtered_rows.append(row)
                continue

            # Additional check: ensure energy and tokens are positive (sanity check)
            if energy_val <= 0 or tokens_val <= 0:
                filtered_rows.append(row)
                continue

            valid_rows.append(row)

    except Exception as e:
        logger.error(f"Error reading raw file: {e}")
        raise

    # Ensure output directory exists
    os.makedirs(DATA_PROCESSED_DIR, exist_ok=True)

    # Write filtered rows (evidence of failure)
    if filtered_rows:
        with open(filtered_path, "w", newline="", encoding="utf-8") as f:
            fieldnames = ["model_id", "problem_id", "tokens_generated", "energy_kwh", "runtime_seconds", "pass_fail_status"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in filtered_rows:
                writer.writerow(row)
        logger.info(f"Filtered rows written to {filtered_path}")
    else:
        logger.info("No rows were filtered; all data is valid.")

    # Write clean dataset
    if not valid_rows:
        logger.warning("No valid rows found after filtering. Creating empty output file.")

    with open(agg_path, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["model_id", "problem_id", "tokens_generated", "energy_kwh", "runtime_seconds", "pass_fail_status"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in valid_rows:
            writer.writerow(row)
    
    logger.info(f"Aggregated results written to {agg_path}")
    logger.info(f"Filtered {len(filtered_rows)} invalid rows, kept {len(valid_rows)} valid rows.")
    print(f"Aggregated results written to {agg_path}")
    print(f"Filtered {len(filtered_rows)} invalid rows, kept {len(valid_rows)} valid rows.")

if __name__ == "__main__":
    aggregate_results()