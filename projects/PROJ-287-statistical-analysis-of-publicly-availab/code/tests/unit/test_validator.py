import unittest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import numpy as np

from src.models.lda.validator import (
    compute_c_v_coherence,
    validate_lda_model,
    validate_and_save_results,
    COHERENCE_THRESHOLD
)

class TestValidatorLogic(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_dir = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    @patch('src.models.lda.validator.get_logger')
    def test_validate_lda_model_pass(self, mock_logger):
        """Test that a model with coherence above threshold passes."""
        is_valid, msg = validate_lda_model("test_window", 0.5, threshold=0.4)
        self.assertTrue(is_valid)
        self.assertIn("passed", msg)

    @patch('src.models.lda.validator.get_logger')
    def test_validate_lda_model_fail(self, mock_logger):
        """Test that a model with coherence below threshold fails."""
        is_valid, msg = validate_lda_model("test_window", 0.3, threshold=0.4)
        self.assertFalse(is_valid)
        self.assertIn("failed", msg)

    @patch('src.models.lda.validator.get_logger')
    def test_validate_and_save_results(self, mock_logger):
        """Test saving validation results to a JSON file."""
        results = validate_and_save_results(
            "test_window",
            0.5,
            True,
            output_dir=self.output_dir,
            topic_words=[["word1", "word2"]]
        )
        
        self.assertTrue(results["is_valid"])
        self.assertEqual(results["coherence_score"], 0.5)
        self.assertEqual(results["window"], "test_window")
        
        # Check file was created
        expected_file = self.output_dir / "validation_test_window.json"
        self.assertTrue(expected_file.exists())

    @patch('src.models.lda.validator.CoherenceModel')
    @patch('src.models.lda.validator.corpora')
    def test_compute_c_v_coherence(self, mock_corpora, mock_coherence_model):
        """Test coherence computation with mocked gensim."""
        # Mock the CoherenceModel instance
        mock_instance = MagicMock()
        mock_instance.get_coherence.return_value = 0.65
        mock_coherence_model.return_value = mock_instance
        
        # Mock dictionary
        mock_dict = MagicMock()
        mock_corpora.Dictionary = MagicMock(return_value=mock_dict)
        
        # Mock model
        mock_model = MagicMock()
        
        corpus = [[1, 2], [3, 4]]
        
        score = compute_c_v_coherence(mock_model, corpus, mock_dict)
        
        self.assertEqual(score, 0.65)
        mock_coherence_model.assert_called_once()

    def test_compute_c_v_coherence_import_error(self):
        """Test that ImportError is raised if gensim is not available."""
        with patch.dict('sys.modules', {'gensim': None, 'gensim.models': None}):
            with self.assertRaises(ImportError):
                # Re-import to trigger the ImportError inside the function
                from importlib import reload
                import src.models.lda.validator as validator_module
                reload(validator_module)
                # Try to call the function (this might be tricky due to import caching)
                # Instead, we test the logic by checking the exception handling in the function
                pass

    @patch('src.models.lda.validator.get_logger')
    def test_validate_lda_model_exact_threshold(self, mock_logger):
        """Test validation at the exact threshold boundary."""
        is_valid, msg = validate_lda_model("test_window", 0.4, threshold=0.4)
        self.assertTrue(is_valid)

    @patch('src.models.lda.validator.get_logger')
    def test_validate_lda_model_just_below_threshold(self, mock_logger):
        """Test validation just below threshold."""
        is_valid, msg = validate_lda_model("test_window", 0.399, threshold=0.4)
        self.assertFalse(is_valid)
