import os
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import torch

logger = logging.getLogger(__name__)

class ClassificationResult:
    def __init__(self, label: str, score: float, timestamp: Optional[datetime] = None):
        self.label = label
        self.score = score
        self.timestamp = timestamp or datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "label": self.label,
            "score": self.score,
            "timestamp": self.timestamp.isoformat()
        }

class FrozenDistilBERTClassifier:
    """
    A wrapper for a frozen DistilBERT model used for intent classification.
    Runs on CPU only.
    """
    def __init__(self, model_name: str = "distilbert-base-uncased", device: str = "cpu"):
        self.model_name = model_name
        self.device = device
        self.model = None
        self.tokenizer = None
        self._load_model()

    def _load_model(self):
        try:
            from transformers import AutoModelForSequenceClassification, AutoTokenizer
            
            logger.info(f"Loading model {self.model_name} on {self.device}...")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            # Load a pre-trained model for sequence classification (binary: leak vs safe)
            # Note: In a real scenario, we would load a fine-tuned checkpoint.
            # Here we assume a generic checkpoint or initialize a head if needed.
            # For the purpose of this pipeline, we simulate a valid load if the model exists.
            self.model = AutoModelForSequenceClassification.from_pretrained(
                self.model_name, 
                num_labels=2
            )
            self.model.to(self.device)
            self.model.eval()
            logger.info("Model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load model: {str(e)}")
            raise

    def predict(self, text: str) -> ClassificationResult:
        if self.model is None:
            raise RuntimeError("Model not loaded.")
        
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, padding=True)
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = self.model(**inputs)
            probabilities = torch.nn.functional.softmax(outputs.logits, dim=-1)
            score, predicted_class = torch.max(probabilities, dim=1)
        
        # Assuming class 0 is "safe" and class 1 is "leak"
        label = "leak" if predicted_class.item() == 1 else "safe"
        score_val = score.item()
        
        return ClassificationResult(label=label, score=score_val)

def run_intent_classification(texts: List[str], classifier: FrozenDistilBERTClassifier) -> List[ClassificationResult]:
    return [classifier.predict(t) for t in texts]

def main():
    # Demo / Test
    classifier = FrozenDistilBERTClassifier()
    result = classifier.predict("This is a test query.")
    print(json.dumps(result.to_dict(), indent=2))

if __name__ == "__main__":
    main()
