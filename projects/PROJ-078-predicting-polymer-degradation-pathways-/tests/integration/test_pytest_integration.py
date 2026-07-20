"""
Integration tests for the pytest framework setup.

These tests verify that the testing infrastructure works end-to-end,
including interaction with the temporary file system and mock objects.
"""
import os
import tempfile
from pathlib import Path
import pytest

@pytest.mark.integration
def test_full_workflow_with_temp_dir(temp_project_dir):
    """
    Simulate a full workflow where a script would write to the temp directories.
    """
    # Create a dummy file in raw data
    raw_file = temp_project_dir / "data" / "raw" / "test_data.csv"
    raw_file.write_text("id,smiles,label\n1,CCO,hydrolysis\n")
    
    assert raw_file.exists()
    assert raw_file.read_text() == "id,smiles,label\n1,CCO,hydrolysis\n"
    
    # Process the file
    processed_dir = temp_project_dir / "data" / "processed"
    processed_file = processed_dir / "test_data_processed.csv"
    processed_file.write_text("id,smiles,label,graph_id\n1,CCO,hydrolysis,graph_001\n")
    
    assert processed_file.exists()

@pytest.mark.integration
def test_mock_rdkit_usage(mock_rdkit_mol):
    """
    Verify that the mock RDKit molecule behaves as expected in a test scenario.
    """
    assert mock_rdkit_mol.GetNumAtoms() == 5
    assert mock_rdkit_mol.GetNumBonds() == 4
    
    # Test method chaining
    atom = mock_rdkit_mol.GetAtomWithIdx(0)
    assert atom.GetSymbol.return_value == "C"

@pytest.mark.integration
def test_config_loading_via_env(temp_project_dir):
    """
    Test that configuration loading (simulated) respects the environment setup.
    """
    # This test ensures that the environment variables set by conftest
    # are accessible to the code being tested.
    raw_path = os.environ.get("DATA_RAW_DIR")
    assert raw_path is not None
    assert "data" in raw_path
    assert "raw" in raw_path

@pytest.mark.integration
def test_logging_configuration(setup_test_environment):
    """
    Verify that logging is configured correctly for the test run.
    """
    import logging
    logger = logging.getLogger("test_logger")
    # Check that the logger has handlers (configured by conftest)
    # Note: The root logger is configured, so child loggers inherit.
    assert len(logging.getLogger().handlers) > 0
