import os
import json
import pandas as pd
import pytest
from pathlib import Path
import tempfile
import shutil

# Import the function under test
# We assume the module is code/preprocess.py
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))
from preprocess import subsample_dataset_stratified, compute_checksum

class TestT017bSubsampling:
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test artifacts."""
        tmp = tempfile.mkdtemp()
        yield tmp
        shutil.rmtree(tmp)

    @pytest.fixture
    def sample_dataset(self, temp_dir):
        """Create a sample CSV dataset with stratification column."""
        # Create a dataset with > 150 rows to trigger subsampling
        # We need at least 2 classes for stratification
        data = []
        for i in range(200):
            label = "hydrolysis" if i % 2 == 0 else "oxidation"
            data.append({
                "smiles": f"C{i}C{i}C{i}",
                "temperature": 25.0 + i,
                "ph": 7.0,
                "uv": 10.0,
                "degradation_pathway": label,
                "source_id": f"src_{i}"
            })
        df = pd.DataFrame(data)
        csv_path = os.path.join(temp_dir, "input.csv")
        df.to_csv(csv_path, index=False)
        return csv_path, df

    def test_subsample_stratified_correctness(self, temp_dir, sample_dataset):
        """Test that subsampling preserves class distribution roughly."""
        input_path, original_df = sample_dataset
        output_path = os.path.join(temp_dir, "output.csv")
        target_size = 150

        result = subsample_dataset_stratified(
            input_path=input_path,
            output_path=output_path,
            target_size=target_size,
            seed=42,
            stratify_column="degradation_pathway"
        )

        assert os.path.exists(output_path)
        assert result["action"] == "subsample"
        assert result["final_n"] == target_size
        assert result["original_n"] == 200
        assert result["seed"] == 42

        # Verify the output file
        output_df = pd.read_csv(output_path)
        assert len(output_df) == target_size

        # Check stratification: counts should be proportional
        original_counts = original_df["degradation_pathway"].value_counts()
        output_counts = output_df["degradation_pathway"].value_counts()

        # Since we have 100 of each in input, and target 150, we expect ~75 each
        # Allow some tolerance for integer rounding in the sampling logic
        for label, count in output_counts.items():
            expected = int(original_counts[label] * target_size / len(original_df))
            # Allow 10% variance due to sampling randomness/implementation details
            assert abs(count - expected) <= max(5, int(expected * 0.1)), \
                f"Class {label} count {count} deviates too much from expected {expected}"

    def test_subsample_when_n_less_than_target(self, temp_dir, sample_dataset):
        """Test behavior when input is smaller than target."""
        input_path, original_df = sample_dataset
        # Create a smaller input
        small_input = os.path.join(temp_dir, "small.csv")
        small_df = original_df.head(100)
        small_df.to_csv(small_input, index=False)

        output_path = os.path.join(temp_dir, "small_out.csv")
        result = subsample_dataset_stratified(
            input_path=small_input,
            output_path=output_path,
            target_size=150,
            seed=42,
            stratify_column="degradation_pathway"
        )

        assert result["action"] == "copy"
        assert result["final_n"] == 100
        assert os.path.exists(output_path)
        output_df = pd.read_csv(output_path)
        assert len(output_df) == 100

    def test_subsample_missing_column(self, temp_dir, sample_dataset):
        """Test that missing stratify column raises error."""
        input_path, _ = sample_dataset
        output_path = os.path.join(temp_dir, "out.csv")

        with pytest.raises(ValueError, match="Stratify column"):
            subsample_dataset_stratified(
                input_path=input_path,
                output_path=output_path,
                target_size=150,
                seed=42,
                stratify_column="non_existent_column"
            )

    def test_checksum_computation(self, temp_dir, sample_dataset):
        """Test that checksums are computed correctly."""
        input_path, _ = sample_dataset
        output_path = os.path.join(temp_dir, "out.csv")

        subsample_dataset_stratified(
            input_path=input_path,
            output_path=output_path,
            target_size=150,
            seed=42,
            stratify_column="degradation_pathway"
        )

        checksum = compute_checksum(output_path)
        assert len(checksum) == 64  # SHA-256 hex length
        assert all(c in "0123456789abcdef" for c in checksum)