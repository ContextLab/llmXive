import pytest
import os
import sys
import json
import tempfile
import shutil
from pathlib import Path

# Ensure code/src is in path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path.parent))

from src.synthetic_gen import SyntheticDataGenerator
from src.models import DatasetRecord

class TestSyntheticDataGenerator:
    """Unit tests for SyntheticDataGenerator output schema and data integrity."""

    def setup_method(self):
        """Create a temporary directory for test outputs."""
        self.test_dir = tempfile.mkdtemp()
        self.output_dir = os.path.join(self.test_dir, "output")
        os.makedirs(self.output_dir, exist_ok=True)

    def teardown_method(self):
        """Remove the temporary directory after tests."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_generate_creates_required_columns(self):
        """Verify that generated data contains all required columns for DatasetRecord."""
        generator = SyntheticDataGenerator(seed=42)
        df = generator.generate(n_samples=50, mean_diff=0.5)

        required_columns = {
            "pre_test_score",
            "post_test_score",
            "instruction_type",
            "covariates"
        }

        assert set(df.columns).issuperset(required_columns), \
            f"Missing columns: {required_columns - set(df.columns)}"

    def test_generate_instruction_type_values(self):
        """Verify that instruction_type contains valid categorical values."""
        generator = SyntheticDataGenerator(seed=42)
        df = generator.generate(n_samples=100, mean_diff=0.0)

        valid_types = {"embodied", "static"}
        actual_types = set(df["instruction_type"].unique())

        assert actual_types.issubset(valid_types), \
            f"Invalid instruction_type values found: {actual_types - valid_types}"

    def test_generate_scores_within_range(self):
        """Verify that pre and post scores are within valid range [0, 100]."""
        generator = SyntheticDataGenerator(seed=42)
        df = generator.generate(n_samples=200, mean_diff=0.3)

        assert (df["pre_test_score"] >= 0).all() and (df["pre_test_score"] <= 100).all(), \
            "pre_test_score out of range [0, 100]"
        assert (df["post_test_score"] >= 0).all() and (df["post_test_score"] <= 100).all(), \
            "post_test_score out of range [0, 100]"

    def test_generate_covariates_structure(self):
        """Verify that covariates column contains valid JSON-serializable dictionaries."""
        generator = SyntheticDataGenerator(seed=42)
        df = generator.generate(n_samples=50, mean_diff=0.1)

        for idx, row in df.iterrows():
            cov = row["covariates"]
            assert isinstance(cov, dict), f"Covariates at index {idx} is not a dict"
            # Basic check that it's JSON serializable
            try:
                json.dumps(cov)
            except TypeError:
                pytest.fail(f"Covariates at index {idx} is not JSON serializable: {cov}")

    def test_generate_mapping_log_created(self):
        """Verify that generate_mapping_log creates the expected JSON file."""
        generator = SyntheticDataGenerator(seed=42)
        log_path = os.path.join(self.output_dir, "mapping_log.json")
        
        # Call the mapping log generation directly
        generator.generate_mapping_log(log_path)

        assert os.path.exists(log_path), "mapping_log.json was not created"

        with open(log_path, 'r') as f:
            log_data = json.load(f)

        # Verify structure per Constitution Principle VI
        assert "causal_chain" in log_data, "mapping_log missing 'causal_chain'"
        assert "Physics_Action" in log_data["causal_chain"], "Missing Physics_Action"
        assert "Virtual_Object_State" in log_data["causal_chain"], "Missing Virtual_Object_State"
        assert "Abstract_Principle_Inference" in log_data["causal_chain"], "Missing Abstract_Principle_Inference"

    def test_generate_deterministic_with_seed(self):
        """Verify that same seed produces identical data."""
        generator1 = SyntheticDataGenerator(seed=123)
        generator2 = SyntheticDataGenerator(seed=123)

        df1 = generator1.generate(n_samples=50, mean_diff=0.5)
        df2 = generator2.generate(n_samples=50, mean_diff=0.5)

        assert df1.equals(df2), "Data generation is not deterministic with same seed"

    def test_generate_sample_size_accuracy(self):
        """Verify that generated dataset has exactly the requested number of samples."""
        generator = SyntheticDataGenerator(seed=42)
        n_requested = 75
        df = generator.generate(n_samples=n_requested, mean_diff=0.2)

        assert len(df) == n_requested, \
            f"Expected {n_requested} samples, got {len(df)}"