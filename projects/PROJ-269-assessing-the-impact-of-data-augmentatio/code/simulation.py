"""
Simulation module for the augmentation impact study.

Provides Monte Carlo simulation infrastructure for estimating Type I and Type II
error rates under different data augmentation scenarios.
"""

import os
import json
import logging
import argparse
import hashlib
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

RESULTS_DIR: Path = Path("results")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

CONTRACTS_DIR: Path = Path("contracts")
CONTRACTS_DIR.mkdir(parents=True, exist_ok=True)


def validate_schema(data: Dict[str, Any], schema_path: str) -> bool:
    """
    Validate simulation output against JSON schema.

    Args:
        data: Simulation output data.
        schema_path: Path to the JSON schema file.

    Returns:
        True if valid, False otherwise.
    """
    try:
        with open(schema_path, 'r') as f:
            schema: Dict[str, Any] = json.load(f)

        # Basic validation (simplified for this implementation)
        required_keys: List[str] = ['metadata', 'p_values', 'error_rates']
        for key in required_keys:
            if key not in data:
                logger.error(f"Missing required key in output: {key}")
                return False

        logger.debug("Schema validation passed")
        return True

    except Exception as e:
        logger.error(f"Schema validation failed: {str(e)}")
        return False


def load_dataset(filepath: Path) -> pd.DataFrame:
    """
    Load a dataset from CSV file.

    Args:
        filepath: Path to the CSV file.

    Returns:
        Loaded DataFrame.
    """
    try:
        df: pd.DataFrame = pd.read_csv(filepath)
        logger.info(f"Loaded dataset from {filepath}: {len(df)} rows, {len(df.columns)} columns")
        return df
    except Exception as e:
        logger.error(f"Failed to load dataset from {filepath}: {str(e)}")
        raise


def generate_type_i_condition(
    df: pd.DataFrame,
    target_col: str,
    random_state: Optional[int] = None
) -> pd.DataFrame:
    """
    Generate Type I error condition by permuting labels.

    Args:
        df: Input DataFrame.
        target_col: Name of the target column.
        random_state: Random seed.

    Returns:
        DataFrame with permuted labels.
    """
    if random_state is not None:
        np.random.seed(random_state)

    df_copy: pd.DataFrame = df.copy()
    df_copy[target_col] = np.random.permutation(df_copy[target_col].values)

    logger.debug(f"Generated Type I condition (label permutation) with seed {random_state}")
    return df_copy


def generate_type_ii_condition(
    df: pd.DataFrame,
    target_col: str,
    effect_size: float = 0.5,
    random_state: Optional[int] = None
) -> pd.DataFrame:
    """
    Generate Type II error condition by shifting means (Cohen's d = effect_size).

    Args:
        df: Input DataFrame.
        target_col: Name of the target column.
        effect_size: Cohen's d effect size.
        random_state: Random seed.

    Returns:
        DataFrame with shifted means for one class.
    """
    if random_state is not None:
        np.random.seed(random_state)

    df_copy: pd.DataFrame = df.copy()
    features: pd.DataFrame = df_copy.drop(columns=[target_col])
    target: pd.Series = df_copy[target_col]

    # Calculate mean and std of features
    mean: np.ndarray = features.mean().values
    std: np.ndarray = features.std().values

    # Shift one class
    minority_class: int = target.value_counts().idxmin()
    mask: np.ndarray = target == minority_class

    shift: np.ndarray = effect_size * std
    features.values[mask] += shift[mask]

    df_copy[features.columns] = features

    logger.debug(
        f"Generated Type II condition (mean shift, d={effect_size}) "
        f"for class {minority_class}"
    )
    return df_copy


def run_hypothesis_test(
    df: pd.DataFrame,
    target_col: str
) -> Tuple[float, float]:
    """
    Run a two-sample t-test hypothesis test.

    Args:
        df: Input DataFrame.
        target_col: Name of the target column.

    Returns:
        Tuple of (p_value, t_statistic).
    """
    try:
        features: pd.DataFrame = df.drop(columns=[target_col])
        target: pd.Series = df[target_col]

        # Get unique classes
        classes: np.ndarray = np.unique(target)

        if len(classes) != 2:
            logger.warning(f"Expected 2 classes, got {len(classes)}. Using first two.")
            classes = classes[:2]

        # Separate by class
        group1: np.ndarray = features[target == classes[0]].values.mean(axis=0)
        group2: np.ndarray = features[target == classes[1]].values.mean(axis=0)

        # Perform t-test
        t_stat: float
        p_value: float
        t_stat, p_value = stats.ttest_ind(
            features[target == classes[0]],
            features[target == classes[1]],
            equal_var=False
        )

        # Average p-value across features if multivariate
        if isinstance(p_value, np.ndarray):
            p_value = np.mean(p_value)

        return float(p_value), float(t_stat)

    except Exception as e:
        logger.error(f"Hypothesis test failed: {str(e)}")
        return 1.0, 0.0


def run_simulation_iteration(
    df: pd.DataFrame,
    target_col: str,
    condition: str,
    random_state: int
) -> Dict[str, Any]:
    """
    Run a single simulation iteration.

    Args:
        df: Input DataFrame.
        target_col: Name of the target column.
        condition: 'null' or 'alt'.
        random_state: Random seed.

    Returns:
        Dictionary with p-value and condition info.
    """
    if condition == 'null':
        processed_df: pd.DataFrame = generate_type_i_condition(df, target_col, random_state)
    elif condition == 'alt':
        processed_df = generate_type_ii_condition(df, target_col, random_state=random_state)
    else:
        processed_df = df

    p_value, t_stat = run_hypothesis_test(processed_df, target_col)

    return {
        'p_value': p_value,
        't_statistic': t_stat,
        'condition': condition,
        'random_state': random_state
    }


def run_full_simulation(
    df: pd.DataFrame,
    target_col: str,
    n_iterations: int,
    condition: str,
    seed: int
) -> List[Dict[str, Any]]:
    """
    Run full Monte Carlo simulation.

    Args:
        df: Input DataFrame.
        target_col: Name of the target column.
        n_iterations: Number of iterations.
        condition: 'null' or 'alt'.
        seed: Base random seed.

    Returns:
        List of iteration results.
    """
    results: List[Dict[str, Any]] = []

    for i in range(n_iterations):
        iteration_seed: int = seed + i
        result: Dict[str, Any] = run_simulation_iteration(
            df, target_col, condition, iteration_seed
        )
        results.append(result)

        if (i + 1) % 100 == 0:
            logger.info(f"Completed {i + 1}/{n_iterations} iterations")

    logger.info(f"Simulation complete: {len(results)} iterations")
    return results


def save_results(
    results: List[Dict[str, Any]],
    dataset_name: str,
    size: int,
    condition: str,
    method: str = 'baseline'
) -> Path:
    """
    Save simulation results to JSON file.

    Args:
        results: List of iteration results.
        dataset_name: Name of the dataset.
        size: Sample size.
        condition: 'null' or 'alt'.
        method: Augmentation method ('baseline', 'gaussian', etc.).

    Returns:
        Path to the saved file.
    """
    # Calculate error rates
    p_values: List[float] = [r['p_value'] for r in results]
    type_i_rate: float = np.mean([1.0 if p < 0.05 else 0.0 for p in p_values])

    output: Dict[str, Any] = {
        'metadata': {
            'dataset': dataset_name,
            'size': size,
            'condition': condition,
            'method': method,
            'n_iterations': len(results),
            'timestamp': str(pd.Timestamp.now())
        },
        'p_values': p_values,
        'error_rates': {
            'type_i': type_i_rate,
            'alpha_threshold': 0.05
        },
        'results': results
    }

    filename: str = f"{dataset_name}_{size}_{method}_{condition}.json"
    filepath: Path = RESULTS_DIR / filename

    with open(filepath, 'w') as f:
        json.dump(output, f, indent=2)

    logger.info(f"Saved results to {filepath}")
    return filepath


def main() -> int:
    """
    Main function to run simulation.

    Returns:
        Exit code: 0 for success, 1 for failure.
    """
    logger.info("Simulation module ready. Use run_full_simulation() with specific configs.")
    return 0


if __name__ == "__main__":
    exit(main())
