"""
Unit tests for the synthetic dataset generator.
"""

import json
import os
import sys
import tempfile
from pathlib import Path

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.src.audit.synthetic import (
    generate_synthetic_corpus,
    generate_binary_summary,
    generate_continuous_summary,
    generate_base_metadata,
    MIN_RECORDS
)
from code.src.config import SEED


class TestSyntheticGenerator:
    """Tests for synthetic dataset generation."""

    def test_generate_base_metadata(self):
        """Test base metadata generation."""
        metadata = generate_base_metadata("test_domain", 2023)
        
        assert metadata["domain"] == "test_domain"
        assert metadata["year"] == 2023
        assert "url" in metadata
        assert "timestamp" in metadata
        assert "repository_id" in metadata

    def test_generate_binary_summary(self):
        """Test binary summary generation with known parameters."""
        metadata = generate_base_metadata("test", 2023)
        
        summary = generate_binary_summary(
            metadata=metadata,
            true_baseline_rate=0.10,
            true_effect_size=0.05,
            n_control=1000,
            n_treatment=1000,
            noise_level=0.0
        )
        
        assert summary.test_type == "binary"
        assert summary.sample_size_control == 1000
        assert summary.sample_size_treatment == 1000
        assert summary.ground_truth_baseline_rate == 0.10
        assert summary.ground_truth_effect_size == 0.05
        assert 0 <= summary.reported_p_value <= 1.0

    def test_generate_continuous_summary(self):
        """Test continuous summary generation with known parameters."""
        metadata = generate_base_metadata("test", 2023)
        
        summary = generate_continuous_summary(
            metadata=metadata,
            true_baseline_mean=50.0,
            true_effect_size=5.0,
            baseline_std=10.0,
            n_control=1000,
            n_treatment=1000,
            noise_level=0.0
        )
        
        assert summary.test_type == "continuous"
        assert summary.sample_size_control == 1000
        assert summary.sample_size_treatment == 1000
        assert summary.ground_truth_baseline_rate == 50.0
        assert summary.ground_truth_effect_size == 5.0
        assert 0 <= summary.reported_p_value <= 1.0

    def test_synthetic_corpus_generation(self):
        """Test full corpus generation meets minimum record count."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            csv_path, gt_path = generate_synthetic_corpus(
                output_dir=output_dir,
                total_records=MIN_RECORDS,
                binary_ratio=0.6,
                noise_level=0.0
            )
            
            # Verify files exist
            assert csv_path.exists()
            assert gt_path.exists()
            
            # Verify record count
            with open(csv_path, 'r') as f:
                record_count = sum(1 for _ in f) - 1  # Exclude header
            
            assert record_count >= MIN_RECORDS, f"Expected >= {MIN_RECORDS} records, got {record_count}"
            
            # Verify ground truth structure
            with open(gt_path, 'r') as f:
                ground_truth = json.load(f)
            
            assert len(ground_truth) == record_count
            
            # Verify binary/continuous mix
            binary_count = sum(1 for gt in ground_truth if gt["test_type"] == "binary")
            continuous_count = sum(1 for gt in ground_truth if gt["test_type"] == "continuous")
            
            expected_binary = int(MIN_RECORDS * 0.6)
            assert abs(binary_count - expected_binary) <= 5, f"Binary count mismatch: {binary_count} vs {expected_binary}"
            assert binary_count + continuous_count == record_count

    def test_synthetic_corpus_with_noise(self):
        """Test corpus generation with noise applied."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            csv_path, gt_path = generate_synthetic_corpus(
                output_dir=output_dir,
                total_records=1000,
                binary_ratio=0.5,
                noise_level=0.1
            )
            
            # Verify files exist
            assert csv_path.exists()
            assert gt_path.exists()
            
            # With noise, some records should be flagged as inconsistent
            with open(csv_path, 'r') as f:
                import csv
                reader = csv.DictReader(f)
                inconsistent_count = sum(1 for row in reader if row["is_inconsistent"] == "True")
            
            # Should have some inconsistencies with noise
            assert inconsistent_count > 0, "Expected some inconsistencies with noise applied"

    def test_reproducibility(self):
        """Test that generation is reproducible with fixed seed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir1 = Path(tmpdir) / "run1"
            output_dir2 = Path(tmpdir) / "run2"
            
            # Run twice with same seed
            csv_path1, gt_path1 = generate_synthetic_corpus(
                output_dir=output_dir1,
                total_records=100,
                binary_ratio=0.5,
                noise_level=0.0
            )
            
            csv_path2, gt_path2 = generate_synthetic_corpus(
                output_dir=output_dir2,
                total_records=100,
                binary_ratio=0.5,
                noise_level=0.0
            )
            
            # Compare ground truth (should be identical due to fixed seed)
            with open(gt_path1, 'r') as f1, open(gt_path2, 'r') as f2:
                gt1 = json.load(f1)
                gt2 = json.load(f2)
            
            assert gt1 == gt2, "Ground truth should be identical with fixed seed"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
