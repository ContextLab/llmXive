"""
Generate Baseline Results for Reproducibility Verification (T030a).

This script executes the full analysis pipeline (run_statistics.py) to generate
the ground truth results required for the 5% numerical tolerance check in the
CI reproducibility workflow.

It ensures:
1. The analysis script is run end-to-end.
2. The resulting metrics are captured.
3. A 'baseline_results.json' is written to data/analysis_results/.
4. The script fails loudly if input data is missing (no synthetic fallback).
"""
import os
import sys
import json
import time
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path to ensure imports work regardless of CWD
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.logging_utils import get_logger

logger = get_logger(__name__)

# Configuration paths
ANALYSIS_SCRIPT = PROJECT_ROOT / "code" / "analysis" / "run_statistics.py"
INPUT_LOGS = PROJECT_ROOT / "data" / "interaction_logs" / "anonymized_logs.csv"
INPUT_SUMMARIES_LLM = PROJECT_ROOT / "data" / "summaries" / "llm_sim_summaries.csv"
INPUT_SUMMARIES_RULE = PROJECT_ROOT / "data" / "summaries" / "rule_summaries.csv"
OUTPUT_DIR = PROJECT_ROOT / "data" / "analysis_results"
BASELINE_FILE = OUTPUT_DIR / "baseline_results.json"

def verify_input_data() -> bool:
    """
    Verify that all required input files exist.
    Returns True if all are present, False otherwise.
    """
    required_files = [
        ANALYSIS_SCRIPT,
        INPUT_LOGS,
        INPUT_SUMMARIES_LLM,
        INPUT_SUMMARIES_RULE
    ]

    missing = []
    for f in required_files:
        if not f.exists():
            missing.append(str(f))

    if missing:
        logger.error(f"Missing required input files: {missing}")
        logger.error("Cannot generate baseline results without real input data.")
        logger.error("Ensure US1 (Data Collection) and US2 (Analysis Setup) are complete.")
        return False

    return True

def load_analysis_results() -> Optional[Dict[str, Any]]:
    """
    Attempt to load existing analysis results if the script has been run previously.
    This is a fallback for verification, but the primary goal is to re-run the script.
    """
    # We actually want to force a re-run to ensure the baseline matches the current code state.
    # However, if the script fails, we might want to check if previous results exist to report error context.
    if BASELINE_FILE.exists():
        try:
            with open(BASELINE_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.warning("Existing baseline_results.json is corrupt. Will regenerate.")
            return None
    return None

def save_baseline_results(results: Dict[str, Any]) -> bool:
    """
    Save the results to the baseline file.
    """
    try:
        # Ensure output directory exists
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        with open(BASELINE_FILE, 'w') as f:
            json.dump(results, f, indent=2, sort_keys=True)

        logger.info(f"Baseline results saved to {BASELINE_FILE}")
        return True
    except Exception as e:
        logger.error(f"Failed to save baseline results: {e}")
        return False

def run_analysis_pipeline() -> Dict[str, Any]:
    """
    Execute the run_statistics.py script to generate fresh results.
    Returns the parsed JSON output or raises an exception on failure.
    """
    logger.info(f"Executing analysis script: {ANALYSIS_SCRIPT}")
    
    start_time = time.time()
    
    try:
        # Run the script as a subprocess to ensure a clean environment
        # and to capture any stdout/stderr that might be JSON or logs.
        # We pass the path to the script directly.
        result = subprocess.run(
            [sys.executable, str(ANALYSIS_SCRIPT)],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour timeout for the analysis
        )

        elapsed = time.time() - start_time

        if result.returncode != 0:
            logger.error(f"Analysis script failed with return code {result.returncode}")
            logger.error(f"STDOUT:\n{result.stdout}")
            logger.error(f"STDERR:\n{result.stderr}")
            raise RuntimeError(f"Analysis pipeline failed: {result.stderr}")

        logger.info(f"Analysis script completed in {elapsed:.2f}s")

        # The run_statistics.py script writes results to data/analysis_results/results.csv
        # and potentially other files. We need to load the primary results to package as baseline.
        # We assume run_statistics.py writes 'results.csv' as per T024a.
        
        results_csv = OUTPUT_DIR / "results.csv"
        if not results_csv.exists():
            raise FileNotFoundError(f"Analysis script did not produce expected output: {results_csv}")

        # Load the CSV into a dict structure for the baseline JSON
        import pandas as pd
        df = pd.read_csv(results_csv)
        
        # Convert to a JSON-serializable structure
        # We convert the dataframe to a list of records to preserve the structure
        results_data = df.to_dict(orient='records')
        
        # Also include metadata about the run
        baseline_package = {
            "run_metadata": {
                "script": "run_statistics.py",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "duration_seconds": elapsed,
                "python_version": sys.version,
                "input_files": {
                    "logs": str(INPUT_LOGS),
                    "summaries_llm": str(INPUT_SUMMARIES_LLM),
                    "summaries_rule": str(INPUT_SUMMARIES_RULE)
                }
            },
            "metrics": results_data
        }

        return baseline_package

    except subprocess.TimeoutExpired:
        logger.error("Analysis script timed out (>1 hour)")
        raise RuntimeError("Analysis pipeline timed out")
    except Exception as e:
        logger.error(f"Unexpected error running analysis: {e}")
        raise

def main():
    """
    Main entry point for T030a.
    """
    logger.info("Starting Baseline Results Generation (T030a)...")

    # 1. Verify inputs exist (Fail loudly if not)
    if not verify_input_data():
        logger.error("Input verification failed. Aborting baseline generation.")
        sys.exit(1)

    # 2. Run the analysis pipeline
    try:
        baseline_data = run_analysis_pipeline()
    except Exception as e:
        logger.error(f"Failed to run analysis pipeline: {e}")
        sys.exit(1)

    # 3. Save the baseline
    if not save_baseline_results(baseline_data):
        logger.error("Failed to save baseline results.")
        sys.exit(1)

    logger.info("Baseline results generation completed successfully.")
    logger.info(f"Artifact ready for CI verification: {BASELINE_FILE}")

if __name__ == "__main__":
    main()