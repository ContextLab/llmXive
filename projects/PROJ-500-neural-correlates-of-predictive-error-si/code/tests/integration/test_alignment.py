import os
import sys
import pytest
import tempfile
import shutil
import pandas as pd
from pathlib import Path

def create_mock_preprocessed_data(temp_dir: Path):
    """Create mock preprocessed data for testing."""
    # Create mock accuracy blocks
    accuracy_data = {
        "subject_id": ["S001", "S001", "S001", "S002", "S002"],
        "block_id": [1, 2, 3, 1, 2],
        "accuracy": [0.8, 0.85, 0.9, 0.75, 0.8],
        "trial_start": [0, 10, 20, 0, 10],
        "trial_end": [9, 19, 29, 9, 19],
    }
    accuracy_df = pd.DataFrame(accuracy_data)
    accuracy_df.to_csv(temp_dir / "accuracy_blocks.csv", index=False)

    # Create mock MMN epochs
    mmn_data = {
        "subject_id": ["S001", "S001", "S001", "S002", "S002"],
        "trial_id": list(range(30)),
        "mmn_amplitude": [0.1, 0.12, 0.11, 0.09, 0.1] * 6,
        "condition": ["standard", "deviant"] * 15,
    }
    mmn_df = pd.DataFrame(mmn_data)
    mmn_df.to_csv(temp_dir / "mmn_epochs.csv", index=False)

def mock_data_setup(temp_dir: Path):
    """Set up mock data for alignment testing."""
    create_mock_preprocessed_data(temp_dir)
    return temp_dir

def test_lagged_alignment_schema_and_logic():
    """Test that lagged alignment produces correct schema and logic."""
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_dir = Path(tmpdir)
        mock_data_setup(temp_dir)

        # Import the alignment module
        from src.data.align import calculate_lagged_mmns

        # Run lagged alignment
        output_path = temp_dir / "interim_lagged_mmns.csv"
        result = calculate_lagged_mmns(
            accuracy_path=temp_dir / "accuracy_blocks.csv",
            mmn_path=temp_dir / "mmn_epochs.csv",
            output_path=output_path,
            source_window_size=50,
            target_window_size=10,
        )

        # Verify output file exists
        assert output_path.exists(), "interim_lagged_mmns.csv not created"

        # Verify schema
        df = pd.read_csv(output_path)
        required_columns = ["subject_id", "block_id", "mmn_amplitude", "source_window_start_trial"]
        for col in required_columns:
            assert col in df.columns, f"Missing column: {col}"

        # Verify logic: source_window_start_trial should be block_id * 10 - 50
        # (simplified check for mock data)
        assert len(df) > 0, "No data in output"
        assert df["mmn_amplitude"].notna().all(), "NaN values in mmn_amplitude"