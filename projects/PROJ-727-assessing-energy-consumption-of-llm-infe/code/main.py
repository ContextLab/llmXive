"""
Main orchestrator for the energy consumption pipeline.
"""
import os
import csv
from code.config import DATA_PROCESSED_DIR

def aggregate_results():
    """
    Reads energy_results_raw.csv, filters rows where energy_kwh is null or tokens_generated is 0,
    and writes the clean dataset to energy_results_aggregated.csv.
    
    Filters:
    - Removes rows where energy_kwh is None, empty string, "None", or non-numeric.
    - Removes rows where tokens_generated is None, empty string, "0", or non-numeric.
    
    Output columns: model_id, problem_id, tokens_generated, energy_kwh, runtime_seconds, pass_fail_status
    """
    raw_path = os.path.join(DATA_PROCESSED_DIR, "energy_results_raw.csv")
    agg_path = os.path.join(DATA_PROCESSED_DIR, "energy_results_aggregated.csv")

    if not os.path.exists(raw_path):
        raise FileNotFoundError(f"Raw results not found at {raw_path}. Run inference first.")

    rows = []
    with open(raw_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Filter out rows where energy_kwh is null or tokens_generated is 0
            energy = row.get("energy_kwh")
            tokens = row.get("tokens_generated")
            
            # Check for null/None string or empty
            if energy is None or energy == "" or energy == "None":
                continue
            if tokens is None or tokens == "" or tokens == "0":
                continue
            
            # Convert to float for safety to ensure numeric validity
            try:
                energy_val = float(energy)
                tokens_val = float(tokens)
            except ValueError:
                continue

            # Additional check: ensure energy and tokens are positive (sanity check)
            if energy_val <= 0 or tokens_val <= 0:
                continue

            rows.append(row)

    # Ensure output directory exists
    os.makedirs(os.path.dirname(agg_path), exist_ok=True)

    with open(agg_path, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["model_id", "problem_id", "tokens_generated", "energy_kwh", "runtime_seconds", "pass_fail_status"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    
    print(f"Aggregated results written to {agg_path}")
    print(f"Filtered {len(rows)} valid rows from raw data.")

if __name__ == "__main__":
    aggregate_results()