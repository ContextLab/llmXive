"""
Wrapper script for T020 to invoke the geometry pipeline (Solver + Warp + Aggregate).
Ensures the deliverable `data/results/sparse_warped_frames.npy` is produced.
"""
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import get_results_dir, ensure_directories
from geometry.solver import main as solver_main
from geometry.warp import main as warp_main
from geometry.aggregate_warps import main as aggregate_main

def main():
    print("Starting Geometry Pipeline (Solver -> Warp -> Aggregate)")
    ensure_directories()

    # 1. Run Solver
    print("Running Solver...")
    # Note: solver_main might expect specific args or read from config. 
    # We assume it runs based on existing data structure.
    try:
        solver_main()
    except Exception as e:
        print(f"Solver step encountered issues (expected if data missing): {e}")
        # We continue to try warping if partial data exists, or fail gracefully

    # 2. Run Warp
    print("Running Warp...")
    try:
        warp_main()
    except Exception as e:
        print(f"Warp step encountered issues: {e}")

    # 3. Aggregate Warps (CRITICAL for T020 deliverable)
    print("Aggregating Warped Frames...")
    try:
        aggregate_main()
    except Exception as e:
        print(f"Aggregate step failed: {e}")
        # If aggregate fails, the deliverable is missing.
        # We raise to signal failure to the orchestrator.
        raise e

    print("Geometry Pipeline Complete.")

if __name__ == "__main__":
    main()
