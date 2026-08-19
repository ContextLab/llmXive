"""
Unit tests for T032: Manual Verification Fallback.
"""
import json
import os
import tempfile
import csv
from pathlib import Path
import pytest
import sys

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.analysis.editing_fallback import (
    calculate_overall_accuracy,
    get_failed_samples,
    sample_failed_indices,
    write_verification_queue,
    ACCURACY_THRESHOLD,
    MIN_SAMPLE_SIZE,
    MAX_SAMPLE_SIZE,
    RANDOM_SEED
)


class TestCalculateOverallAccuracy:
    def test_explicit_accuracy_field(self):
        results = {"overall_accuracy": 0.92, "samples": []}
        assert calculate_overall_accuracy(results) == 0.92

    def test_calculation_from_samples(self):
        # 4 correct, 1 wrong = 0.8
        samples = [
            {"is_correct": True},
            {"is_correct": True},
            {"is_correct": True},
            {"is_correct": True},
            {"is_correct": False}
        ]
        results = {"samples": samples}
        assert calculate_overall_accuracy(results) == 0.8

    def test_empty_samples(self):
        results = {"samples": []}
        assert calculate_overall_accuracy(results) == 1.0


class TestGetFailedSamples:
    def test_filter_failures(self):
        samples = [
            {"sample_id": "1", "is_correct": True},
            {"sample_id": "2", "is_correct": False},
            {"sample_id": "3", "is_correct": False}
        ]
        failed = get_failed_samples({"samples": samples})
        assert len(failed) == 2
        assert all(not s["is_correct"] for s in failed)
        assert {s["sample_id"] for s in failed} == {"2", "3"}

    def test_no_failures(self):
        samples = [{"sample_id": "1", "is_correct": True}]
        failed = get_failed_samples({"samples": samples})
        assert len(failed) == 0


class TestSampleFailedIndices:
    def test_less_than_min_all_sampled(self):
        # 3 failures, min is 5 -> should return all 3
        failures = [{"id": str(i)} for i in range(3)]
        sampled = sample_failed_indices(failures)
        assert len(sampled) == 3

    def test_more_than_max_sampled(self):
        # 100 failures, max is 50 -> should return 50
        failures = [{"id": str(i)} for i in range(100)]
        sampled = sample_failed_indices(failures)
        assert len(sampled) == MAX_SAMPLE_SIZE
        # Check randomness (should not be the first 50 in order if we didn't sort)
        # But since we use random.sample, order is random.
        # We just check count.

    def test_exact_min(self):
        # 5 failures -> should return 5
        failures = [{"id": str(i)} for i in range(5)]
        sampled = sample_failed_indices(failures)
        assert len(sampled) == 5

    def test_reproducibility(self):
        failures = [{"id": str(i)} for i in range(20)]
        s1 = sample_failed_indices(failures)
        s2 = sample_failed_indices(failures)
        # Since seed is set inside function, results should be identical
        assert [s["id"] for s in s1] == [s["id"] for s in s2]

    def test_empty_list(self):
        sampled = sample_failed_indices([])
        assert len(sampled) == 0


class TestWriteVerificationQueue:
    def test_write_empty_queue_high_accuracy(self, tmp_path):
        # Mock the path writing
        output_file = tmp_path / "queue.csv"
        
        # We need to patch the global path or pass it. 
        # Since the function writes to a global constant, we will test the logic 
        # by creating a mock scenario where we call the function logic directly 
        # or by temporarily changing the global variable if possible.
        # However, for simplicity in unit testing, let's just test the CSV writing logic
        # by importing the internal logic or mocking.
        
        # Instead, let's just verify the file creation logic by calling the function
        # and checking the file content.
        # We can't easily change the global constant in the module without re-importing.
        # So we will test the behavior by assuming the function works as written.
        
        # Let's test the logic of writing to a specific path provided by the test.
        # We'll create a temporary file and verify the content.
        
        import code.analysis.editing_fallback as mod
        original_path = mod.VERIFICATION_QUEUE_PATH
        mod.VERIFICATION_QUEUE_PATH = output_file
        
        try:
            write_verification_queue([], 0.99)
            assert output_file.exists()
            with open(output_file, 'r') as f:
                reader = csv.reader(f)
                rows = list(reader)
                assert len(rows) == 2 # Header + 1 data row with reason
                assert "No verification needed" in rows[1][5]
        finally:
            mod.VERIFICATION_QUEUE_PATH = original_path

    def test_write_sampled_queue(self, tmp_path):
        import code.analysis.editing_fallback as mod
        output_file = tmp_path / "queue.csv"
        original_path = mod.VERIFICATION_QUEUE_PATH
        mod.VERIFICATION_QUEUE_PATH = output_file
        
        try:
            failures = [
                {"sample_id": "1", "image_path": "img1.png", "target_text": "A", "predicted_text": "B", "confidence": 0.5},
                {"sample_id": "2", "image_path": "img2.png", "target_text": "C", "predicted_text": "D", "confidence": 0.6}
            ]
            write_verification_queue(failures, 0.8)
            
            assert output_file.exists()
            with open(output_file, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == 2
                assert rows[0]["sample_id"] == "1"
                assert rows[1]["sample_id"] == "2"
                assert rows[0]["reason"] == "OCR Accuracy < 95% - Manual Review Required"
        finally:
            mod.VERIFICATION_QUEUE_PATH = original_path
