"""
Unit tests for the LDA Model Validator.
"""

import unittest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

import numpy as np
from gensim import corpora, models
from gensim.models.coherencemodel import CoherenceModel

from src.models.lda.validator import (
    compute_c_v_coherence,
    validate_lda_model,
    validate_and_save_results,
    DEFAULT_COHERENCE_THRESHOLD
)


class TestValidatorLogic(unittest.TestCase):
    """Test cases for LDA validation logic."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a small mock dictionary and corpus
        self.dictionary = corpora.Dictionary([['human', 'interface', 'computer'],
                                              ['user', 'response', 'time']])
        self.corpus = [self.dictionary.doc2bow(text) for text in [['human', 'interface', 'computer'],
                                                                  ['user', 'response', 'time'],
                                                                  ['human', 'computer', 'system']]]

        # Create a mock LDA model
        self.mock_lda = MagicMock(spec=models.LdaModel)
        self.mock_lda.num_topics = 2
        self.mock_lda.get_document_topics = MagicMock(return_value=[])
        self.mock_lda.show_topic = MagicMock(return_value=[])

    def test_compute_c_v_coherence_with_mock(self):
        """Test coherence computation with mocked CoherenceModel."""
        with patch('src.models.lda.validator.CoherenceModel') as mock_cm:
            mock_instance = MagicMock()
            mock_instance.get_coherence.return_value = 0.45
            mock_cm.return_value = mock_instance

            score = compute_c_v_coherence(self.mock_lda, self.dictionary, self.corpus)

            self.assertEqual(score, 0.45)
            mock_cm.assert_called_once()

    def test_compute_c_v_coherence_none_model(self):
        """Test that None model raises ValueError."""
        with self.assertRaises(ValueError):
            compute_c_v_coherence(None, self.dictionary, self.corpus)

    def test_compute_c_v_coherence_none_dictionary(self):
        """Test that None dictionary raises ValueError."""
        with self.assertRaises(ValueError):
            compute_c_v_coherence(self.mock_lda, None, self.corpus)

    def test_compute_c_v_coherence_empty_corpus(self):
        """Test that empty corpus raises ValueError."""
        with self.assertRaises(ValueError):
            compute_c_v_coherence(self.mock_lda, self.dictionary, [])

    def test_validate_lda_model_passes(self):
        """Test validation when coherence score passes threshold."""
        with patch('src.models.lda.validator.CoherenceModel') as mock_cm:
            mock_instance = MagicMock()
            mock_instance.get_coherence.return_value = 0.5  # Above default threshold
            mock_cm.return_value = mock_instance

            result = validate_lda_model(
                self.mock_lda,
                self.dictionary,
                self.corpus,
                threshold=DEFAULT_COHERENCE_THRESHOLD,
                window_name="test_window"
            )

            self.assertTrue(result['valid'])
            self.assertEqual(result['coherence_score'], 0.5)
            self.assertEqual(result['window'], "test_window")
            self.assertIn("passed", result['message'].lower())

    def test_validate_lda_model_fails(self):
        """Test validation when coherence score fails threshold."""
        with patch('src.models.lda.validator.CoherenceModel') as mock_cm:
            mock_instance = MagicMock()
            mock_instance.get_coherence.return_value = 0.3  # Below default threshold
            mock_cm.return_value = mock_instance

            result = validate_lda_model(
                self.mock_lda,
                self.dictionary,
                self.corpus,
                threshold=DEFAULT_COHERENCE_THRESHOLD,
                window_name="test_window"
            )

            self.assertFalse(result['valid'])
            self.assertEqual(result['coherence_score'], 0.3)
            self.assertIn("failed", result['message'].lower())

    def test_validate_lda_model_exception_handling(self):
        """Test validation handles exceptions gracefully."""
        with patch('src.models.lda.validator.CoherenceModel') as mock_cm:
            mock_cm.side_effect = Exception("Test error")

            result = validate_lda_model(
                self.mock_lda,
                self.dictionary,
                self.corpus,
                threshold=DEFAULT_COHERENCE_THRESHOLD,
                window_name="test_window"
            )

            self.assertFalse(result['valid'])
            self.assertIsNone(result['coherence_score'])
            self.assertIn("error", result['message'].lower())

    def test_validate_and_save_results_success(self):
        """Test saving validation results for passing models."""
        results = [
            {'window': 'w1', 'valid': True, 'coherence_score': 0.5, 'threshold': 0.4},
            {'window': 'w2', 'valid': True, 'coherence_score': 0.45, 'threshold': 0.4}
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'results.json')
            success = validate_and_save_results(results, output_path, fail_fast=True)

            self.assertTrue(success)
            self.assertTrue(os.path.exists(output_path))

            with open(output_path, 'r') as f:
                import json
                saved = json.load(f)
            self.assertEqual(len(saved), 2)

    def test_validate_and_save_results_failure_no_fail_fast(self):
        """Test saving results when some fail but fail_fast is False."""
        results = [
            {'window': 'w1', 'valid': True, 'coherence_score': 0.5, 'threshold': 0.4},
            {'window': 'w2', 'valid': False, 'coherence_score': 0.3, 'threshold': 0.4}
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'results.json')
            success = validate_and_save_results(results, output_path, fail_fast=False)

            self.assertFalse(success)
            self.assertTrue(os.path.exists(output_path))

    def test_validate_and_save_results_failure_with_fail_fast(self):
        """Test that fail_fast raises exception on failure."""
        results = [
            {'window': 'w1', 'valid': True, 'coherence_score': 0.5, 'threshold': 0.4},
            {'window': 'w2', 'valid': False, 'coherence_score': 0.3, 'threshold': 0.4}
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'results.json')
            with self.assertRaises(RuntimeError):
                validate_and_save_results(results, output_path, fail_fast=True)


if __name__ == '__main__':
    unittest.main()
