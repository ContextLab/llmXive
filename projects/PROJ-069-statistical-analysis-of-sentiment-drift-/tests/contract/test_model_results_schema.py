"""
Contract test for the ModelResult schema.
Ensures the modeling output structures are valid.
"""
import pytest
from contracts.model_results import (
    ModelResult,
    StationarityTestResult,
    CointegrationTestResult,
    GrangerCausalityResult,
    CollinearityDiagnostic,
    BootstrapValidationResult
)

def test_stationarity_result_valid():
    """Test valid stationarity result."""
    res = StationarityTestResult(
        variable="GDP",
        statistic=-3.5,
        p_value=0.01,
        is_stationary=True,
        transformation_applied="log"
    )
    assert res.is_stationary is True

def test_cointegration_result_valid():
    """Test valid cointegration result."""
    res = CointegrationTestResult(
        statistic_trace=25.5,
        p_value_trace=0.04,
        cointegration_rank=1,
        model_selection="VECM"
    )
    assert res.model_selection == "VECM"

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
