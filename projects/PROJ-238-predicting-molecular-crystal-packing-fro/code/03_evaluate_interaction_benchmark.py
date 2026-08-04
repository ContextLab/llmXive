"""
Task T036: Evaluate interaction-type prediction against external benchmarks.

This script checks for the existence of interaction classification data
(produced by T035.2) and attempts to evaluate it against any available
external benchmark. If no external benchmark is found or defined in the
project specifications, it logs the status and exits cleanly with a
report indicating the benchmark was not available.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.config import setup_logging, get_config

# Configure logging
logger = setup_logging(__name__)
config = get_config()

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DESCRIPTORS_DIR = DATA_DIR / "descriptors"
RESULTS_DIR = PROJECT_ROOT / "results"

# Input file from T035.2
INTERACTION_FILE = DESCRIPTORS_DIR / "derived.csv"

# Output file for T036
BENCHMARK_LOG = RESULTS_DIR / "interaction_benchmark.log"

# Ensure results directory exists
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

def check_external_benchmark_availability() -> Optional[Dict[str, Any]]:
    """
    Checks if an external benchmark for interaction classification exists.
    
    In the context of this project, we look for:
    1. A specific file defined in contracts/ or specs/
    2. A standard benchmark dataset path (e.g., from a known repository)
    
    Currently, no external benchmark file is defined in the project specs
    for interaction type prediction.
    """
    # Check for a benchmark file in the expected location
    benchmark_path = DATA_DIR / "raw" / "interaction_benchmark_ground_truth.csv"
    
    if benchmark_path.exists():
        logger.info(f"Found external benchmark file: {benchmark_path}")
        return {"status": "found", "path": str(benchmark_path)}
    
    # Check for a benchmark reference in config
    benchmark_ref = config.get("benchmark_interaction", None)
    if benchmark_ref:
        logger.info(f"Config references benchmark: {benchmark_ref}")
        # Attempt to load if path is provided
        if os.path.exists(benchmark_ref):
            return {"status": "found", "path": benchmark_ref}
    
    logger.info("No external benchmark for interaction type prediction found.")
    return None

def load_interaction_data() -> Optional[Any]:
    """
    Loads the interaction classification data generated in T035.2.
    """
    if not INTERACTION_FILE.exists():
        logger.warning(f"Interaction data file not found: {INTERACTION_FILE}")
        return None
    
    try:
        import pandas as pd
        df = pd.read_csv(INTERACTION_FILE)
        
        required_cols = ["CIF_ID", "interaction_type", "interaction_confidence"]
        missing_cols = [c for c in required_cols if c not in df.columns]
        
        if missing_cols:
            logger.error(f"Interaction data missing required columns: {missing_cols}")
            return None
        
        logger.info(f"Loaded interaction data with {len(df)} rows.")
        return df
    except Exception as e:
        logger.error(f"Failed to load interaction data: {e}")
        return None

def evaluate_against_benchmark(df: Any, benchmark_path: str) -> Dict[str, Any]:
    """
    Evaluates the predicted interaction types against the ground truth.
    """
    try:
        import pandas as pd
        from sklearn.metrics import accuracy_score, f1_score, confusion_matrix
        import numpy as np

        benchmark_df = pd.read_csv(benchmark_path)
        
        # Merge on CIF_ID
        merged = pd.merge(df, benchmark_df, on="CIF_ID", suffixes=("_pred", "_true"))
        
        if len(merged) == 0:
            return {
                "status": "error",
                "message": "No matching CIF IDs found between prediction and benchmark."
            }

        y_true = merged["interaction_type_true"]
        y_pred = merged["interaction_type_pred"]

        accuracy = accuracy_score(y_true, y_pred)
        f1 = f1_score(y_true, y_pred, average="weighted")
        
        # Get unique classes
        classes = sorted(set(y_true.unique()) | set(y_pred.unique()))
        
        return {
            "status": "success",
            "total_comparisons": len(merged),
            "accuracy": float(accuracy),
            "f1_score_weighted": float(f1),
            "classes": classes,
            "confusion_matrix_shape": list(confusion_matrix(y_true, y_pred, labels=classes).shape)
        }
    except Exception as e:
        logger.error(f"Evaluation failed: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}

def write_log_report(results: Dict[str, Any]):
    """
    Writes the final evaluation log to the specified output file.
    """
    with open(BENCHMARK_LOG, "w") as f:
        f.write(f"Interaction Benchmark Evaluation Report\n")
        f.write(f"Generated: {Path(BENCHMARK_LOG).stat().st_mtime}\n")
        f.write(f"=" * 50 + "\n\n")
        
        if results.get("status") == "skipped":
            f.write("RESULT: SKIPPED\n")
            f.write(f"Reason: {results.get('reason', 'No external benchmark available.')}\n")
            f.write("\n")
            f.write("ACTION: To enable benchmarking, provide a ground truth file at:\n")
            f.write(f"  {DATA_DIR}/raw/interaction_benchmark_ground_truth.csv\n")
            f.write("  or configure 'benchmark_interaction' in the project config.\n")
        
        elif results.get("status") == "error":
            f.write("RESULT: ERROR\n")
            f.write(f"Message: {results.get('message', 'Unknown error')}\n")
        
        elif results.get("status") == "success":
            f.write("RESULT: SUCCESS\n")
            f.write(f"Total Comparisons: {results.get('total_comparisons', 0)}\n")
            f.write(f"Accuracy: {results.get('accuracy', 0):.4f}\n")
            f.write(f"F1 Score (Weighted): {results.get('f1_score_weighted', 0):.4f}\n")
            f.write(f"Classes Evaluated: {', '.join(results.get('classes', []))}\n")
        
        f.write("\n")
        f.write("End of Report\n")
    
    logger.info(f"Benchmark log written to: {BENCHMARK_LOG}")

def main():
    """
    Main entry point for T036.
    """
    logger.info("Starting Interaction Benchmark Evaluation (T036)...")
    
    # Step 1: Check for external benchmark
    benchmark_info = check_external_benchmark_availability()
    
    if not benchmark_info:
        # No benchmark found
        results = {
            "status": "skipped",
            "reason": "No external benchmark dataset found for interaction type prediction."
        }
        write_log_report(results)
        logger.info("Task completed: Skipped (no benchmark available).")
        return 0
    
    # Step 2: Load interaction data
    interaction_df = load_interaction_data()
    if interaction_df is None:
        results = {
            "status": "error",
            "message": "Could not load interaction prediction data from T035.2."
        }
        write_log_report(results)
        logger.error("Task failed: Missing input data.")
        return 1
    
    # Step 3: Evaluate
    eval_results = evaluate_against_benchmark(interaction_df, benchmark_info["path"])
    write_log_report(eval_results)
    
    if eval_results["status"] == "success":
        logger.info("Task completed: Benchmark evaluation successful.")
        return 0
    else:
        logger.error("Task failed: Evaluation error.")
        return 1

if __name__ == "__main__":
    sys.exit(main())