import pytest
import os
import sys
import json
import tempfile
import shutil
from src.synthetic_gen import SyntheticDataGenerator

class TestSyntheticDataGenerator:
    """Tests for SyntheticDataGenerator output schema."""
    
    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.generator = SyntheticDataGenerator()
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self) -> None:
        """Tear down test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_generate_basic(self) -> None:
        """Test basic generation of synthetic data."""
        records = self.generator.generate(
            n=10,
            seed=42,
            mean_diff_embodied=5.0,
            mean_diff_static=2.0
        )
        assert len(records) == 10
        assert all(r.instruction_type in ["embodied", "static"] for r in records)
        assert all(isinstance(r.pre_test_score, float) for r in records)
        assert all(isinstance(r.post_test_score, float) for r in records)
    
    def test_deterministic_generation(self) -> None:
        """Test that generation is deterministic with the same seed."""
        records1 = self.generator.generate(
            n=10,
            seed=42,
            mean_diff_embodied=5.0,
            mean_diff_static=2.0
        )
        records2 = self.generator.generate(
            n=10,
            seed=42,
            mean_diff_embodied=5.0,
            mean_diff_static=2.0
        )
        assert len(records1) == len(records2)
        for r1, r2 in zip(records1, records2):
            assert r1.pre_test_score == r2.pre_test_score
            assert r1.post_test_score == r2.post_test_score
    
    def test_mapping_log_creation(self) -> None:
        """Test that mapping log is created."""
        output_path = os.path.join(self.temp_dir, "mapping_log.json")
        self.generator.generate(
            n=10,
            seed=42,
            mean_diff_embodied=5.0,
            mean_diff_static=2.0
        )
        self.generator.write_mapping_log(output_path)
        
        assert os.path.exists(output_path)
        with open(output_path, "r") as f:
            log_data = json.load(f)
        
        assert isinstance(log_data, list)
        assert len(log_data) == 10
        for entry in log_data:
            assert "physics_param" in entry
            assert "math_concept" in entry
            assert "mapping_rule" in entry
    
    def test_group_distribution(self) -> None:
        """Test that records are distributed between groups."""
        records = self.generator.generate(
            n=100,
            seed=42,
            mean_diff_embodied=5.0,
            mean_diff_static=2.0
        )
        embodied_count = sum(1 for r in records if r.instruction_type == "embodied")
        static_count = sum(1 for r in records if r.instruction_type == "static")
        
        assert embodied_count + static_count == 100
        assert embodied_count == 50
        assert static_count == 50