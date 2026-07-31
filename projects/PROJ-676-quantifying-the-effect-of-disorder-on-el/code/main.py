"""
Main orchestration script for the disorder effect analysis pipeline.
Implements parallel execution of disorder realizations using joblib.
"""
import argparse
import json
import os
import sys
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Tuple

from joblib import Parallel, delayed
import numpy as np

from code.config import get_config
from code.generate_hamiltonian import generate_hamiltonian
from code.analyze_pr import analyze_single_realization
from code.storage_utils import log_provenance_entry
from code.logger import NumericalLogger

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def process_realization(L: int, W: float, realization_index: int, seed: int, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process a single disorder realization: generate H, diagonalize, compute PR.
    
    Args:
        L: System size
        W: Disorder strength
        realization_index: Index of this realization
        seed: Random seed for this realization
        config: Configuration dictionary
        
    Returns:
        Dictionary with results
    """
    try:
        # Initialize logger for this realization
        logger_instance = NumericalLogger(
            output_path=Path(config["PROJECT_ROOT"]) / "data" / "metadata" / "residuals.json"
        )
        
        # Generate Hamiltonian
        H = generate_hamiltonian(L, W, seed)
        
        # Log provenance
        log_provenance_entry(
            realization_index=realization_index,
            seed=seed,
            W=W,
            L=L,
            output_path=Path(config["PROJECT_ROOT"]) / "data" / "metadata" / "provenance.json"
        )
        
        # Analyze
        results = analyze_single_realization(H, L, W, realization_index, logger_instance)
        
        if "error" in results:
            logger.warning(f"Realization {realization_index} failed: {results['error']}")
            return results
        
        return results
        
    except Exception as e:
        logger.error(f"Error processing realization {realization_index}: {e}")
        return {"error": str(e), "L": L, "W": W, "realization_index": realization_index}

def run_orchestration(args):
    """
    Run the full orchestration pipeline with parallel execution.
    
    Args:
        args: Parsed command line arguments
    """
    config = get_config()
    logger.info(f"Starting orchestration with L={args.Llist}, W={args.Wlist}, N={args.realizations}, jobs={args.n_jobs}")
    
    # Ensure output directories exist
    processed_dir = Path(config["PROJECT_ROOT"]) / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    metadata_dir = Path(config["PROJECT_ROOT"]) / "data" / "metadata"
    metadata_dir.mkdir(parents=True, exist_ok=True)
    
    all_results = {}
    total_processed = 0
    total_failed = 0
    
    # Prepare jobs
    jobs = []
    for W in args.Wlist:
        for L in args.Llist:
            for i in range(args.realizations):
                seed = args.seed + i * 1000
                realization_idx = i
                jobs.append((L, W, realization_idx, seed))
    
    logger.info(f"Submitting {len(jobs)} jobs with n_jobs={args.n_jobs}")
    
    # Execute in parallel
    start_time = datetime.now()
    results = Parallel(n_jobs=args.n_jobs, backend='loky')(
        delayed(process_realization)(L, W, idx, seed, config) 
        for L, W, idx, seed in jobs
    )
    end_time = datetime.now()
    
    # Aggregate results
    job_idx = 0
    for W in args.Wlist:
        all_results[W] = {}
        L_results = {}
        
        for L in args.Llist:
            L_results[L] = []
            for i in range(args.realizations):
                result = results[job_idx]
                job_idx += 1
                
                if "error" not in result:
                    L_results[L].append(result)
                    total_processed += 1
                else:
                    total_failed += 1
                    logger.warning(f"Skipped failed realization L={L}, W={W}, realization={i}")
        
        # Aggregate results for this W
        for L in args.Llist:
            if L_results[L]:
                mean_pr = sum(r["pr_results"]["mean_pr"] for r in L_results[L]) / len(L_results[L])
                all_results[W][L] = {
                    "mean_pr": mean_pr,
                    "num_realizations": len(L_results[L]),
                    "individual_pr": [r["pr_results"]["mean_pr"] for r in L_results[L]]
                }
    
    # Save results
    output_file = processed_dir / "scaling_fits.json"
    with open(output_file, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    # Generate summary log
    summary = {
        "timestamp": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "duration_seconds": (end_time - start_time).total_seconds(),
        "parameters": {
            "L_list": args.Llist,
            "W_list": args.Wlist,
            "realizations_per_pair": args.realizations,
            "n_jobs": args.n_jobs,
            "seed": args.seed
        },
        "statistics": {
            "total_jobs": len(jobs),
            "total_processed": total_processed,
            "total_failed": total_failed,
            "success_rate": total_processed / len(jobs) if jobs else 0.0
        }
    }
    
    log_file = processed_dir / "orchestration_summary.json"
    with open(log_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"Orchestration complete. Processed {total_processed} realizations, {total_failed} failed.")
    logger.info(f"Saved scaling fits to {output_file}")
    logger.info(f"Saved summary log to {log_file}")
    
    return all_results, summary

def main():
    parser = argparse.ArgumentParser(description="Disorder Effect Analysis Pipeline - Orchestration")
    parser.add_argument("--w_range", type=float, nargs="+", required=True,
                      help="List of disorder strengths (e.g., --w_range 0.5 1.0 2.0)")
    parser.add_argument("--l_range", type=int, nargs="+", required=True,
                      help="List of system sizes (e.g., --l_range 100 200 400)")
    parser.add_argument("--n_jobs", type=int, default=-1,
                      help="Number of parallel jobs (-1 for all available cores)")
    parser.add_argument("--realizations", type=int, default=10,
                      help="Number of realizations per (L, W) pair (default: 10 for quick test)")
    parser.add_argument("--seed", type=int, default=42,
                      help="Base random seed (default: 42)")
    parser.add_argument("--output", type=str, help="Optional custom output directory")
    
    args = parser.parse_args()
    
    # Validate inputs
    if not args.w_range:
        logger.error("--w_range is required")
        sys.exit(1)
    if not args.l_range:
        logger.error("--l_range is required")
        sys.exit(1)
    if args.n_jobs < 1:
        logger.warning("n_jobs must be >= 1, setting to 1")
        args.n_jobs = 1
    
    try:
        run_orchestration(args)
    except Exception as e:
        logger.error(f"Orchestration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()