"""
Unit tests for the SocioCognitiveClassifier logic.
Tests cover training, prediction, and configuration handling.
"""
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

import numpy as np
import sys

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from models.classifier import ClassifierConfig, SocioCognitiveClassifier
from models.entities import SocioCognitiveStateType
from config import set_all_seeds


class TestClassifierConfig(unittest.TestCase):
    def test_default_values(self):
        """Test that default configuration values are set correctly."""
        config = ClassifierConfig()
        self.assertEqual(config.test_split_ratio, 0.2)
        self.assertEqual(config.random_seed, 42)
        self.assertIsNotNone(config.model_path)

    def test_custom_values(self):
        """Test custom configuration values."""
        config = ClassifierConfig(test_split_ratio=0.3, random_seed=123)
        self.assertEqual(config.test_split_ratio, 0.3)
        self.assertEqual(config.random_seed, 123)


class TestSocioCognitiveClassifier(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures."""
        set_all_seeds(42)
        self.config = ClassifierConfig()
        
        # Create sample training data
        self.training_data = [
            {
                "turn_text": "I feel frustrated because my cultural norms are being ignored.",
                "label": SocioCognitiveStateType.HIGH_EMOTIONAL_REACTIVITY,
                "trajectory_id": "traj_001",
                "confidence_score": 0.9,
                "threshold_used": 0.7
            },
            {
                "turn_text": "Let's try to understand each other's perspectives.",
                "label": SocioCognitiveStateType.NEUTRAL_MONITORING,
                "trajectory_id": "traj_001",
                "confidence_score": 0.85,
                "threshold_used": 0.7
            },
            {
                "turn_text": "I don't see why this is a problem. We should just move on.",
                "label": SocioCognitiveStateType.LOW_EMOTIONAL_REACTIVITY,
                "trajectory_id": "traj_002",
                "confidence_score": 0.95,
                "threshold_used": 0.7
            },
            {
                "turn_text": "This is exactly what I was afraid of. The cultural context is completely missing!",
                "label": SocioCognitiveStateType.HIGH_EMOTIONAL_REACTIVITY,
                "trajectory_id": "traj_003",
                "confidence_score": 0.88,
                "threshold_used": 0.7
            },
            {
                "turn_text": "I'm willing to listen and find common ground.",
                "label": SocioCognitiveStateType.NEUTRAL_MONITORING,
                "trajectory_id": "traj_003",
                "confidence_score": 0.82,
                "threshold_used": 0.7
            }
        ]

    def test_training_creates_model(self):
        """Test that training creates a valid model."""
        classifier = SocioCognitiveClassifier(self.config)
        classifier.train(self.training_data)
        
        # Verify model attributes are set
        self.assertIsNotNone(classifier.vectorizer)
        self.assertIsNotNone(classifier.model)
        self.assertTrue(hasattr(classifier, 'classes_'))
        self.assertEqual(len(classifier.classes_), 3)  # HIGH_EMOTIONAL, LOW_EMOTIONAL, NEUTRAL

    def test_prediction_returns_valid_labels(self):
        """Test that predictions return valid SocioCognitiveStateType values."""
        classifier = SocioCognitiveClassifier(self.config)
        classifier.train(self.training_data)
        
        test_samples = [
            "I am very angry about this situation.",
            "This is fine, no problem.",
            "Let's discuss this calmly."
        ]
        
        predictions = classifier.predict(test_samples)
        
        self.assertEqual(len(predictions), len(test_samples))
        for pred in predictions:
            self.assertIn(pred, [e.value for e in SocioCognitiveStateType])

    def test_prediction_returns_confidence_scores(self):
        """Test that prediction returns confidence scores."""
        classifier = SocioCognitiveClassifier(self.config)
        classifier.train(self.training_data)
        
        test_samples = ["I feel very emotional about this."]
        
        # Test predict_proba if available (sklearn models usually have it)
        try:
            probas = classifier.model.predict_proba(classifier.vectorizer.transform(test_samples))
            self.assertEqual(len(probas), 1)
            self.assertAlmostEqual(sum(probas[0]), 1.0, places=5)
        except AttributeError:
            # If predict_proba is not available, that's okay for some model types
            self.skipTest("Model does not support probability prediction")

    def test_save_and_load_model(self):
        """Test that model can be saved and loaded correctly."""
        classifier = SocioCognitiveClassifier(self.config)
        classifier.train(self.training_data)
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            model_path = Path(tmp_dir) / "test_classifier.pkl"
            
            # Save
            classifier.save(model_path)
            self.assertTrue(model_path.exists())
            
            # Load
            loaded_classifier = SocioCognitiveClassifier.load(model_path)
            
            # Verify loaded model works
            test_sample = ["Test prediction"]
            original_pred = classifier.predict(test_sample)[0]
            loaded_pred = loaded_classifier.predict(test_sample)[0]
            
            self.assertEqual(original_pred, loaded_pred)

    def test_empty_training_data(self):
        """Test that training with empty data raises an error."""
        classifier = SocioCognitiveClassifier(self.config)
        
        with self.assertRaises(ValueError):
            classifier.train([])

    def test_malformed_training_data(self):
        """Test that training with missing required fields raises an error."""
        malformed_data = [
            {
                "turn_text": "Some text",
                # Missing "label" field
                "trajectory_id": "traj_001"
            }
        ]
        
        classifier = SocioCognitiveClassifier(self.config)
        
        with self.assertRaises(ValueError):
            classifier.train(malformed_data)

    def test_single_class_training(self):
        """Test training with only one class present."""
        single_class_data = [
            {
                "turn_text": "Text 1",
                "label": SocioCognitiveStateType.NEUTRAL_MONITORING,
                "trajectory_id": "traj_001",
                "confidence_score": 0.9,
                "threshold_used": 0.7
            },
            {
                "turn_text": "Text 2",
                "label": SocioCognitiveStateType.NEUTRAL_MONITORING,
                "trajectory_id": "traj_001",
                "confidence_score": 0.85,
                "threshold_used": 0.7
            }
        ]
        
        classifier = SocioCognitiveClassifier(self.config)
        # This should not crash, but might warn about single class
        classifier.train(single_class_data)
        self.assertIsNotNone(classifier.model)

    def test_prediction_consistency(self):
        """Test that predictions are consistent with the same seed."""
        set_all_seeds(42)
        classifier1 = SocioCognitiveClassifier(self.config)
        classifier1.train(self.training_data)
        
        set_all_seeds(42)
        classifier2 = SocioCognitiveClassifier(self.config)
        classifier2.train(self.training_data)
        
        test_sample = ["Consistent prediction test"]
        pred1 = classifier1.predict(test_sample)[0]
        pred2 = classifier2.predict(test_sample)[0]
        
        self.assertEqual(pred1, pred2)

    def test_load_from_checkpoint(self):
        """Test loading a classifier from a checkpoint file."""
        classifier = SocioCognitiveClassifier(self.config)
        classifier.train(self.training_data)
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            model_path = Path(tmp_dir) / "checkpoint.pkl"
            classifier.save(model_path)
            
            # Load using the class method
            loaded = SocioCognitiveClassifier.load(model_path)
            
            # Verify it's the correct type
            self.assertIsInstance(loaded, SocioCognitiveClassifier)
            self.assertIsNotNone(loaded.model)
            self.assertIsNotNone(loaded.vectorizer)


if __name__ == "__main__":
    unittest.main()
