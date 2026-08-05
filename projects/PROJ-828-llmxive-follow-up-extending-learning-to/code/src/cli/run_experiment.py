"""
Main CLI entry point for the Low-Rank RL Foresight experiment.
Orchestrates training, analysis, and enforces strict resource/time limits.
"""

import argparse
import json
import os
import sys
import signal
import time
import threading
from pathlib import Path
from typing import List, Optional, Dict, Any

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.seeds import set_seed, get_seed_config
from src.utils.memory_monitor import MemoryMonitor, enforce_memory_limit
from src.data.loader import load_gsm8k_streaming
from src.training.opd_baseline import run_opd_baseline
from src.training.low_rank_rl import run_low_rank_rl
from src.training.rl_baseline import run_rl_baseline
from src.analysis.metrics import aggregate_multiple_seeds, compute_convergence_metrics

# Constants
TIME_BUDGET_SECONDS = 6 * 3600  # 6 hours
EXIT_CODE_INCONCLUSIVE = 42
RESULTS_DIR = PROJECT_ROOT / "results"
STATUS_FILE = RESULTS_DIR / "experiment_status.json"


class TimeBudgetEnforcer:
    """
    Thread-safe time budget enforcer that tracks elapsed time and triggers
    abort logic if the 6-hour limit is exceeded.
    """
    def __init__(self, start_time: float, budget_seconds: int = TIME_BUDGET_SECONDS):
        self.start_time = start_time
        self.budget_seconds = budget_seconds
        self.exceeded = False
        self.lock = threading.Lock()

    def check(self) -> bool:
        """
        Check if time budget is exceeded.
        Returns True if exceeded, False otherwise.
        """
        elapsed = time.time() - self.start_time
        if elapsed > self.budget_seconds:
            with self.lock:
                self.exceeded = True
            return True
        return False

    def time_remaining(self) -> float:
        """Return remaining time in seconds."""
        return max(0.0, self.budget_seconds - (time.time() - self.start_time))


def write_inconclusive_status(reason: str, active_variants: List[str]):
    """
    Writes the 'inconclusive' status to results/experiment_status.json
    and exits with code 42.
    """
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    status = {
        "status": "inconclusive",
        "reason": reason,
        "timestamp": time.time(),
        "active_variants": active_variants
    }
    with open(STATUS_FILE, "w") as f:
        json.dump(status, f, indent=2)
    sys.exit(EXIT_CODE_INCONCLUSIVE)


def run_variant_seed(
    variant: str,
    seed: int,
    data_loader,
    time_enforcer: TimeBudgetEnforcer,
    memory_monitor: Optional[MemoryMonitor] = None
) -> Dict[str, Any]:
    """
    Executes a single seed for a specific variant.
    Handles timeout checks before and during execution.
    """
    # Pre-check timeout
    if time_enforcer.check():
        write_inconclusive_status(
            "Time budget exceeded before completing required seeds.",
            active_variants=[variant]
        )

    # Set seed
    set_seed(seed)

    try:
        if variant == "opd":
            # Run OPD baseline
            results = run_opd_baseline(
                data_loader=data_loader,
                seed=seed,
                max_steps=100, # Capped for feasibility
                early_window_config_path=str(PROJECT_ROOT / "results" / "early_window_config.json")
            )
        elif variant == "low_rank_rl":
            # Run Low-Rank RL
            results = run_low_rank_rl(
                data_loader=data_loader,
                seed=seed,
                max_steps=100,
                subspace_path=str(PROJECT_ROOT / "results" / "opd_subspace.npy")
            )
        elif variant == "standard_rl":
            # Run Standard RL
            results = run_rl_baseline(
                data_loader=data_loader,
                seed=seed,
                max_steps=100
            )
        else:
            raise ValueError(f"Unknown variant: {variant}")

        # Post-step timeout check
        if time_enforcer.check():
            write_inconclusive_status(
                "Time budget exceeded during execution of seed.",
                active_variants=[variant]
            )

        return {"variant": variant, "seed": seed, "status": "success", "metrics": results}

    except Exception as e:
        # Log error but don't exit immediately unless it's a resource failure
        print(f"Error running {variant} seed {seed}: {e}")
        return {"variant": variant, "seed": seed, "status": "failed", "error": str(e)}


def main():
    parser = argparse.ArgumentParser(description="Run Low-Rank RL Foresight Experiment")
    parser.add_argument("--run-list", type=str, help="Path to JSON file containing list of variants and seeds")
    parser.add_argument("--seeds", type=int, default=3, help="Number of seeds per variant (default: 3)")
    parser.add_argument("--variants", type=str, nargs="+", default=["opd", "standard_rl", "low_rank_rl"],
                        help="List of variants to run")
    parser.add_argument("--time-budget", type=int, default=TIME_BUDGET_SECONDS,
                        help=f"Time budget in seconds (default: {TIME_BUDGET_SECONDS})")
    parser.add_argument("--rerun-seeds", action="store_true", help="Flag to trigger adaptive re-run logic")

    args = parser.parse_args()

    # Initialize results directory
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # Determine active variants and seeds
    if args.run_list:
        if not Path(args.run_list).exists():
            print(f"Error: Run list file {args.run_list} not found.")
            sys.exit(1)
        with open(args.run_list, "r") as f:
            run_config = json.load(f)
        active_variants = run_config.get("variants", args.variants)
        seeds_per_variant = run_config.get("seeds_per_variant", args.seeds)
    else:
        active_variants = args.variants
        seeds_per_variant = args.seeds

    # Initialize time enforcer
    start_time = time.time()
    time_enforcer = TimeBudgetEnforcer(start_time, args.time_budget)

    # Initialize memory monitor
    memory_monitor = MemoryMonitor(limit_gb=7.0)
    memory_monitor.start()

    # Load data (streaming)
    print("Loading GSM8K dataset (streaming)...")
    try:
        data_loader = load_gsm8k_streaming(split="train", num_examples=1000)
    except Exception as e:
        print(f"Failed to load data: {e}")
        write_inconclusive_status("Data loading failed.", active_variants)

    # Execute runs
    all_results = []
    required_seeds = 3 # Minimum N=3 for statistical validity

    for variant in active_variants:
        print(f"Running variant: {variant}")
        for i in range(seeds_per_variant):
            # Check time budget before starting each seed
            if time_enforcer.check():
                write_inconclusive_status(
                    "Time budget exceeded before completing N=3 seeds for all variants.",
                    active_variants
                )

            result = run_variant_seed(
                variant=variant,
                seed=i,
                data_loader=data_loader,
                time_enforcer=time_enforcer,
                memory_monitor=memory_monitor
            )
            all_results.append(result)

            # Check if we have enough successful seeds for this variant
            successful_count = sum(1 for r in all_results if r["variant"] == variant and r["status"] == "success")
            if successful_count < required_seeds and time_enforcer.check():
                write_inconclusive_status(
                    f"Time budget exceeded before completing N={required_seeds} seeds for {variant}.",
                    active_variants
                )

    # Final aggregation and status check
    memory_monitor.stop()

    # Check if we successfully completed N=3 for all active variants
    for variant in active_variants:
        successful_count = sum(1 for r in all_results if r["variant"] == variant and r["status"] == "success")
        if successful_count < required_seeds:
            write_inconclusive_status(
                f"Insufficient successful seeds ({successful_count} < {required_seeds}) for variant {variant}.",
                active_variants
            )

    # Save results
    results_file = RESULTS_DIR / "experiment_results.json"
    with open(results_file, "w") as f:
        json.dump({"results": all_results, "timestamp": time.time()}, f, indent=2)

    # Write success status
    status = {
        "status": "success",
        "timestamp": time.time(),
        "active_variants": active_variants,
        "total_seeds": len(all_results)
    }
    with open(STATUS_FILE, "w") as f:
        json.dump(status, f, indent=2)

    print("Experiment completed successfully.")
    sys.exit(0)


if __name__ == "__main__":
    main()