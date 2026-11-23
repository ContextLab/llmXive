"""
Integration test for the basic pipeline flow (Ingest -> Validate -> Filter).
"""
import pytest
import pandas as pd
import numpy as np
import json
import os
import sys
from pathlib import Path
import tempfile

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.ingest import load_required_variables, validate_variables, detect_outliers_iqr, filter_outliers, save_outlier_report, save_filtered_data

@pytest.fixture
def config_path():
    return Path(__file__).parent.parent.parent / "data" / "config" / "required_variables.yaml"

def test_full_ingest_flow(config_path):
    """
    Test the flow: Load Config -> Create Data -> Validate -> Detect Outliers -> Filter -> Save Artifacts.
    """
    variables = load_required_variables(str(config_path))
    
    # Create a dataset with some outliers
    np.random.seed(42)
    data_dict = {}
    # Predictors
    for col in variables["predictors"]:
        data_dict[col] = np.random.normal(0, 1, 100).tolist()
    # Outcomes
    for col in variables["outcomes"]:
        data_dict[col] = np.random.normal(0, 1, 100).tolist()
    data_dict["subject_id"] = list(range(100))
    
    # Inject an outlier in the first outcome
    if variables["outcomes"]:
        first_outcome = variables["outcomes"][0]
        data_dict[first_outcome][50] = 100.0 # Extreme value
    
    df = pd.DataFrame(data_dict)
    
    # 1. Validate
    validation_result = validate_variables(df, variables)
    assert validation_result["valid"], "Data should be valid structurally"
    
    # 2. Detect Outliers (using first outcome for simplicity)
    if variables["outcomes"]:
        first_outcome = variables["outcomes"][0]
        outliers = detect_outliers_iqr(df, first_outcome)
        
        # 3. Filter
        filtered_df, filter_report = filter_outliers(df, first_outcome)
        
        # 4. Verify counts
        assert len(filtered_df) < len(df), "Filtered data should be smaller"
        assert filter_report["exclusion_count"] == len(outliers), "Exclusion count mismatch"
        
        # 5. Save artifacts to temp dir to verify write capability
        with tempfile.TemporaryDirectory() as tmpdir:
            outlier_path = os.path.join(tmpdir, "outlier_report.json")
            filtered_path = os.path.join(tmpdir, "filtered_data.parquet")
            
            save_outlier_report(outliers, outlier_path)
            save_filtered_data(filtered_df, filtered_path)
            
            assert os.path.exists(outlier_path), "Outlier report not written"
            assert os.path.exists(filtered_path), "Filtered data not written"
            
            with open(outlier_path, 'r') as f:
                report = json.load(f)
                assert "exclusion_count" in report
    
    else:
        pytest.skip("No outcomes defined in config to test outlier flow")
