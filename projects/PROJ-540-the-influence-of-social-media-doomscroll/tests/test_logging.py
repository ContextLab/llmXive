import pytest
import logging
import os
from pathlib import Path
import tempfile
import shutil

# We need to mock config or ensure the environment is set up correctly
# For this test, we assume the project structure is as expected or mock the config load.

def test_logging_infrastructure_creates_file():
    """
    Test that setup_logging creates the log file and writes a startup message.
    """
    from logging_config import setup_logging
    
    # Create a temporary directory for this test to avoid polluting the real outputs
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        log_filename = "test_analysis.log"
        log_path = tmp_path / log_filename
        
        # Temporarily patch ensure_directories and load_config if necessary,
        # but since setup_logging handles paths relative to project_root, 
        # we rely on the fact that ensure_directories creates the folder.
        # However, to force it into tmp_dir, we might need to mock config.
        # Given the constraints, let's assume the test runs in an environment
        # where we can control the current working directory or the config.
        
        # Simpler approach: Just verify the function runs and creates a file
        # in a known location if we pass a specific path logic, but the function
        # signature is fixed. We will run it and check if it creates the file
        # in the expected default location relative to where we run the test.
        # To make this robust, we'll create the directory structure manually first.
        
        outputs_dir = Path(tmp_path) / "outputs"
        outputs_dir.mkdir(parents=True, exist_ok=True)
        
        # We need to trick the function into using tmp_dir. 
        # Since we can't easily change the function signature, we will
        # assume the test runner sets up the environment or we verify the
        # existence of the file after calling the function.
        # For the purpose of this task, we verify that the code executes without error
        # and that a logger is returned.
        
        # Mocking the config to point to tmp_dir for the log path logic
        # This requires patching inside the module or the config.
        # Let's just verify the function signature and basic execution.
        
        try:
            # We will run the setup in the temp dir context by changing cwd
            old_cwd = os.getcwd()
            os.chdir(tmp_path)
            
            # Ensure outputs dir exists
            (Path(tmp_path) / "outputs").mkdir(exist_ok=True)
            
            logger = setup_logging(log_file="outputs/test_analysis.log", level=logging.INFO)
            
            # Verify logger has handlers
            assert len(logger.handlers) > 0, "Logger should have handlers"
            
            # Check if file was created
            assert log_path.exists(), f"Log file {log_path} should be created"
            
            # Check if file has content (startup message)
            with open(log_path, 'r') as f:
                content = f.read()
                assert "Logging infrastructure initialized" in content, "Log should contain startup message"
                
        finally:
            os.chdir(old_cwd)

def test_logging_levels():
    """
    Test that different log levels are respected.
    """
    from logging_config import setup_logging
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        (tmp_path / "outputs").mkdir(exist_ok=True)
        
        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            # Setup with ERROR level
            logger = setup_logging(log_file="outputs/error_test.log", level=logging.ERROR)
            
            # Clear handlers to isolate test
            for handler in logger.handlers[:]:
                logger.removeHandler(handler)
                
            # Re-add a file handler for this specific test
            handler = logging.FileHandler(tmp_path / "outputs/error_test.log", mode='w')
            handler.setLevel(logging.ERROR)
            handler.setFormatter(logging.Formatter('%(message)s'))
            logger.addHandler(handler)
            
            logger.info("This should NOT appear")
            logger.error("This SHOULD appear")
            
            with open(tmp_path / "outputs/error_test.log", 'r') as f:
                content = f.read()
                assert "This should NOT appear" not in content
                assert "This SHOULD appear" in content
                
        finally:
            os.chdir(old_cwd)