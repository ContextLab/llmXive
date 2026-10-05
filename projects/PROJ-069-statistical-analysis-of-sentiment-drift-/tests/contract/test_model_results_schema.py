"""
Contract test for the ModelResult schema.
Ensures the modeling output structures are valid.
"""
import json
import pytest
from pathlib import Path
from typing import Any, Dict

from contracts.model_results import (
    ModelResult,
    StationarityTestResult,
    CointegrationTestResult,
    GrangerCausalityResult,
    CollinearityDiagnostic,
    BootstrapValidationResult
)

PROJECT_ROOT = Path(__file__).parent.parent.parent
RESULTS_DIR = PROJECT_ROOT / "results"
MODEL_STATS_PATH = RESULTS_DIR / "model_stats.json"

def test_stationarity_result_valid():
    """Test valid stationarity result construction."""
    res = StationarityTestResult(
        variable="GDP",
        statistic=-3.5,
        p_value=0.01,
        is_stationary=True,
        transformation_applied="log"
    )
    assert res.is_stationary is True
    assert res.variable == "GDP"

def test_cointegration_result_valid():
    """Test valid cointegration result construction."""
    res = CointegrationTestResult(
        statistic_trace=25.5,
        p_value_trace=0.04,
        cointegration_rank=1,
        model_selection="VECM"
    )
    assert res.model_selection == "VECM"
    assert res.cointegration_rank == 1

def test_granger_causality_result_valid():
    """Test valid Granger causality result construction."""
    res = GrangerCausalityResult(
        test_direction="Sentiment -> GDP",
        f_statistic=5.5,
        p_value=0.03,
        is_causal=True,
        lag_length=2
    )
    assert res.is_causal is True
    assert res.f_statistic == 5.5

def test_collinearity_diagnostic_valid():
    """Test valid collinearity diagnostic construction."""
    res = CollinearityDiagnostic(
        variable="GDP",
        vif_score=2.0,
        is_high=False
    )
    assert res.vif_score == 2.0
    assert res.is_high is False

def test_bootstrap_validation_result_valid():
    """Test valid bootstrap validation result construction."""
    res = BootstrapValidationResult(
        original_coefficient=0.5,
        confidence_interval_95=[0.4, 0.6],
        ci_width=0.2,
        convergence_achieved=True,
        block_length=1,
        iterations=1000
    )
    assert res.convergence_achieved is True
    assert res.ci_width == 0.2

def test_model_result_aggregation():
    """Test full ModelResult aggregation."""
    model = ModelResult(
        model_type="VECM",
        optimal_lag_length=2,
        stationarity_results=[
            StationarityTestResult(
                variable="GDP", statistic=-4.0, p_value=0.01, is_stationary=True
            )
        ],
        cointegration_result=CointegrationTestResult(
            statistic_trace=20.0, p_value_trace=0.02, cointegration_rank=1, model_selection="VECM"
        ),
        granger_causality_results=[
            GrangerCausalityResult(
                test_direction="Sentiment -> GDP",
                f_statistic=5.5,
                p_value=0.03,
                is_causal=True,
                lag_length=2
            )
        ],
        collinearity_diagnostics=[
            CollinearityDiagnostic(variable="GDP", vif_score=2.0, is_high=False)
        ],
        validation_result=BootstrapValidationResult(
            original_coefficient=0.5,
            confidence_interval_95=[0.4, 0.6],
            ci_width=0.2,
            convergence_achieved=True,
            block_length=1,
            iterations=1000
        )
    )
    assert model.model_type == "VECM"
    assert len(model.stationarity_results) == 1

def test_model_stats_json_schema_contracts():
    """
    Contract test: Validates that the actual output file `results/model_stats.json`
    conforms to the `ModelResult` Pydantic schema defined in `contracts/model_results.py`.
    
    This ensures that the modeling pipeline (T026-T031) produces data that strictly
    matches the expected structure.
    """
    if not MODEL_STATS_PATH.exists():
        pytest.fail(f"Contract test failed: Expected file {MODEL_STATS_PATH} does not exist. "
                    "Run the modeling pipeline (T026-T031) to generate this file first.")

    try:
        with open(MODEL_STATS_PATH, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
    except json.JSONDecodeError as e:
        pytest.fail(f"Contract test failed: {MODEL_STATS_PATH} is not valid JSON. Error: {e}")

    try:
        # Attempt to instantiate the Pydantic model from the JSON data.
        # This will raise ValidationError if the schema does not match.
        model_result = ModelResult.model_validate(raw_data)
        
        # Verify critical fields exist and are of expected types
        assert isinstance(model_result.model_type, str), "model_type must be a string"
        assert model_result.model_type in ["VAR", "VECM"], f"model_type must be VAR or VECM, got {model_result.model_type}"
        assert isinstance(model_result.optimal_lag_length, int), "optimal_lag_length must be an integer"
        
        assert isinstance(model_result.stationarity_results, list), "stationarity_results must be a list"
        for res in model_result.stationarity_results:
            assert isinstance(res.variable, str), "Stationarity variable must be string"
            assert isinstance(res.p_value, (int, float)), "Stationarity p_value must be numeric"
            assert isinstance(res.is_stationary, bool), "Stationarity is_stationary must be boolean"

        assert isinstance(model_result.cointegration_result, dict) or isinstance(model_result.cointegration_result, CointegrationTestResult)
        # Pydantic handles the dict-to-model conversion in model_validate, but let's ensure the nested object is valid
        coint_res = model_result.cointegration_result
        assert coint_res.model_selection in ["VAR", "VECM"], "Cointegration model_selection must be VAR or VECM"

        assert isinstance(model_result.granger_causality_results, list), "granger_causality_results must be a list"
        for gc in model_result.granger_causality_results:
            assert isinstance(gc.test_direction, str), "Granger direction must be string"
            assert isinstance(gc.p_value, (int, float)), "Granger p_value must be numeric"

        assert isinstance(model_result.collinearity_diagnostics, list), "collinearity_diagnostics must be a list"
        for diag in model_result.collinearity_diagnostics:
            assert isinstance(diag.vif_score, (int, float)), "VIF score must be numeric"

        assert isinstance(model_result.validation_result, dict) or isinstance(model_result.validation_result, BootstrapValidationResult)
        val_res = model_result.validation_result
        assert isinstance(val_res.confidence_interval_95, list), "CI must be a list"
        assert len(val_res.confidence_interval_95) == 2, "CI must have 2 elements"

    except Exception as e:
        pytest.fail(f"Contract test failed: model_stats.json does not conform to ModelResult schema. "
                    f"Error: {e}")