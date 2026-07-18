"""
Tests for the synthetic data generator.
"""
import pytest
import os
import sys
import json
import tempfile
import shutil

from src.synthetic_gen import SyntheticDataGenerator, generate_mapping_log
from src.models import DatasetRecord


class TestSyntheticDataGenerator:
    """Test cases for SyntheticDataGenerator."""

    def test_generate_output_schema(self):
        """Test that generated data matches the expected schema."""
        records = SyntheticDataGenerator.generate(sample_size=20, seed=42)
        assert len(records) == 20
        for record in records:
            assert isinstance(record, DatasetRecord)
            assert record.pre_test_score is not None
            assert record.post_test_score is not None
            assert record.instruction_type in ["embodied", "static"]

    def test_generate_mapping_log(self):
        """Test that the mapping log is created correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, "test_mapping_log.json")
            generate_mapping_log(log_path)
            assert os.path.exists(log_path)
            with open(log_path, 'r') as f:
                data = json.load(f)
            assert "causal_chain" in data
            assert len(data["causal_chain"]) == 3