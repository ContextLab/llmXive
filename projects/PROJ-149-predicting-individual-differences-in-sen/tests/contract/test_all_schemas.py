"""
Integration test to run all schema validations for T035b.
Runs all test classes defined in test_result_schemas.py.
"""
import pytest
from test_result_schemas import (
    TestModelResultsSchema,
    TestCorrelationsCorrectedSchema,
    TestNonLinearComparisonSchema,
    TestPermutationResultsSchema
)

# This file simply imports and runs the tests defined in test_result_schemas.py
# pytest will discover and run them automatically.

def test_all_schemas_exist():
    """Smoke test to ensure all schema files exist"""
    from pathlib import Path
    
    files = [
        'data/processed/model_results.json',
        'data/processed/correlations_corrected.csv',
        'data/processed/non_linear_comparison.json',
        'data/processed/permutation_results.json'
    ]
    
    for f in files:
        assert Path(f).exists(), f"Required output file missing: {f}"