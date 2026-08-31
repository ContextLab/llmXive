"""
Unit tests for LDA Model Validator (T021).
"""
import unittest
import tempfile
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import numpy as np

# Mock gensim before importing the module if necessary, or assume installed
try:
    from gensim import corpora
    from gensim.models import LdaModel
except ImportError:
    # If gensim is not installed, we skip these tests or mock heavily
    # For the purpose of the test file, we assume the environment has gensim
    # or the test runner handles the import error gracefully.
    pass

from src.models.lda.validator import (
    compute_c_v_coherence,
    validate_lda_model,
    validate_and_save_results,
    CoherenceValidationError,
    COHERENCE_THRESHOLD
)

class TestValidatorLogic(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_dir = Path(self.temp_dir.name)
        self.window_id = "2000-2004"
        
        # Create mock dictionary and corpus
        self.mock_dictionary = MagicMock()
        self.mock_corpus = [[(0, 1), (1, 2)], [(0, 3), (2, 1)]]
        
        # Create mock LDA model
        self.mock_lda_model = MagicMock()
        # Mock the get_topics or similar methods if coherence model needs them
        self.mock_lda_model.get_topics.return_value = np.array([[0.1, 0.9], [0.8, 0.2]])

    def tearDown(self):
        self.temp_dir.cleanup()

    @patch('src.models.lda.validator.CoherenceModel')
    def test_compute_c_v_coherence_success(self, mock_coherence_model_class):
        """Test that coherence is computed correctly."""
        mock_instance = MagicMock()
        mock_instance.get_coherence.return_value = 0.55
        mock_coherence_model_class.return_value = mock_instance

        score = compute_c_v_coherence(self.mock_lda_model, self.mock_dictionary, self.mock_corpus)

        self.assertAlmostEqual(score, 0.55)
        mock_coherence_model_class.assert_called_once()

    @patch('src.models.lda.validator.CoherenceModel')
    def test_compute_c_v_coherence_empty_corpus(self, mock_coherence_model_class):
        """Test handling of empty corpus."""
        score = compute_c_v_coherence(self.mock_lda_model, self.mock_dictionary, [])
        self.assertEqual(score, 0.0)
        mock_coherence_model_class.assert_not_called()

    @patch('src.models.lda.validator.CoherenceModel')
    def test_validate_lda_model_pass(self, mock_coherence_model_class):
        """Test validation passes when score >= threshold."""
        mock_instance = MagicMock()
        mock_instance.get_coherence.return_value = 0.45
        mock_coherence_model_class.return_value = mock_instance

        is_valid, score, msg = validate_lda_model(self.window_id, self.mock_lda_model, self.mock_dictionary, self.mock_corpus)

        self.assertTrue(is_valid)
        self.assertAlmostEqual(score, 0.45)
        self.assertIn("PASSED", msg)

    @patch('src.models.lda.validator.CoherenceModel')
    def test_validate_lda_model_fail(self, mock_coherence_model_class):
        """Test validation fails when score < threshold."""
        mock_instance = MagicMock()
        mock_instance.get_coherence.return_value = 0.35
        mock_coherence_model_class.return_value = mock_instance

        is_valid, score, msg = validate_lda_model(self.window_id, self.mock_lda_model, self.mock_dictionary, self.mock_corpus)

        self.assertFalse(is_valid)
        self.assertAlmostEqual(score, 0.35)
        self.assertIn("FAILED", msg)
        self.assertIn("BLOCKED", msg)

    @patch('src.models.lda.validator.CoherenceModel')
    def test_validate_lda_model_error(self, mock_coherence_model_class):
        """Test validation raises error on computation failure."""
        mock_coherence_model_class.side_effect = RuntimeError("Gensim error")

        with self.assertRaises(CoherenceValidationError):
            validate_lda_model(self.window_id, self.mock_lda_model, self.mock_dictionary, self.mock_corpus)

    @patch('src.models.lda.validator.validate_lda_model')
    @patch('builtins.open', new_callable=mock_open)
    @patch('src.models.lda.validator.json.dump')
    def test_validate_and_save_results_success(self, mock_json_dump, mock_file, mock_validate):
        """Test successful validation and file saving."""
        mock_validate.return_value = (True, 0.50, "PASSED")
        
        result = validate_and_save_results(self.window_id, self.mock_lda_model, self.mock_dictionary, self.mock_corpus, self.output_dir)

        self.assertTrue(result["is_valid"])
        self.assertEqual(result["status"], "PROCEEDING")
        mock_file.assert_called_once()
        mock_json_dump.assert_called_once()

    @patch('src.models.lda.validator.validate_lda_model')
    def test_validate_and_save_results_failure_raises(self, mock_validate):
        """Test that validation failure raises an exception."""
        mock_validate.return_value = (False, 0.30, "FAILED")
        
        with self.assertRaises(CoherenceValidationError):
            validate_and_save_results(self.window_id, self.mock_lda_model, self.mock_dictionary, self.mock_corpus, self.output_dir)

if __name__ == '__main__':
    unittest.main()