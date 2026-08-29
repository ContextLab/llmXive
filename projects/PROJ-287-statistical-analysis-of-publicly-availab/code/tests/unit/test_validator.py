import unittest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import numpy as np

from src.models.lda.validator import compute_c_v_coherence, validate_lda_model, validate_and_save_results

class TestValidatorLogic(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)
        self.results_dir = self.project_root / "results" / "stats"
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        # Mock dictionary and corpus
        self.mock_dict = MagicMock()
        self.mock_dict.__len__ = MagicMock(return_value=1000)
        self.mock_corpus = [[(0, 1), (1, 2)], [(2, 3)]]
        
        # Mock topics
        self.mock_topics = [[0, 1, 2], [3, 4, 5]]

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)

    @patch('src.models.lda.validator.CoherenceModel')
    def test_compute_c_v_coherence_success(self, mock_cm):
        mock_instance = MagicMock()
        mock_instance.get_coherence.return_value = 0.55
        mock_cm.return_value = mock_instance

        score = compute_c_v_coherence(
            topics=self.mock_topics,
            dictionary=self.mock_dict,
            corpus=self.mock_corpus
        )

        self.assertAlmostEqual(score, 0.55)
        mock_cm.assert_called_once()
        mock_instance.get_coherence.assert_called_once()

    @patch('src.models.lda.validator.CoherenceModel')
    def test_compute_c_v_coherence_below_threshold(self, mock_cm):
        mock_instance = MagicMock()
        mock_instance.get_coherence.return_value = 0.30
        mock_cm.return_value = mock_instance

        # This should not raise in compute_c_v_coherence itself, 
        # but in validate_lda_model
        score = compute_c_v_coherence(
            topics=self.mock_topics,
            dictionary=self.mock_dict,
            corpus=self.mock_corpus
        )
        
        self.assertAlmostEqual(score, 0.30)

    def test_validate_lda_model_passes(self):
        with patch('src.models.lda.validator.compute_c_v_coherence') as mock_compute:
            mock_compute.return_value = 0.55
            
            is_valid, score = validate_lda_model(
                window_name="2000-2004",
                topics=self.mock_topics,
                dictionary=self.mock_dict,
                corpus=self.mock_corpus,
                threshold=0.4
            )
            
            self.assertTrue(is_valid)
            self.assertAlmostEqual(score, 0.55)
            mock_compute.assert_called_once()

    def test_validate_lda_model_fails(self):
        with patch('src.models.lda.validator.compute_c_v_coherence') as mock_compute:
            mock_compute.return_value = 0.30
            
            with self.assertRaises(RuntimeError) as context:
                validate_lda_model(
                    window_name="2000-2004",
                    topics=self.mock_topics,
                    dictionary=self.mock_dict,
                    corpus=self.mock_corpus,
                    threshold=0.4
                )
            
            self.assertIn("Validation FAILED", str(context.exception))

    def test_validate_and_save_results(self):
        with patch('src.models.lda.validator.compute_c_v_coherence') as mock_compute:
            mock_compute.return_value = 0.55
            
            # Mock update_manifest_with_analysis_params
            with patch('src.models.lda.validator.update_manifest_with_analysis_params'):
                result = validate_and_save_results(
                    window_name="2000-2004",
                    coherence_score=0.55,
                    topics=self.mock_topics,
                    dictionary=self.mock_dict,
                    output_dir=self.results_dir,
                    manifest_path=Path("dummy.json")
                )
                
                self.assertEqual(result["status"], "PASSED")
                self.assertEqual(result["coherence_score"], 0.55)
                
                # Check file creation
                expected_file = self.results_dir / "validation_2000_2004.json"
                self.assertTrue(expected_file.exists())
                
                import json
                with open(expected_file, 'r') as f:
                    saved_data = json.load(f)
                
                self.assertEqual(saved_data["status"], "PASSED")

    def test_validate_and_save_results_fails_low_score(self):
        with self.assertRaises(RuntimeError) as context:
            validate_and_save_results(
                window_name="2000-2004",
                coherence_score=0.30,
                topics=self.mock_topics,
                dictionary=self.mock_dict,
                output_dir=self.results_dir,
                manifest_path=Path("dummy.json")
            )
        
        self.assertIn("Cannot save results", str(context.exception))

    @patch('src.models.lda.validator.CoherenceModel')
    def test_compute_c_v_coherence_gensim_import_error(self, mock_cm):
        # Simulate gensim not being installed by patching HAS_GENSIM
        # This is tricky to test directly without reloading module, 
        # so we test the logic path if CoherenceModel is not found
        # We rely on the fact that if CoherenceModel is not found, 
        # the import at the top fails, but we assume it's installed for tests.
        # Instead, we test the RuntimeError if get_coherence fails.
        mock_cm.side_effect = Exception("Coherence calculation failed")
        
        with self.assertRaises(RuntimeError) as context:
            compute_c_v_coherence(
                topics=self.mock_topics,
                dictionary=self.mock_dict,
                corpus=self.mock_corpus
            )
        
        self.assertIn("Coherence computation failed", str(context.exception))

if __name__ == '__main__':
    unittest.main()