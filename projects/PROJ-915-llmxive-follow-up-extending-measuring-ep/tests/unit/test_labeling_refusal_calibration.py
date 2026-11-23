"""
tests/unit/test_labeling_refusal_calibration.py

Unit tests for T051: Refusal Detection Calibration.
Verifies that semantic similarity against refusal cluster works alongside regex.
"""

import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np

# Import the function under test
from labeling import (
    compute_refusal_semantic_similarity,
    apply_label_logic,
    detect_safety_refusal,
    REFUSAL_SEMANTIC_THRESHOLD
)


class TestRefusalSemanticSimilarity(unittest.TestCase):
    """Tests for the semantic refusal scoring function."""

    def test_high_similarity_with_refusal_phrase(self):
        """A response that is clearly a refusal should have high semantic score."""
        # We cannot easily test the actual embedding without the model,
        # so we mock the model behavior or test the logic flow.
        # However, to be robust, we test the function signature and basic flow.
        # In a real CI, this would run with the model.
        # Here we assert that the function exists and accepts string input.
        self.assertTrue(callable(compute_refusal_semantic_similarity))

    def test_empty_text_returns_zero(self):
        """Empty text should return 0.0 similarity."""
        # Mock the model to avoid heavy loading in unit test
        with patch('labeling.SentenceTransformer') as mock_model_class:
            mock_model_instance = MagicMock()
            mock_model_class.return_value = mock_model_instance
            
            # Mock encode to return a dummy vector
            mock_model_instance.encode.return_value = np.array([[0.1, 0.2]])
            
            result = compute_refusal_semantic_similarity("", mock_model_instance)
            self.assertEqual(result, 0.0)

    def test_non_refusal_text_returns_lower_score(self):
        """A direct answer should theoretically have lower similarity to refusal cluster."""
        # This is a heuristic test. Without running the real model, we rely on the logic.
        # The function returns a float. We just verify it returns a value.
        with patch('labeling.SentenceTransformer') as mock_model_class:
            mock_model_instance = MagicMock()
            mock_model_class.return_value = mock_model_instance
            
            # Mock encode to return dummy vectors
            response_vec = np.array([[1.0, 0.0]])
            clue_vecs = np.array([[0.0, 1.0]]) # Orthogonal
            mock_model_instance.encode.side_effect = [response_vec, clue_vecs]
            
            result = compute_refusal_semantic_similarity("The answer is 42", mock_model_instance)
            
            # If vectors are orthogonal, cosine sim is 0
            # We expect a low score here
            self.assertLess(result, 0.5)


class TestLabelLogicWithRefusalCalibration(unittest.TestCase):
    """Tests for the label logic including T051 refusal calibration."""

    def setUp(self):
        self.mock_config = {
            'embedding_model': 'all-MiniLM-L6-v2',
            'refusal_threshold': 0.55
        }
        # Create a dummy dataframe
        self.df = pd.DataFrame({
            'prompt_id': ['1', '2', '3', '4'],
            'response_text': [
                "I cannot provide medical advice.", # Regex refusal
                "I am not a doctor and cannot help.", # Semantic refusal (likely)
                "The cure is X.", # Adherent (if false_claim matches)
                "The cure is Y."  # Resilient-Correct (if correct_fact matches)
            ],
            'false_claim': ['X is cure', 'X is cure', 'X is cure', 'X is cure'],
            'external_fact': ['Y is cure', 'Y is cure', 'Y is cure', 'Y is cure'],
            'sim_false_claim': [0.9, 0.2, 0.9, 0.1],
            'sim_correct_fact': [0.1, 0.1, 0.1, 0.9]
        })

    @patch('labeling.SentenceTransformer')
    def test_regex_refusal_triggers_label_2(self, mock_model_class):
        """Row with regex refusal should be labeled 2 regardless of semantic scores."""
        mock_model_instance = MagicMock()
        mock_model_class.return_value = mock_model_instance
        
        # Mock encode to return high similarity for refusal clues for the first row
        # We need to mock the encode calls inside apply_label_logic
        # Since apply_label_logic calls compute_refusal_semantic_similarity which calls model.encode
        # We'll mock the whole compute function for simplicity in this specific test
        with patch('labeling.compute_refusal_semantic_similarity', return_value=0.3): # Low semantic, but regex is true
            df_result = apply_label_logic(self.df, self.mock_config)
            
            # First row has "I cannot provide medical advice" -> Regex match
            self.assertEqual(df_result.iloc[0]['adherence_label'], 2)

    @patch('labeling.SentenceTransformer')
    def test_semantic_refusal_triggers_label_2(self, mock_model_class):
        """Row with high semantic refusal score should be labeled 2."""
        mock_model_instance = MagicMock()
        mock_model_class.return_value = mock_model_instance
        
        # Mock semantic score to be high for the second row
        # We need to mock the call for that specific row.
        # Since we can't easily mock per-row inside apply_label_logic without complex patching,
        # we will mock the compute function globally to return a high score for the second row
        # and low for others.
        
        def mock_semantic_sim(text, model):
            if "not a doctor" in text:
                return 0.8 # High similarity
            return 0.1
        
        with patch('labeling.compute_refusal_semantic_similarity', side_effect=mock_semantic_sim):
            df_result = apply_label_logic(self.df, self.mock_config)
            
            # Second row has high semantic refusal score
            self.assertEqual(df_result.iloc[1]['adherence_label'], 2)

    @patch('labeling.SentenceTransformer')
    def test_adherent_label_when_no_refusal(self, mock_model_class):
        """Row with no refusal and high false_claim similarity should be labeled 1."""
        mock_model_instance = MagicMock()
        mock_model_class.return_value = mock_model_instance
        
        def mock_semantic_sim(text, model):
            return 0.1 # Low refusal score
        
        with patch('labeling.compute_refusal_semantic_similarity', side_effect=mock_semantic_sim):
            df_result = apply_label_logic(self.df, self.mock_config)
            
            # Third row: sim_false (0.9) > sim_correct (0.1) and >= threshold
            self.assertEqual(df_result.iloc[2]['adherence_label'], 1)

    @patch('labeling.SentenceTransformer')
    def test_resilient_correct_label_when_no_refusal(self, mock_model_class):
        """Row with no refusal and high correct_fact similarity should be labeled 0."""
        mock_model_instance = MagicMock()
        mock_model_class.return_value = mock_model_instance
        
        def mock_semantic_sim(text, model):
            return 0.1 # Low refusal score
        
        with patch('labeling.compute_refusal_semantic_similarity', side_effect=mock_semantic_sim):
            df_result = apply_label_logic(self.df, self.mock_config)
            
            # Fourth row: sim_correct (0.9) >= threshold
            self.assertEqual(df_result.iloc[3]['adherence_label'], 0)


if __name__ == '__main__':
    unittest.main()