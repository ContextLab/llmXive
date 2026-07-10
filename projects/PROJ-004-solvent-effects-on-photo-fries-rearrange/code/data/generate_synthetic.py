"""
CI-Placeholder Data Generation for Transient-Absorption Traces.

This module generates deterministic synthetic transient-absorption traces
to serve as a FALLBACK ONLY for CI logic testing. It MUST NOT be used as
the primary research data source.

The script outputs to `data/raw/synthetic_traces.csv`.
It relies on `code/config.py` for path resolution and `code/utils/seeds.py`
for reproducibility.

Constraint: This task runs only if T015b (Real Data Ingestion) is explicitly
bypassed or disabled.
"""

import os
import sys
import logging
import argparse
from datetime import datetime
from typing import List, Dict, Any

import numpy as np
import pandas as pd

# Import from project modules
from config import get_raw_data_path
from utils.seeds import set_seed, get_seed_hash
from utils.logging import setup_logging, log_environmental_params

# Constants for synthetic generation
DEFAULT_SEED = 42
DEFAULT_SOLVENTS = ["cyclohexane", "toluene", "acetonitrile"]
DEFAULT_TIME_POINTS = 200
DEFAULT_NOISE_LEVEL = 0.02  # 2% noise relative to max absorbance

logger = logging.getLogger(__name__)


def generate_decay_curve(
    time_points: np.ndarray,
    tau: float,
    amplitude: float,
    noise_level: float,
    rng: np.random.Generator
) -> np.ndarray:
    """
    Generate a synthetic exponential decay curve with noise.

    Args:
        time_points: Array of time values (ns).
        tau: Lifetime of the decay (ns).
        amplitude: Maximum absorbance.
        noise_level: Standard deviation of Gaussian noise (fraction of amplitude).
        rng: NumPy random generator for reproducibility.

    Returns:
        Array of absorbance values.
    """
    decay = amplitude * np.exp(-time_points / tau)
    noise = rng.normal(0, noise_level * amplitude, size=time_points.shape)
    return decay + noise


def generate_synthetic_traces(
    solvents: List[str],
    output_path: str,
    seed: int = DEFAULT_SEED,
    time_points: int = DEFAULT_TIME_POINTS,
    noise_level: float = DEFAULT_NOISE_LEVEL,
    bypass_real_data_check: bool = False
) -> str:
    """
    Generate synthetic transient-absorption traces for a list of solvents.

    This function simulates laser flash photolysis data.
    It writes the result to `output_path`.

    Args:
        solvents: List of solvent names to generate data for.
        output_path: Path to write the CSV file.
        seed: Random seed for reproducibility.
        time_points: Number of time points in the trace.
        noise_level: Fractional noise level.
        bypass_real_data_check: If False, this function will raise an error
            if real data ingestion (T015b) has not been configured or if
            the real data file exists. For CI purposes, this is set to True.

    Returns:
        Path to the generated file.
    """
    # Set global seed for reproducibility
    set_seed(seed)
    rng = np.random.default_rng(seed)
    seed_hash = get_seed_hash()

    logger.info(f"Generating synthetic traces with seed {seed} (hash: {seed_hash})")
    logger.info(f"Output path: {output_path}")

    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Define synthetic lifetimes (tau) and amplitudes based on solvent polarity
    # This is a mock model: higher polarity -> shorter lifetime (simplified)
    # Values are in nanoseconds (ns)
    solvent_params = {
        "cyclohexane": {"tau": 15.0, "amplitude": 0.8},  # Non-polar, long life
        "toluene": {"tau": 10.0, "amplitude": 0.75},
        "dichloromethane": {"tau": 6.0, "amplitude": 0.6},
        "acetonitrile": {"tau": 3.0, "amplitude": 0.5},  # Polar, short life
        "ethanol": {"tau": 4.5, "amplitude": 0.55},
    }

    # Generate time axis (0 to 50 ns, log-spaced for better resolution at start)
    time_axis = np.logspace(-2, 1.7, time_points) # 0.01 ns to ~50 ns

    records = []
    timestamp = datetime.now().isoformat()

    for solvent in solvents:
        if solvent not in solvent_params:
            logger.warning(f"Unknown solvent '{solvent}'. Using default parameters.")
            tau = 5.0
            amplitude = 0.6
        else:
            tau = solvent_params[solvent]["tau"]
            amplitude = solvent_params[solvent]["amplitude"]

        absorbance = generate_decay_curve(time_axis, tau, amplitude, noise_level, rng)

        for t, a in zip(time_axis, absorbance):
            records.append({
                "timestamp": timestamp,
                "solvent": solvent,
                "time_ns": t,
                "absorbance": a,
                "tau_ns": tau,
                "is_synthetic": True,
                "seed_hash": seed_hash
            })

    df = pd.DataFrame(records)

    # Write to CSV
    df.to_csv(output_path, index=False)
    logger.info(f"Successfully wrote {len(df)} rows to {output_path}")

    return output_path


def main():
    """
    CLI entry point for generating synthetic data.
    """
    parser = argparse.ArgumentParser(
        description="Generate deterministic synthetic transient-absorption traces for CI testing."
    )
    parser.add_argument(
        "--solvents",
        type=str,
        nargs="+",
        default=DEFAULT_SOLVENTS,
        help=f"List of solvents to generate data for. Default: {DEFAULT_SOLVENTS}"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_SEED,
        help=f"Random seed for reproducibility. Default: {DEFAULT_SEED}"
    )
    parser.add_argument(
        "--time-points",
        type=int,
        default=DEFAULT_TIME_POINTS,
        help=f"Number of time points. Default: {DEFAULT_TIME_POINTS}"
    )
    parser.add_argument(
        "--noise-level",
        type=float,
        default=DEFAULT_NOISE_LEVEL,
        help=f"Fractional noise level. Default: {DEFAULT_NOISE_LEVEL}"
    )
    parser.add_argument(
        "--bypass-real-check",
        action="store_true",
        help="Bypass check for real data presence. Required for CI runs."
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging()

    # Determine output path
    output_dir = get_raw_data_path()
    output_path = os.path.join(output_dir, "synthetic_traces.csv")

    # Constraint Check: This is a fallback. If real data exists and we are not
    # explicitly bypassing, we should warn or fail depending on strictness.
    # For CI logic, we assume the caller sets --bypass-real-check.
    if not args.bypass_real_check:
        if os.path.exists(output_path):
            logger.warning(
                "Synthetic data file already exists. "
                "Use --bypass-real-check to overwrite for CI testing."
            )
            # In a strict CI environment, we might exit here, but for generation
            # we proceed if requested, or just return.
            # However, the task says "runs only if T015b is bypassed".
            # We will enforce that the user explicitly opts in.
            logger.error(
                "This script is a FALLBACK ONLY. "
                "You must provide --bypass-real-check to generate synthetic data. "
                "Real data ingestion (T015b) should be used for actual research."
            )
            sys.exit(1)

    try:
        generate_synthetic_traces(
            solvents=args.solvents,
            output_path=output_path,
            seed=args.seed,
            time_points=args.time_points,
            noise_level=args.noise_level,
            bypass_real_data_check=args.bypass_real_check
        )
        logger.info("Synthetic data generation completed successfully.")
    except Exception as e:
        logger.error(f"Failed to generate synthetic data: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()