import os
import json
import logging
from typing import List, Dict, Any, Optional, Tuple, NamedTuple
from datetime import datetime
import torch

logger = logging.getLogger(__name__)

class ClassificationResult(NamedTuple):
    label: str
    score: float
    timestamp: str

class FrozenDistilBERTClassifier:
    def __init__(self, model_name: str = "distilbert-base-uncased", device: str = "cpu"):
        self.model_name = model_name
        self.device = device
        self.model = None
        self.tokenizer = None
        self._load_model()
    
    def _load_model(self):
        """Load the frozen DistilBERT model (CPU-only)."""
        try:
            from transformers import AutoTokenizer, AutoModelForSequenceClassification
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
            self.model.to(self.device)
            self.model.eval()
            logger.info(f"Model loaded: {self.model_name} on {self.device}")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise

    def predict(self, text: str) -> Dict[str, Any]:
        """Predict intent for a single text."""
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, padding=True)
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = self.model(**inputs)
            probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
        
        label_ids = torch.argmax(probs, dim=-1).item()
        score = probs[0, label_ids].item()
        
        return {
            "label": str(label_ids),
            "score": score,
            "probs": probs[0].tolist()
        }

def run_intent_classification(text: str) -> Dict[str, Any]:
    """Wrapper for intent classification."""
    classifier = FrozenDistilBERTClassifier()
    return classifier.predict(text)

def main():
    """Test classifier."""
    logger.info("Testing classifier...")
    result = run_intent_classification("What is the patient's name?")
    logger.info(f"Classification result: {result}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
