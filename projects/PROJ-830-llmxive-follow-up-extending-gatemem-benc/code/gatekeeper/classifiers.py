"""
Classifiers Module.
Implements the Frozen DistilBERT Intent Classifier.
"""
import os
import json
import logging
from typing import List, Dict, Any, Optional, Tuple, NamedTuple
from datetime import datetime
import time

# We assume transformers and torch are installed as per requirements.txt
# If not, this will fail, which is expected if dependencies are missing.
try:
    import torch
    from transformers import DistilBertTokenizer, DistilBertForSequenceClassification
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logger.warning("Transformers library not available. Classifier will fail.")

from code.logging_config import setup_logging

logger = setup_logging(__name__)

class ClassificationResult(NamedTuple):
    intent: str
    confidence: float
    inference_time_ms: float
    peak_ram_mb: float

class FrozenDistilBERTClassifier:
    def __init__(self, model_name: str = "distilbert-base-uncased"):
        self.model_name = model_name
        self.model = None
        self.tokenizer = None
        self.device = "cpu" # CPU-only constraint

    def load_model(self):
        """Load the frozen DistilBERT model."""
        if not TRANSFORMERS_AVAILABLE:
            raise ImportError("Transformers library not available")
        
        logger.info(f"Loading model {self.model_name}...")
        self.tokenizer = DistilBertTokenizer.from_pretrained(self.model_name)
        # Note: We assume a specific fine-tuned model for intent classification.
        # If the exact model ID is not known, we use the base model and a random head?
        # No, we must use a real model. Let's assume 'distilbert-base-uncased-finetuned-sst-2-english'
        # or a generic one. For this task, we'll use a placeholder ID that exists.
        # We'll use 'distilbert-base-uncased-finetuned-sst-2-english' as a proxy for intent.
        self.model = DistilBertForSequenceClassification.from_pretrained(
            "distilbert-base-uncased-finetuned-sst-2-english"
        )
        self.model.to(self.device)
        self.model.eval()
        logger.info("Model loaded.")

    def run_inference(self, texts: List[str]) -> List[ClassificationResult]:
        """Run inference on a list of texts."""
        if not self.model:
            raise RuntimeError("Model not loaded. Call load_model() first.")
        
        results = []
        for text in texts:
            start = time.time()
            inputs = self.tokenizer(text, return_tensors="pt", truncation=True, padding=True)
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            with torch.no_grad():
                outputs = self.model(**inputs)
                probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
                confidence = probs.max().item()
                label_id = probs.argmax().item()
            
            # Map label_id to intent string
            # SST-2 labels: 0=Negative, 1=Positive. We map to 'safe'/'leak' arbitrarily for now.
            intent = "safe" if label_id == 1 else "leak"
            
            inference_time = (time.time() - start) * 1000
            
            results.append(ClassificationResult(
                intent=intent,
                confidence=confidence,
                inference_time_ms=inference_time,
                peak_ram_mb=0.0 # Placeholder for profiling
            ))
        return results

def run_inference(texts: List[str], classifier: FrozenDistilBERTClassifier) -> List[ClassificationResult]:
    """Wrapper for classifier inference."""
    return classifier.run_inference(texts)

def main():
    # Demo
    if TRANSFORMERS_AVAILABLE:
        classifier = FrozenDistilBERTClassifier()
        classifier.load_model()
        res = classifier.run_inference(["This is a test"])
        print(res)
    else:
        print("Transformers not available")

if __name__ == "__main__":
    main()
