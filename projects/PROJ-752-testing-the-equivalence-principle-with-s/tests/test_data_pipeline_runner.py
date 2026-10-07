"""
Runner script to execute the integration test T013b: test_lageos1_fetch.

This script executes the specific test case defined in test_data_pipeline.py
to verify the end-to-end download and CSV generation for LAGEOS-1.

Requirement:
1. Run the test written in T013a against the implemented code.
2. Dependency: T013a (Test must be written first), T014b (Implementation must exist).
"""
import sys
import os
import pytest

# Ensure the code directory is in the path so imports work correctly
# The project structure assumes 'code/' is the root for imports
code_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'code')
if code_dir not in sys.path:
    sys.path.insert(0, code_dir)

def run_test_lageos1_fetch():
    """
    Execute the specific integration test for LAGEOS-1 data fetch.
    
    This function invokes pytest on the specific test case defined in 
    test_data_pipeline.py::TestDataPipeline::test_end_to_end_download_and_csv_generation.
    """
    # Path to the test file
    test_file_path = os.path.join(os.path.dirname(__file__), 'test_data_pipeline.py')
    
    # Check if the test file exists
    if not os.path.exists(test_file_path):
        print(f"ERROR: Test file not found at {test_file_path}")
        print("T013a (Write Integration Test) must be completed before T013b.")
        return 1
    
    # Construct the pytest command arguments
    # We target the specific method as per T013b requirement
    pytest_args = [
        "-v",
        "-s",
        f"{test_file_path}::TestDataPipeline::test_end_to_end_download_and_csv_generation",
        "--tb=short"
    ]
    
    print(f"Executing T013b: Running integration test for LAGEOS-1...")
    print(f"Command: pytest {' '.join(pytest_args)}")
    print("-" * 80)
    
    # Run pytest
    exit_code = pytest.main(pytest_args)
    
    print("-" * 80)
    if exit_code == 0:
        print("SUCCESS: T013b Integration Test passed.")
        print("LAGEOS-1 data was successfully fetched, parsed, and written to CSV.")
    else:
        print(f"FAILURE: T013b Integration Test failed with exit code {exit_code}.")
        print("Check the output above for specific error details.")
    
    return exit_code

if __name__ == "__main__":
    sys.exit(run_test_lageos1_fetch())