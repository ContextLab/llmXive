import pytest
import os
import sys
import json
import tempfile
import shutil
from src.synthetic_gen import SyntheticDataGenerator
from src.models import DatasetRecord

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
        assert all(isinstance(r, DatasetRecord) for r in records)
        assert all(r.instruction_type in ["embodied", "static"] for r in records)
        assert all(isinstance(r.pre_test_score, (int, float)) for r in records)
        assert all(isinstance(r.post_test_score, (int, float)) for r in records)
    
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
            assert r1.instruction_type == r2.instruction_type
    
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
    
    def test_schema_types(self) -> None:
        """Test that all fields in the generated records have correct types."""
        records = self.generator.generate(
            n=5,
            seed=123,
            mean_diff_embodied=5.0,
            mean_diff_static=2.0
        )
        for r in records:
            assert isinstance(r.pre_test_score, (int, float))
            assert isinstance(r.post_test_score, (int, float))
            assert isinstance(r.instruction_type, str)
            assert r.instruction_type in ["embodied", "static"]
    
    def test_mean_difference_impact(self) -> None:
        """Test that changing mean_diff parameters affects the generated scores."""
        # Generate with a large difference
        records_high = self.generator.generate(
            n=100,
            seed=42,
            mean_diff_embodied=10.0,
            mean_diff_static=1.0
        )
        
        # Generate with a small difference
        records_low = self.generator.generate(
            n=100,
            seed=42,
            mean_diff_embodied=1.0,
            mean_diff_static=1.0
        )
        
        embodied_scores_high = [r.post_test_score - r.pre_test_score for r in records_high if r.instruction_type == "embodied"]
        embodied_scores_low = [r.post_test_score - r.pre_test_score for r in records_low if r.instruction_type == "embodied"]
        
        avg_gain_high = sum(embodied_scores_high) / len(embodied_scores_high)
        avg_gain_low = sum(embodied_scores_low) / len(embodied_scores_low)
        
        # The high difference scenario should produce a significantly higher average gain
        assert avg_gain_high > avg_gain_low