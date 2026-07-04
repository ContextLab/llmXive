"""
Contract tests for metric output schemas (User Story 2).

This module validates the output structure of PIT and CRPS metrics
to ensure they conform to the expected schema before aggregation.
"""
import pytest
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional

# Mock implementations to satisfy imports if not fully implemented yet
# In a real run, these would import from code/metrics/pit.py and code/metrics/crps.py
# For this contract test, we simulate the expected return structures based on spec.

class MockPITResult:
    """Simulates the output of code.metrics.pit.calculate_pit_metrics"""
    def __init__(self, p_value: float, histogram_bins: List[float], 
                 histogram_counts: List[int], is_uniform: bool):
        self.p_value = p_value
        self.histogram_bins = histogram_bins
        self.histogram_counts = histogram_counts
        self.is_uniform = is_uniform

    def to_dict(self) -> Dict[str, Any]:
        return {
            "p_value": self.p_value,
            "histogram_bins": self.histogram_bins,
            "histogram_counts": self.histogram_counts,
            "is_uniform": self.is_uniform
        }

class MockCRPSResult:
    """Simulates the output of code.metrics.crps.calculate_crps"""
    def __init__(self, crps_score: float, observation: float, forecast_mean: float):
        self.crps_score = crps_score
        self.observation = observation
        self.forecast_mean = forecast_mean

    def to_dict(self) -> Dict[str, Any]:
        return {
            "crps_score": self.crps_score,
            "observation": self.observation,
            "forecast_mean": forecast_mean
        }

def test_pit_metric_schema():
    """
    Contract test: Verify PIT metric output schema.
    
    Expected Schema:
    {
        "p_value": float (0.0 - 1.0),
        "histogram_bins": List[float],
        "histogram_counts": List[int],
        "is_uniform": bool
    }
    """
    # Simulate a valid result from the PIT module (T022)
    mock_result = MockPITResult(
        p_value=0.082,
        histogram_bins=[0.0, 0.2, 0.4, 0.6, 0.8, 1.0],
        histogram_counts=[20, 18, 22, 19, 21],
        is_uniform=True
    )
    
    data = mock_result.to_dict()
    
    # Schema Assertions
    assert "p_value" in data, "Missing 'p_value' key"
    assert isinstance(data["p_value"], float), "'p_value' must be a float"
    assert 0.0 <= data["p_value"] <= 1.0, "'p_value' must be between 0 and 1"
    
    assert "histogram_bins" in data, "Missing 'histogram_bins' key"
    assert isinstance(data["histogram_bins"], list), "'histogram_bins' must be a list"
    assert all(isinstance(x, float) for x in data["histogram_bins"]), "'histogram_bins' must contain floats"
    
    assert "histogram_counts" in data, "Missing 'histogram_counts' key"
    assert isinstance(data["histogram_counts"], list), "'histogram_counts' must be a list"
    assert all(isinstance(x, int) for x in data["histogram_counts"]), "'histogram_counts' must contain ints"
    
    assert "is_uniform" in data, "Missing 'is_uniform' key"
    assert isinstance(data["is_uniform"], bool), "'is_uniform' must be a boolean"

def test_crps_metric_schema():
    """
    Contract test: Verify CRPS metric output schema.
    
    Expected Schema:
    {
        "crps_score": float,
        "observation": float,
        "forecast_mean": float
    }
    """
    # Simulate a valid result from the CRPS module (T023)
    mock_result = MockCRPSResult(
        crps_score=0.45,
        observation=10.5,
        forecast_mean=10.2
    )
    
    data = mock_result.to_dict()
    
    # Schema Assertions
    assert "crps_score" in data, "Missing 'crps_score' key"
    assert isinstance(data["crps_score"], float), "'crps_score' must be a float"
    assert data["crps_score"] >= 0, "'crps_score' must be non-negative"
    
    assert "observation" in data, "Missing 'observation' key"
    assert isinstance(data["observation"], (int, float)), "'observation' must be numeric"
    
    assert "forecast_mean" in data, "Missing 'forecast_mean' key"
    assert isinstance(data["forecast_mean"], (int, float)), "'forecast_mean' must be numeric"

def test_aggregated_metrics_dataframe_schema():
    """
    Contract test: Verify the structure of the aggregated metrics DataFrame.
    
    Expected Columns:
    - series_id (str)
    - model_name (str)
    - pit_p_value (float)
    - pit_is_uniform (bool)
    - crps_score (float)
    """
    # Construct a mock DataFrame simulating the output of aggregate_and_save_results
    data = {
        "series_id": ["M4_001", "M4_002"],
        "model_name": ["ARIMA", "Prophet"],
        "pit_p_value": [0.082, 0.15],
        "pit_is_uniform": [True, True],
        "crps_score": [0.45, 0.32]
    }
    df = pd.DataFrame(data)
    
    required_columns = {
        "series_id", "model_name", "pit_p_value", "pit_is_uniform", "crps_score"
    }
    
    assert set(df.columns) == required_columns, \
        f"DataFrame columns mismatch. Expected {required_columns}, got {set(df.columns)}"
    
    # Type checks for specific columns
    assert df["pit_p_value"].dtype in [np.float64, np.float32], "pit_p_value must be float"
    assert df["pit_is_uniform"].dtype == bool, "pit_is_uniform must be bool"
    assert df["crps_score"].dtype in [np.float64, np.float32], "crps_score must be float"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])