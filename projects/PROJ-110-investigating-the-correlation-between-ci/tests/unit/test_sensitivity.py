import pytest
import pandas as pd
import numpy as np
import json
from pathlib import Path
import tempfile
import os

# Import the function to test
from code.main import apply_atp_iii_criteria, run_sensitivity_analysis

@pytest.fixture
def sample_df():
    """Create a sample dataframe for testing."""
    data = {
        "sample_id": ["S1", "S2", "S3", "S4", "S5"],
        "bmi": [30.0, 29.9, 31.0, 25.0, 35.0],
        "glucose": [100.0, 99.0, 110.0, 90.0, 120.0],
        "bp_sys": [130.0, 129.0, 140.0, 120.0, 150.0],
        "bp_dia": [85.0, 84.0, 90.0, 80.0, 95.0],
        "tg": [150.0, 149.0, 160.0, 100.0, 200.0],
        "hdl": [35.0, 45.0, 30.0, 55.0, 35.0],
        "sex": ["M", "M", "M", "M", "M"]
    }
    # S1: BMI(>=30), Glu(>=100), BP(>=130/85), TG(>=150), HDL(<40) -> 5 conditions -> MetS
    # S2: BMI(29.9 - No), Glu(99 - No), BP(129/84 - No), TG(149 - No), HDL(45 - No) -> 0 -> Control
    # S3: BMI(31 - Yes), Glu(110 - Yes), BP(140/90 - Yes), TG(160 - Yes), HDL(30 - Yes) -> 5 -> MetS
    # S4: All No -> Control
    # S5: All Yes -> MetS
    return pd.DataFrame(data)

def test_atp_iii_classifies_metabolic_syndrome(sample_df):
    """Test that samples meeting >= 3 criteria are classified as MetS."""
    labels = apply_atp_iii_criteria(sample_df, {
        "bmi": {"op": ">=", "val": 30.0},
        "glucose": {"op": ">=", "val": 100.0},
        "bp_sys": {"op": ">=", "val": 130.0},
        "bp_dia": {"op": ">=", "val": 85.0},
        "tg": {"op": ">=", "val": 150.0},
        "hdl_men": {"op": "<", "val": 40.0},
        "hdl_women": {"op": "<", "val": 50.0},
    })
    
    # S1, S3, S5 should be MetS (True)
    # S2, S4 should be Control (False)
    assert labels.iloc[0] == True
    assert labels.iloc[1] == False
    assert labels.iloc[2] == True
    assert labels.iloc[3] == False
    assert labels.iloc[4] == True

def test_boundary_conditions(sample_df):
    """Test strict thresholds (e.g., BMI=29.9 vs 30.0)."""
    # S2 has BMI=29.9, Glucose=99, etc. All just below threshold.
    labels = apply_atp_iii_criteria(sample_df, {
        "bmi": {"op": ">=", "val": 30.0},
        "glucose": {"op": ">=", "val": 100.0},
        "bp_sys": {"op": ">=", "val": 130.0},
        "bp_dia": {"op": ">=", "val": 85.0},
        "tg": {"op": ">=", "val": 150.0},
        "hdl_men": {"op": "<", "val": 40.0},
        "hdl_women": {"op": "<", "val": 50.0},
    })
    
    # S2 should be False because 29.9 < 30.0
    assert labels.iloc[1] == False
    
    # S1 should be True because 30.0 >= 30.0
    assert labels.iloc[0] == True

def test_run_sensitivity_analysis_writes_files(sample_df):
    """Test that run_sensitivity_analysis writes the expected output files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Prepare input
        input_file = tmpdir / "baseline_labels.csv"
        # Add metabolic_status column to match expected input format
        df_with_status = sample_df.copy()
        df_with_status["metabolic_status"] = apply_atp_iii_criteria(
            sample_df, 
            {
                "bmi": {"op": ">=", "val": 30.0},
                "glucose": {"op": ">=", "val": 100.0},
                "bp_sys": {"op": ">=", "val": 130.0},
                "bp_dia": {"op": ">=", "val": 85.0},
                "tg": {"op": ">=", "val": 150.0},
                "hdl_men": {"op": "<", "val": 40.0},
                "hdl_women": {"op": "<", "val": 50.0},
            }
        ).apply(lambda x: "MetS" if x else "Control")
        
        df_with_status.to_csv(input_file, index=False)
        
        output_csv = tmpdir / "sensitivity_analysis.csv"
        output_json = tmpdir / "sensitivity_metric.json"
        
        # Run analysis
        run_sensitivity_analysis(input_file, output_csv, output_json)
        
        # Verify files exist
        assert output_csv.exists(), "sensitivity_analysis.csv not created"
        assert output_json.exists(), "sensitivity_metric.json not created"
        
        # Verify CSV content
        df_out = pd.read_csv(output_csv)
        assert "sample_id" in df_out.columns
        assert "baseline_label" in df_out.columns
        assert "varied_label" in df_out.columns
        assert "reclassified" in df_out.columns
        assert "scenario" in df_out.columns
        
        # Verify JSON content
        with open(output_json, "r") as f:
            metric = json.load(f)
        
        assert "value" in metric
        assert "metric_name" in metric
        assert metric["metric_name"] == "percent_reclassified"
        assert isinstance(metric["value"], float)