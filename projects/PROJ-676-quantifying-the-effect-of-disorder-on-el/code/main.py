"""
Main orchestration script for the disorder effect analysis pipeline.
"""
import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
import logging

from code.config import get_config
from code.generate_hamiltonian import generate_hamiltonian
from code.analyze_pr import analyze_single_realization, finite_size_scaling
from code.storage_utils import log_provenance_entry, save_eigenstates_to_hdf5
from code.logger import get_logger

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def process_realization(L: int, W: float, realization_index: int, seed: int) -> Dict[str, Any]:
    """
    Process a single disorder realization: generate H, diagonalize, compute PR.
    
    Args:
        L: System size
        W: Disorder strength
        realization_index: Index of this realization
        seed: Random seed for this realization
        
    Returns:
        Dictionary with results
    """
    try:
        # Generate Hamiltonian
        H = generate_hamiltonian(L, W, seed)
        
        # Analyze
        results = analyze_single_realization(H, L, W, realization_index)
        
        if "error" in results:
            logger.warning(f"Realization {realization_index} failed: {results['error']}")
            return results
        
        # Save eigenstates if needed
        # save_eigenstates_to_hdf5(H, results['eigenvalues'], results['eigenvectors'], ...)
        
        return results
        
    except Exception as e:
        logger.error(f"Error processing realization {realization_index}: {e}")
        return {"error": str(e), "L": L, "W": W, "realization_index": realization_index}

def run_orchestration(args):
    """
    Run the full orchestration pipeline.
    
    Args:
        args: Parsed command line arguments
    """
    config = get_config()
    logger.info(f"Starting orchestration with L={args.Llist}, W={args.Wlist}, N={args.realizations}")
    
    # Ensure output directories exist
    processed_dir = Path(config.PROJECT_ROOT) / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    all_results = {}
    
    for W in args.Wlist:
        all_results[W] = {}
        L_results = {}
        
        for L in args.Llist:
            L_results[L] = []
            
            for i in range(args.realizations):
                seed = args.seed + i * 1000
                realization_idx = i
                
                result = process_realization(L, W, realization_idx, seed)
                
                if "error" not in result:
                    L_results[L].append(result)
                    logger.info(f"Completed L={L}, W={W}, realization={i}")
                else:
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
        
        # Perform finite-size scaling for this W
        L_vals = sorted([L for L in args.Llist if L in all_results[W]])
        pr_vals = [all_results[W][L]["mean_pr"] for L in L_vals]
        
        if len(L_vals) >= 2:
            scaling_result = finite_size_scaling(L_vals, pr_vals)
            all_results[W]["scaling"] = scaling_result
            logger.info(f"Scaling result for W={W}: xi={scaling_result.get('xi', 'N/A')}")
    
    # Save results
    output_file = processed_dir / "scaling_fits.json"
    with open(output_file, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    logger.info(f"Saved scaling fits to {output_file}")
    
    return all_results

def main():
    parser = argparse.ArgumentParser(description="Disorder Effect Analysis Pipeline")
    parser.add_argument("--mode", choices=["generate_and_analyze", "scaling_analysis", "visualize"], 
                      default="generate_and_analyze", help="Operation mode")
    parser.add_argument("--Llist", type=int, nargs="+", default=[100, 200, 400, 800, 1600],
                      help="List of system sizes")
    parser.add_argument("--Wlist", type=float, nargs="+", default=[0.5, 1.0, 2.0],
                      help="List of disorder strengths")
    parser.add_argument("--realizations", type=int, default=100,
                      help="Number of realizations per (L, W) pair")
    parser.add_argument("--seed", type=int, default=42,
                      help="Base random seed")
    parser.add_argument("--L", type=int, help="Single system size for visualization")
    parser.add_argument("--W", type=float, help="Single disorder strength for visualization")
    parser.add_argument("--realization", type=int, help="Specific realization index for visualization")
    parser.add_argument("--output", type=str, help="Output file path")
    
    args = parser.parse_args()
    
    if args.mode == "generate_and_analyze":
        run_orchestration(args)
    elif args.mode == "scaling_analysis":
        logger.info("Scaling analysis mode - results saved in generate_and_analyze")
    elif args.mode == "visualize":
        logger.info("Visualization mode - use code/visualize.py for specific visualizations")
    else:
        logger.error("Unknown mode")
        sys.exit(1)

if __name__ == "__main__":
    main()