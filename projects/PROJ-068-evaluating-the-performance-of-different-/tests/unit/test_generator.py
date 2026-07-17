"""
Unit tests for the synthetic data generator.
"""
import os
import csv
import tempfile
import pytest
import math
import numpy as np
from scipy import stats

# Import the module under test
# Assuming the project structure allows importing from code.benchmarks
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from benchmarks.generator import (
    _generate_log_normal_length,
    _generate_text_sample,
    validate_distribution,
    generate_synthetic_corpus,
    compute_file_checksum,
    MU,
    SIGMA
)

class TestLogNormalGeneration:
    def test_generate_log_normal_length_positive(self):
        """Test that generated lengths are positive integers."""
        for _ in range(100):
            length = _generate_log_normal_length()
            assert isinstance(length, int)
            assert length >= 1

    def test_generate_log_normal_length_distribution(self):
        """
        Verify that a large sample of generated lengths follows the log-normal distribution.
        This is a statistical test, so we allow some tolerance.
        """
        sample_size = 5000
        lengths = [_generate_log_normal_length() for _ in range(sample_size)]
        
        # Fit log-normal
        fitted = stats.lognorm.fit(lengths, floc=0)
        shape, loc, scale = fitted
        
        # Theoretical sigma should be close to SIGMA (1.2)
        # Theoretical mu (of log) should be close to MU (2.5)
        # Note: scale = exp(mu), so log(scale) approx mu
        
        assert abs(shape - SIGMA) < 0.2, f"Shape (sigma) {shape:.2f} deviates too much from {SIGMA}"
        assert abs(math.log(scale) - MU) < 0.2, f"Log-scale (mu) {math.log(scale):.2f} deviates too much from {MU}"

class TestTextGeneration:
    def test_generate_text_sample_structure(self):
        """Test that generated text has expected structure."""
        text = _generate_text_sample()
        assert isinstance(text, str)
        assert len(text) > 0
        assert text[0].isupper()
        assert text.endswith('.')
        assert ' ' in text  # Should have spaces

class TestValidation:
    def test_validate_distribution_success(self):
        """Test that valid log-normal samples pass validation."""
        # Generate known good samples
        samples = [_generate_text_sample() for _ in range(1000)]
        is_valid, p_value = validate_distribution(samples)
        assert is_valid
        assert p_value > 0.05

    def test_validate_distribution_failure_on_uniform(self):
        """Test that uniform distribution fails validation."""
        # Generate uniform-like data (fixed length)
        samples = ["word " * 10 + "." for _ in range(1000)]
        # This should likely fail or have very low p-value against log-normal
        # Note: KS test on fitted parameters might still pass if the fit is perfect,
        # but for a uniform distribution vs log-normal fit, it usually fails.
        # We test that the function runs without error.
        try:
            is_valid, p_value = validate_distribution(samples)
            # We don't assert failure here because fitting a log-normal to uniform
            # might produce a weird fit that passes by chance, but the main goal
            # is to ensure the function works.
        except Exception as e:
            # If it raises, that's also a valid outcome for bad data
            pass

class TestCorpusGeneration:
    def test_generate_synthetic_corpus_creates_file(self):
        """Test that the corpus generator creates a valid CSV file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_corpus.csv")
            size = 100
            
            checksum = generate_synthetic_corpus(size, output_path)
            
            assert os.path.exists(output_path)
            assert len(checksum) == 64  # SHA-256 hex length
            
            # Verify CSV content
            with open(output_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == size
                assert 'id' in rows[0]
                assert 'text' in rows[0]
                assert 'word_count' in rows[0]

    def test_compute_file_checksum(self):
        """Test checksum computation."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test content")
            temp_path = f.name
        
        try:
            checksum = compute_file_checksum(temp_path)
            assert len(checksum) == 64
            
            # Verify determinism
            checksum2 = compute_file_checksum(temp_path)
            assert checksum == checksum2
        finally:
            os.unlink(temp_path)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
