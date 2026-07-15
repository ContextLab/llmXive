"""
Unit tests for the synthetic data generator.

Tests verify:
1. Correct file generation
2. Log-normal distribution validity (KS-test)
3. Data integrity (no empty rows, correct lengths)
4. Reproducibility (same seed produces same output)
"""
import os
import csv
import json
import tempfile
import shutil
import numpy as np
import pytest
from scipy import stats

# Import the generator module
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from benchmarks.generator import (
    generate_synthetic_corpus,
    _generate_log_normal_lengths,
    _generate_text_sample,
    LOG_NORMAL_PARAMS
)


class TestLengthGeneration:
    """Tests for log-normal length generation."""

    def test_generate_lengths_proper_distribution(self):
        """Verify generated lengths follow log-normal distribution."""
        lengths = _generate_log_normal_lengths(
            n_samples=10000,
            mu=LOG_NORMAL_PARAMS['mu'],
            sigma=LOG_NORMAL_PARAMS['sigma'],
            min_len=LOG_NORMAL_PARAMS['min_length'],
            max_len=LOG_NORMAL_PARAMS['max_length']
        )

        # Check basic properties
        assert len(lengths) == 10000
        assert lengths.min() >= LOG_NORMAL_PARAMS['min_length']
        assert lengths.max() <= LOG_NORMAL_PARAMS['max_length']

        # KS-test against theoretical distribution
        ks_stat, p_value = stats.kstest(
            lengths,
            'lognorm',
            args=(LOG_NORMAL_PARAMS['sigma'], 0, np.exp(LOG_NORMAL_PARAMS['mu']))
        )

        # With clipping, p-value might be lower, but should still show
        # reasonable fit (not extremely low)
        assert p_value > 0.001, "Distribution does not match log-normal"

    def test_generate_lengths_reproducibility(self):
        """Verify same seed produces same lengths."""
        np.random.seed(42)
        lengths1 = _generate_log_normal_lengths(
            n_samples=1000,
            mu=LOG_NORMAL_PARAMS['mu'],
            sigma=LOG_NORMAL_PARAMS['sigma'],
            min_len=LOG_NORMAL_PARAMS['min_length'],
            max_len=LOG_NORMAL_PARAMS['max_length']
        )

        np.random.seed(42)
        lengths2 = _generate_log_normal_lengths(
            n_samples=1000,
            mu=LOG_NORMAL_PARAMS['mu'],
            sigma=LOG_NORMAL_PARAMS['sigma'],
            min_len=LOG_NORMAL_PARAMS['min_length'],
            max_len=LOG_NORMAL_PARAMS['max_length']
        )

        np.testing.assert_array_equal(lengths1, lengths2)


class TestTextGeneration:
    """Tests for text sample generation."""

    def test_generate_text_length_accuracy(self):
        """Verify generated text is approximately the target length."""
        target_length = 100
        text = _generate_text_sample(target_length)

        # Text should be close to target length (allow some variance due to word boundaries)
        assert len(text) <= target_length
        assert len(text) >= target_length - 10  # Allow small variance

    def test_generate_text_non_empty(self):
        """Verify generated text is not empty for reasonable lengths."""
        for length in [10, 50, 100, 500]:
            text = _generate_text_sample(length)
            assert len(text) > 0
            assert text.strip() != ""


class TestCorpusGeneration:
    """Tests for full corpus generation."""

    def setup_method(self):
        """Create temporary directory for test outputs."""
        self.temp_dir = tempfile.mkdtemp()
        self.output_path = os.path.join(self.temp_dir, "test_corpus.csv")

    def teardown_method(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir)

    def test_generate_corpus_creates_file(self):
        """Verify corpus generation creates the output file."""
        stats_dict = generate_synthetic_corpus(
            n_samples=100,
            output_path=self.output_path,
            seed=42
        )

        assert os.path.exists(self.output_path)
        assert os.path.getsize(self.output_path) > 0

    def test_generate_corpus_csv_structure(self):
        """Verify CSV has correct headers and structure."""
        generate_synthetic_corpus(
            n_samples=50,
            output_path=self.output_path,
            seed=42
        )

        with open(self.output_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            headers = next(reader)

            assert headers == ['id', 'text', 'length']

            rows = list(reader)
            assert len(rows) == 50

            for row in rows:
                assert len(row) == 3
                assert row[0].isdigit()  # id
                assert len(row[1]) > 0   # text
                assert int(row[2]) > 0   # length

    def test_generate_corpus_length_consistency(self):
        """Verify text length matches reported length."""
        generate_synthetic_corpus(
            n_samples=100,
            output_path=self.output_path,
            seed=42
        )

        with open(self.output_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                text = row['text']
                reported_length = int(row['length'])

                # Text length should match reported length
                assert len(text) == reported_length

    def test_generate_corpus_statistics(self):
        """Verify returned statistics are correct."""
        stats_dict = generate_synthetic_corpus(
            n_samples=1000,
            output_path=self.output_path,
            seed=42
        )

        assert stats_dict['n_samples'] == 1000
        assert 'mean_length' in stats_dict
        assert 'std_length' in stats_dict
        assert 'ks_test' in stats_dict
        assert 'p_value' in stats_dict['ks_test']

    def test_generate_corpus_reproducibility(self):
        """Verify same seed produces identical output."""
        # First run
        generate_synthetic_corpus(
            n_samples=100,
            output_path=self.output_path,
            seed=123
        )

        with open(self.output_path, 'r', encoding='utf-8') as f:
            content1 = f.read()

        # Second run with same seed
        generate_synthetic_corpus(
            n_samples=100,
            output_path=self.output_path,
            seed=123
        )

        with open(self.output_path, 'r', encoding='utf-8') as f:
            content2 = f.read()

        assert content1 == content2

    def test_generate_corpus_different_seeds(self):
        """Verify different seeds produce different output."""
        # First run
        generate_synthetic_corpus(
            n_samples=100,
            output_path=self.output_path,
            seed=42
        )

        with open(self.output_path, 'r', encoding='utf-8') as f:
            content1 = f.read()

        # Second run with different seed
        generate_synthetic_corpus(
            n_samples=100,
            output_path=self.output_path,
            seed=999
        )

        with open(self.output_path, 'r', encoding='utf-8') as f:
            content2 = f.read()

        assert content1 != content2

    def test_generate_corpus_large_sample(self):
        """Test generation with larger sample size."""
        stats_dict = generate_synthetic_corpus(
            n_samples=10000,
            output_path=self.output_path,
            seed=42
        )

        assert stats_dict['n_samples'] == 10000
        assert stats_dict['ks_test']['is_valid_fit']