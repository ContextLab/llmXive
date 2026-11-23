"""
Unit tests for the SocioCognitiveClassifier logic.
Tests T020 (Training) and T029 (Low Confidence Fallback).
"""
import json
import os
import tempfile
import unittest
from pathlib import Path
import sys
import numpy as np

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from models.classifier import SocioCognitiveClassifier, ClassifierConfig
from models.entities import SocioCognitiveStateType


class TestClassifierLogic(unittest.TestCase):
    """Tests for classifier training and inference logic."""

    def setUp(self):
        """Set up temporary directory and mock training data."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.data_path = Path(self.temp_dir.name) / "training_data.json"

        # Create realistic mock data matching T019 output schema
        mock_data = [
            {
                "turn_text": "I feel very frustrated by this disagreement.",
                "label": SocioCognitiveStateType.HIGH_REACTIVITY.value,
                "trajectory_id": "traj_001"
            },
            {
                "turn_text": "I understand your perspective, let's find common ground.",
                "label": SocioCognitiveStateType.DEEPENING_UNDERSTANDING.value,
                "trajectory_id": "traj_001"
            },
            {
                "turn_text": "This is unacceptable and I am angry.",
                "label": SocioCognitiveStateType.HIGH_REACTIVITY.value,
                "trajectory_id": "traj_002"
            },
            {
                "turn_text": "Let's take a step back and listen.",
                "label": SocioCognitiveStateType.MONITORING.value,
                "trajectory_id": "traj_002"
            },
            {
                "turn_text": "We have different cultural views on this issue.",
                "label": SocioCognitiveStateType.DIVERSE_CULTURAL_IDENTITY.value,
                "trajectory_id": "traj_003"
            },
            {
                "turn_text": "I appreciate your cultural background.",
                "label": SocioCognitiveStateType.DIVERSE_CULTURAL_IDENTITY.value,
                "trajectory_id": "traj_003"
            }
        ]

        with open(self.data_path, 'w') as f:
            json.dump(mock_data, f)

        self.config = ClassifierConfig(
            confidence_threshold=0.5,
            model_path=Path(self.temp_dir.name) / "classifier.pkl"
        )

    def tearDown(self):
        """Clean up temporary directory."""
        self.temp_dir.cleanup()

    def test_classifier_training_creates_model(self):
        """Test that training on valid data creates a model file."""
        classifier = SocioCognitiveClassifier(self.config)
        classifier.train(self.data_path)

        self.assertTrue(self.config.model_path.exists(), "Model file should be created")
        self.assertIsNotNone(classifier.tfidf_vectorizer, "TF-IDF vectorizer should be fitted")
        self.assertIsNotNone(classifier.model, "Logistic Regression model should be fitted")

    def test_classifier_predicts_known_labels(self):
        """Test that classifier predicts correct labels for training-like data."""
        classifier = SocioCognitiveClassifier(self.config)
        classifier.train(self.data_path)

        # Test with data similar to training set
        test_text = "I feel very frustrated"
        state, confidence = classifier.predict(test_text)

        self.assertIsInstance(state, SocioCognitiveStateType)
        self.assertIsInstance(confidence, float)
        self.assertGreaterEqual(confidence, 0.0)
        self.assertLessEqual(confidence, 1.0)
        # Should predict HIGH_REACTIVITY or similar
        self.assertIn(state, [SocioCognitiveStateType.HIGH_REACTIVITY, SocioCognitiveStateType.MONITORING])

    def test_low_confidence_fallback_to_monitoring(self):
        """Test T029: Low confidence triggers MONITORING state fallback."""
        classifier = SocioCognitiveClassifier(self.config)
        classifier.train(self.data_path)

        # Use gibberish or out-of-distribution text to force low confidence
        gibberish_text = "xkcd 9fj2 k2l3 m4n5"
        state, confidence = classifier.predict(gibberish_text)

        # Verify the fallback logic
        self.assertLess(confidence, self.config.confidence_threshold,
                        "Confidence should be below threshold for gibberish")
        self.assertEqual(state, SocioCognitiveStateType.MONITORING,
                         "Low confidence should fallback to MONITORING state")

    def test_classifier_handles_empty_input(self):
        """Test handling of empty string input."""
        classifier = SocioCognitiveClassifier(self.config)
        classifier.train(self.data_path)

        state, confidence = classifier.predict("")
        self.assertEqual(state, SocioCognitiveStateType.MONITORING)

    def test_classifier_config_defaults(self):
        """Test that default config values are sensible."""
        config = ClassifierConfig()
        self.assertEqual(config.confidence_threshold, 0.5)
        self.assertEqual(config.model_path, Path("data/processed/classifier_model.pkl"))


if __name__ == '__main__':
    unittest.main()
