"""
Unit tests for the independence_checker module.

Tests FR-015: Synthetic data independence verification.
Tests SC-004: Diff check logic.
"""

import pytest
import os
import tempfile
import json
from pathlib import Path

from src.bias_pipeline.independence_checker import (
    normalize_token,
    compute_string_hash,
    extract_tokens_from_text,
    perform_diff_check,
    generate_independence_report,
    validate_synthetic_independence,
    PipelineError
)


class TestNormalizeToken:
    def test_lowercase_conversion(self):
        assert normalize_token("Hello") == "hello"
        assert normalize_token("WORLD") == "world"
    
    def test_whitespace_stripping(self):
        assert normalize_token("  token  ") == "token"
        assert normalize_token("\ntoken\n") == "token"
    
    def test_combined(self):
        assert normalize_token("  Hello  ") == "hello"


class TestComputeStringHash:
    def test_deterministic(self):
        hash1 = compute_string_hash("test")
        hash2 = compute_string_hash("test")
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hex length
    
    def test_different_values(self):
        hash1 = compute_string_hash("test")
        hash2 = compute_string_hash("Test")
        assert hash1 != hash2  # Case sensitive before normalization
    
    def test_empty_string(self):
        assert compute_string_hash("") != ""
        assert len(compute_string_hash("")) == 64


class TestExtractTokensFromText:
    def test_basic_extraction(self):
        text = "hello world"
        tokens = extract_tokens_from_text(text)
        assert len(tokens) == 2
        # Verify they are hashes
        for t in tokens:
            assert len(t) == 64
    
    def test_empty_text(self):
        assert extract_tokens_from_text("") == set()
        assert extract_tokens_from_text(None) == set()  # type: ignore
    
    def test_punctuation_handling(self):
        text = "hello, world! test."
        tokens = extract_tokens_from_text(text)
        assert len(tokens) == 3
        assert compute_string_hash("hello") in tokens
        assert compute_string_hash("world") in tokens
        assert compute_string_hash("test") in tokens
    
    def test_case_sensitivity_in_extraction(self):
        text = "Hello hello"
        tokens = extract_tokens_from_text(text)
        # "Hello" and "hello" normalize to same, so only 1 unique hash
        assert len(tokens) == 1


class TestPerformDiffCheck:
    def test_no_overlap(self):
        set_a = {compute_string_hash("a"), compute_string_hash("b")}
        set_b = {compute_string_hash("c"), compute_string_hash("d")}
        count, independent = perform_diff_check(set_a, set_b)
        assert count == 0
        assert independent is True
    
    def test_partial_overlap(self):
        common = compute_string_hash("common")
        set_a = {compute_string_hash("a"), common}
        set_b = {compute_string_hash("b"), common}
        count, independent = perform_diff_check(set_a, set_b)
        assert count == 1
        assert independent is False
    
    def test_full_overlap(self):
        s = {compute_string_hash("x")}
        count, independent = perform_diff_check(s, s)
        assert count == 1
        assert independent is False
    
    def test_invalid_input_type(self):
        with pytest.raises(PipelineError):
            perform_diff_check([], set())  # type: ignore
    
    def test_empty_sets(self):
        count, independent = perform_diff_check(set(), set())
        assert count == 0
        assert independent is True


class TestGenerateIndependenceReport:
    def test_pass_status(self):
        report = generate_independence_report(0, True, 100, 200)
        assert report["status"] == "PASS"
        assert report["pass_fail"] is True
        assert report["overlap_count"] == 0
    
    def test_fail_status(self):
        report = generate_independence_report(5, False, 100, 200)
        assert report["status"] == "FAIL"
        assert report["pass_fail"] is False
        assert report["overlap_count"] == 5


class TestValidateSyntheticIndependence:
    def test_valid_independence(self):
        code_text = "def process_data(user_id): return user_id"
        synthetic_text = "random noise data for simulation purposes"
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "report.json")
            result = validate_synthetic_independence(code_text, synthetic_text, output_path)
            
            assert result is True
            assert os.path.exists(output_path)
            
            with open(output_path, 'r') as f:
                report = json.load(f)
            
            assert report["status"] == "PASS"
            assert report["pass_fail"] is True
            assert report["overlap_count"] == 0
    
    def test_overlap_detected_raises_error(self):
        # Create text with a shared token that won't be filtered by punctuation
        # Use a specific word that appears in both
        shared_word = "supersecrettoken123"
        code_text = f"def use_{shared_word}(): pass"
        synthetic_text = f"this is synthetic data containing {shared_word}"
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "report.json")
            
            with pytest.raises(PipelineError) as exc_info:
                validate_synthetic_independence(code_text, synthetic_text, output_path)
            
            assert "SC-004 Gate Failed" in str(exc_info.value)
            
            # Verify report was written even on failure
            assert os.path.exists(output_path)
            with open(output_path, 'r') as f:
                report = json.load(f)
            assert report["status"] == "FAIL"
    
    def test_output_directory_creation(self):
        code_text = "simple code"
        synthetic_text = "simple synthetic"
        
        with tempfile.TemporaryDirectory() as tmpdir:
            nested_path = os.path.join(tmpdir, "subdir", "deep", "report.json")
            result = validate_synthetic_independence(code_text, synthetic_text, nested_path)
            
            assert result is True
            assert os.path.exists(nested_path)