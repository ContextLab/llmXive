"""
CLI entry point for the Low-Rank RL Foresight experiment.
Orchestrates training variants, manages time budgets, and handles execution flow.
"""
import argparse
import json
import os
import sys
import signal
import time
from pathlib import Path
from typing import Optional, List, Dict, Any

# Import from project API surface
from src.utils.seeds import set_seed, get_seed_config
from src.utils.memory_monitor import MemoryMonitor, enforce_memory_limit
from src.utils.time_estimator import estimate_total_time
from src.data.loader import load_gsm8k_streaming
from src.training.opd_baseline import run_opd_baseline
from src.training.low_rank_rl import run_low_rank_rl
from src.training.rl_baseline import run_standard_rl
from src.training.random_projection import run_random_projection
from src.training.random_walk_prior import run_random_walk_prior
from src.training.opd_initialized_rl import run_opd_initialized_rl

# Constants
RESULTS_DIR = Path("results")
EXPERIMENT_STATUS_FILE = RESULTS_DIR / "experiment_status.json"
TIME_ESTIMATE_FILE = RESULTS_DIR / "time_estimate.json"
MEMORY_ESTIMATE_FILE = RESULTS_DIR / "memory_estimate.json"
ACTIVE_VARIANTS_FILE = RESULTS_DIR / "active_variants.json"
RUN_LIST_FILE = RESULTS_DIR / "run_list.json"
EARLY_WINDOW_CONFIG_FILE = RESULTS_DIR / "early_window_config.json"
WALL_CLOCK_LIMIT_SECONDS = 21600  # 6 hours

# Global start time for time budget tracking
_start_time = None

def write_inconclusive_status(reason: str):
    """Write an inconclusive status to the experiment status file."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    status = {
        "status": "inconclusive",
        "reason": reason,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }
    with open(EXPERIMENT_STATUS_FILE, "w") as f:
        json.dump(status, f, indent=2)

def check_time_budget() -> bool:
    """Check if the time budget is exceeded. Returns True if we should abort."""
    if _start_time is None:
        return False
    elapsed = time.time() - _start_time
    if elapsed > WALL_CLOCK_LIMIT_SECONDS:
        return True
    return False

class TimeBudgetEnforcer:
    """Context manager to enforce time budget on a block of code."""
    def __init__(self, variant: str, seed: int):
        self.variant = variant
        self.seed = seed
        self.start = None

    def __enter__(self):
        self.start = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed = time.time() - self.start
        if check_time_budget():
            write_inconclusive_status(f"Time budget exceeded for {self.variant} seed {self.seed}")
            sys.exit(124)  # Standard timeout exit code
        return False

def run_variant_seed(variant: str, seed: int, args: argparse.Namespace) -> bool:
    """
    Execute a single training run for a specific variant and seed.
    Returns True if successful, False if failed (but not due to timeout).
    """
    set_seed(seed)
    config = get_seed_config(seed)
    
    # Setup paths
    variant_dir = RESULTS_DIR / variant
    variant_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize memory monitor
    memory_monitor = MemoryMonitor(limit_gb=7.0)
    memory_monitor.start()

    try:
        with TimeBudgetEnforcer(variant, seed):
            if variant == "opd":
                run_opd_baseline(seed=seed, num_steps=args.num_steps, early_window_fraction=args.early_window_fraction)
            elif variant == "low_rank_rl":
                # Check for OPD subspace
                subspace_path = RESULTS_DIR / "opd_subspace.npy"
                if not subspace_path.exists():
                    raise FileNotFoundError(
                        f"OPD subspace not found at {subspace_path}. "
                        "Please run OPD baseline first."
                    )
                run_low_rank_rl(
                    seed=seed, 
                    num_steps=args.num_steps,
                    early_window_fraction=args.early_window_fraction,
                    alignment_threshold=args.early_alignment_threshold
                )
            elif variant == "standard_rl":
                run_standard_rl(seed=seed, num_steps=args.num_steps)
            elif variant == "random_projection":
                run_random_projection(seed=seed, num_steps=args.num_steps)
            elif variant == "random_walk_prior":
                run_random_walk_prior(seed=seed, num_steps=args.num_steps)
            elif variant == "opd_initialized_rl":
                run_opd_initialized_rl(seed=seed, num_steps=args.num_steps)
            else:
                raise ValueError(f"Unknown variant: {variant}")
        
        # Record success
        memory_monitor.stop()
        peak_mem = memory_monitor.get_peak_memory_mb()
        log_entry = {
            "variant": variant,
            "seed": seed,
            "status": "completed",
            "peak_memory_mb": peak_mem,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
        
        # Append to log
        log_file = variant_dir / "run_log.jsonl"
        with open(log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
        
        return True

    except FileNotFoundError as e:
        # Propagate missing subspace errors
        raise
    except Exception as e:
        # Log failure but don't crash the whole pipeline
        memory_monitor.stop()
        log_entry = {
            "variant": variant,
            "seed": seed,
            "status": "failed",
            "error": str(e),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
        log_file = variant_dir / "run_log.jsonl"
        with open(log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
        return False

def prepare_data(args: argparse.Namespace):
    """Prepare and verify the dataset."""
    print("Loading GSM8K dataset (streaming)...")
    try:
        loader = load_gsm8k_streaming()
        # Just verify we can iterate
        count = 0
        for batch in loader:
            count += 1
            if count >= 10: # Just a quick check
                break
        print(f"Data loaded successfully. Verified {count} batches.")
    except Exception as e:
        print(f"Failed to load data: {e}")
        sys.exit(1)

def run_full_pipeline(args: argparse.Namespace):
    """Orchestrate the full pipeline based on active variants."""
    global _start_time
    _start_time = time.time()

    # 1. Load active variants
    if not ACTIVE_VARIANTS_FILE.exists():
        print("Error: active_variants.json not found. Run feasibility check first.")
        sys.exit(1)
    
    with open(ACTIVE_VARIANTS_FILE, "r") as f:
        manifest = json.load(f)
    
    variants = manifest.get("variants", [])
    num_seeds = manifest.get("num_seeds", args.num_seeds)
    
    print(f"Running pipeline for variants: {variants} with {num_seeds} seeds each.")

    # 2. Execute runs
    failed_seeds = []
    for variant in variants:
        for seed in range(1, num_seeds + 1):
            if check_time_budget():
                write_inconclusive_status("Global time budget exceeded during pipeline execution.")
                sys.exit(124)
            
            success = run_variant_seed(variant, seed, args)
            if not success:
                failed_seeds.append((variant, seed))
    
    # 3. Final status
    if failed_seeds:
        status = {
            "status": "partial_failure",
            "failed_runs": [{"variant": v, "seed": s} for v, s in failed_seeds],
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
    else:
        status = {
            "status": "completed",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
    
    with open(EXPERIMENT_STATUS_FILE, "w") as f:
        json.dump(status, f, indent=2)

def analyze(args: argparse.Namespace):
    """Run analysis on completed experiments."""
    # Placeholder for analysis logic that aggregates results
    # In a real implementation, this would call T036, T037, T038b etc.
    print("Analysis phase triggered. Aggregating metrics...")
    # This would typically call src/analysis/metrics.py and src/analysis/plots.py
    # For now, we just ensure the status file is updated if not already done
    if not EXPERIMENT_STATUS_FILE.exists():
        write_inconclusive_status("Analysis requested but no experiment status found.")

def verify_alignment(args: argparse.Namespace):
    """Verify early trajectory alignment for a specific variant."""
    variant = args.variant
    variant_dir = RESULTS_DIR / variant
    log_file = variant_dir / "early_alignment_log.json"
    
    if not log_file.exists():
        print(f"Error: Alignment log not found for {variant}.")
        sys.exit(1)
    
    with open(log_file, "r") as f:
        data = json.load(f)
    
    # Simple verification: check if average alignment > threshold
    if isinstance(data, list):
        scores = [d.get("alignment_score", 0) for d in data]
        avg_score = sum(scores) / len(scores) if scores else 0
    else:
        # Handle single object case if schema varies
        avg_score = data.get("alignment_score", 0)
    
    threshold = args.early_alignment_threshold
    if avg_score >= threshold:
        print(f"Alignment verified for {variant}: {avg_score:.4f} >= {threshold}")
    else:
        print(f"Low alignment for {variant}: {avg_score:.4f} < {threshold}")
        # Do not abort, just log as per T030c-early

def main():
    parser = argparse.ArgumentParser(description="LLM-Xive Low-Rank RL Experiment CLI")
    
    # Global arguments
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--num-seeds", type=int, default=3, help="Number of seeds for full pipeline")
    parser.add_argument("--num-steps", type=int, default=100, help="Number of training steps")
    parser.add_argument("--early-window-fraction", type=float, default=0.1, help="Fraction of steps for early window")
    parser.add_argument("--early-alignment-threshold", type=float, default=0.95, help="Threshold for alignment verification")
    
    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # prepare-data
    subparsers.add_parser("prepare-data", help="Prepare and verify dataset")
    
    # full-pipeline
    full_parser = subparsers.add_parser("full-pipeline", help="Run full pipeline with active variants")
    full_parser.add_argument("--seeds", type=int, default=3, help="Override number of seeds")
    
    # variant-specific run
    variant_parser = subparsers.add_parser("variant", help="Run a specific variant")
    variant_parser.add_argument("--variant", type=str, required=True, 
                                choices=["opd", "low_rank_rl", "standard_rl", "random_projection", 
                                         "random_walk_prior", "opd_initialized_rl"],
                                help="Variant to run")
    variant_parser.add_argument("--seeds", type=int, default=1, help="Number of seeds for this variant")
    
    # analyze
    subparsers.add_parser("analyze", help="Run analysis on results")
    
    # verify-alignment
    align_parser = subparsers.add_parser("verify-alignment", help="Verify alignment for a variant")
    align_parser.add_argument("--variant", type=str, required=True, help="Variant to verify")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Ensure results directory exists
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    
    if args.command == "prepare-data":
        prepare_data(args)
    elif args.command == "full-pipeline":
        run_full_pipeline(args)
    elif args.command == "variant":
        # Run specific variant with specified seeds
        for seed in range(1, args.seeds + 1):
            run_variant_seed(args.variant, seed, args)
    elif args.command == "analyze":
        analyze(args)
    elif args.command == "verify-alignment":
        verify_alignment(args)

if __name__ == "__main__":
    main()