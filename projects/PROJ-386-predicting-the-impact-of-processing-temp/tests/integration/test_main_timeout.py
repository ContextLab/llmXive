"""
Integration test for main.py timeout enforcement and runner verification.
"""
import os
import sys
import signal
import time
import subprocess
import pytest
from pathlib import Path

# Ensure code directory is in path
code_dir = Path(__file__).parent.parent.parent / 'code'
sys.path.insert(0, str(code_dir))

def test_runner_verification():
    """Test that runner verification completes without error."""
    from main import verify_runner_environment
    
    # This should complete without raising an exception
    result = verify_runner_environment()
    assert result is True

def test_timeout_handler():
    """Test that the timeout handler sets the flag correctly."""
    from main import timeout_handler, timeout_occurred
    
    # Reset the global flag
    import main
    main.timeout_occurred = False
    
    # Call the handler
    timeout_handler(signal.SIGALRM, None)
    
    assert main.timeout_occurred is True

def test_pipeline_timeout_simulation():
    """
    Test that a simulated long-running process triggers timeout.
    This test mocks the run_pipeline function to simulate a long delay.
    """
    import main
    from unittest.mock import patch, MagicMock
    
    # Mock the run_pipeline function to simulate a long-running task
    def mock_run_pipeline(args):
        time.sleep(10)  # Simulate a long-running task
    
    # Set a short timeout for testing
    args = MagicMock()
    args.timeout = 1
    args.urls = ['http://example.com']
    args.output = 'test_output.csv'
    args.stats = False
    
    with patch('main.run_pipeline', side_effect=mock_run_pipeline):
        with pytest.raises(TimeoutError):
            main.run_pipeline(args)

def test_main_execution_with_real_timeout():
    """
    Test that running main.py with a very short timeout fails as expected.
    This is a real integration test that actually runs the script.
    """
    # Create a test script that sleeps
    test_script = """
    import time
    import sys
    sys.path.insert(0, 'code')
    from main import run_pipeline
    import argparse
    
    args = argparse.Namespace(
        urls=['http://example.com'],
        output='test.csv',
        stats=False,
        sample_size=None,
        timeout=1
    )
    
    # Mock the ingestion to sleep
    import data.ingestion
    original_run = data.ingestion.run_pipeline
    def mock_run(*args, **kwargs):
        time.sleep(10)
    data.ingestion.run_pipeline = mock_run
    
    try:
        run_pipeline(args)
        print("ERROR: Should have timed out")
        sys.exit(1)
    except TimeoutError:
        print("SUCCESS: Timeout triggered correctly")
        sys.exit(0)
    finally:
        data.ingestion.run_pipeline = original_run
    """
    
    # Write the test script
    test_file = Path('test_timeout_temp.py')
    test_file.write_text(test_script)
    
    try:
        # Run the test script with a timeout
        result = subprocess.run(
            [sys.executable, str(test_file)],
            timeout=5,  # Give it 5 seconds max
            capture_output=True,
            text=True
        )
        
        # Check that it timed out correctly
        assert "SUCCESS" in result.stdout
        assert result.returncode == 0
    except subprocess.TimeoutExpired:
        pytest.fail("Test script itself timed out, indicating an issue with timeout handling")
    finally:
        # Clean up
        if test_file.exists():
            test_file.unlink()

def test_main_execution_with_sample():
    """
    Test that main.py can be called with sample-size argument without crashing.
    This test mocks all the heavy pipeline steps to avoid actual data processing.
    """
    from unittest.mock import patch, MagicMock
    import main
    
    # Mock all pipeline steps
    with patch('main.verify_runner_environment'), \
         patch('data.ingestion.run_pipeline'), \
         patch('data.preprocessing.run_preprocessing_pipeline'), \
         patch('modeling.baseline.run_baseline_pipeline'), \
         patch('modeling.rf_model.run_rf_pipeline'), \
         patch('analysis.reporting.run_reporting_pipeline'):
        
        args = MagicMock()
        args.urls = ['http://example.com']
        args.output = 'test.csv'
        args.stats = False
        args.sample_size = 100
        args.timeout = 3600
        
        # This should complete without error
        main.run_pipeline(args)

if __name__ == '__main__':
    pytest.main([__file__, '-v'])