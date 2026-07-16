"""Integration tests for the full analysis pipeline."""
import pytest
import pandas as pd
import numpy as np
from stats_engine import (
    generate_synthetic_dataset,
    run_full_analysis_pipeline,
    validate_null_model,
)


def test_synthetic_validation():
    """Verify that observed statistics fall within null distribution for synthetic data."""
    # Generate synthetic data with no correlation
    df = generate_synthetic_dataset(n_samples=500, n_vars=20, random_seed=42)

    # Run full pipeline
    results = run_full_analysis_pipeline(df, threshold=0.3, n_permutations=100, random_seed=42)

    p_values = results["p_values"]

    # For synthetic uncorrelated data, p-values should be > 0.05
    for stat, p_val in p_values.items():
        assert p_val > 0.05, f"Statistic {stat} has p-value {p_val} <= 0.05"
