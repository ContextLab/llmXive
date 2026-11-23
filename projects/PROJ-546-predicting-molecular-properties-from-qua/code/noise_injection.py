"""
Noise Injection Module for Sensitivity Analysis (T030b)

Injects Gaussian noise into descriptor features to evaluate model robustness
as per User Story 3, FR-007.

Dependencies:
    - T029: Sensitivity analysis (feature importance extraction)
    - T030: Top descriptor identification
"""

import argparse
import csv
import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np

# Project-relative imports
# Note: We assume this script is run from the project root or code/ directory
# and that the project structure is as defined in T001.
try:
    from utils.logging_utils import setup_logger
except ImportError:
    # Fallback if running directly without proper path setup
    def setup_logger(name: str, log_file: Optional[str] = None, level=logging.INFO):
        logger = logging.getLogger(name)
        logger.setLevel(level)
        if not logger.handlers:
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            if log_file:
                fh = logging.FileHandler(log_file)
                fh.setFormatter(formatter)
                logger.addHandler(fh)
            ch = logging.StreamHandler()
            ch.setFormatter(formatter)
            logger.addHandler(ch)
        return logger


def load_descriptors(input_path: str) -> Tuple[Dict[str, List[str]], np.ndarray, List[str]]:
    """
    Loads descriptors from a CSV file.

    Args:
        input_path: Path to the input CSV file (e.g., data/descriptors_semi.csv).

    Returns:
        A tuple containing:
            - molecule_ids: Dict mapping row index to molecule_id
            - X: Numpy array of descriptor features
            - feature_names: List of feature column names
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    molecule_ids = {}
    data_rows = []
    feature_names = []
    first_row = True

    with open(input_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            if first_row:
                feature_names = row
                first_row = False
                continue

            # Assuming first column is molecule_id
            mol_id = row[0]
            molecule_ids[len(data_rows)] = mol_id

            # Convert remaining columns to float
            try:
                features = [float(val) for val in row[1:]]
                data_rows.append(features)
            except ValueError as e:
                logging.warning(f"Skipping row {len(data_rows)} due to non-numeric value: {e}")
                continue

    if not data_rows:
        raise ValueError("No valid data rows found in input file.")

    return molecule_ids, np.array(data_rows), feature_names


def inject_noise(X: np.ndarray, sigma: float, seed: int = 42) -> np.ndarray:
    """
    Injects Gaussian noise into the feature matrix.

    Args:
        X: Input feature matrix (N_samples, N_features).
        sigma: Standard deviation of the Gaussian noise.
        seed: Random seed for reproducibility.

    Returns:
        Perturbed feature matrix with injected noise.
    """
    rng = np.random.default_rng(seed)
    noise = rng.normal(loc=0.0, scale=sigma, size=X.shape)
    return X + noise


def write_perturbed_dataset(
    molecule_ids: Dict[int, str],
    X_perturbed: np.ndarray,
    feature_names: List[str],
    output_path: str,
    sigma: float
) -> None:
    """
    Writes the perturbed dataset to a CSV file.

    Args:
        molecule_ids: Mapping of row index to molecule_id.
        X_perturbed: Perturbed feature matrix.
        feature_names: List of feature column names.
        output_path: Path to the output CSV file.
        sigma: The sigma value used for noise injection (for logging/metadata).
    """
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        # Write header
        writer.writerow(['molecule_id'] + feature_names)

        # Write data rows
        for i, features in enumerate(X_perturbed):
            mol_id = molecule_ids.get(i, f"unknown_{i}")
            writer.writerow([mol_id] + [f"{val:.6f}" for val in features])

    logging.info(f"Wrote perturbed dataset (sigma={sigma}) to {output_path}")


def main():
    """
    Main entry point for noise injection.

    Usage:
        python code/noise_injection.py --input data/descriptors_semi.csv --output-dir data/perturbed --sigmas 0.01 0.05
    """
    parser = argparse.ArgumentParser(description="Inject Gaussian noise into descriptor datasets.")
    parser.add_argument(
        "--input",
        type=str,
        default="data/descriptors_semi.csv",
        help="Path to the input descriptor CSV file."
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/perturbed",
        help="Directory to write perturbed datasets."
    )
    parser.add_argument(
        "--sigmas",
        type=float,
        nargs="+",
        default=[0.01, 0.05],
        help="List of sigma values for noise injection."
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for noise generation."
    )
    parser.add_argument(
        "--log-file",
        type=str,
        default="logs/noise_injection.log",
        help="Path to the log file."
    )

    args = parser.parse_args()

    # Setup logging
    logger = setup_logger("noise_injection", args.log_file)
    logger.info(f"Starting noise injection for {args.input}")
    logger.info(f"Target output directory: {args.output_dir}")
    logger.info(f"Sigma values: {args.sigmas}")

    # Ensure output directory exists
    os.makedirs(args.output_dir, exist_ok=True)

    try:
        # Load original data
        logger.info(f"Loading descriptors from {args.input}")
        molecule_ids, X, feature_names = load_descriptors(args.input)
        logger.info(f"Loaded {len(X)} molecules with {len(feature_names)} features.")

        # Process each sigma level
        for sigma in args.sigmas:
            logger.info(f"Injecting noise with sigma={sigma}")
            X_perturbed = inject_noise(X, sigma, seed=args.seed)

            output_filename = f"descriptors_semi_sigma_{sigma:.4f}.csv"
            output_path = os.path.join(args.output_dir, output_filename)

            write_perturbed_dataset(molecule_ids, X_perturbed, feature_names, output_path, sigma)
            logger.info(f"Completed noise injection for sigma={sigma}")

        logger.info("Noise injection completed successfully.")

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Data processing error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()