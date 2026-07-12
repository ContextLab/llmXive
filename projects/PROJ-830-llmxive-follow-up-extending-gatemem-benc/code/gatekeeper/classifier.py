"""
Frozen DistilBERT Intent Classifier for GateMem Gatekeeper.

This module implements a CPU-only intent classifier using a frozen DistilBERT model.
It is designed to classify user queries into intents (e.g., 'access', 'delete', 'info')
to assist the gatekeeper in enforcing access policies.

Constraints:
- CPU-only execution (no GPU tensors).
- Frozen weights (no fine-tuning).
- Default precision (float32).
"""
import os
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from dataclasses import dataclass

# Import logging setup from project root
from logging_config import setup_logging, pin_random_seed

# Configure logger
logger = logging.getLogger(__name__)

# Constants
MODEL_NAME = "distilbert-base-uncased"
# Mapping for standard intent classification labels if not provided by a specific fine-tuned model
# In a real scenario, we might load a specific fine-tuned model. 
# For this task, we assume a generic classification setup or a specific path if provided.
# We will use a standard setup that loads the base model and ensures it is frozen.
# If a specific intent model is needed, it would be loaded here.
# For the purpose of the GateMem pipeline, we assume a label set: ['access', 'delete', 'other']
DEFAULT_LABELS = ["access", "delete", "other"]

@dataclass
class ClassificationResult:
    text: str
    intent: str
    confidence: float
    all_scores: Dict[str, float]

class FrozenDistilBERTClassifier:
    """
    A wrapper around a frozen DistilBERT model for intent classification.
    Ensures CPU-only operation and frozen weights.
    """
    
    def __init__(
        self, 
        model_name: str = MODEL_NAME, 
        labels: Optional[List[str]] = None,
        device: str = "cpu"
    ):
        """
        Initialize the classifier.
        
        Args:
            model_name: HuggingFace model identifier.
            labels: List of intent labels. Defaults to DEFAULT_LABELS.
            device: Device to run inference on. Must be 'cpu'.
        """
        if device != "cpu":
            raise ValueError("FrozenDistilBERTClassifier is CPU-only. Please set device='cpu'.")
        
        self.device = device
        self.labels = labels or DEFAULT_LABELS
        self.model_name = model_name
        self.model = None
        self.tokenizer = None
        self.is_loaded = False

    def load(self) -> None:
        """
        Load the tokenizer and model. Ensures weights are frozen and on CPU.
        """
        if self.is_loaded:
            return

        logger.info(f"Loading tokenizer and model: {self.model_name} on {self.device}")
        
        # Pin random seed for reproducibility
        pin_random_seed()

        try:
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            
            # Load model
            # We use AutoModelForSequenceClassification. 
            # If the model is not specifically fine-tuned for our labels, 
            # this will initialize a new classification head.
            # For a "frozen" classifier in a research context, we might load a pre-trained
            # one if available, or freeze the backbone here.
            self.model = AutoModelForSequenceClassification.from_pretrained(
                self.model_name,
                num_labels=len(self.labels)
            )
            
            # Ensure model is on CPU
            self.model.to(self.device)
            
            # Verify no GPU tensors
            if torch.cuda.is_available():
                for param in self.model.parameters():
                    if param.is_cuda:
                        raise RuntimeError("GPU tensor detected in model despite CPU request.")
            
            # Freeze all parameters
            for param in self.model.parameters():
                param.requires_grad = False
            
            self.model.eval()
            self.is_loaded = True
            logger.info("Model loaded, frozen, and set to eval mode.")
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise

    def classify(self, text: str) -> ClassificationResult:
        """
        Classify a single text string into an intent.
        
        Args:
            text: The input query text.
            
        Returns:
            ClassificationResult object.
        """
        if not self.is_loaded:
            self.load()

        # Tokenize
        inputs = self.tokenizer(
            text, 
            return_tensors="pt", 
            truncation=True, 
            padding=True, 
            max_length=512
        )
        
        # Move inputs to device (CPU)
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = self.model(**inputs)
            logits = outputs.logits
            probs = torch.softmax(logits, dim=-1)

        # Get results
        probs = probs.squeeze(0).cpu().numpy()
        max_idx = int(torch.argmax(logits, dim=-1).cpu().numpy())
        
        intent = self.labels[max_idx]
        confidence = float(probs[max_idx])
        
        all_scores = {label: float(probs[i]) for i, label in enumerate(self.labels)}

        return ClassificationResult(
            text=text,
            intent=intent,
            confidence=confidence,
            all_scores=all_scores
        )

    def classify_batch(self, texts: List[str]) -> List[ClassificationResult]:
        """
        Classify a batch of text strings.
        
        Args:
            texts: List of input query texts.
            
        Returns:
            List of ClassificationResult objects.
        """
        return [selfclassify(t) for t in texts]

def run_intent_classification(
    query_text: str, 
    labels: Optional[List[str]] = None,
    model_name: str = MODEL_NAME
) -> Dict[str, Any]:
    """
    Convenience function to run classification on a single query.
    
    Args:
        query_text: The query string.
        labels: Optional list of labels.
        model_name: Optional model name.
        
    Returns:
        Dictionary with intent, confidence, and scores.
    """
    classifier = FrozenDistilBERTClassifier(model_name=model_name, labels=labels)
    result = classifier.classify(query_text)
    
    return {
        "text": result.text,
        "intent": result.intent,
        "confidence": result.confidence,
        "all_scores": result.all_scores
    }

def main():
    """
    Main entry point for testing the classifier.
    Reads a sample query (or uses a default) and prints the result.
    """
    setup_logging()
    pin_random_seed()
    
    test_queries = [
        "Please show me my financial records.",
        "Delete all my personal data.",
        "What is the weather like today?",
        "I want to access my account history."
    ]
    
    logger.info("Starting Frozen DistilBERT Intent Classifier test.")
    
    try:
        classifier = FrozenDistilBERTClassifier()
        classifier.load()
        
        for query in test_queries:
            result = classifier.classify(query)
            logger.info(f"Query: {query}")
            logger.info(f"  -> Intent: {result.intent} (Confidence: {result.confidence:.4f})")
            
        # Save a sample output to data/processed/classifier_test.json
        os.makedirs("data/processed", exist_ok=True)
        output_path = "data/processed/classifier_test.json"
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "model": MODEL_NAME,
                "device": "cpu",
                "results": [
                    {
                        "text": q,
                        "intent": classifier.classify(q).intent,
                        "confidence": classifier.classify(q).confidence
                    }
                    for q in test_queries
                ]
            }, f, indent=2)
        
        logger.info(f"Test results saved to {output_path}")
        
    except Exception as e:
        logger.error(f"Classifier execution failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()