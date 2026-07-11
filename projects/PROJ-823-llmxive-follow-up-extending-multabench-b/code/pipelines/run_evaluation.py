"""
Pipeline to run evaluation (T027) for all available datasets.

This script orchestrates the evaluation of the conditioned projection model
on held-out test sets, computing AUC/RMSE metrics.
"""
import os
import sys
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import ensure_directories
from utils.logging import get_logger, log_info, log_warning, log_error, log_debug
from utils.memory_monitor import get_process_memory_mb, track_memory

from analysis.evaluate_metrics import main as evaluate_main

logger = get_logger(__name__)


def main():
    """
    Main entry point for the evaluation pipeline.
    """
    log_info("Starting evaluation pipeline (T027)")
    
    # Ensure directories exist
    ensure_directories([
        Path("data/processed"),
        Path("data/artifacts"),
        Path("data/metadata")
    ])
    
    # Get run_id from environment or default to current timestamp
    run_id = os.environ.get("LLMXIVE_RUN_ID")
    if run_id is None:
        # Try to infer from existing files or use timestamp
        run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_info(f"No RUN_ID provided, using {run_id}")
    
    log_info(f"Running evaluation for run_id: {run_id}")
    
    # Check if embeddings from T025 exist
    embeddings_path = Path(f"data/processed/embeddings_{run_id}.parquet")
    conditioned_path = Path(f"data/processed/conditioned_{run_id}.parquet")
    
    if not embeddings_path.exists() and not conditioned_path.exists():
        log_error(f"No embeddings found for run_id {run_id}. "
                  "Please run T025 (run_conditioned) first.")
        sys.exit(1)
    
    # Run evaluation
    try:
        output_path = evaluate_main(run_id=run_id)
        
        if output_path:
            log_info(f"Evaluation completed. Results saved to {output_path}")
            print(f"SUCCESS: Evaluation completed. Output: {output_path}")
        else:
            log_error("Evaluation failed to produce output.")
            sys.exit(1)
            
    except Exception as e:
        log_error(f"Evaluation pipeline failed: {e}")
        raise


if __name__ == "__main__":
    main()