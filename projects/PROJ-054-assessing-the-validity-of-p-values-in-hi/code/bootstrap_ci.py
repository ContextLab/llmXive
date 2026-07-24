"""
Bootstrap Confidence Interval Calculation for KS Statistics (T030).

Implements Constitution Principle VII: Report bootstrap confidence intervals
for KS statistics to quantify uncertainty in p-value distribution deviations.

Output: data/results/bootstrap_cis.json
"""
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import numpy as np
from scipy import stats

# Add parent directory to path for imports if running as script
if __name__ == "__main__":
    parent_dir = Path(__file__).resolve().parent
    if str(parent_dir) not in sys.path:
        sys.path.insert(0, str(parent_dir))

from analyze_pvalues import calculate_ks_statistic
from utils.exceptions import AnalysisError

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def calculate_bootstrap_ci(
    pvalues: np.ndarray,
    permutation_pvalues: np.ndarray,
    n_bootstraps: int = 1000,
    confidence_level: float = 0.95,
    random_seed: Optional[int] = None
) -> Tuple[float, float, float]:
    """
    Calculate bootstrap confidence intervals for the KS statistic.

    Args:
        pvalues: Array of p-values from standard hypothesis tests (n_features,).
        permutation_pvalues: Array of p-values from permutation-based gold standard (n_features,).
        n_bootstraps: Number of bootstrap resamples to generate.
        confidence_level: Confidence level for the interval (e.g., 0.95).
        random_seed: Random seed for reproducibility.

    Returns:
        Tuple of (KS_statistic, ci_lower, ci_upper).
    """
    if random_seed is not None:
        np.random.seed(random_seed)

    if len(pvalues) != len(permutation_pvalues):
        raise AnalysisError(
            f"p-values and permutation_p-values must have the same length. "
            f"Got {len(pvalues)} vs {len(permutation_pvalues)}"
        )

    n = len(pvalues)
    ks_stats = []

    # Calculate the observed KS statistic
    observed_ks = calculate_ks_statistic(pvalues, permutation_pvalues)
    logger.info(f"Observed KS statistic: {observed_ks:.6f}")

    # Bootstrap resampling
    for i in range(n_bootstraps):
        # Resample with replacement
        indices = np.random.choice(n, size=n, replace=True)
        boot_pvalues = pvalues[indices]
        boot_perm_pvalues = permutation_pvalues[indices]

        # Calculate KS statistic for this resample
        ks = calculate_ks_statistic(boot_pvalues, boot_perm_pvalues)
        ks_stats.append(ks)

    ks_stats = np.array(ks_stats)

    # Calculate confidence interval
    alpha = 1 - confidence_level
    ci_lower = np.percentile(ks_stats, (alpha / 2) * 100)
    ci_upper = np.percentile(ks_stats, (1 - alpha / 2) * 100)

    logger.info(f"Bootstrap CI ({confidence_level*100}%): [{ci_lower:.6f}, {ci_upper:.6f}]")

    return observed_ks, ci_lower, ci_upper


def load_trajectory_data(
    trajectory_file: Path
) -> Tuple[np.ndarray, np.ndarray, Dict[str, Any]]:
    """
    Load p-value trajectory and metadata from a JSON file.

    Args:
        trajectory_file: Path to the trajectory JSON file.

    Returns:
        Tuple of (pvalues, permutation_pvalues, metadata_dict).
    """
    if not trajectory_file.exists():
        raise FileNotFoundError(f"Trajectory file not found: {trajectory_file}")

    with open(trajectory_file, 'r') as f:
        data = json.load(f)

    if 'pvalues' not in data or 'permutation_pvalues' not in data:
        raise AnalysisError(
            f"Trajectory file missing required fields: {trajectory_file}"
        )

    pvalues = np.array(data['pvalues'])
    permutation_pvalues = np.array(data['permutation_pvalues'])

    metadata = {
        'seed': data.get('seed'),
        'n': data.get('n'),
        'p': data.get('p'),
        'rho': data.get('rho'),
        'distribution_type': data.get('distribution_type', 'unknown')
    }

    return pvalues, permutation_pvalues, metadata


def run_bootstrap_analysis(
    trajectory_file: Path,
    output_file: Path,
    n_bootstraps: int = 1000,
    confidence_level: float = 0.95,
    random_seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Run bootstrap analysis on a single trajectory and save results.

    Args:
        trajectory_file: Path to the trajectory JSON file.
        output_file: Path to save the bootstrap CI results.
        n_bootstraps: Number of bootstrap resamples.
        confidence_level: Confidence level for the interval.
        random_seed: Random seed for reproducibility.

    Returns:
        Dictionary containing the bootstrap CI results.
    """
    logger.info(f"Processing trajectory: {trajectory_file}")

    pvalues, permutation_pvalues, metadata = load_trajectory_data(trajectory_file)

    ks_stat, ci_lower, ci_upper = calculate_bootstrap_ci(
        pvalues,
        permutation_pvalues,
        n_bootstraps=n_bootstraps,
        confidence_level=confidence_level,
        random_seed=random_seed
    )

    result = {
        'KS_statistic': float(ks_stat),
        'bootstrap_ci_lower': float(ci_lower),
        'bootstrap_ci_upper': float(ci_upper),
        'confidence_level': confidence_level,
        'n_bootstraps': n_bootstraps,
        'seed': metadata['seed'],
        'n': metadata['n'],
        'p': metadata['p'],
        'rho': metadata['rho'],
        'distribution_type': metadata['distribution_type']
    }

    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)

    logger.info(f"Results saved to: {output_file}")

    return result


def main():
    """
    Main entry point for bootstrap CI calculation.

    Usage:
        python code/bootstrap_ci.py --trajectory data/synthetic/trajectories/{seed}.json
                                    --output data/results/bootstrap_cis.json
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Calculate bootstrap confidence intervals for KS statistics."
    )
    parser.add_argument(
        '--trajectory',
        type=str,
        required=True,
        help="Path to the trajectory JSON file (e.g., data/synthetic/trajectories/12345.json)"
    )
    parser.add_argument(
        '--output',
        type=str,
        default='data/results/bootstrap_cis.json',
        help="Path to save the bootstrap CI results (default: data/results/bootstrap_cis.json)"
    )
    parser.add_argument(
        '--n-bootstraps',
        type=int,
        default=1000,
        help="Number of bootstrap resamples (default: 1000)"
    )
    parser.add_argument(
        '--confidence-level',
        type=float,
        default=0.95,
        help="Confidence level for the interval (default: 0.95)"
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=None,
        help="Random seed for reproducibility (default: None)"
    )

    args = parser.parse_args()

    trajectory_path = Path(args.trajectory)
    output_path = Path(args.output)

    if not trajectory_path.is_absolute():
        # Make relative to project root if needed
        project_root = Path(__file__).resolve().parent.parent
        trajectory_path = project_root / trajectory_path

    if not output_path.is_absolute():
        project_root = Path(__file__).resolve().parent.parent
        output_path = project_root / output_path

    try:
        result = run_bootstrap_analysis(
            trajectory_path,
            output_path,
            n_bootstraps=args.n_bootstraps,
            confidence_level=args.confidence_level,
            random_seed=args.seed
        )

        print(json.dumps(result, indent=2))

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except AnalysisError as e:
        logger.error(f"Analysis error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
