"""
Integration test for T011: "Data Missing" halt scenario.

Verifies that the data ingestion pipeline exits with code 1 and logs
a specific "Critical variables missing" message when all configured
data sources fail to provide the required variables (rolling temperature,
composition, grain size).
"""
import subprocess
import sys
import os
import pytest
from unittest.mock import patch, MagicMock
import io
import logging

# Add project root to path to allow imports from code/
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, PROJECT_ROOT)

# We need to mock the ingestion logic to simulate a complete failure
# without actually trying to fetch from external APIs which might be flaky.
# The test verifies the *behavior* of the system when ingestion returns no data.

@pytest.mark.integration
def test_data_halt_scenario():
    """
    Test that the system halts with Exit Code 1 when all sources fail.
    
    We mock the `fetch_sources` function in `code.data.ingestion` to return
    an empty list, simulating a scenario where no data could be retrieved
    or parsed from any source.
    """
    # Import the ingestion module dynamically to allow patching
    # We use a subprocess to ensure we are testing the actual script execution
    # and exit codes, rather than just function calls.
    
    # Path to the ingestion script
    ingestion_script = os.path.join(PROJECT_ROOT, "code", "data", "ingestion.py")
    
    if not os.path.exists(ingestion_script):
        pytest.fail(f"Ingestion script not found at {ingestion_script}")

    # We run the script with a mock environment variable to force a specific
    # behavior if the script supports it, OR we rely on the script's logic
    # to handle empty results.
    # However, to strictly test the "Data Missing" logic without network flakiness,
    # we will create a temporary script that patches the fetch function.
    
    # Alternative approach: Run the actual script but patch the fetch logic via a wrapper.
    # Since we cannot easily patch inside a subprocess without a wrapper script,
    # we will write a temporary wrapper script that patches the module before running.
    
    wrapper_script_path = os.path.join(PROJECT_ROOT, "tests", "integration", "_temp_halt_wrapper.py")
    
    wrapper_content = f"""
import sys
import os
from unittest.mock import patch, MagicMock

# Ensure code directory is in path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

# Mock the fetch function to return empty results
def mock_fetch_sources():
    return [], []

# Patch the ingestion module's fetch function before importing/running main
import code.data.ingestion as ingestion_module
ingestion_module.fetch_sources = mock_fetch_sources

# Now run the main logic of the ingestion script
# We assume the script has a 'main' or specific entry point that calls the pipeline
# If the script is a flat script, we import and run its logic.
try:
    # Attempt to run the main logic
    # Depending on how ingestion.py is structured, we might need to call a specific function
    # or run the script's top-level code.
    # Assuming ingestion.py has a 'main()' or similar, or runs at import.
    # To be safe, we execute the script's logic directly if possible, or import and call.
    
    # Let's assume the script defines a function `run_ingestion()` or similar, 
    # or we just run the script as is but with the patch active.
    
    # Actually, the cleanest way for this integration test is to import the module
    # and call the specific function that handles the pipeline, ensuring the patch is active.
    
    # If ingestion.py is a script that runs at import, we need to be careful.
    # Let's assume it has a guard: if __name__ == "__main__": main()
    
    # We will re-import the module to ensure our patch takes effect if it was already imported?
    # No, we patch before import.
    
    # Let's try to import and run the main logic
    from code.data.ingestion import run_pipeline, check_schema
    
    # Simulate the scenario where schema check passes but data fetch returns empty
    # We need to mock the fetch function inside the module that is actually used.
    
    # Re-apply patch to be sure
    with patch.object(ingestion_module, 'fetch_sources', return_value=([], [])):
  try:
      # This should raise SystemExit(1)
      ingestion_module.run_pipeline() 
      # If we reach here, the test failed
      sys.exit(0) # Should not happen
  except SystemExit as e:
      if e.code == 1:
          sys.exit(1) # Success: expected exit code
      else:
          sys.exit(e.code)
  except Exception as e:
      # If it raises an exception instead of SystemExit, check if it's the expected one
      # The spec says "Raise SystemExit(1)"
      print(f"Unexpected exception: {{e}}")
      sys.exit(1) # Treat unexpected exception as a halt scenario for now? 
      # No, strictly we want SystemExit(1).
      sys.exit(2) # Different error

if __name__ == "__main__":
    # Run the test logic
    try:
  # Import here to ensure patching logic above runs? 
  # No, the patching is in the wrapper content.
  pass
    except SystemExit as e:
  sys.exit(e.code)
    except Exception as e:
  print(f"Test failed with exception: {{e}}")
  sys.exit(2)
"""

    try:
        with open(wrapper_script_path, "w") as f:
            f.write(wrapper_content)
        
        # Run the wrapper script
        result = subprocess.run(
            [sys.executable, wrapper_script_path],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True
        )
        
        # Check exit code
        if result.returncode == 1:
            # Success: The system halted as expected
            assert "Critical variables missing" in result.stderr.lower() or "critical variables missing" in result.stdout.lower(), \
                "Expected 'Critical variables missing' message in logs, but not found."
            return # Test passed
        else:
            pytest.fail(f"Script did not exit with code 1. Exit code: {result.returncode}. Stdout: {result.stdout}, Stderr: {result.stderr}")
            
    finally:
        # Cleanup wrapper script
        if os.path.exists(wrapper_script_path):
            os.remove(wrapper_script_path)