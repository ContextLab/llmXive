"""
Tests for T040: Enforce "Fail Loudly" on Data Fetch.
Verifies that ingestion does not fallback to synthetic data.
"""
import pytest
import os
from unittest.mock import patch, MagicMock
from ingestion import load_hcp_fmri_data, validate_schema
import pandas as pd

def test_load_hcp_fmri_data_fails_on_missing_credentials():
    """Test that load_hcp_fmri_data raises FileNotFoundError if credentials are missing."""
    # Ensure credentials are not set
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(FileNotFoundError, match="HCP credentials missing"):
            load_hcp_fmri_data(streaming=False)

def test_load_hcp_fmri_data_fails_on_connection_error():
    """Test that load_hcp_fmri_data raises ConnectionError if dataset fetch fails."""
    # Mock load_dataset to raise a connection error
    with patch('ingestion.load_dataset') as mock_load:
        mock_load.side_effect = ConnectionError("Network error")
        with pytest.raises(ConnectionError, match="Failed to fetch HCP dataset"):
            load_hcp_fmri_data(streaming=False)

def test_load_hcp_fmri_data_fails_on_empty_stream():
    """Test that load_hcp_fmri_data raises RuntimeError if stream is empty."""
    # Mock dataset to return an empty iterator
    mock_dataset = MagicMock()
    mock_dataset.__iter__ = MagicMock(return_value=iter([]))
    
    with patch('ingestion.load_dataset', return_value=mock_dataset):
        with pytest.raises(RuntimeError, match="Dataset stream is empty"):
            load_hcp_fmri_data(streaming=True)

def test_validate_schema_fails_on_missing_columns():
    """Test that validate_schema raises ValueError if required columns are missing."""
    schema_path = "contracts/dataset.schema.yaml"
    # Create a mock schema file if it doesn't exist
    os.makedirs("contracts", exist_ok=True)
    with open(schema_path, 'w') as f:
        f.write("required_columns: ['Subject_ID', 'global_signal']\n")
    
    df = pd.DataFrame({"Subject_ID": [1]}) # Missing 'global_signal'
    
    with pytest.raises(ValueError, match="Schema Validation Failed"):
        validate_schema(df, schema_path)

def test_no_synthetic_fallback_in_ingestion():
    """
    Verify that no synthetic data generation code is reachable during ingestion.
    This is a static check / logic verification.
    """
    # We check that the function does not call any known synthetic generators.
    # In a real test, we might inspect the source code or mock the load_dataset
    # to ensure no fallback path is taken.
    import inspect
    source = inspect.getsource(load_hcp_fmri_data)
    
    # Assert that common synthetic generation patterns are not present
    assert "generate_synthetic" not in source
    assert "mock_" not in source
    assert "np.random" not in source or "load_hcp_fmri_data" not in source.split("np.random")[0] # Rough check
    
    # The logic should be: try load, if fail -> raise. No else branch for synthetic.
    # This test ensures the code structure adheres to T040.