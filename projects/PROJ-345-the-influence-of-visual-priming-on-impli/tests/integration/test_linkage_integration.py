"""
Integration tests for linkage derivation and metadata percentage calculation (T016, T017, T018).
"""
import os
import tempfile
import pytest
import pandas as pd
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.data.generate_linked_trials import (
    load_preprocessed_trials,
    ensure_linkage,
    normalize_columns,
    write_linked_trials,
    verify_metadata_percentage
)
from code.data.linkage import derive_stimulus_id_from_trial_id


class TestLinkageDerivationIntegration:
    def test_full_linkage_pipeline(self, tmp_path):
        """Test the full pipeline from preprocessed trials to linked_trials.csv."""
        # Create mock preprocessed data
        input_file = tmp_path / "preprocessed_trials.csv"
        data = {
            "trial_id": ["trial_001", "trial_002", "trial_003", "trial_004", "trial_005"],
            "response_time": [500, 600, 550, 700, 450],
            "prime_condition": ["positive", "negative", "positive", "negative", "positive"],
            "participant_id": ["p1", "p1", "p2", "p2", "p3"]
        }
        pd.DataFrame(data).to_csv(input_file, index=False)

        # Mock the derive_stimulus_id_from_trial_id function behavior
        # In real usage, this would hash the trial_id and match to images
        def mock_derive(trial_id, method="hash_derivation"):
            # Simulate successful derivation for most trials
            if trial_id in ["trial_001", "trial_002", "trial_003", "trial_005"]:
                return f"stimulus_{trial_id.split('_')[1]}"
            return None  # Simulate failure for trial_004

        # Patch the function
        import code.data.generate_linked_trials as gen_module
        original_derive = gen_module.derive_stimulus_id_from_trial_id
        gen_module.derive_stimulus_id_from_trial_id = mock_derive

        try:
            # Run the pipeline
            df = load_preprocessed_trials(input_file)
            df = ensure_linkage(df, halt_threshold=0.10)  # 1/5 = 20% failure, should pass (<10% threshold)
            df = normalize_columns(df)
            output_file = write_linked_trials(df, tmp_path / "linked_trials.csv")

            # Verify output
            assert output_file.exists()
            result_df = pd.read_csv(output_file)

            assert len(result_df) == 5
            assert "stimulus_id" in result_df.columns

            # Check that 4 out of 5 have stimulus_id (80%)
            linked_count = result_df["stimulus_id"].notna().sum()
            assert linked_count == 4

        finally:
            # Restore original function
            gen_module.derive_stimulus_id_from_trial_id = original_derive

    def test_linkage_halt_on_high_failure_rate(self, tmp_path):
        """Test that the pipeline halts when >10% trials fail linkage."""
        # Create mock preprocessed data
        input_file = tmp_path / "preprocessed_trials.csv"
        data = {
            "trial_id": [f"trial_{i:03d}" for i in range(1, 11)],  # 10 trials
            "response_time": [500] * 10,
            "prime_condition": ["positive"] * 10,
            "participant_id": ["p1"] * 10
        }
        pd.DataFrame(data).to_csv(input_file, index=False)

        # Mock derivation to fail for 2 out of 10 (20% > 10% threshold)
        def mock_derive_fail(trial_id, method="hash_derivation"):
            if trial_id in ["trial_001", "trial_002"]:
                return f"stimulus_{trial_id.split('_')[1]}"
            return None

        import code.data.generate_linked_trials as gen_module
        original_derive = gen_module.derive_stimulus_id_from_trial_id
        gen_module.derive_stimulus_id_from_trial_id = mock_derive_fail

        try:
            df = load_preprocessed_trials(input_file)

            # This should raise RuntimeError
            with pytest.raises(RuntimeError, match="Data Gap: Linkage derivation failed"):
                ensure_linkage(df, halt_threshold=0.10)

        finally:
            gen_module.derive_stimulus_id_from_trial_id = original_derive

    def test_metadata_percentage_verification(self, tmp_path):
        """Test metadata percentage verification against threshold."""
        # Create linked_trials.csv
        output_file = tmp_path / "linked_trials.csv"
        data = {
            "trial_id": [f"trial_{i:03d}" for i in range(1, 101)],  # 100 trials
            "response_time": [500] * 100,
            "stimulus_id": [f"stimulus_{i:03d}" if i != 5 else "" for i in range(1, 101)],  # 1 missing
            "prime_condition": ["positive"] * 100,
            "participant_id": ["p1"] * 100
        }
        pd.DataFrame(data).to_csv(output_file, index=False)

        # Verify with 0.95 threshold (95%)
        result = verify_metadata_percentage(output_file, threshold=0.95)

        assert result["total_trials"] == 100
        assert result["linked_trials"] == 99
        assert result["percentage"] == 0.99
        assert result["meets_threshold"] is True

    def test_metadata_percentage_below_threshold(self, tmp_path):
        """Test verification when percentage is below threshold."""
        output_file = tmp_path / "linked_trials.csv"
        data = {
            "trial_id": [f"trial_{i:03d}" for i in range(1, 101)],
            "response_time": [500] * 100,
            "stimulus_id": [f"stimulus_{i:03d}" if i <= 80 else "" for i in range(1, 101)],  # 20 missing
            "prime_condition": ["positive"] * 100,
            "participant_id": ["p1"] * 100
        }
        pd.DataFrame(data).to_csv(output_file, index=False)

        result = verify_metadata_percentage(output_file, threshold=0.95)

        assert result["total_trials"] == 100
        assert result["linked_trials"] == 80
        assert result["percentage"] == 0.80
        assert result["meets_threshold"] is False

class TestDerivedStimulusId:
    def test_derive_stimulus_id_hash_method(self):
        """Test that derive_stimulus_id_from_trial_id produces consistent hashes."""
        trial_id = "trial_001"

        id1 = derive_stimulus_id_from_trial_id(trial_id, method="hash_derivation")
        id2 = derive_stimulus_id_from_trial_id(trial_id, method="hash_derivation")

        assert id1 == id2
        assert id1 is not None
        assert isinstance(id1, str)

    def test_derive_stimulus_id_different_trials(self):
        """Test that different trial IDs produce different stimulus IDs."""
        id1 = derive_stimulus_id_from_trial_id("trial_001", method="hash_derivation")
        id2 = derive_stimulus_id_from_trial_id("trial_002", method="hash_derivation")

        assert id1 != id2
        assert id1 is not None
        assert id2 is not None
