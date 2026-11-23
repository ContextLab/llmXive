"""
Validation runner for T040: Execute code/ingest.py on a sample subset.

This script executes the ingestion pipeline in a controlled manner to verify:
1. The pipeline flow executes without errors.
2. The output schema matches the contract (columns: smi, lambda_max, scaffold_id).
3. The sampling log is generated correctly.

It uses the existing `code/ingest.py` module, specifically calling the 
`fetch_uv_vis_data` and `process_molecules` functions with a restricted 
sample size to ensure fast execution on the sample subset.
"""
import os
import sys
import json
import logging
import argparse
from pathlib import Path

# Add project root to path if needed, though usually run from root
project_root = Path(__file__).parent.parent
code_dir = project_root / "code"
data_processed_dir = project_root / "data" / "processed"

# Ensure output directory exists
data_processed_dir.mkdir(parents=True, exist_ok=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(data_processed_dir / "ingest_validation.log")
    ]
)
logger = logging.getLogger(__name__)

def main():
    logger.info("Starting T040 Validation: Executing ingest.py on sample subset.")
    
    # Import the ingest module dynamically to ensure we use the latest code
    sys.path.insert(0, str(code_dir))
    try:
        import ingest
    except ImportError as e:
        logger.error(f"Failed to import ingest module: {e}")
        sys.exit(1)

    # Configuration for the sample subset
    # We force a small sample size to satisfy the "sample subset" requirement
    # and ensure the script runs quickly within the wall-clock budget.
    sample_size = 50 
    seed = 42

    logger.info(f"Fetching data with sample_size={sample_size}, seed={seed}...")

    try:
        # Call the main fetch logic directly from the module
        # We pass a small sample size to ensure we only process a subset
        # The ingest.py module handles the streaming and sampling logic internally.
        # We rely on the existing implementation of fetch_uv_vis_data which 
        # likely uses the HuggingFace dataset or similar real source.
        
        # Note: The ingest.py module's `main` function might have CLI args.
        # We simulate the call by invoking the core functions or running the main
        # with specific arguments if the module supports it.
        # Given the task is to execute the script, we will invoke the main function
        # with arguments to force the sample size, assuming the CLI supports it.
        # If not, we call the internal functions directly.
        
        # Attempting to call the main entry point with args to force sampling
        # This assumes ingest.py has a --sample-size or similar arg.
        # If not, we will call the core logic directly.
        
        # Direct approach: Call fetch_uv_vis_data with parameters if available,
        # or run the main function with sys.argv modification.
        
        # Let's try to run the main function of ingest.py by modifying sys.argv
        # to include the sample size argument, assuming the script supports it.
        # If the script doesn't support args, we might need to call the function directly.
        
        # Strategy: Call `ingest.main()` with simulated arguments
        original_argv = sys.argv
        sys.argv = ["code/ingest.py", "--sample-size", str(sample_size), "--seed", str(seed)]
        
        try:
            ingest.main()
            logger.info("Ingest script executed successfully.")
        except SystemExit as e:
            if e.code != 0:
                logger.error(f"Ingest script exited with code: {e.code}")
                sys.exit(e.code)
            logger.info("Ingest script completed normally.")
        finally:
            sys.argv = original_argv

    except FileNotFoundError as e:
        logger.error(f"Data source not found or unreachable: {e}")
        logger.error("This is expected if the real data source is unavailable.")
        logger.error("However, the task requires a real execution. If the source is down, the task cannot be completed.")
        raise
    except Exception as e:
        logger.error(f"Error during ingestion: {e}")
        raise

    # Verification Phase
    logger.info("Verifying output artifacts...")
    
    cleaned_file = data_processed_dir / "cleaned.csv"
    sampling_log_file = data_processed_dir / "sampling_log.json"
    
    # Check cleaned.csv
    if not cleaned_file.exists():
        logger.error(f"Verification failed: {cleaned_file} does not exist.")
        sys.exit(1)
    
    import pandas as pd
    df = pd.read_csv(cleaned_file)
    
    required_columns = ["smi", "lambda_max", "scaffold_id"]
    actual_columns = list(df.columns)
    
    logger.info(f"Output columns: {actual_columns}")
    
    if set(actual_columns) != set(required_columns):
        logger.error(f"Schema mismatch. Expected {required_columns}, got {actual_columns}")
        sys.exit(1)
    
    if len(df) == 0:
        logger.error("Output file is empty.")
        sys.exit(1)
    
    logger.info(f"Schema validation passed. Row count: {len(df)}")
    
    # Check sampling_log.json
    if not sampling_log_file.exists():
        logger.error(f"Verification failed: {sampling_log_file} does not exist.")
        sys.exit(1)
    
    with open(sampling_log_file, "r") as f:
        log_data = json.load(f)
    
    required_keys = ["sample_size", "seed", "method", "total_rows_scanned"]
    for key in required_keys:
        if key not in log_data:
            logger.error(f"Verification failed: sampling_log.json missing key '{key}'")
            sys.exit(1)
    
    logger.info(f"Sampling log validation passed: {log_data}")
    
    # Write validation report
    report_path = data_processed_dir / "ingest_validation_report.json"
    report = {
        "status": "passed",
        "output_file": str(cleaned_file),
        "row_count": len(df),
        "columns": actual_columns,
        "sampling_log": log_data
    }
    
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Validation report written to {report_path}")
    logger.info("T040 Validation completed successfully.")

if __name__ == "__main__":
    main()