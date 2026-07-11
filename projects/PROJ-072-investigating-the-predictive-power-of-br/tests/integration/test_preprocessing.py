"""
Integration test for preprocessing pipeline on 1 subject.
Task: T010 [P] [US1]
"""
import os
import sys
import numpy as np
import pytest
from pathlib import Path

# Ensure code/ is in path for imports
ROOT_DIR = Path(__file__).resolve().parents[2]
CODE_DIR = ROOT_DIR / "code"
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

# Import the preprocessing pipeline logic
# Based on the API surface, we assume the logic is in preprocessing/preprocess.py
# We need to import the function that orchestrates the preprocessing.
# Since the API surface only lists download.py, we must implement the
# missing pipeline logic or assume it exists.
# The task requires running `pipeline.preprocess(subject_id='sub')`.
# We will implement a minimal pipeline module to satisfy the import and execution.

try:
    from preprocessing.preprocess import preprocess_single_subject
except ImportError:
    # Fallback if the file doesn't exist yet, though T011/T012 should create it.
    # For the purpose of this test to be runnable, we define a mock or 
    # raise a clear failure if the dependency is missing.
    # However, per constraints, we must write real code. 
    # We will assume T011/T012 are implemented or provide the minimal 
    # implementation here if the file is missing? 
    # No, "Extend, don't re-author". We assume T011/T012 exist.
    # If they don't, the test fails, which is correct behavior for a missing dependency.
    raise RuntimeError(
        "Missing dependency: code/preprocessing/preprocess.py must be implemented (T011/T012) "
        "to run this integration test."
    )

def test_preprocess_single_subject():
    """
    Runs pipeline.preprocess(subject_id='sub') and asserts:
    1. Output file `data/processed/sub-<id>_matrix.npy` exists.
    2. Shape is (90, 90).
    3. Contains no NaNs.
    4. All values within [-1.0, 1.0].
    """
    subject_id = "sub-001" # Using a realistic ID format
    output_dir = ROOT_DIR / "data" / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    expected_output_path = output_dir / f"{subject_id}_matrix.npy"
    
    # Check if raw data exists (simulating the prerequisite for preprocessing)
    # In a real run, T011 would have downloaded this.
    # We check if the expected raw file exists to proceed, or skip if not.
    # For this test to be robust, we assume the raw data is present or
    # the preprocess function handles missing data gracefully (though it should fail loudly).
    
    # Execute the preprocessing
    try:
        # The function signature from the task description: pipeline.preprocess(subject_id='sub')
        # We map this to our imported function.
        preprocess_single_subject(subject_id)
    except FileNotFoundError as e:
        pytest.fail(f"Preprocessing failed: Raw data not found for {subject_id}. "
                    f"Ensure T011 (download) has been run. Error: {e}")
    except Exception as e:
        pytest.fail(f"Preprocessing failed with unexpected error: {e}")

    # Assertions
    assert expected_output_path.exists(), f"Output file {expected_output_path} was not created."
    
    matrix = np.load(expected_output_path)
    
    # Check shape (AAL atlas typically has 90 or 116 regions; spec says 90)
    assert matrix.shape == (90, 90), f"Matrix shape is {matrix.shape}, expected (90, 90)."
    
    # Check for NaNs
    assert not np.isnan(matrix).any(), "Matrix contains NaN values."
    
    # Check range [-1.0, 1.0]
    assert matrix.min() >= -1.0, f"Matrix contains values < -1.0 (min: {matrix.min()})."
    assert matrix.max() <= 1.0, f"Matrix contains values > 1.0 (max: {matrix.max()})."

    print(f"Integration test passed for {subject_id}. Matrix shape: {matrix.shape}, "
          f"Range: [{matrix.min():.4f}, {matrix.max():.4f}]")
