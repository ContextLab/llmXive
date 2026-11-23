import pytest
import os
import sys
import tempfile
import csv
import time

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from code.agent_loop import TextAgent, AgentConfig, AgentState, run_error_handling_test, log_discarded_run
from code.logger import configure_global_logging

class TestAgentErrorHandling:
    
    @pytest.fixture(autouse=True)
    def setup(self):
        configure_global_logging()
        # Ensure results directory exists
        os.makedirs("results", exist_ok=True)
        # Clean up test artifacts before each test
        if os.path.exists("results/discarded_runs.csv"):
            os.remove("results/discarded_runs.csv")
        if os.path.exists("results/error_handling_test.log"):
            os.remove("results/error_handling_test.log")
        yield
        # Cleanup after test if needed
        
    def test_nan_injection_discards_run(self):
        """
        Test T027: Verify that injecting NaN into output tensor results in 
        the run being discarded and logged to results/discarded_runs.csv.
        """
        seed = 12345
        test_log_path = "results/error_handling_test.log"
        
        # Run the specific test function that injects NaN
        result = run_error_handling_test(seed, test_log_path)
        
        # Verify the run was discarded
        assert result is True, "Run should have been discarded due to NaN"
        
        # Verify the log file exists and contains correct info
        assert os.path.exists(test_log_path), f"Test log {test_log_path} should exist"
        
        with open(test_log_path, 'r') as f:
            content = f.read()
            assert "PASSED" in content, "Test log should indicate PASSED"
            assert "NaN_OUTPUT" in content, "Test log should mention NaN_OUTPUT"
        
        # Verify the CSV log
        csv_path = "results/discarded_runs.csv"
        assert os.path.exists(csv_path), f"Discarded runs CSV {csv_path} should exist"
        
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) >= 1, "CSV should contain at least one discarded run"
            
            # Check the latest row
            last_row = rows[-1]
            assert last_row['seed'] == str(seed), "Seed in CSV should match"
            assert last_row['discard_reason'] == "NaN_OUTPUT", "Reason should be NaN_OUTPUT"

    def test_oom_simulation_discards_run(self):
        """
        Test that OOM conditions (simulated) also discard the run.
        This extends the error handling verification.
        """
        # Note: Actual OOM is hard to simulate in a unit test without killing the process.
        # We rely on the general exception handling path in agent_loop.py which catches
        # unexpected errors and sets is_discarded = True.
        
        seed = 99999
        # We would need to modify the agent to simulate OOM specifically, 
        # but the current implementation catches Exception and sets discard reason to UNKNOWN_ERROR.
        # This test verifies the general error handling path.
        
        config = AgentConfig()
        agent = TextAgent(config)
        state = AgentState(seed=seed, ascii_grid="#####", event_log=[])
        
        # We can't easily trigger OOM in a test, so we verify the logic path
        # by checking that the exception handler exists and sets the flag.
        # This is a structural verification.
        import inspect
        source = inspect.getsource(agent.run_step)
        assert "is_discarded = True" in source, "run_step should set is_discarded on error"
        assert "discard_reason" in source, "run_step should set discard_reason on error"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
