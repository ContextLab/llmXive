"""Unit tests for the local Phi-2 runner (T012)."""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# We cannot import the actual runner for full execution in unit tests
# because it requires the model file. Instead, we test the logic flow
# and verify that the script structure is correct.

def test_runner_local_imports():
    """Verify that runner_local.py can be imported without errors."""
    try:
        # Import the module to check for syntax errors and missing imports
        from code.generation import runner_local
        assert hasattr(runner_local, 'HardwareError')
        assert hasattr(runner_local, 'check_hardware_requirements')
        assert hasattr(runner_local, 'load_model')
        assert hasattr(runner_local, 'generate_sample')
        assert hasattr(runner_local, 'run_generation_pipeline')
        assert hasattr(runner_local, 'main')
    except ImportError as e:
        pytest.fail(f"Failed to import runner_local: {e}")

def test_runner_local_cli_parsing():
    """Test that the CLI argument parser is set up correctly."""
    from code.generation.runner_local import main
    import sys

    # Mock sys.argv to simulate --test flag
    with patch('sys.argv', ['runner_local.py', '--test']):
        with patch('code.generation.runner_local.run_generation_pipeline') as mock_run:
            mock_run.return_value = [{"id": "test"}]
            with patch('sys.exit'):
                # This should not raise an error
                try:
                    main()
                except SystemExit:
                    pass  # Expected after successful run
                assert mock_run.called

def test_hardware_error_exception():
    """Verify that HardwareError is raised when model is missing."""
    from code.generation.runner_local import HardwareError, load_model

    with pytest.raises(HardwareError):
        # This should fail because the model file doesn't exist
        load_model("/nonexistent/path/model.gguf")

def test_output_path_creation():
    """Verify that the output directory is created if it doesn't exist."""
    from code.generation.runner_local import run_generation_pipeline
    import tempfile
    import os

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "subdir", "output.json")
        
        # Mock the model and generation to avoid actual inference
        with patch('code.generation.runner_local.load_model') as mock_load:
            mock_load.return_value = MagicMock()
            with patch('code.generation.runner_local.generate_sample') as mock_gen:
                mock_gen.return_value = {"id": "test", "text": "hello"}
                
                # Run the pipeline
                result = run_generation_pipeline(
                    num_samples=1,
                    output_path=output_path,
                    model_path="/fake/model.gguf",
                    test_mode=True
                )
                
                # Verify the output file was created
                assert os.path.exists(output_path)
                
                # Verify the content is valid JSON
                with open(output_path, 'r') as f:
                    data = json.load(f)
                    assert isinstance(data, list)
                    assert len(data) == 1
