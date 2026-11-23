"""
Main orchestrator for the energy consumption pipeline.

This module coordinates the aggregation of raw inference results into a clean,
analysis-ready dataset. It enforces data integrity by filtering out invalid
entries (null energy, zero tokens) before downstream statistical analysis.

It also provides runtime estimation logic for T034 verification.
"""
import os
import csv
import logging
import time
from code.config import DATA_PROCESSED_DIR, MODEL_IDS

# Configure logging for the orchestrator
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def estimate_runtime():
    """
    Estimates the total runtime of the pipeline based on model sizes and HumanEval count.
    
    Logic:
    1. Load HumanEval count (approx 164 problems).
    2. Define base inference times per problem for each model tier (empirical estimates for CPU).
       - GPT2-small: ~2.0s
       - CodeBERT: ~3.5s
       - StarCoder-1B: ~12.0s (larger model, CPU bound)
    3. Add overhead for stats (negligible) and plotting (negligible).
    4. Return total estimated seconds.
    
    Returns:
        float: Estimated total runtime in seconds.
    """
    # Constants
    NUM_PROBLEMS = 164
    
    # Empirical estimates for CPU inference per problem (seconds)
    # These are conservative estimates to ensure the 6-hour limit is respected.
    # GPT2-small (34M params)
    time_gpt2 = 2.0 
    # CodeBERT (125M params)
    time_codebert = 3.5
    # StarCoder-1B (1.1B params)
    time_starcoder = 12.0
    
    total_inference_time = (
        (NUM_PROBLEMS * time_gpt2) +
        (NUM_PROBLEMS * time_codebert) +
        (NUM_PROBLEMS * time_starcoder)
    )
    
    # Overhead for evaluation, stats, plotting (approx 5 mins)
    overhead_seconds = 300
    
    total_estimated = total_inference_time + overhead_seconds
    
    logger.info(f"Estimated runtime: {total_estimated:.2f} seconds ({total_estimated/3600:.2f} hours)")
    return total_estimated

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
        logger.error(f"Raw results not found at {raw_path}. Run inference and evaluation first.")
        raise FileNotFoundError(f"Raw results not found at {raw_path}. Run inference and evaluation first.")

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
                str(energy).lower() == "nan"
            )
            
            tokens_is_zero_or_null = (
                tokens is None or 
                tokens == "" or 
                tokens == "0" or 
                str(tokens).lower() == "nan"
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

def run_full_pipeline():
    """
    Orchestrates the full pipeline: Inference -> Evaluation -> Aggregation -> Analysis -> Visualization.
    This function is called by run.sh to execute the full workflow.
    """
    logger.info("Starting full pipeline execution.")
    
    # 1. Inference
    logger.info("Step 1: Running Inference...")
    try:
        from code.inference import main as inference_main
        inference_main()
    except Exception as e:
        logger.error(f"Inference failed: {e}")
        raise

    # 2. Evaluation
    logger.info("Step 2: Running Evaluation...")
    try:
        from code.evaluation import main as evaluation_main
        evaluation_main()
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        raise

    # 3. Aggregation
    logger.info("Step 3: Running Aggregation...")
    try:
        aggregate_results()
    except Exception as e:
        logger.error(f"Aggregation failed: {e}")
        raise

    # 4. Analysis
    logger.info("Step 4: Running Statistical Analysis...")
    try:
        from code.analysis import main as analysis_main
        analysis_main()
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise

    # 5. Visualization
    logger.info("Step 5: Running Visualization...")
    try:
        from code.visualization import main as visualization_main
        visualization_main()
    except Exception as e:
        logger.error(f"Visualization failed: {e}")
        raise

    logger.info("Pipeline execution completed successfully.")
    print("Pipeline completed successfully.")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--estimate":
        estimate_runtime()
    else:
        run_full_pipeline()
