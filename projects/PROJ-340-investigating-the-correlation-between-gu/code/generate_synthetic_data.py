"""
Synthetic Data Generator for Pipeline Validation.

This module generates synthetic metagenomic count data and sleep architecture
metrics for testing the pipeline's validation logic, specifically the handling
of missing variables and zero-inflation.

CRITICAL: This data is for LOCAL VALIDATION ONLY. It must not be used in
production runs or reported as real scientific results.
"""
import os
import sys
import json
import argparse
import numpy as np
import pandas as pd
from pathlib import Path

# Set seeds for reproducibility
def set_seeds(seed: int = 42):
    np.random.seed(seed)

def load_required_variables(config_path: str = "data/config/required_variables.yaml") -> tuple:
    """
    Load required predictor and outcome variables from the configuration file.
    """
    import yaml
    path = Path(config_path)
    if not path.exists():
        # Fallback for testing if config is missing, though task requires it
        return ["taxon_a", "taxon_b"], ["rem_duration", "sws_duration", "total_sleep_time"]

    with open(path, 'r') as f:
        config = yaml.safe_load(f)

    predictors = config.get('required_predictors', [])
    outcomes = config.get('required_outcomes', [])
    return predictors, outcomes

def generate_metagenomic_counts(predictors: list, n_samples: int, zero_inflation_ratio: float = 0.4) -> pd.DataFrame:
    """
    Generate synthetic metagenomic count data using Zero-Inflated Negative Binomial distribution.
    """
    data = {}
    for taxon in predictors:
        # Parameters for Negative Binomial
        mu = np.random.uniform(10, 100)
        alpha = np.random.uniform(0.1, 0.5)

        # Generate counts
        counts = np.random.negative_binomial(alpha, alpha / (alpha + mu), n_samples)

        # Apply zero-inflation
        zero_mask = np.random.random(n_samples) < zero_inflation_ratio
        counts[zero_mask] = 0

        data[taxon] = counts

    return pd.DataFrame(data)

def generate_sleep_metrics(outcomes: list, n_samples: int, missing_variable: str = None) -> pd.DataFrame:
    """
    Generate synthetic sleep architecture metrics using Normal distribution.
    """
    data = {}
    for outcome in outcomes:
        if outcome == missing_variable:
            # Inject missing variable by not adding it to the dataframe
            continue

        # Generate based on typical sleep metrics (minutes)
        if 'rem' in outcome.lower():
            mean, std = 100, 20
        elif 'sws' in outcome.lower() or 'deep' in outcome.lower():
            mean, std = 120, 30
        elif 'total' in outcome.lower():
            mean, std = 450, 45
        else:
            mean, std = 60, 15

        values = np.random.normal(mean, std, n_samples)
        # Ensure non-negative
        values = np.maximum(0, values)
        data[outcome] = values

    return pd.DataFrame(data)

def generate_synthetic_dataset(n_samples: int = 100, missing_variable: str = None, seed: int = 42) -> pd.DataFrame:
    """
    Generate a complete synthetic dataset combining metagenomic and sleep data.
    """
    set_seeds(seed)
    predictors, outcomes = load_required_variables()

    # Generate data
    meta_df = generate_metagenomic_counts(predictors, n_samples)
    sleep_df = generate_sleep_metrics(outcomes, n_samples, missing_variable)

    # Combine
    df = pd.concat([meta_df, sleep_df], axis=1)

    # Add subject IDs
    df.insert(0, 'subject_id', [f'SUBJ_{i:04d}' for i in range(n_samples)])

    return df

def main():
    parser = argparse.ArgumentParser(description='Generate synthetic data for pipeline validation.')
    parser.add_argument('--output', type=str, default='data/raw/synthetic_test_data.csv',
                        help='Path to save the output CSV file.')
    parser.add_argument('--n-samples', type=int, default=100,
                        help='Number of samples to generate.')
    parser.add_argument('--missing-var', type=str, default=None,
                        help='Name of a variable to intentionally omit (for testing T011).')
    parser.add_argument('--seed', type=int, default=42,
                        help='Random seed for reproducibility.')

    args = parser.parse_args()

    # Ensure output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Generate data
    print(f"Generating synthetic dataset with {args.n_samples} samples...")
    if args.missing_var:
        print(f"Injecting missing variable: {args.missing_var}")
    
    df = generate_synthetic_dataset(
        n_samples=args.n_samples,
        missing_variable=args.missing_var,
        seed=args.seed
    )

    # Save to CSV
    df.to_csv(output_path, index=False)
    print(f"Synthetic data saved to: {output_path}")
    print(f"Shape: {df.shape}")
    print(f"Columns: {list(df.columns)}")

    # Verify missing variable logic if requested
    if args.missing_var and args.missing_var in df.columns:
        print(f"ERROR: Variable {args.missing_var} was supposed to be missing but is present!")
        sys.exit(1)
    elif args.missing_var:
        print(f"SUCCESS: Variable {args.missing_var} correctly omitted.")

if __name__ == '__main__':
    main()