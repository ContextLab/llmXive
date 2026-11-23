import json
import logging
import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder

from config import ensure_directories, get_config_summary

logger = logging.getLogger(__name__)

# Constants for confidence handling (Edge Case FR-002)
DEFAULT_CONFIDENCE_THRESHOLD = 0.6
NEUTRAL_MONITORING_LABEL = "monitoring_state"

class ClassifierConfig:
    """Configuration for the SocioCognitiveClassifier."""

    def __init__(
        self,
        confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
        vectorizer_kwargs: Optional[Dict[str, Any]] = None,
        classifier_kwargs: Optional[Dict[str, Any]] = None,
    ):
        self.confidence_threshold = confidence_threshold
        self.vectorizer_kwargs = vectorizer_kwargs or {
            "max_features": 5000,
            "ngram_range": (1, 2),
            "stop_words": "english",
        }
        self.classifier_kwargs = classifier_kwargs or {
            "max_iter": 1000,
            "solver": "lbfgs",
            "n_jobs": -1,
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "confidence_threshold": self.confidence_threshold,
            "vectorizer_kwargs": self.vectorizer_kwargs,
            "classifier_kwargs": self.classifier_kwargs,
        }

class SocioCognitiveClassifier:
    """
    Lightweight logistic regression classifier for socio-cognitive state inference.

    Implements FR-002: Trained on turn-level dialogue text.
    Implements Edge Case FR-002: Fails gracefully to a neutral "monitoring" state
    on low confidence predictions.
    """

    def __init__(self, config: Optional[ClassifierConfig] = None):
        self.config = config or ClassifierConfig()
        self.pipeline: Optional[Pipeline] = None
        self.label_encoder: Optional[LabelEncoder] = None
        self.is_fitted = False
        self.training_samples = 0

    def fit(self, training_data: List[Dict[str, Any]]) -> "SocioCognitiveClassifier":
        """
        Train the classifier on turn-level dialogue data.

        Args:
            training_data: List of dicts with keys 'turn_text' and 'label'.

        Returns:
            Self for chaining.
        """
        if not training_data:
            raise ValueError("Training data cannot be empty.")

        texts = [item["turn_text"] for item in training_data]
        labels = [item["label"] for item in training_data]

        # Initialize and fit LabelEncoder
        self.label_encoder = LabelEncoder()
        encoded_labels = self.label_encoder.fit_transform(labels)

        # Initialize and fit Pipeline (TF-IDF + Logistic Regression)
        self.pipeline = Pipeline(
            [
                ("tfidf", TfidfVectorizer(**self.config.vectorizer_kwargs)),
                ("clf", LogisticRegression(**self.config.classifier_kwargs)),
            ]
        )

        self.pipeline.fit(texts, encoded_labels)
        self.is_fitted = True
        self.training_samples = len(texts)

        logger.info(
            f"Classifier trained on {self.training_samples} samples. "
            f"Classes: {list(self.label_encoder.classes_)}"
        )
        return self

    def predict_with_confidence(
        self, text: str
    ) -> Tuple[Optional[str], float]:
        """
        Predict the socio-cognitive state for a given text.

        Implements Edge Case FR-002: If confidence < threshold, returns
        the neutral "monitoring_state" label instead of the low-confidence prediction.

        Args:
            text: The dialogue turn text.

        Returns:
            Tuple of (predicted_label, confidence_score).
            If confidence is low, predicted_label is "monitoring_state".
        """
        if not self.is_fitted:
            raise RuntimeError("Classifier has not been fitted yet.")

        # Get probability distribution
        proba = self.pipeline.predict_proba([text])[0]
        max_prob = float(np.max(proba))
        predicted_idx = int(np.argmax(proba))

        # Decode the label
        predicted_label = self.label_encoder.inverse_transform([predicted_idx])[0]

        # Edge Case FR-002: Graceful failure to neutral state
        if max_prob < self.config.confidence_threshold:
            logger.debug(
                f"Low confidence ({max_prob:.3f}) for input text. "
                f"Falling back to neutral 'monitoring_state'."
            )
            return NEUTRAL_MONITORING_LABEL, max_prob

        return predicted_label, max_prob

    def predict(self, text: str) -> Optional[str]:
        """
        Simple prediction wrapper (returns label or None if low confidence).
        """
        label, _ = self.predict_with_confidence(text)
        return label

    def save(self, path: Union[str, Path]) -> None:
        """Save the classifier and config to disk."""
        path = Path(path)
        ensure_directories(path)
        data = {
            "pipeline": self.pipeline,
            "label_encoder": self.label_encoder,
            "config": self.config,
            "is_fitted": self.is_fitted,
            "training_samples": self.training_samples,
        }
        with open(path, "wb") as f:
            pickle.dump(data, f)
        logger.info(f"Classifier saved to {path}")

    @classmethod
    def load(cls, path: Union[str, Path]) -> "SocioCognitiveClassifier":
        """Load a classifier from disk."""
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Classifier file not found: {path}")

        with open(path, "rb") as f:
            data = pickle.load(f)

        instance = cls(config=data["config"])
        instance.pipeline = data["pipeline"]
        instance.label_encoder = data["label_encoder"]
        instance.is_fitted = data["is_fitted"]
        instance.training_samples = data["training_samples"]
        return instance

def main() -> None:
    """
    Main entry point for training the classifier from generated data.
    Expects data/processed/classifier_training_data.json to exist.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    config = get_config_summary()
    data_path = Path(config["data_processed"]) / "classifier_training_data.json"
    model_path = Path(config["data_processed"]) / "classifier.pkl"

    logger.info(f"Loading training data from {data_path}")
    if not data_path.exists():
        raise FileNotFoundError(
            f"Training data not found at {data_path}. "
            "Please run the generator first (Task T019)."
        )

    with open(data_path, "r", encoding="utf-8") as f:
        training_data = json.load(f)

    logger.info(f"Loaded {len(training_data)} training samples.")

    classifier = SocioCognitiveClassifier()
    classifier.fit(training_data)
    classifier.save(model_path)

    # Quick validation: test a sample
    if training_data:
        sample_text = training_data[0]["turn_text"]
        label, conf = classifier.predict_with_confidence(sample_text)
        logger.info(
            f"Sample prediction: '{sample_text[:50]}...' -> {label} (conf: {conf:.3f})"
        )

if __name__ == "__main__":
    main()
