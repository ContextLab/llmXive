import os
import sys
import json
import time
import numpy as np
from pathlib import Path

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import verify_pilot_feasibility, calculate_batch_constraints

def main():
    """
    Verify that the pilot batch (N=1200) fits within CI constraints.
    Prints detailed feasibility report to stdout and logs to a file.
    """
    print("=" * 60)
    print("PILOT BATCH FEASIBILITY VERIFICATION")
    print("=" * 60)
    
    feasible, message = verify_pilot_feasibility()
    constraints = calculate_batch_constraints()
    
    print(f"\nConfiguration:")
    print(f"  Total Signals (N): {constraints['pilot_n']}")
    print(f"  Bit Depths: {constraints['bit_depths']}")
    print(f"  SNR Bins: {constraints['snr_bins']}")
    print(f"  Signals per Bin: {constraints['signals_per_bin']}")
    
    print(f"\nResource Estimates:")
    print(f"  Memory Required: {constraints['memory_needed_gb']:.2f} GB")
    print(f"  Memory Limit: {constraints['memory_limit_gb']} GB")
    print(f"  Memory Feasible: {constraints['memory_feasible']}")
    
    print(f"  Estimated Runtime: {constraints['estimated_time_hours']:.2f} hours")
    print(f"  Time Limit: {constraints['time_limit_hours']} hours")
    print(f"  Time Feasible: {constraints['time_feasible']}")
    
    print(f"\nOverall Feasibility: {feasible}")
    print(f"Message: {message}")
    
    # Save report to data directory
    reports_dir = Path("code/data/results")
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    report_path = reports_dir / "pilot_feasibility_report.json"
    report_data = {
        "feasible": feasible,
        "message": message,
        "constraints": constraints,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    with open(report_path, "w") as f:
        json.dump(report_data, f, indent=2)
    
    print(f"\nReport saved to: {report_path}")
    
    return 0 if feasible else 1

if __name__ == "__main__":
    sys.exit(main())
