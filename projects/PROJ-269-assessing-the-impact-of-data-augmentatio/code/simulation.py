"""
Monte Carlo simulation module.

This module implements the generic Monte Carlo loop infrastructure for
running hypothesis tests on baseline and augmented datasets.
"""

import os
import json
import logging
import argparse
import hashlib
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np
from scipy import stats
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def validate_schema(data: Dict[str, Any], schema_path: str) -> bool:
    """
    Validate data against a JSON schema.

    Args:
        data: Data to validate.
        schema_path: Path to the schema file.

    Returns:
        True if valid, False otherwise.
    """
    # Simplified validation - in production, use jsonschema library
    required_keys = ['p_values', 'error_rates', 'metadata']
    for key in required_keys:
        if key not in data:
            logger.warning(f"Missing required key: {key}")
            return False
    return True


def load_dataset(filepath: str) -> pd.DataFrame:
    """
    Load a dataset from a CSV file.

    Args:
        filepath: Path to the CSV file.

    Returns:
        Loaded DataFrame.
    """
    return pd.read_csv(filepath)


def generate_type_i_condition(
    df: pd.DataFrame,
    target_col: str,
    random_state: int
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
    df_copy = df.copy()
    np.random.seed(random_state)
    df_copy[target_col] = np.random.permutation(df_copy[target_col].values)
    return df_copy


def generate_type_ii_condition(
    df: pd.DataFrame,
    target_col: str,
    effect_size: float = 0.5,
    random_state: int = 42
) -> pd.DataFrame:
    """
    Generate Type II error condition by shifting mean of first numeric feature.

    Args:
        df: Input DataFrame.
        target_col: Name of the target column.
        effect_size: Cohen's d effect size.
        random_state: Random seed.

    Returns:
        DataFrame with shifted feature values.
    """
    df_copy = df.copy()
    numeric_cols = df_copy.select_dtypes(include=[np.number]).columns
    # Exclude target column
    numeric_cols = [col for col in numeric_cols if col != target_col]

    if not numeric_cols:
        return df_copy

    first_feature = numeric_cols[0]
    np.random.seed(random_state)

    # Calculate mean and std of the feature for each class
    mean_0 = df_copy[df_copy[target_col] == 0][first_feature].mean()
    mean_1 = df_copy[df_copy[target_col] == 1][first_feature].mean()
    std_1 = df_copy[df_copy[target_col] == 1][first_feature].std()

    if std_1 == 0:
        return df_copy

    # Shift class 1 mean
    shift = effect_size * std_1
    mask = df_copy[target_col] == 1
    df_copy.loc[mask, first_feature] += shift

    return df_copy


def run_hypothesis_test(
    df: pd.DataFrame,
    target_col: str
) -> float:
    """
    Run a two-sample t-test.

    Args:
        df: Input DataFrame.
        target_col: Name of the target column.

    Returns:
        P-value from the t-test.
    """
    X = df.drop(columns=[target_col])
    y = df[target_col]

    # Get first numeric feature
    numeric_cols = X.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) == 0:
        return 1.0

    feature = numeric_cols[0]
    group_0 = X[y == 0][feature]
    group_1 = X[y == 1][feature]

    if len(group_0) < 2 or len(group_1) < 2:
        return 1.0

    _, p_value = stats.ttest_ind(group_0, group_1)
    return p_value


def run_simulation_iteration(
    df: pd.DataFrame,
    target_col: str,
    condition: str,
    augmentation_method: Optional[str] = None,
    random_state: Optional[int] = None
) -> float:
    """
    Run a single simulation iteration.

    Args:
        df: Input DataFrame.
        target_col: Name of the target column.
        condition: 'null' or 'alt'.
        augmentation_method: Optional augmentation method.
        random_state: Random seed for this iteration.

    Returns:
        P-value from the hypothesis test.
    """
    if random_state is not None:
        np.random.seed(random_state)

    df_work = df.copy()

    if condition == 'null':
        df_work = generate_type_i_condition(df_work, target_col, random_state or 42)
    elif condition == 'alt':
        df_work = generate_type_ii_condition(df_work, target_col, random_state=random_state or 42)

    if augmentation_method:
        # Import augmentation functions here to avoid circular imports
        from augment import augment_dataset
        df_work = augment_dataset(df_work, augmentation_method, target_col, random_state=random_state or 42)
        if df_work is None:
            return None

    p_value = run_hypothesis_test(df_work, target_col)
    return p_value


def run_full_simulation(
    dataset_path: str,
    target_col: str,
    condition: str,
    n_iterations: int,
    augmentation_method: Optional[str] = None,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Run the full Monte Carlo simulation.

    Args:
        dataset_path: Path to the dataset.
        target_col: Name of the target column.
        condition: 'null' or 'alt'.
        n_iterations: Number of iterations.
        augmentation_method: Optional augmentation method.
        seed: Base random seed.

    Returns:
        Dictionary with p-values and metadata.
    """
    df = load_dataset(dataset_path)
    p_values = []

    for i in range(n_iterations):
        iter_seed = seed + i
        p_value = run_simulation_iteration(
            df, target_col, condition, augmentation_method, iter_seed
        )
        if p_value is not None:
            p_values.append(p_value)

    return {
        'p_values': p_values,
        'n_iterations': n_iterations,
        'condition': condition,
        'augmentation_method': augmentation_method,
        'seed': seed
    }


def save_results(
    results: Dict[str, Any],
    output_path: str
) -> None:
    """
    Save simulation results to a JSON file.

    Args:
        results: Results dictionary.
        output_path: Path to save the results.
    """
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Results saved to {output_path}")


def main() -> None:
    """Main entry point for simulation."""
    parser = argparse.ArgumentParser(description="Run Monte Carlo simulation")
    parser.add_argument("--dataset", type=str, required=True, help="Path to dataset")
    parser.add_argument("--target", type=str, default="target", help="Target column")
    parser.add_argument("--condition", type=str, choices=["null", "alt"], default="null")
    parser.add_argument("--iterations", type=int, default=100)
    parser.add_argument("--output", type=str, required=True)
    parser.add_argument("--augmentation", type=str, default=None)
    parser.add_argument("--seed", type=int, default=42)

    args = parser.parse_args()

    results = run_full_simulation(
        args.dataset,
        args.target,
        args.condition,
        args.iterations,
        args.augmentation,
        args.seed
    )

    save_results(results, args.output)


if __name__ == "__main__":
    main()
