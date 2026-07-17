"""
Unit tests for the Socio-Cognitive State Classifier.
"""

import json
import tempfile
from pathlib import Path

import pytest
import numpy as np

# Add parent to path for imports
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from code.models.classifier import (
    SocioCognitiveClassifier,
    ClassifierConfig
)


@pytest.fixture
def sample_training_data():
    """Generate sample training data for testing."""
    return [
        {
            "turn_text": "I understand your perspective, but I think we need to consider other factors.",
            "label": "empathetic_validation",
            "trajectory_id": "traj_001"
        },
        {
            "turn_text": "That's completely wrong! You're not listening to me at all!",
            "label": "aggressive_confrontation",
            "trajectory_id": "traj_001"
        },
        {
            "turn_text": "Let me try to summarize what I heard you say to make sure I understand.",
            "label": "active_listening",
            "trajectory_id": "traj_002"
        },
        {
            "turn_text": "I feel frustrated when my ideas are dismissed without consideration.",
            "label": "emotional_expression",
            "trajectory_id": "traj_002"
        },
        {
            "turn_text": "Perhaps we could find a middle ground that addresses both our concerns.",
            "label": "collaborative_problem_solving",
            "trajectory_id": "traj_003"
        },
        {
            "turn_text": "I don't care what you think. My way is the only way.",
            "label": "aggressive_confrontation",
            "trajectory_id": "traj_003"
        },
        {
            "turn_text": "Thank you for sharing that. It helps me understand your position better.",
            "label": "empathetic_validation",
            "trajectory_id": "traj_004"
        },
        {
            "turn_text": "I see your point, but I'm not sure I agree with your conclusion.",
            "label": "respectful_disagreement",
            "trajectory_id": "traj_004"
        },
        {
            "turn_text": "Can you explain more about why you feel that way?",
            "label": "active_listening",
            "trajectory_id": "traj_005"
        },
        {
            "turn_text": "This is getting nowhere. We're just going in circles.",
            "label": "frustration_escalation",
            "trajectory_id": "traj_005"
        },
        {
            "turn_text": "Let's take a step back and reconsider our approach.",
            "label": "collaborative_problem_solving",
            "trajectory_id": "traj_006"
        },
        {
            "turn_text": "I appreciate your patience as we work through this.",
            "label": "empathetic_validation",
            "trajectory_id": "traj_006"
        },
        {
            "turn_text": "You're being unreasonable and refusing to see the facts.",
            "label": "aggressive_confrontation",
            "trajectory_id": "traj_007"
        },
        {
            "turn_text": "I hear that you're concerned about the timeline.",
            "label": "active_listening",
            "trajectory_id": "traj_007"
        },
        {
            "turn_text": "My feelings are hurt by how this was handled.",
            "label": "emotional_expression",
            "trajectory_id": "traj_008"
        },
        {
            "turn_text": "We should explore all options before making a decision.",
            "label": "collaborative_problem_solving",
            "trajectory_id": "traj_008"
        },
        {
            "turn_text": "I disagree with your assessment of the situation.",
            "label": "respectful_disagreement",
            "trajectory_id": "traj_009"
        },
        {
            "turn_text": "This conversation is making me angry.",
            "label": "emotional_expression",
            "trajectory_id": "traj_009"
        },
        {
            "turn_text": "I think we're missing an important perspective here.",
            "label": "respectful_disagreement",
            "trajectory_id": "traj_010"
        },
        {
            "turn_text": "Let's pause and take a breath before continuing.",
            "label": "de_escalation",
            "trajectory_id": "traj_010"
        },
    ]


@pytest.fixture
def temp_training_file(sample_training_data):
    """Create a temporary file with training data."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(sample_training_data, f)
        temp_path = f.name
    yield temp_path
    Path(temp_path).unlink()


def test_classifier_initialization():
    """Test that classifier initializes correctly."""
    classifier = SocioCognitiveClassifier()
    assert classifier.model is None
    assert classifier.vectorizer is None
    assert not classifier.is_trained
    assert classifier.labels_ is None


def test_classifier_config_defaults():
    """Test default configuration values."""
    config = ClassifierConfig()
    assert config.test_size == 0.2
    assert config.random_state == 42
    assert config.max_features == 5000
    assert config.ngram_range == (1, 2)
    assert config.max_iter == 1000
    assert config.solver == 'lbfgs'
    assert config.confidence_threshold == 0.75


def test_classifier_config_custom():
    """Test custom configuration values."""
    config = ClassifierConfig(
        test_size=0.3,
        random_state=123,
        max_features=1000,
        confidence_threshold=0.85
    )
    assert config.test_size == 0.3
    assert config.random_state == 123
    assert config.max_features == 1000
    assert config.confidence_threshold == 0.85


def test_load_training_data_valid(temp_training_file, sample_training_data):
    """Test loading valid training data."""
    classifier = SocioCognitiveClassifier()
    data = classifier.load_training_data(temp_training_file)

    assert len(data) == len(sample_training_data)
    assert all('turn_text' in item for item in data)
    assert all('label' in item for item in data)
    assert all('trajectory_id' in item for item in data)


def test_load_training_data_missing_file():
    """Test loading from non-existent file raises error."""
    classifier = SocioCognitiveClassifier()
    with pytest.raises(FileNotFoundError):
        classifier.load_training_data('/nonexistent/path/data.json')


def test_load_training_data_empty_list():
    """Test loading empty data raises error."""
    classifier = SocioCognitiveClassifier()
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump([], f)
        temp_path = f.name

    try:
        with pytest.raises(ValueError, match="Training data is empty"):
            classifier.load_training_data(temp_path)
    finally:
        Path(temp_path).unlink()


def test_load_training_data_invalid_schema():
    """Test loading data with missing keys raises error."""
    classifier = SocioCognitiveClassifier()
    invalid_data = [{"turn_text": "test"}]  # Missing label and trajectory_id

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(invalid_data, f)
        temp_path = f.name

    try:
        with pytest.raises(ValueError, match="missing required keys"):
            classifier.load_training_data(temp_path)
    finally:
        Path(temp_path).unlink()


def test_fit_and_predict(temp_training_file):
    """Test full training and prediction pipeline."""
    classifier = SocioCognitiveClassifier()

    # Load and train
    training_data = classifier.load_training_data(temp_training_file)
    metrics = classifier.fit(training_data)

    assert classifier.is_trained
    assert classifier.model is not None
    assert classifier.vectorizer is not None
    assert classifier.labels_ is not None
    assert len(classifier.labels_) > 1

    # Check metrics
    assert 'accuracy' in metrics
    assert 'classification_report' in metrics
    assert metrics['train_size'] + metrics['test_size'] == len(training_data)

    # Predict
    test_texts = [
        "I understand your concerns and want to work together.",
        "This is completely unacceptable!"
    ]
    predictions = classifier.predict(test_texts)

    assert len(predictions) == 2
    for pred in predictions:
        assert 'predicted_label' in pred
        assert 'confidence' in pred
        assert 'is_confident' in pred
        assert 0 <= pred['confidence'] <= 1


def test_predict_untrained_raises_error():
    """Test predicting without training raises error."""
    classifier = SocioCognitiveClassifier()

    with pytest.raises(RuntimeError, match="not trained"):
        classifier.predict(["test text"])


def test_predict_with_fallback(temp_training_file):
    """Test prediction with fallback to neutral monitoring."""
    classifier = SocioCognitiveClassifier(
        config=ClassifierConfig(confidence_threshold=0.99)  # High threshold to trigger fallback
    )

    training_data = classifier.load_training_data(temp_training_file)
    classifier.fit(training_data)

    # Predict with high threshold should trigger fallback
    predictions = classifier.predict_with_fallback(["random text"])

    assert len(predictions) == 1
    assert 'fallback_used' in predictions[0]
    if not predictions[0]['is_confident']:
        assert predictions[0]['predicted_label'] == 'neutral_monitoring'
        assert predictions[0]['fallback_used'] is True


def test_save_and_load(temp_training_file):
    """Test saving and loading a trained classifier."""
    classifier = SocioCognitiveClassifier()

    training_data = classifier.load_training_data(temp_training_file)
    classifier.fit(training_data)

    with tempfile.NamedTemporaryFile(suffix='.pkl', delete=False) as f:
        temp_model_path = f.name

    try:
        # Save
        classifier.save(temp_model_path)
        assert Path(temp_model_path).exists()

        # Load
        loaded_classifier = SocioCognitiveClassifier.load(temp_model_path)

        assert loaded_classifier.is_trained
        assert loaded_classifier.labels_ == classifier.labels_

        # Verify predictions match
        test_text = "I understand your perspective."
        original_pred = classifier.predict([test_text])[0]
        loaded_pred = loaded_classifier.predict([test_text])[0]

        assert original_pred['predicted_label'] == loaded_pred['predicted_label']
        assert abs(original_pred['confidence'] - loaded_pred['confidence']) < 1e-6

    finally:
        Path(temp_model_path).unlink()


def test_save_untrained_raises_error():
    """Test saving untrained classifier raises error."""
    classifier = SocioCognitiveClassifier()

    with tempfile.NamedTemporaryFile(suffix='.pkl', delete=False) as f:
        temp_path = f.name

    try:
        with pytest.raises(RuntimeError, match="untrained"):
            classifier.save(temp_path)
    finally:
        Path(temp_path).unlink()


def test_load_nonexistent_model():
    """Test loading non-existent model raises error."""
    with pytest.raises(FileNotFoundError):
        SocioCognitiveClassifier.load('/nonexistent/model.pkl')


def test_single_text_prediction(temp_training_file):
    """Test predicting on single string (not list)."""
    classifier = SocioCognitiveClassifier()

    training_data = classifier.load_training_data(temp_training_file)
    classifier.fit(training_data)

    # Single string input
    prediction = classifier.predict("I feel frustrated with this situation.")

    assert len(prediction) == 1
    assert isinstance(prediction[0]['predicted_label'], str)


def test_classification_report_structure(temp_training_file):
    """Test that classification report has expected structure."""
    classifier = SocioCognitiveClassifier()

    training_data = classifier.load_training_data(temp_training_file)
    metrics = classifier.fit(training_data)

    report = metrics['classification_report']

    # Check that report contains class metrics
    assert isinstance(report, dict)
    # Should have at least one class
    assert any(k not in ['accuracy', 'macro avg', 'weighted avg'] for k in report.keys())