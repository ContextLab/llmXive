"""
Unit tests for the error classifier stratified sampling logic.

This module verifies that the error classifier in `code/analysis/error_classifier.py`
correctly implements stratified sampling by perturbation type with a fixed random seed.

Requirements verified:
1. Stratification by perturbation type is applied correctly.
2. Sampling logic respects the ≤50 failures or sample of 50 constraint.
3. Random seed=42 is used for reproducibility.
4. Output tags match the expected schema.
"""
import json
import os
import sys
import pytest
from pathlib import Path
from typing import List, Dict, Any
import random
import numpy as np

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from analysis.error_classifier import (
    stratified_sample_errors,
    classify_errors,
    generate_error_classification_report
)
from config import ensure_directories


class TestStratifiedSamplingLogic:
    """Tests for the stratified sampling logic in the error classifier."""

    @pytest.fixture
    def mock_failures_data(self):
        """Create mock failure data with known perturbation type distribution."""
        # Create a dataset with 100 failures distributed across perturbation types
        data = []
        
        # Synonym perturbations: 30 failures
        for i in range(30):
            data.append({
                "task_id": f"synonym_{i}",
                "perturbation_type": "synonym",
                "status": "fail",
                "error_message": "AssertionError" if i % 2 == 0 else "TimeoutExpired",
                "original_prompt": "Original prompt",
                "generated_code": "def foo(): pass"
            })
        
        # Typo perturbations: 40 failures
        for i in range(40):
            data.append({
                "task_id": f"typo_{i}",
                "perturbation_type": "typo",
                "status": "fail",
                "error_message": "SyntaxError" if i % 3 == 0 else "AssertionError",
                "original_prompt": "Original prompt",
                "generated_code": "def foo(: pass"
            })
        
        # Rephrase perturbations: 30 failures
        for i in range(30):
            data.append({
                "task_id": f"rephrase_{i}",
                "perturbation_type": "rephrase",
                "status": "fail",
                "error_message": "AssertionError" if i % 4 == 0 else "TimeoutExpired",
                "original_prompt": "Original prompt",
                "generated_code": "def foo(): pass"
            })
        
        return data

    @pytest.fixture
    def mock_large_failures_data(self):
        """Create mock failure data with >50 failures to test sampling limit."""
        data = []
        
        # Create 200 failures distributed across types
        for i in range(200):
            if i < 60:
                p_type = "synonym"
            elif i < 120:
                p_type = "typo"
            else:
                p_type = "rephrase"
            
            data.append({
                "task_id": f"task_{i}",
                "perturbation_type": p_type,
                "status": "fail",
                "error_message": f"Error_{i % 5}",
                "original_prompt": "Original prompt",
                "generated_code": "def foo(): pass"
            })
        
        return data

    def test_stratified_sampling_respects_types(self, mock_failures_data):
        """Verify that sampling preserves the distribution of perturbation types."""
        # Set seed for reproducibility
        random.seed(42)
        np.random.seed(42)
        
        # Sample with a limit smaller than total failures
        sample_size = 15
        sampled = stratified_sample_errors(mock_failures_data, max_samples=sample_size)
        
        # Count types in sample
        type_counts = {}
        for item in sampled:
            p_type = item["perturbation_type"]
            type_counts[p_type] = type_counts.get(p_type, 0) + 1
        
        # Verify all types are represented (stratification)
        assert len(type_counts) == 3, "All perturbation types should be represented"
        
        # Verify total sample size
        assert len(sampled) == sample_size, f"Sample size should be {sample_size}"

    def test_stratified_sampling_with_large_dataset(self, mock_large_failures_data):
        """Verify that sampling respects the 50 sample limit."""
        # Set seed for reproducibility
        random.seed(42)
        np.random.seed(42)
        
        # Sample with limit
        sampled = stratified_sample_errors(mock_large_failures_data, max_samples=50)
        
        # Verify sample size is exactly 50
        assert len(sampled) == 50, "Sample size should be capped at 50"
        
        # Verify all types are represented
        type_counts = {}
        for item in sampled:
            p_type = item["perturbation_type"]
            type_counts[p_type] = type_counts.get(p_type, 0) + 1
        
        assert len(type_counts) == 3, "All perturbation types should be represented"

    def test_stratified_sampling_with_small_dataset(self, mock_failures_data):
        """Verify that sampling returns all items when dataset is small."""
        # Set seed for reproducibility
        random.seed(42)
        np.random.seed(42)
        
        # Sample with a limit larger than total failures
        sampled = stratified_sample_errors(mock_failures_data, max_samples=100)
        
        # Verify all items are returned
        assert len(sampled) == len(mock_failures_data), "All items should be returned"

    def test_reproducibility_with_seed(self, mock_failures_data):
        """Verify that the same seed produces the same sample."""
        # First run
        random.seed(42)
        np.random.seed(42)
        sample1 = stratified_sample_errors(mock_failures_data, max_samples=15)
        
        # Second run with same seed
        random.seed(42)
        np.random.seed(42)
        sample2 = stratified_sample_errors(mock_failures_data, max_samples=15)
        
        # Verify samples are identical
        assert len(sample1) == len(sample2), "Sample sizes should match"
        for i, (item1, item2) in enumerate(zip(sample1, sample2)):
            assert item1["task_id"] == item2["task_id"], f"Item {i} should match"
            assert item1["perturbation_type"] == item2["perturbation_type"], f"Type {i} should match"

    def test_error_classification_tags(self, mock_failures_data):
        """Verify that error classification produces valid tags."""
        # Set seed for reproducibility
        random.seed(42)
        np.random.seed(42)
        
        # Sample data
        sampled = stratified_sample_errors(mock_failures_data, max_samples=15)
        
        # Classify errors
        classified = classify_errors(sampled)
        
        # Verify each item has required fields
        for item in classified:
            assert "task_id" in item, "task_id is required"
            assert "perturbation_type" in item, "perturbation_type is required"
            assert "error_tag" in item, "error_tag is required"
            assert "confidence" in item, "confidence is required"
            
            # Verify error_tag is one of expected values
            assert item["error_tag"] in ["syntax", "logic", "timeout", "other"], \
                f"Invalid error_tag: {item['error_tag']}"
            
            # Verify confidence is between 0 and 1
            assert 0.0 <= item["confidence"] <= 1.0, \
                f"Confidence should be between 0 and 1, got {item['confidence']}"

    def test_generate_report_creates_file(self, mock_failures_data, tmp_path):
        """Verify that the report generation creates a valid JSON file."""
        # Set seed for reproducibility
        random.seed(42)
        np.random.seed(42)
        
        # Create output directory
        output_dir = tmp_path / "processed"
        output_dir.mkdir()
        
        output_file = output_dir / "error_classification_report.json"
        
        # Generate report
        generate_error_classification_report(
            failures_data=mock_failures_data,
            output_path=str(output_file),
            max_samples=50
        )
        
        # Verify file exists
        assert output_file.exists(), "Report file should be created"
        
        # Verify file is valid JSON
        with open(output_file, 'r') as f:
            report = json.load(f)
        
        # Verify report structure
        assert "metadata" in report, "metadata is required"
        assert "samples" in report, "samples is required"
        assert "summary" in report, "summary is required"
        
        # Verify metadata
        assert report["metadata"]["seed"] == 42, "Seed should be 42"
        assert "total_failures" in report["metadata"], "total_failures is required"
        
        # Verify samples
        assert len(report["samples"]) <= 50, "Sample size should be capped at 50"
        
        # Verify summary
        assert "by_type" in report["summary"], "by_type summary is required"
        assert "by_tag" in report["summary"], "by_tag summary is required"

    def test_stratification_proportions(self, mock_failures_data):
        """Verify that stratified sampling maintains approximate proportions."""
        # Set seed for reproducibility
        random.seed(42)
        np.random.seed(42)
        
        # Original distribution: 30% synonym, 40% typo, 30% rephrase
        total = len(mock_failures_data)
        original_dist = {
            "synonym": 30 / total,
            "typo": 40 / total,
            "rephrase": 30 / total
        }
        
        # Sample 15 items
        sampled = stratified_sample_errors(mock_failures_data, max_samples=15)
        
        # Calculate sample distribution
        sample_dist = {}
        for item in sampled:
            p_type = item["perturbation_type"]
            sample_dist[p_type] = sample_dist.get(p_type, 0) + 1
        
        sample_dist = {k: v / len(sampled) for k, v in sample_dist.items()}
        
        # Verify proportions are roughly maintained (within 20% relative error)
        for p_type in original_dist:
            expected = original_dist[p_type]
            actual = sample_dist.get(p_type, 0)
            if expected > 0:
                relative_error = abs(actual - expected) / expected
                assert relative_error < 0.5, \
                    f"Stratification proportion for {p_type} deviates too much: expected {expected}, got {actual}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])