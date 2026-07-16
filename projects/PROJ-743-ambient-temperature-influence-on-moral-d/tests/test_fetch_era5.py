"""
Tests for code/fetch_era5.py

Note: These tests check the logic and structure of the script, not the actual
API call (which requires credentials and network).
"""
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path to import code module
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_imports():
    """Test that the script can be imported without errors."""
    try:
        # We cannot run the main block directly in a test without mocking the network
        # But we can ensure the module structure is valid
        import importlib.util
        spec = importlib.util.spec_from_file_location("fetch_era5", "code/fetch_era5.py")
        module = importlib.util.module_from_spec(spec)
        # This will fail if there are syntax errors or missing imports (like cdsapi)
        # We expect cdsapi to be installed in the environment
        spec.loader.exec_module(module)
        assert hasattr(module, 'fetch_era5_sample')
        assert hasattr(module, 'logger')
    except ImportError as e:
        # If cdsapi is missing, this is an environment issue, not a code logic issue
        # But for the test to pass, we assume the environment is set up correctly
        if "cdsapi" in str(e):
            pytest.skip("cdsapi not installed in test environment")
        raise

def test_file_paths_exist():
    """Test that the script defines valid file paths."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("fetch_era5", "code/fetch_era5.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    # Check that output directory is defined
    assert hasattr(module, 'DATA_RAW_DIR')
    assert hasattr(module, 'RESULTS_LOGS_DIR')
    assert hasattr(module, 'OUTPUT_FILE')
    assert hasattr(module, 'LOG_FILE')

def test_fetch_logic_with_mock():
    """Test the fetch logic by mocking the CDS client."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("fetch_era5", "code/fetch_era5.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        # Patch the paths to use the temp directory
        temp_output = Path(tmpdir) / "test_output.nc"
        temp_log = Path(tmpdir) / "test_log.txt"
        
        module.DATA_RAW_DIR = Path(tmpdir)
        module.RESULTS_LOGS_DIR = Path(tmpdir)
        module.OUTPUT_FILE = temp_output
        module.LOG_FILE = temp_log

        # Mock the CDS client
        with patch('cdsapi.Client') as mock_client_class:
            mock_client_instance = MagicMock()
            mock_client_class.return_value = mock_client_instance
            
            # Mock the retrieve method to create a dummy file
            def mock_retrieve(*args, **kwargs):
                Path(kwargs['target']).write_text("dummy content")
            
            mock_client_instance.retrieve = mock_retrieve

            # Run the function
            success = module.fetch_era5_sample()
            
            # Assert that the client was called
            mock_client_class.assert_called_once()
            mock_client_instance.retrieve.assert_called_once()
            
            # Assert that the file was created
            assert temp_output.exists()
            assert temp_output.stat().st_size > 0
            
            # Assert success return
            assert success is True
