import os
import json
import pandas as pd
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

# We need to import the module to check its content or behavior
# Since we can't easily inspect source code at runtime without reading the file,
# we will test the behavior: does it try to set regression family?
# The task requires that it DOES NOT modify regression family.
# We verify that outcome_type.json is written, but no family is set.

def test_no_regression_family_logic_in_preprocess():
    """
    Verify that preprocess.py does not contain logic to set regression family.
    This is a static analysis check by reading the source file.
    """
    # Read the source file
    source_path = "code/preprocess.py"
    with open(source_path, 'r') as f:
        content = f.read()

    # Check for forbidden patterns
    forbidden_patterns = [
        "set_regression_family",
        "family_type = ",
        "family = 'binomial'",
        "family = 'gaussian'",
        "regression_family"
    ]

    found_forbidden = []
    for pattern in forbidden_patterns:
        if pattern in content:
            found_forbidden.append(pattern)

    assert len(found_forbidden) == 0, (
        f"Found forbidden logic in preprocess.py that sets regression family: {found_forbidden}. "
        "Regression family selection must be handled in analysis.py (T021b)."
    )

def test_outcome_type_detection_exists():
    """
    Verify that preprocess.py still detects outcome type and writes it to outcome_type.json.
    """
    source_path = "code/preprocess.py"
    with open(source_path, 'r') as f:
        content = f.read()

    # Check for required patterns
    required_patterns = [
        "detect_outcome_type",
        "outcome_type.json",
        '"type":'
    ]

    missing_patterns = []
    for pattern in required_patterns:
        if pattern not in content:
            missing_patterns.append(pattern)

    assert len(missing_patterns) == 0, (
        f"Missing required logic in preprocess.py for outcome type detection: {missing_patterns}"
    )

def test_preprocess_pipeline_writes_outcome_type():
    """
    Test that the pipeline actually writes the outcome_type.json file.
    """
    import tempfile
    import shutil
    from code import preprocess

    # Create a temporary directory for test data
    temp_dir = tempfile.mkdtemp()
    try:
        # Create a mock raw data file
        raw_data_path = os.path.join(temp_dir, "raw_data.csv")
        df_mock = pd.DataFrame({
            'participant_id': [1, 2, 3, 4],
            'status_level': ['High', 'Low', 'High', 'Low'],
            'observed_behavior': ['Risky', 'Conservative', 'Risky', 'Conservative'],
            'risk_taking_score': [0.8, 0.2, 0.9, 0.1]
        })
        df_mock.to_csv(raw_data_path, index=False)

        output_path = os.path.join(temp_dir, "cleaned_data.csv")
        structure_output_path = os.path.join(temp_dir, "structure_config.json")
        outcome_type_path = "data/processed/outcome_type.json" # This is hardcoded in the function

        # Ensure data/processed directory exists for the test
        os.makedirs("data/processed", exist_ok=True)

        # Run the pipeline
        result_df = preprocess.preprocess_pipeline(
            raw_data_path, 
            output_path, 
            config={'seed': 42, 'outcome_column': 'risk_taking_score'}
        )

        # Check that outcome_type.json was created and contains the correct type
        assert os.path.exists(outcome_type_path), "outcome_type.json was not created"
        
        with open(outcome_type_path, 'r') as f:
            outcome_data = json.load(f)
        
        assert 'type' in outcome_data, "outcome_type.json missing 'type' key"
        assert outcome_data['type'] == 'continuous', f"Expected 'continuous', got {outcome_data['type']}"

    finally:
        # Cleanup
        shutil.rmtree(temp_dir)
        if os.path.exists("data/processed/outcome_type.json"):
            os.remove("data/processed/outcome_type.json")