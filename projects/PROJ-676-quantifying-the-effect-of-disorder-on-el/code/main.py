"""
Main orchestration script for the disorder effect analysis.
"""
import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Tuple

# Import configuration and core modules
from code.config import get_config
from code.generate_hamiltonian import generate_hamiltonian
from code.analyze_pr import analyze_single_realization, finite_size_scaling
from code.logger import get_logger

def process_realization(L: int, W: float, realization_index: int, seed: int) -> Dict[str, Any]:
    """
    Process a single disorder realization: generate Hamiltonian, compute eigenstates,
    calculate PR, and log residuals.
    
    Args:
        L: System size
        W: Disorder strength
        realization_index: Index of the realization
        seed: Random seed for this realization
    
    Returns:
        Dictionary containing results and metadata
    """
    logger = get_logger()
    
    try:
        # Generate Hamiltonian
        hamiltonian, on_site = generate_hamiltonian(L, W, seed)
        
        # Analyze (compute eigenvalues/vectors and PR)
        # Note: analyze_single_realization should handle the eigenvalue solving
        # and log residuals via the logger.
        results = analyze_single_realization(hamiltonian, L, W, realization_index, seed, logger)
        
        return {
            "success": True,
            "L": L,
            "W": W,
            "realization_index": realization_index,
            "seed": seed,
            "results": results
        }
    except Exception as e:
        # Log the error
        logger.log_residual(0.0, False, task="error", L=L, W=W, realization_index=realization_index)
        return {
            "success": False,
            "error": str(e),
            "L": L,
            "W": W,
            "realization_index": realization_index,
            "seed": seed
        }

def run_orchestration(args):
    """
    Run the main orchestration loop based on command line arguments.
    """
    config = get_config()
    logger = get_logger()
    
    print(f"Starting analysis at {datetime.now()}")
    print(f"Configuration: L={args.Llist}, W={args.Wlist}, Realizations={args.realizations}")
    
    all_results = []
    
    for W in args.Wlist:
        for L in args.Llist:
            for idx in range(args.realizations):
                seed = config.SEED + idx # Use a base seed + index
                result = process_realization(L, W, idx, seed)
                all_results.append(result)
                
                if idx % 10 == 0:
                    print(f"Completed L={L}, W={W}, realization {idx}/{args.realizations}")
    
    # Save summary
    summary_path = config.data_dir / "processed" / "orchestration_summary.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(summary_path, 'w') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "total_realizations": len(all_results),
            "config": {
                "Llist": args.Llist,
                "Wlist": args.Wlist,
                "realizations": args.realizations
            },
            "results": all_results
        }, f, indent=2)
    
    print(f"Orchestration complete. Summary saved to {summary_path}")
    return all_results

def main():
    parser = argparse.ArgumentParser(description="Disorder Effect Analysis Orchestration")
    parser.add_argument("--mode", choices=["generate_and_analyze", "scaling_analysis", "visualize"], 
                      default="generate_and_analyze", help="Operation mode")
    parser.add_argument("--Llist", type=int, nargs="+", default=[100, 200, 400, 800, 1600],
                      help="List of system sizes")
    parser.add_argument("--Wlist", type=float, nargs="+", default=[0.5, 1.0, 2.0],
                      help="List of disorder strengths")
    parser.add_argument("--realizations", type=int, default=100,
                      help="Number of realizations per (L, W)")
    parser.add_argument("--seed", type=int, default=42,
                      help="Base random seed")
    parser.add_argument("--L", type=int, default=200, help="System size for visualization")
    parser.add_argument("--W", type=float, default=2.0, help="Disorder strength for visualization")
    parser.add_argument("--realization", type=int, default=5, help="Realization index for visualization")
    parser.add_argument("--output", type=str, default=None, help="Output path for visualization")
    
    args = parser.parse_args()
    
    # Update config with seed if provided
    config = get_config()
    # Note: We don't modify the global config object directly here to avoid side effects,
    # but we use the seed for generation.
    
    if args.mode == "generate_and_analyze":
        run_orchestration(args)
    elif args.mode == "scaling_analysis":
        # Placeholder for scaling analysis mode
        print("Scaling analysis mode not fully implemented in this stub.")
    elif args.mode == "visualize":
        # Placeholder for visualization mode
        print("Visualization mode not fully implemented in this stub.")
    else:
        print(f"Unknown mode: {args.mode}")
        sys.exit(1)

if __name__ == "__main__":
    main()
