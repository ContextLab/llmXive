"""
Synthetic Transient-Absorption Trace Generator (CI Placeholder).

This module generates deterministic synthetic transient-absorption traces
(mocking laser flash photolysis) strictly as a FALLBACK for CI logic testing.

CONSTRAINT: This data MUST NOT be used as the primary research data source.
It runs only if T015b (Real Data Ingestion) is explicitly bypassed or disabled.
Output is written to `data/raw/synthetic_traces.csv`.

The generation is deterministic based on a fixed seed to ensure reproducible
CI builds.
"""
import os
import sys
import logging
import argparse
import csv
import math
from datetime import datetime

# Project-relative imports
from utils.seeds import set_seed
from config import get_raw_data_path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Fixed seed for deterministic CI generation
CI_SEED = 42
# Standard decay time constants (nanoseconds) for different "solvents"
# Mocking: Non-polar (fast), Polar (slow)
DECAY_CONSTANTS = {
    'cyclohexane': 2.5,   # ns
    'toluene': 3.8,       # ns
    'acetonitrile': 5.2,  # ns
    'methanol': 6.1,      # ns
    'water': 7.5          # ns
}

def exponential_decay(t: float, tau: float, amplitude: float = 1.0, offset: float = 0.0) -> float:
    """
    Calculate exponential decay: A * exp(-t/tau) + offset.

    Args:
        t: Time in nanoseconds.
        tau: Decay time constant in nanoseconds.
        amplitude: Initial amplitude.
        offset: Baseline offset.

    Returns:
        Calculated absorbance change.
    """
    if t < 0:
        return 0.0
    return amplitude * math.exp(-t / tau) + offset

def generate_decay_curve(
    tau: float,
    n_points: int = 100,
    time_max_ns: float = 50.0,
    noise_level: float = 0.005
) -> list:
    """
    Generate a deterministic synthetic decay curve.

    Note: This function uses NO random number generation to ensure
    determinism for CI. Noise is simulated via a deterministic
    perturbation function based on the index.

    Args:
        tau: Decay time constant.
        n_points: Number of time points.
        time_max_ns: Maximum time in ns.
        noise_level: Amplitude of deterministic perturbation.

    Returns:
        List of (time, absorbance) tuples.
    """
    set_seed(CI_SEED) # Ensure any internal state is reset, though we avoid random here
    data = []
    dt = time_max_ns / n_points

    for i in range(n_points):
        t = i * dt
        # Base signal
        signal = exponential_decay(t, tau)
        # Deterministic "noise" pattern to mimic instrument jitter without randomness
        # Using a sine wave based on index to simulate periodic noise artifacts
        noise = noise_level * math.sin(i * 0.5) * math.cos(i * 0.1)
        absorbance = signal + noise
        data.append((t, absorbance))

    return data

def generate_synthetic_traces(output_path: str, solvents: list = None) -> None:
    """
    Generate synthetic transient-absorption traces for a list of solvents
    and write them to a CSV file.

    Args:
        output_path: Path to the output CSV file.
        solvents: List of solvent names to generate traces for.
    """
    if solvents is None:
        solvents = list(DECAY_CONSTANTS.keys())

    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    logger.info(f"Generating synthetic traces for {len(solvents)} solvents...")
    logger.info(f"Output path: {output_path}")
    logger.warning("GENERATING SYNTHETIC DATA FOR CI ONLY. NOT FOR RESEARCH.")

    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        # Header: solvent, time_ns, delta_absorbance, tau_used
        writer.writerow(['solvent', 'time_ns', 'delta_absorbance', 'tau_used'])

        for solvent in solvents:
            if solvent not in DECAY_CONSTANTS:
                logger.warning(f"Unknown solvent '{solvent}', skipping.")
                continue

            tau = DECAY_CONSTANTS[solvent]
            logger.info(f"  Generating {solvent} (tau={tau} ns)...")
            curve = generate_decay_curve(tau, n_points=100, time_max_ns=50.0)

            for t, absorbance in curve:
                writer.writerow([solvent, f"{t:.4f}", f"{absorbance:.6f}", f"{tau:.2f}"])

    logger.info(f"Successfully wrote synthetic data to {output_path}")

def main() -> None:
    """
    Entry point for generating synthetic data.
    """
    parser = argparse.ArgumentParser(
        description="Generate deterministic synthetic transient-absorption traces for CI testing."
    )
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help="Output CSV path. Defaults to data/raw/synthetic_traces.csv."
    )
    parser.add_argument(
        '--solvents',
        type=str,
        nargs='+',
        default=None,
        help="Space-separated list of solvents to generate. Defaults to all configured."
    )

    args = parser.parse_args()

    # Determine output path
    if args.output:
        output_path = args.output
    else:
        raw_data_path = get_raw_data_path()
        output_path = os.path.join(raw_data_path, "synthetic_traces.csv")

    # Check if file exists to avoid overwriting in a real run (though CI should be clean)
    if os.path.exists(output_path):
        logger.warning(f"Synthetic data file already exists at {output_path}. Overwriting for CI.")

    solvents = args.solvents

    try:
        generate_synthetic_traces(output_path, solvents)
        logger.info("Synthetic data generation completed successfully.")
    except Exception as e:
        logger.error(f"Failed to generate synthetic data: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()