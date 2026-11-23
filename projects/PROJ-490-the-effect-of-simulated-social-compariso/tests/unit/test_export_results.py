import os
import json
import tempfile
from pathlib import Path
import pandas as pd
import pytest

from analysis.export_results import export_coefficients_to_csv, export_diagnostics_to_json, run_export

@pytest.fixture
def sample_coefficients():
    data = {
        "term": ["Intercept", "avatar_condition", "pre_self_esteem", "comparison_tendency", "interaction"],
        "estimate": [2.5, 0.3, 0.8, -0.1, 0.05],
        "std_err": [0.1, 0.05, 0.04, 0.06, 0.02],
        "t_stat": [25.0, 6.0, 20.0, -1.67, 2.5],
        "p_value": [0.001, 0.0001, 0.0001, 0.095, 0.012],
        "ci_lower": [2.3, 0.2, 0.72, -0.22, 0.01],
        "ci_upper": [2.7, 0.4, 0.88, 0.02, 0.09]
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_diagnostics():
    return {
        "model_summary": {
            "r_squared": 0.65,
            "adj_r_squared": 0.64,
            "f_statistic": 45.2,
            "f_p_value": 0.0001
        },
        "assumptions": {
            "normality": {
                "shapiro_w_stat": 0.98,
                "shapiro_p_value": 0.45,
                "passed": True
            },
            "homoscedasticity": {
                "breusch_pagan_stat": 2.1,
                "breusch_pagan_p_value": 0.15,
                "passed": True
            }
        },
        "collinearity": {
            "vif_scores": {
                "avatar_condition": 1.2,
                "pre_self_esteem": 1.1,
                "comparison_tendency": 1.3,
                "interaction": 1.4
            },
            "max_vif": 1.4,
            "flagged": False
        },
        "interpretation_label": "Simulated Causal Effect"
    }

def test_export_coefficients_to_csv(sample_coefficients, tmp_path):
    output_file = tmp_path / "test_coeffs.csv"
    export_coefficients_to_csv(sample_coefficients, output_file)

    assert output_file.exists()
    loaded_df = pd.read_csv(output_file)
    assert list(loaded_df.columns) == list(sample_coefficients.columns)
    assert len(loaded_df) == len(sample_coefficients)

def test_export_diagnostics_to_json(sample_diagnostics, tmp_path):
    output_file = tmp_path / "test_diagnostics.json"
    export_diagnostics_to_json(sample_diagnostics, output_file)

    assert output_file.exists()
    with open(output_file, 'r') as f:
        loaded_data = json.load(f)
    
    assert loaded_data == sample_diagnostics

def test_run_export_integration(sample_coefficients, sample_diagnostics, tmp_path):
    csv_path, json_path = run_export(
        sample_coefficients, 
        sample_diagnostics, 
        output_dir=tmp_path
    )

    assert csv_path.exists()
    assert json_path.exists()
    
    # Verify content
    loaded_csv = pd.read_csv(csv_path)
    assert len(loaded_csv) == len(sample_coefficients)

    with open(json_path, 'r') as f:
        loaded_json = json.load(f)
    assert loaded_json == sample_diagnostics
