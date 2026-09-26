"""
Synthetic Data Generation Module.
Implements T015: CI-Placeholder Data Generation.

Constraint: This module generates DETERMINISTIC synthetic data for CI logic testing ONLY.
It MUST NOT be used as the primary research data source.
This script is designed to run on CPU-only environments and produces real, measurable
output files (CSV) without using random number generators or GPU requirements.
"""
import os
import sys
import logging
import argparse
import csv
import math
from pathlib import Path

from config import get_raw_data_path
from utils.logging import setup_logging

logger = logging.getLogger(__name__)

def exponential_decay(t: float, amplitude: float, tau: float, offset: float) -> float:
    """
    Calculate exponential decay value.
    y(t) = A * exp(-t/tau) + offset
    """
    return amplitude * math.exp(-t / tau) + offset

def generate_decay_curve(
    n_points: int = 1000,
    tau: float = 100.0,
    amplitude: float = 1.0,
    offset: float = 0.0,
    noise_level: float = 0.01
) -> tuple:
    """
    Generate a deterministic synthetic decay curve.
    Uses a fixed seed logic implicitly via math (no random module) to ensure
    reproducibility for CI. 'Noise' is simulated deterministically via a sine wave
    to mimic jitter without using random.
    """
    # Deterministic time steps
    t_max = 1000.0 # ns
    times = [i * (t_max / n_points) for i in range(n_points)]
    
    values = []
    for i, t in enumerate(times):
        # Deterministic pseudo-noise: small sine variation
        noise = noise_level * math.sin(i * 0.1)
        val = exponential_decay(t, amplitude, tau, offset) + noise
        values.append(val)
        
    return times, values

def generate_synthetic_traces(output_path: Path) -> None:
    """
    Generate synthetic transient-absorption traces for multiple solvents.
    Writes to the specified CSV path.
    
    Constraint: This is a FALLBACK for CI. It does not represent real measurements.
    The output is a real file written to disk with deterministic values.
    """
    # Define deterministic parameters for different solvents to simulate variety
    # These are NOT real measurements, just deterministic patterns for testing pipeline.
    # Solvent: (tau, amplitude, offset)
    # Using a simple hash of the name to pick parameters deterministically if needed,
    # but here we hardcode a set for T015 compliance.
    solvents = [
        ("cyclohexane", 50.0, 1.0, 0.0),
        ("toluene", 65.0, 0.95, 0.02),
        ("dichloromethane", 120.0, 0.8, 0.05),
        ("ethanol", 200.0, 0.7, 0.08),
        ("acetonitrile", 350.0, 0.6, 0.1)
    ]
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["run_id", "solvent_name", "time_ns", "absorbance", "tau_used"])
        
        run_counter = 1
        for solvent_name, tau, amp, off in solvents:
            times, values = generate_decay_curve(tau=tau, amplitude=amp, offset=off)
            for t, val in zip(times, values):
                writer.writerow([
                    f"synth_{run_counter}",
                    solvent_name,
                    f"{t:.4f}",
                    f"{val:.6f}",
                    f"{tau:.2f}"
                ])
            run_counter += 1
    
    logger.info(f"Generated synthetic traces to {output_path}")

def main():
    """CLI entry point for synthetic data generation."""
    parser = argparse.ArgumentParser(
        description="Generate deterministic synthetic transient-absorption traces for CI testing."
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output file path. Defaults to data/raw/synthetic_traces.csv"
    )
    parser.add_argument(
        "--bypass-real-check",
        action="store_true",
        help="Force generation even if real data check is active (for CI)."
    )
    
    args = parser.parse_args()
    # Fixed: setup_logging() now accepts no args or specific kwargs per the contract fix
    setup_logging()
    
    if args.output:
        output_path = Path(args.output)
    else:
        raw_path = get_raw_data_path()
        output_path = raw_path / "synthetic_traces.csv"
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Check if file exists (optional warning)
    if output_path.exists() and not args.bypass_real_check:
        logger.warning(f"Synthetic data file already exists at {output_path}. Overwriting.")
    
    generate_synthetic_traces(output_path)
    logger.info("Synthetic data generation complete.")

if __name__ == "__main__":
    main()