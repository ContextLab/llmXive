"""
Bootstrap analysis module for computing 95% confidence intervals.
Implements runtime monitoring to enforce 5.5h limit.
"""
import os
import sys
import json
import time
import logging
import numpy as np
from pathlib import Path
from typing import Dict, Any, Tuple, List

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logger = logging.getLogger(__name__)

# Constants
DEFAULT_BOOTSTRAP_COUNT = 1000
MIN_BOOTSTRAP_COUNT = 500
RUNTIME_LIMIT_HOURS = 5.5
RUNTIME_LIMIT_SECONDS = RUNTIME_LIMIT_HOURS * 3600
CHECK_INTERVAL = 100  # Check runtime every N resamples

def load_correlation_data(filepath: str) -> Tuple[np.ndarray, np.ndarray]:
    """
    Load correlation data from CSV file.
    Returns: (metacognitive_scores, accuracy_scores)
    """
    import pandas as pd

    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Correlation data file not found: {filepath}")

    df = pd.read_csv(filepath)

    # Validate required columns
    required_cols = ['metacognitive_score', 'accuracy_score']
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    # Drop rows with NaN values
    df = df.dropna(subset=required_cols)

    return df['metacognitive_score'].values, df['accuracy_score'].values

def compute_correlation_statistic(x: np.ndarray, y: np.ndarray) -> float:
    """
    Compute Pearson correlation coefficient.
    Returns: r value
    """
    if len(x) != len(y) or len(x) == 0:
        return np.nan

    # Handle constant input
    if np.std(x) == 0 or np.std(y) == 0:
        return np.nan

    return np.corrcoef(x, y)[0, 1]

def run_bootstrap_analysis(
    x: np.ndarray,
    y: np.ndarray,
    n_resamples: int = DEFAULT_BOOTSTRAP_COUNT,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Run bootstrap resampling to compute 95% CI for correlation.
    Monitors runtime and reduces resamples if limit exceeded.

    Returns:
        Dictionary with:
          - original_r: Original correlation coefficient
          - bootstrap_rs: Array of bootstrap correlation values
          - ci_lower: Lower bound of 95% CI
          - ci_upper: Upper bound of 95% CI
          - bootstrap_count: Actual number of resamples performed
          - runtime_seconds: Total runtime
          - warning: Warning message if runtime limit triggered
    """
    start_time = time.time()
    rng = np.random.default_rng(seed)

    bootstrap_rs = []
    n_actual = n_resamples
    warning_msg = None

    for i in range(n_resamples):
        # Check runtime periodically
        if i > 0 and i % CHECK_INTERVAL == 0:
            elapsed = time.time() - start_time
            if elapsed > RUNTIME_LIMIT_SECONDS:
                warning_msg = f"Runtime limit detected ({elapsed:.1f}s > {RUNTIME_LIMIT_HOURS}h), reducing bootstrap count to {MIN_BOOTSTRAP_COUNT}"
                logger.warning(warning_msg)
                n_actual = MIN_BOOTSTRAP_COUNT
                # Adjust loop to stop early
                if i >= n_actual:
                    break

        # Resample with replacement
        indices = rng.choice(len(x), size=len(x), replace=True)
        x_boot = x[indices]
        y_boot = y[indices]

        # Compute correlation
        r = compute_correlation_statistic(x_boot, y_boot)
        if not np.isnan(r):
            bootstrap_rs.append(r)

    # If we stopped early due to runtime, adjust count
    if warning_msg:
        n_actual = len(bootstrap_rs)

    runtime = time.time() - start_time

    # Compute statistics
    original_r = compute_correlation_statistic(x, y)
    bootstrap_rs = np.array(bootstrap_rs)

    if len(bootstrap_rs) == 0:
        return {
            'original_r': original_r,
            'bootstrap_rs': [],
            'ci_lower': np.nan,
            'ci_upper': np.nan,
            'bootstrap_count': 0,
            'runtime_seconds': runtime,
            'warning': warning_msg
        }

    # Percentile-based CI (95%)
    ci_lower = np.percentile(bootstrap_rs, 2.5)
    ci_upper = np.percentile(bootstrap_rs, 97.5)

    return {
        'original_r': original_r,
        'bootstrap_rs': bootstrap_rs.tolist(),
        'ci_lower': float(ci_lower),
        'ci_upper': float(ci_upper),
        'bootstrap_count': len(bootstrap_rs),
        'runtime_seconds': runtime,
        'warning': warning_msg
    }

def write_results(results: Dict[str, Any], output_path: str) -> None:
    """
    Write bootstrap results to JSON file.
    """
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    # Convert numpy types for JSON serialization
    serializable = {}
    for k, v in results.items():
        if isinstance(v, np.ndarray):
            serializable[k] = v.tolist()
        elif isinstance(v, (np.floating, np.integer)):
            serializable[k] = float(v)
        else:
            serializable[k] = v

    with open(output_path, 'w') as f:
        json.dump(serializable, f, indent=2)

    logger.info(f"Bootstrap results written to {output_path}")

def main():
    """
    Main entry point for bootstrap analysis.
    Reads from data/derived/correlation_data.csv and writes to data/results/bootstrap_config.json
    """
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Define paths
    project_root = Path(__file__).parent.parent.parent.parent
    input_path = project_root / 'data' / 'derived' / 'correlation_data.csv'
    output_path = project_root / 'data' / 'results' / 'bootstrap_config.json'

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Load config for parameters
    from config.env_config import load_config, get_seed
    config = load_config()
    n_resamples = config.analysis.get('bootstrap_count', DEFAULT_BOOTSTRAP_COUNT)
    seed = get_seed()

    logger.info(f"Starting bootstrap analysis with {n_resamples} resamples")

    try:
        # Load data
        x, y = load_correlation_data(str(input_path))
        logger.info(f"Loaded {len(x)} samples for correlation analysis")

        # Run bootstrap
        results = run_bootstrap_analysis(x, y, n_resamples, seed)

        # Write results
        write_results(results, str(output_path))

        # Log summary
        logger.info(f"Bootstrap complete: r={results['original_r']:.4f}, "
                   f"95% CI [{results['ci_lower']:.4f}, {results['ci_upper']:.4f}], "
                   f"n_resamples={results['bootstrap_count']}, "
                   f"runtime={results['runtime_seconds']:.1f}s")

        if results.get('warning'):
            logger.warning(results['warning'])

        return 0

    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())