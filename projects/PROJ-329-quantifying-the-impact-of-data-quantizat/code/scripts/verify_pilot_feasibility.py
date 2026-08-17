"""
Pilot Feasibility Verification Script for PROJ-329.

This script calculates and documents whether the proposed pilot batch size
(N=1200 signals: 6 depths x 4 bins x 50) fits within the CI constraints:
- Time: 6 hours (21,600 seconds)
- Memory: 7 GB RAM

It performs a theoretical calculation based on estimated per-signal costs
and validates against the constraints.
"""
import os
import sys
import json
import time
import logging
import numpy as np
from pathlib import Path
from typing import Dict, Tuple, Any

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.config import get_resource_limits, calculate_batch_constraints

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants for the pilot study
NUM_BIT_DEPTHS = 6  # 1, 8, 10, 12, 14, 16
NUM_SNR_BINS = 4    # 8-14, 14-20, 20-30, 30-50
SIGNALS_PER_BIN = 50
TOTAL_SIGNALS = NUM_BIT_DEPTHS * NUM_SNR_BINS * SIGNALS_PER_BIN  # 1200

# Estimated resource costs per signal (based on typical PyCBC/Bilby inference)
# These are conservative estimates for CPU-optimized inference
ESTIMATED_MEMORY_PER_SIGNAL_MB = 40  # ~40MB per signal for waveform + likelihood
ESTIMATED_TIME_PER_SIGNAL_SECONDS = 90  # ~1.5 minutes per signal (conservative)

def calculate_pilot_requirements() -> Dict[str, Any]:
    """
    Calculate total memory and time requirements for the pilot batch.

    Returns:
        Dictionary containing calculated metrics and feasibility status.
    """
    logger.info(f"Calculating requirements for pilot batch: N={TOTAL_SIGNALS}")
    logger.info(f"Configuration: {NUM_BIT_DEPTHS} bit depths x {NUM_SNR_BINS} SNR bins x {SIGNALS_PER_BIN} signals/bin")

    # Memory calculation (peak usage assumes processing one signal at a time but keeping buffers)
    # We add a 20% overhead for Python/GIL and framework overhead
    total_memory_mb = ESTIMATED_MEMORY_PER_SIGNAL_MB * 1.2
    total_memory_gb = total_memory_mb / 1024.0

    # Time calculation (sequential processing on 2 cores, but we assume parallelization efficiency)
    # With 2 cores, we can process 2 signals simultaneously
    # Effective time = (Total Signals / 2) * Time per signal
    effective_cores = 2
    total_time_seconds = (TOTAL_SIGNALS / effective_cores) * ESTIMATED_TIME_PER_SIGNAL_SECONDS
    total_time_hours = total_time_seconds / 3600.0

    # Resource limits from config
    limits = get_resource_limits()
    max_memory_gb = limits.get('max_memory_gb', 7.0)
    max_time_hours = limits.get('max_time_hours', 6.0)

    # Feasibility check
    memory_feasible = total_memory_gb <= max_memory_gb
    time_feasible = total_time_hours <= max_time_hours
    overall_feasible = memory_feasible and time_feasible

    results = {
        "pilot_configuration": {
            "num_bit_depths": NUM_BIT_DEPTHS,
            "num_snr_bins": NUM_SNR_BINS,
            "signals_per_bin": SIGNALS_PER_BIN,
            "total_signals": TOTAL_SIGNALS
        },
        "estimated_resources": {
            "peak_memory_gb": round(total_memory_gb, 3),
            "estimated_runtime_hours": round(total_time_hours, 2),
            "estimated_runtime_seconds": round(total_time_seconds, 2),
            "effective_cores": effective_cores
        },
        "constraints": {
            "max_memory_gb": max_memory_gb,
            "max_time_hours": max_time_hours
        },
        "feasibility": {
            "memory_ok": memory_feasible,
            "time_ok": time_feasible,
            "overall_feasible": overall_feasible
        },
        "safety_margin": {
            "memory_margin_gb": round(max_memory_gb - total_memory_gb, 3),
            "time_margin_hours": round(max_time_hours - total_time_hours, 2)
        }
    }

    return results

def generate_feasibility_report(results: Dict[str, Any]) -> str:
    """
    Generate a human-readable report of the feasibility analysis.

    Args:
        results: Dictionary from calculate_pilot_requirements

    Returns:
        Formatted string report
    """
    status = "PASS" if results['feasibility']['overall_feasible'] else "FAIL"
    report_lines = [
        "=" * 70,
        "PILOT FEASIBILITY VERIFICATION REPORT",
        "=" * 70,
        "",
        f"Status: {status}",
        "",
        "Configuration:",
        f"  - Bit Depths: {results['pilot_configuration']['num_bit_depths']}",
        f"  - SNR Bins: {results['pilot_configuration']['num_snr_bins']}",
        f"  - Signals per Bin: {results['pilot_configuration']['signals_per_bin']}",
        f"  - Total Signals (N): {results['pilot_configuration']['total_signals']}",
        "",
        "Resource Estimates:",
        f"  - Peak Memory: {results['estimated_resources']['peak_memory_gb']} GB",
        f"  - Estimated Runtime: {results['estimated_resources']['estimated_runtime_hours']} hours",
        f"  - Effective Cores Used: {results['estimated_resources']['effective_cores']}",
        "",
        "Constraints:",
        f"  - Max Memory: {results['constraints']['max_memory_gb']} GB",
        f"  - Max Time: {results['constraints']['max_time_hours']} hours",
        "",
        "Verification:",
        f"  - Memory Constraint: {'PASS' if results['feasibility']['memory_ok'] else 'FAIL'} "
        f"({results['estimated_resources']['peak_memory_gb']} GB <= {results['constraints']['max_memory_gb']} GB)",
        f"  - Time Constraint: {'PASS' if results['feasibility']['time_ok'] else 'FAIL'} "
        f"({results['estimated_resources']['estimated_runtime_hours']} hours <= {results['constraints']['max_time_hours']} hours)",
        "",
        "Safety Margins:",
        f"  - Memory Margin: {results['safety_margin']['memory_margin_gb']} GB",
        f"  - Time Margin: {results['safety_margin']['time_margin_hours']} hours",
        "",
        "Conclusion:",
    ]

    if results['feasibility']['overall_feasible']:
        report_lines.append(
            f"  The pilot batch of N={results['pilot_configuration']['total_signals']} signals "
            f"fits within the CI constraints of {results['constraints']['max_time_hours']} hours "
            f"and {results['constraints']['max_memory_gb']} GB RAM."
        )
    else:
        report_lines.append(
            "  The pilot batch exceeds CI constraints. "
            "Recommendation: Reduce batch size or optimize inference parameters."
        )

    report_lines.append("=" * 70)

    return "\n".join(report_lines)

def main():
    """Main entry point for feasibility verification."""
    logger.info("Starting pilot feasibility verification...")

    try:
        # Calculate requirements
        results = calculate_pilot_requirements()

        # Generate report
        report = generate_feasibility_report(results)

        # Print report to stdout
        print(report)

        # Save detailed JSON results
        output_dir = project_root / "data" / "results"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / "pilot_feasibility_report.json"

        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)

        logger.info(f"Detailed results saved to: {output_file}")

        # Return exit code based on feasibility
        if results['feasibility']['overall_feasible']:
            logger.info("Feasibility check PASSED.")
            return 0
        else:
            logger.error("Feasibility check FAILED.")
            return 1

    except Exception as e:
        logger.error(f"Feasibility verification failed: {e}")
        raise

if __name__ == "__main__":
    sys.exit(main())
