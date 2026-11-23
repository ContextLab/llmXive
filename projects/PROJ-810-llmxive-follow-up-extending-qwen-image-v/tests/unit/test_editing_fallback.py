"""
Unit tests for the Manual Verification Fallback logic (T032).
"""

import json
import csv
import os
import tempfile
from pathlib import Path
import pytest
from analysis.editing_fallback import (
    load_ocr_results,
    calculate_overall_accuracy,
    get_failed_samples,
    sample_failed_indices,
    write_verification_queue,
    main
)


class TestEditingFallback:
    """Test suite for editing_fallback module functions."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test artifacts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def sample_ocr_results(self):
        """Generate a mock OCR results dictionary."""
        return {
            "overall_accuracy": 0.92,
            "total_samples": 100,
            "failed_samples": [
                {"sample_id": "1", "source_image": "img1.jpg", "expected_text": "Hello", "detected_text": "Helo", "confidence": 0.8, "reason": "low_confidence"},
                {"sample_id": "2", "source_image": "img2.jpg", "expected_text": "World", "detected_text": "Worlld", "confidence": 0.7, "reason": "typo"},
                {"sample_id": "3", "source_image": "img3.jpg", "expected_text": "Test", "detected_text": "Tset", "confidence": 0.6, "reason": "scramble"},
                {"sample_id": "4", "source_image": "img4.jpg", "expected_text": "Data", "detected_text": "Dat", "confidence": 0.5, "reason": "missing_char"},
                {"sample_id": "5", "source_image": "img5.jpg", "expected_text": "Code", "detected_text": "Cde", "confidence": 0.4, "reason": "missing_char"},
                {"sample_id": "6", "source_image": "img6.jpg", "expected_text": "Run", "detected_text": "Rn", "confidence": 0.3, "reason": "missing_char"},
            ]
        }

    @pytest.fixture
    def sample_ocr_results_high_acc(self):
        """Generate a mock OCR results dictionary with high accuracy."""
        return {
            "overall_accuracy": 0.98,
            "total_samples": 100,
            "failed_samples": []
        }

    def test_load_ocr_results(self, temp_dir, sample_ocr_results):
        """Test loading OCR results from a JSON file."""
        json_path = temp_dir / "test_ocr.json"
        with open(json_path, 'w') as f:
            json.dump(sample_ocr_results, f)

        loaded = load_ocr_results(json_path)
        assert loaded["overall_accuracy"] == 0.92
        assert len(loaded["failed_samples"]) == 6

    def test_load_ocr_results_file_not_found(self, temp_dir):
        """Test error handling for missing OCR results file."""
        with pytest.raises(FileNotFoundError):
            load_ocr_results(temp_dir / "nonexistent.json")

    def test_calculate_overall_accuracy(self, sample_ocr_results):
        """Test accuracy extraction."""
        acc = calculate_overall_accuracy(sample_ocr_results)
        assert acc == 0.92

    def test_get_failed_samples(self, sample_ocr_results):
        """Test retrieval of failed samples."""
        failed = get_failed_samples(sample_ocr_results)
        assert len(failed) == 6
        assert failed[0]["sample_id"] == "1"

    def test_sample_failed_indices_all(self):
        """Test sampling when count < 5 (should return all)."""
        # Create a small list of 3 items
        items = [{"id": str(i)} for i in range(3)]
        sampled = sample_failed_indices(items, max_samples=50, seed=42)
        assert len(sampled) == 3
        assert all(item in sampled for item in items)

    def test_sample_failed_indices_max(self):
        """Test sampling when count >= 5 (should return up to max_samples)."""
        # Create a list of 100 items
        items = [{"id": str(i)} for i in range(100)]
        sampled = sample_failed_indices(items, max_samples=10, seed=42)
        assert len(sampled) == 10
        # Verify all are from original list
        assert all(item in items for item in sampled)
        # Verify determinism with same seed
        sampled2 = sample_failed_indices(items, max_samples=10, seed=42)
        assert sampled == sampled2

    def test_sample_failed_indices_empty(self):
        """Test sampling on empty list."""
        sampled = sample_failed_indices([], max_samples=50)
        assert sampled == []

    def test_write_verification_queue(self, temp_dir, sample_ocr_results):
        """Test writing verification queue to CSV."""
        output_path = temp_dir / "queue.csv"
        failed = get_failed_samples(sample_ocr_results)
        sampled = sample_failed_indices(failed, max_samples=5, seed=42)

        write_verification_queue(sampled, output_path)

        assert output_path.exists()
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 5
            assert "sample_id" in reader.fieldnames

    def test_write_verification_queue_empty(self, temp_dir):
        """Test writing empty verification queue."""
        output_path = temp_dir / "empty_queue.csv"
        write_verification_queue([], output_path)

        assert output_path.exists()
        with open(output_path, 'r') as f:
            reader = csv.reader(f)
            headers = next(reader)
            assert "sample_id" in headers
            # Check no data rows
            remaining = list(reader)
            assert len(remaining) == 0