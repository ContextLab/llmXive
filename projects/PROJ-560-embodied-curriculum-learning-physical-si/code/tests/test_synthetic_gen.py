import pytest
import os
import sys
import json
import tempfile
import shutil
from src.synthetic_gen import SyntheticDataGenerator, generate_mapping_log
from src.models import DatasetRecord


class TestSyntheticDataGenerator:
    """Tests for synthetic data generation."""
    
    def setup_method(self):
        """Setup temporary directories."""
        self.test_dir = tempfile.mkdtemp()
        
    def teardown_method(self):
        """Clean up."""
        shutil.rmtree(self.test_dir)
        
    def test_generate_basic(self):
        """Test basic generation."""
        generator = SyntheticDataGenerator(seed=42)
        records = generator.generate(n_samples=10, mean_diff=0.5, std_dev=1.0)
        assert len(records) == 10
        assert all(isinstance(r, DatasetRecord) for r in records)
        
    def test_generate_groups(self):
        """Test generation creates expected groups."""
        generator = SyntheticDataGenerator(seed=42)
        records = generator.generate(n_samples=20, instruction_types=["A", "B"])
        types = [r.instruction_type for r in records]
        assert types.count("A") == 10
        assert types.count("B") == 10
        
    def test_mapping_log(self):
        """Test mapping log generation."""
        generator = SyntheticDataGenerator(seed=42)
        records = generator.generate(n_samples=10)
        
        log_path = os.path.join(self.test_dir, "mapping_log.json")
        generate_mapping_log(records, log_path, physics_params={"g": 9.8})
        
        assert os.path.exists(log_path)
        with open(log_path, 'r') as f:
            log_data = json.load(f)
        assert log_data["mapping_type"] == "physics_to_math"
        assert log_data["record_count"] == 10
