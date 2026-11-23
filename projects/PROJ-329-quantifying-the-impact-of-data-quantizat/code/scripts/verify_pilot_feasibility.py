import os
import sys
import json
import time
import logging
import numpy as np
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.config import verify_pilot_feasibility, calculate_batch_constraints, get_resource_limits

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def calculate_pilot_requirements():
    """Calculate detailed pilot requirements."""
    constraints = calculate_batch_constraints()
    return constraints

def generate_feasibility_report():
    """Generate a detailed feasibility report for T010."""
    is_feasible, reason = verify_pilot_feasibility()
    constraints = calculate_pilot_requirements()
    limits = get_resource_limits()

    report = {
        "task_id": "T010",
        "pilot_configuration": {
            "bit_depths": [1, 8, 10, 12, 14, 16],
            "snr_bins": ["8-14", "14-20", "20-30", "30-50"],
            "signals_per_bin": 50,
            "total_signals": constraints["total_pilot_signals"]
        },
        "resource_limits": limits,
        "estimates": {
            "generation_time_hours": constraints["estimated_total_gen_time_hours"],
            "inference_time_hours": constraints["estimated_total_inf_time_hours"],
            "memory_usage_gb": constraints["estimated_total_mem_gb"],
            "max_batch_size": constraints["max_batch_size"]
        },
        "feasibility": {
            "is_feasible": is_feasible,
            "reason": reason
        }
    }

    # Save report to data/processed
    output_dir = project_root / "data" / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "t010_feasibility_report.json"

    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Feasibility report saved to {output_file}")
    return report

def main():
    logger.info("Starting T010 feasibility verification...")
    report = generate_feasibility_report()

    print("\n--- T010 Feasibility Summary ---")
    print(f"Total Pilot Signals: {report['pilot_configuration']['total_signals']}")
    print(f"Estimated Inference Time: {report['estimates']['inference_time_hours']:.2f} hours")
    print(f"Estimated Memory Usage: {report['estimates']['memory_usage_gb']:.2f} GB")
    print(f"Max Batch Size: {report['estimates']['max_batch_size']}")
    print(f"Feasible: {report['feasibility']['is_feasible']}")
    print(f"Reason: {report['feasibility']['reason']}")

    if not report['feasibility']['is_feasible']:
        sys.exit(1)

if __name__ == "__main__":
    main()
