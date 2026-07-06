"""
Integration test for lagged alignment logic (Task T020).

Verification:
- Validates that `data/interim_lagged_mmns.csv` is generated.
- Checks exact schema: subject_id, block_id, mmn_amplitude, source_window_start_trial.
- Confirms lagged logic: 50-trial source window aligns to subsequent target block.
"""
import os
import sys
import pytest
import tempfile
import shutil
import pandas as pd
from pathlib import Path
import numpy as np

# Add project root to path to allow imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.data.align import compute_lagged_alignment, generate_lagged_mmns_csv

# Mock data generator to simulate real preprocessed data structure
# without requiring the full US1 pipeline to have run yet.
# This ensures the test is self-contained and runs against a known state.
def create_mock_preprocessed_data(temp_dir: Path):
    """
    Creates a mock dataset structure simulating the output of US1 (preprocess.py).
    Includes raw EEG data (simulated), metadata, and trial logs.
    """
    data_dir = temp_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Create mock subject directory
    subject_id = "sub-01"
    subject_dir = data_dir / subject_id
    subject_dir.mkdir(parents=True, exist_ok=True)
    
    # Create mock EEG data (simulated as a CSV for speed, mimicking MNE structure)
    # Columns: trial_id, timestamp, stimulus_type (standard/deviant), response_correctness, channel_CP3, channel_CP4, channel_C3, channel_C4
    n_trials = 120
    np.random.seed(42)
    
    trials = []
    for i in range(n_trials):
        # Simulate standard (0) and deviant (1) stimuli
        stimulus_type = "deviant" if i % 10 == 9 else "standard"
        # Simulate response correctness
        response_correctness = np.random.choice([0, 1], p=[0.2, 0.8])
        
        # Simulate EEG signal (random noise + small signal for deviant)
        base_signal = np.random.normal(0, 10, 4)
        if stimulus_type == "deviant":
            base_signal += np.array([2.5, 2.0, 1.5, 1.0]) # Add MMN-like signal
        
        trials.append({
            "trial_id": i,
            "timestamp": i * 1000, # 1s intervals
            "stimulus_type": stimulus_type,
            "response_correctness": response_correctness,
            "channel_CP3": base_signal[0],
            "channel_CP4": base_signal[1],
            "channel_C3": base_signal[2],
            "channel_C4": base_signal[3]
        })
    
    df = pd.DataFrame(trials)
    eeg_path = subject_dir / "eeg_data.csv"
    df.to_csv(eeg_path, index=False)
    
    # Create metadata file
    metadata = {
        "subject_id": subject_id,
        "task": "tactile_discrimination",
        "sampling_rate": 1000,
        "channels": ["CP3", "CP4", "C3", "C4"],
        "stimulus_types": ["standard", "deviant"]
    }
    import json
    meta_path = subject_dir / "metadata.json"
    with open(meta_path, "w") as f:
        json.dump(metadata, f)
        
    return data_dir

@pytest.fixture
def mock_data_setup():
    """Fixture to create temporary mock data and clean up afterwards."""
    temp_root = tempfile.mkdtemp()
    temp_path = Path(temp_root)
    try:
        data_dir = create_mock_preprocessed_data(temp_path)
        yield data_dir
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)

def test_lagged_alignment_schema_and_logic(mock_data_setup):
    """
    Integration test for T020.
    Verifies generation of interim_lagged_mmns.csv with correct schema and lagged logic.
    """
    data_dir = mock_data_setup
    output_dir = data_dir.parent # Output goes to the parent of the subject data in this mock setup
    output_csv_path = output_dir / "interim_lagged_mmns.csv"
    
    # Remove output if it exists from previous runs
    if output_csv_path.exists():
        output_csv_path.unlink()
    
    # Run the alignment logic
    # We need to simulate the input to the alignment function.
    # Since the real pipeline reads from a specific structure, we adapt the call
    # to work with our mock data structure for the purpose of this integration test.
    
    # Mock the necessary inputs for compute_lagged_alignment
    # In a real scenario, this would be called after preprocessing.
    # Here we directly invoke the core logic with the mock data path.
    
    try:
        # The function expects a path to the subject data directory
        # and parameters for the lagged alignment.
        compute_lagged_alignment(
            subject_data_path=data_dir,
            output_path=output_dir,
            window_size=50,
            target_block_size=10,
            channels=["CP3", "CP4", "C3", "C4"],
            time_window_start=-250,
            time_window_end=0
        )
    except Exception as e:
        pytest.fail(f"Lagged alignment computation failed: {e}")
    
    # Verification Step 1: File exists
    assert output_csv_path.exists(), "interim_lagged_mmns.csv was not generated."
    
    # Verification Step 2: Load and check schema
    df = pd.read_csv(output_csv_path)
    required_columns = ["subject_id", "block_id", "mmn_amplitude", "source_window_start_trial"]
    
    missing_cols = [col for col in required_columns if col not in df.columns]
    assert not missing_cols, f"Missing required columns in output: {missing_cols}"
    
    # Verification Step 3: Check data integrity (no NaN in critical columns)
    assert df["mmn_amplitude"].notna().all(), "mmn_amplitude contains NaN values."
    assert df["source_window_start_trial"].notna().all(), "source_window_start_trial contains NaN values."
    
    # Verification Step 4: Verify Lagged Logic
    # The logic is: MMN is calculated from window [t-50, t-10] and aligned to block starting at t.
    # We check that the source_window_start_trial is strictly less than the block_id (representing start trial of target block).
    # Note: In this mock, block_id is effectively the start trial of the target block.
    # The source window starts at (block_id - 50).
    
    # Check that source_window_start_trial is indeed offset by 50 from the block start
    # (Assuming block_id represents the start trial of the target block in our mock logic)
    # The function should have calculated this.
    
    # Let's verify the relationship: source_window_start_trial should be approximately block_id - 50
    # Since block_id in our mock output corresponds to the start of the target block,
    # and the source window is the 50 trials prior to that.
    
    # Calculate expected start trial
    df["expected_source_start"] = df["block_id"] - 50
    
    # Allow for small integer rounding differences if any, but should be exact
    assert (df["source_window_start_trial"] == df["expected_source_start"]).all(), \
        "Lagged logic verification failed: source_window_start_trial does not match block_id - 50."
    
    # Verification Step 5: Check that we have multiple blocks (if enough data)
    # We have 120 trials. Window 50, target block 10.
    # We can have blocks starting at 50, 60, 70, 80, 90, 100, 110 (approx)
    # So we expect at least a few rows.
    assert len(df) >= 2, "Expected multiple blocks in output, but got too few."
    
    # Verification Step 6: Check subject_id consistency
    assert (df["subject_id"] == "sub-01").all(), "Subject ID mismatch in output."

if __name__ == "__main__":
    pytest.main([__file__, "-v"])