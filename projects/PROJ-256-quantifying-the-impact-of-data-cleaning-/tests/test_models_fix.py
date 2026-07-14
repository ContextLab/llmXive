"""
Basic sanity test to ensure that the patched models module loads without
raising a Pydantic schema generation error.
"""

import pytest

from models import CleaningStrategyType, CleaningStrategy, AnalysisResult


def test_cleaning_strategy_type_schema():
    # Instantiating should not raise an exception
    cst = CleaningStrategyType("outlier_removal")
    assert str(cst) == "outlier_removal"


def test_cleaning_strategy_model():
    cs = CleaningStrategy(strategy_type=CleaningStrategyType("mean_impute"))
    # The model should accept arbitrary types for ``strategy_type``
    assert cs.strategy_type.value == "mean_impute"


def test_analysis_result_model():
    # Minimal valid AnalysisResult
    ar = AnalysisResult(
        dataset_name="test_dataset",
        outcome_variable="y",
        predictors=["x1", "x2"],
        t_test={"p_value": 0.05, "ci": [0.1, 0.3]},
        regression={"coefficients": [{"name": "x1", "value": 1.2}]},
    )
    assert ar.dataset_name == "test_dataset"

# Run with: pytest -q tests/test_models_fix.py