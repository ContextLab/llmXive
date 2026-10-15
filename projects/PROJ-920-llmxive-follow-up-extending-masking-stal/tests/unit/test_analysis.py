import json
from pathlib import Path

import pytest

from code.analyze_results import load_analysis_config, load_simulation_data, validate_sample_size, run_logistic_regression

# Helper to locate the test data files
DATA_DIR = Path(__file__).parents[2] / "data" / "logs"
RESULT_DIR = Path(__file__).parents[2] / "results"


def test_load_analysis_config(tmp_path):
    # Create a minimal valid config
    config_path = tmp_path / "analysis_config.json"
    config_path.write_text(
        json.dumps(
            {
                "min_samples_per_bin": 5,
                "splines_df_candidates": [3, 4],
                "p_value_threshold": 0.05,
            }
        )
    )
    # Monkey‑patch the path inside the module
    original_path = Path(__file__).parents[2] / "code" / "config" / "analysis_config.json"
    original_path.parent.mkdir(parents=True, exist_ok=True)
    original_path.write_text(config_path.read_text())
    cfg = load_analysis_config(original_path)
    assert cfg["min_samples_per_bin"] == 5
    assert cfg["splines_df_candidates"] == [3, 4]
    assert cfg["p_value_threshold"] == 0.05


def test_load_simulation_data(tmp_path):
    csv_path = tmp_path / "simulation_results.csv"
    csv_path.write_text(
        "density_value,requested_horizon,success\\n"
        "0.3,1,0\\n"
        "0.7,2,1\\n"
    )
    df = load_simulation_data(csv_path)
    assert len(df) == 2
    assert list(df.columns) == ["density_value", "requested_horizon", "success"]


def test_validate_sample_size():
    import pandas as pd

    df = pd.DataFrame(
        {
            "density_value": [0.1, 0.1, 0.2, 0.2],
            "requested_horizon": [1, 1, 2, 2],
            "success": [0, 1, 0, 1],
        }
    )
    # Each bin has exactly 2 samples, min_samples=2 -> should pass
    validate_sample_size(df, min_samples=2)


def test_run_logistic_regression(tmp_path):
    # Minimal dataset with enough variation
    csv_path = tmp_path / "simulation_results.csv"
    csv_path.write_text(
        "density_value,requested_horizon,success\\n"
        "0.2,1,0\\n"
        "0.4,2,1\\n"
        "0.6,3,0\\n"
        "0.8,4,1\\n"
    )
    df = load_simulation_data(csv_path)
    config = {
        "splines_df_candidates": [3],
        "p_value_threshold": 0.05,
    }
    results = run_logistic_regression(df, config)
    # Basic sanity checks on the output structure
    assert "model_summary" in results
    assert "coefficients" in results
    assert isinstance(results["coefficients"], list)
    assert "interaction_significance" in results
    # Ensure JSON serialization works
    json.dumps(results)  # should not raise