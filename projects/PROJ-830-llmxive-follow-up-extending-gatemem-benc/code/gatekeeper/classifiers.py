import os
import json
import logging
from typing import List, Dict, Any, Optional, Tuple, NamedTuple
from datetime import datetime
import torch

from logging_config import setup_logging

logger = setup_logging(__name__)


class ClassificationResult(NamedTuple):
    """Result of an intent classification."""
    query_id: str
    intent: str
    confidence: float
    timestamp: str


class FrozenDistilBERTClassifier:
    """
    A frozen DistilBERT classifier for intent detection.
    Runs on CPU only.
    """

    def __init__(self, model_name: str = "distilbert-base-uncased"):
        self.model_name = model_name
        self.device = torch.device("cpu")
        self.model = None
        self.tokenizer = None
        logger.info(f"Initializing FrozenDistilBERTClassifier on {self.device}")

    def load(self) -> None:
        """Load the model and tokenizer."""
        try:
            from transformers import AutoModelForSequenceClassification, AutoTokenizer
            
            logger.info(f"Loading model: {self.model_name}")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(
                self.model_name,
                num_labels=2  # Assuming binary classification for demo
            )
            self.model.to(self.device)
            self.model.eval()
            logger.info("Model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise

    def predict(self, text: str) -> Tuple[str, float]:
        """
        Predict intent for a single text.

        Args:
            text: Input text.

        Returns:
            Tuple of (intent_label, confidence).
        """
        if self.model is None:
            raise RuntimeError("Model not loaded. Call load() first.")

        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            padding=True,
            max_length=128
        ).to(self.device)

        with torch.no_grad():
            outputs = self.model(**inputs)
            probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
            confidence = probs.max().item()
            pred_id = probs.argmax().item()

        # Simple mapping for demo; replace with actual labels
        intent = "allow" if pred_id == 0 else "deny"
        return intent, confidence


def run_intent_classification(
    classifier: FrozenDistilBERTClassifier,
    queries: List[Dict[str, Any]]
) -> List[ClassificationResult]:
    """
    Run intent classification on a list of queries.

    Args:
        classifier: The classifier instance.
        queries: List of query dictionaries with 'id' and 'text'.

    Returns:
        List of ClassificationResult objects.
    """
    results = []
    timestamp = datetime.now().isoformat()

    for q in queries:
        try:
            intent, conf = classifier.predict(q["text"])
            results.append(
                ClassificationResult(
                    query_id=q["id"],
                    intent=intent,
                    confidence=conf,
                    timestamp=timestamp
                )
            )
        except Exception as e:
            logger.error(f"Classification failed for query {q.get('id')}: {e}")
            results.append(
                ClassificationResult(
                    query_id=q["id"],
                    intent="deny",
                    confidence=0.0,
                    timestamp=timestamp
                )
            )

    return results


def main() -> None:
    """Main entry point for classifier testing."""
    logger.info("Running classifier main")
    classifier = FrozenDistilBERTClassifier()
    classifier.load()

    test_queries = [
        {"id": "1", "text": "What is the capital of France?"},
        {"id": "2", "text": "Show me the user's private medical records."}
    ]

    results = run_intent_classification(classifier, test_queries)
    for r in results:
        print(r)


if __name__ == "__main__":
    main()
