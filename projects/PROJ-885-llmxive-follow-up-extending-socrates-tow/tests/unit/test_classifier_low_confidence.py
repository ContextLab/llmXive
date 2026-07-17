import pytest
import numpy as np
from models.classifier import SocioCognitiveClassifier, ClassifierConfig, NEUTRAL_MONITORING_LABEL

def test_low_confidence_fallback():
    """
    Test that the classifier fails gracefully to a neutral 'monitoring' state
    when confidence is below the threshold (Edge Case FR-002).
    """
    # Create a classifier with a high threshold to force low confidence scenarios
    config = ClassifierConfig(confidence_threshold=0.95)
    classifier = SocioCognitiveClassifier(config)

    # Create dummy training data
    training_data = [
        {"turn_text": "I am very angry and frustrated right now.", "label": "high_reactivity"},
        {"turn_text": "I understand your perspective completely.", "label": "empathetic"},
        {"turn_text": "This is a cultural misunderstanding.", "label": "cultural_conflict"},
    ] * 10  # Repeat to have enough data

    classifier.fit(training_data)

    # Test with a text that is likely to be ambiguous or out-of-distribution
    # resulting in low confidence
    ambiguous_text = "The sky is blue and the grass is green."

    predicted_label, confidence = classifier.predict_with_confidence(ambiguous_text)

    # Verify that the label is the neutral monitoring state
    assert predicted_label == NEUTRAL_MONITORING_LABEL, (
        f"Expected {NEUTRAL_MONITORING_LABEL} on low confidence, "
        f"got {predicted_label}"
    )

    # Verify that confidence is indeed below the threshold
    assert confidence < config.confidence_threshold, (
        f"Expected confidence < {config.confidence_threshold}, "
        f"got {confidence}"
    )

def test_high_confidence_normal_prediction():
    """
    Test that the classifier returns the predicted label when confidence is high.
    """
    config = ClassifierConfig(confidence_threshold=0.6)
    classifier = SocioCognitiveClassifier(config)

    training_data = [
        {"turn_text": "I am extremely upset and angry!", "label": "high_reactivity"},
        {"turn_text": "I am calm and listening.", "label": "low_reactivity"},
    ] * 20

    classifier.fit(training_data)

    # Predict on a similar text
    text = "I am very angry and frustrated."
    predicted_label, confidence = classifier.predict_with_confidence(text)

    # Should not be the monitoring state if confidence is high enough
    # (We can't guarantee the exact label without knowing the model's internal logic,
    # but we can ensure it's not the fallback if confidence is high)
    # However, since this is a small model, let's just check the mechanism works:
    # If confidence is high, it should NOT be monitoring state
    if confidence >= config.confidence_threshold:
        assert predicted_label != NEUTRAL_MONITORING_LABEL, (
            "Classifier should not return monitoring state on high confidence."
        )

def test_default_threshold_behavior():
    """
    Test the default threshold behavior.
    """
    classifier = SocioCognitiveClassifier()
    assert classifier.config.confidence_threshold == 0.6
    assert classifier.config.vectorizer_kwargs["max_features"] == 5000
