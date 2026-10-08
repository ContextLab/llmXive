"""
Unit tests for the SocioCognitiveClassifier.
"""
import json
import os
import tempfile
from pathlib import Path
import pytest

# Adjust imports for the test environment
try:
    from code.models.classifier import ClassifierConfig, SocioCognitiveClassifier
    from code.models.entities import SocioCognitiveStateType
except ImportError:
    # Fallback if run directly without path setup
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from models.classifier import ClassifierConfig, SocioCognitiveClassifier


class TestClassifierTraining:
    """Tests for the training pipeline."""

    @pytest.fixture
    def sample_training_data(self):
        """Generate a small, valid training dataset in a temporary file."""
        data = [
            {
                "turn_text": "I feel really frustrated with this situation.",
                "label": "high_reactivity",
                "trajectory_id": "traj_001",
                "confidence_score": 0.95,
                "threshold_used": 0.80
            },
            {
                "turn_text": "Let's try to understand each other's perspective.",
                "label": "neutral",
                "trajectory_id": "traj_001",
                "confidence_score": 0.88,
                "threshold_used": 0.80
            },
            {
                "turn_text": "This is not how we do things in my culture.",
                "label": "cultural_friction",
                "trajectory_id": "traj_002",
                "confidence_score": 0.92,
                "threshold_used": 0.80
            },
            {
                "turn_text": "I agree, we need to find a common ground.",
                "label": "neutral",
                "trajectory_id": "traj_002",
                "confidence_score": 0.85,
                "threshold_used": 0.80
            },
            {
                "turn_text": "You are completely ignoring my feelings!",
                "label": "high_reactivity",
                "trajectory_id": "traj_003",
                "confidence_score": 0.98,
                "threshold_used": 0.80
            }
        ]
        return data

    def test_classifier_predicts_correct_label(self, sample_training_data):
        """
        T043A Requirement: test_classifier_predicts_correct_label
        Verifies the classifier learns from the training data and predicts
        the correct label for known examples.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            data_path = Path(tmpdir) / "training_data.json"
            with open(data_path, 'w') as f:
                json.dump(sample_training_data, f)

            config = ClassifierConfig(random_seed=42, test_size=0.0) # No split for deterministic check
            classifier = SocioCognitiveClassifier(config)
            classifier.fit(data_path)

            # Test prediction on a known sample
            predictions = classifier.predict(["I feel really frustrated with this situation."])
            assert len(predictions) == 1
            label, score = predictions[0]
            assert label == "high_reactivity"
            assert score > 0.5

    def test_classifier_handles_low_confidence(self, sample_training_data):
        """
        T043A Requirement: test_classifier_handles_low_confidence
        Verifies that the classifier returns a probability score that can be
        used to detect low confidence (e.g., < threshold).
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            data_path = Path(tmpdir) / "training_data.json"
            with open(data_path, 'w') as f:
                json.dump(sample_training_data, f)

            config = ClassifierConfig(random_seed=42, test_size=0.2)
            classifier = SocioCognitiveClassifier(config)
            classifier.fit(data_path)

            # Predict on ambiguous text not in training set
            ambiguous_text = "Maybe we should talk about it later."
            predictions = classifier.predict([ambiguous_text])
            label, score = predictions[0]

            # The score should be a valid float between 0 and 1
            assert 0.0 <= score <= 1.0
            # We don't assert a specific label here as it's out-of-distribution,
            # but we verify the mechanism works.

    def test_classifier_independence_from_evaluator(self, sample_training_data):
        """
        T043A Requirement: test_classifier_independence_from_evaluator
        Verifies that the classifier training process does not crash or fail
        due to missing evaluator logic, ensuring strict separation.
        The classifier should only depend on 'turn_text' and 'label'.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            data_path = Path(tmpdir) / "training_data.json"
            with open(data_path, 'w') as f:
                json.dump(sample_training_data, f)

            config = ClassifierConfig(random_seed=42, test_size=0.2)
            classifier = SocioCognitiveClassifier(config)
            
            # This should run without importing or using any evaluator modules
            summary = classifier.fit(data_path)
            
            assert summary is not None
            assert "accuracy" in summary
            assert "classes" in summary
            # Verify no evaluator-specific keys are present or required
            assert "evaluator_metrics" not in summary

    def test_classifier_save_and_load(self, sample_training_data):
        """Tests model serialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data_path = Path(tmpdir) / "training_data.json"
            model_path = Path(tmpdir) / "model.pkl"
            
            with open(data_path, 'w') as f:
                json.dump(sample_training_data, f)

            config = ClassifierConfig(random_seed=42, test_size=0.0)
            classifier = SocioCognitiveClassifier(config)
            classifier.fit(data_path)
            classifier.save(model_path)

            # Load and predict
            loaded_classifier = SocioCognitiveClassifier.load(model_path)
            predictions = loaded_classifier.predict(["I feel really frustrated with this situation."])
            assert predictions[0][0] == "high_reactivity"

    def test_classifier_validation_errors(self):
        """Tests error handling for invalid input data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data_path = Path(tmpdir) / "bad_data.json"
            
            # Missing required key
            bad_data = [{"turn_text": "hello"}]
            with open(data_path, 'w') as f:
                json.dump(bad_data, f)

            config = ClassifierConfig()
            classifier = SocioCognitiveClassifier(config)
            
            with pytest.raises(ValueError):
                classifier.fit(data_path)

            # Empty data
            empty_path = Path(tmpdir) / "empty.json"
            with open(empty_path, 'w') as f:
                json.dump([], f)
            
            with pytest.raises(ValueError):
                classifier.fit(empty_path)