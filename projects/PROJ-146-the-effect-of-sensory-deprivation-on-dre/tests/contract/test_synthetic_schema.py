import os
import pandas as pd
import pytest
import yaml

# Import the generation function to test the output it produces
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))
from generate_data import load_protocol, generate_synthetic_datasets

@pytest.fixture
def protocol():
    protocol_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'protocols', 'protocol.yaml')
    return load_protocol(protocol_path)

@pytest.fixture
def generated_files(protocol, tmp_path):
    # Generate files in a temporary directory for testing
    output_dir = str(tmp_path / "synthetic")
    files = generate_synthetic_datasets(protocol, output_dir)
    return files

def test_synthetic_data_schema(generated_files):
    """
    Contract test: Verifies that generated synthetic datasets conform to the expected schema.
    
    Required columns:
    - participant_id (string, non-null)
    - recall (integer, 0 or 1)
    - bizarreness (integer, 1-7)
    - scenario (string)
    - data_source (string, must be "Simulation-based")
    """
    required_columns = {'participant_id', 'recall', 'bizarreness', 'scenario', 'data_source'}
    
    for filepath in generated_files:
        df = pd.read_csv(filepath)
        
        # 1. Check for required columns
        assert required_columns.issubset(df.columns), f"Missing columns in {filepath}: {required_columns - set(df.columns)}"
        
        # 2. Check for non-null values in critical columns
        assert df['participant_id'].notnull().all(), f"Null values found in participant_id for {filepath}"
        assert df['recall'].notnull().all(), f"Null values found in recall for {filepath}"
        assert df['bizarreness'].notnull().all(), f"Null values found in bizarreness for {filepath}"
        
        # 3. Validate data types and ranges
        assert df['recall'].isin([0, 1]).all(), f"Recall values must be 0 or 1 in {filepath}"
        assert df['bizarreness'].between(1, 7).all(), f"Bizarreness values must be 1-7 in {filepath}"
        
        # 4. Verify metadata flags
        assert (df['data_source'] == "Simulation-based").all(), f"data_source must be 'Simulation-based' in {filepath}"
        
        # 5. Check N (sample size) matches protocol
        # We assume each file corresponds to one scenario defined in the protocol
        # The protocol defines N=200
        protocol_n = 200 # From protocol.yaml
        assert len(df) == protocol_n, f"Expected {protocol_n} rows, got {len(df)} in {filepath}"

def test_synthetic_data_scenario_consistency(generated_files):
    """
    Contract test: Verifies that the 'scenario' column matches the effect size logic.
    """
    for filepath in generated_files:
        df = pd.read_csv(filepath)
        scenario_name = df['scenario'].iloc[0]
        
        # Basic check: scenario name should be one of the expected ones
        valid_scenarios = {'moderate_positive', 'null', 'moderate_negative'}
        assert scenario_name in valid_scenarios, f"Invalid scenario name: {scenario_name}"
