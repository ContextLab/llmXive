"""
Gatekeeper Intent Classifier Module.

Implements a frozen DistilBERT intent classifier for CPU-only execution.
Loads a pre-trained model from HuggingFace and provides an inference wrapper.
Includes resource usage logging to verify CPU-only, <2GB memory constraints.
"""
import os
import json
import logging
from typing import List, Dict, Any, Optional, Tuple, NamedTuple
from datetime import datetime

import torch
from transformers import DistilBertTokenizer, DistilBertForSequenceClassification
from transformers import pipeline

from logging_config import setup_logging

# Initialize logger
logger = setup_logging(__name__)

# Constants
MODEL_NAME = "distilbert-base-uncased"  # Generic intent classification base
MAX_LENGTH = 128
DEVICE = "cpu"
BATCH_SIZE = 8

class ClassificationResult(NamedTuple):
    """Result of a single classification inference."""
    label: str
    score: float
    timestamp: str
    resource_info: Dict[str, Any]

class FrozenDistilBERTClassifier:
    """
    Wrapper for a frozen DistilBERT intent classifier.
    
    Constraints:
    - Runs exclusively on CPU (no CUDA).
    - Uses default precision (FP32) to avoid quantization complexity unless specified.
    - Logs resource usage (RAM, device) upon initialization and inference.
    """
    
    def __init__(self, model_name: str = MODEL_NAME, device: str = DEVICE):
        if device != "cpu":
            logger.warning("CPU-only runner enforced. Overriding device request to 'cpu'.")
            device = "cpu"
        
        self.device = device
        self.model_name = model_name
        self.tokenizer = None
        self.model = None
        self.pipeline = None
        self._resource_log: Dict[str, Any] = {}
        
        # Verify CUDA availability but force CPU usage
        if torch.cuda.is_available():
            logger.info("CUDA detected but ignored. Forcing CPU execution as per constraints.")
        else:
            logger.info("CUDA not available. Running on CPU.")

        self._load_model()

    def _load_model(self) -> None:
        """Load the tokenizer and model into memory."""
        logger.info(f"Loading DistilBERT model: {self.model_name} on {self.device}")
        
        try:
            self.tokenizer = DistilBertTokenizer.from_pretrained(self.model_name)
            # Load model for sequence classification (generic intent detection)
            # Using a generic head; in a real scenario, a fine-tuned checkpoint would be used.
            # For this implementation, we assume a standard classification setup.
            # Note: If the model is not fine-tuned for specific intents, we might use a generic
            # sentiment or a placeholder head. Here we simulate a loaded model structure.
            # To strictly follow "frozen", we set requires_grad=False.
            
            self.model = DistilBertForSequenceClassification.from_pretrained(
                self.model_name,
                num_labels=2,  # Example: Authorized vs Unauthorized (placeholder)
                torchscript=True # Optimized for inference
            )
            self.model.eval()
            for param in self.model.parameters():
                param.requires_grad = False

            # Move to device
            self.model.to(self.device)
            
            logger.info(f"Model loaded successfully on {self.device}.")
            
            # Log initial resource usage
            self._log_resource_usage("initialization")
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise

    def _log_resource_usage(self, stage: str) -> None:
        """Log CPU/RAM usage and device info."""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        mem_info = process.memory_info()
        
        resource_data = {
            "stage": stage,
            "timestamp": datetime.now().isoformat(),
            "device": self.device,
            "peak_ram_mb": mem_info.rss / (1024 * 1024),
            "cuda_available": torch.cuda.is_available(),
            "cuda_memory_used": 0 if not torch.cuda.is_available() else torch.cuda.memory_allocated() / (1024 * 1024)
        }
        
        # Verify constraints
        if resource_data["device"] != "cpu":
            raise RuntimeError("Constraint violation: Model is not running on CPU.")
        
        if resource_data["peak_ram_mb"] > 2048:
            logger.warning(f"RAM usage ({resource_data['peak_ram_mb']:.2f} MB) exceeds 2GB soft limit.")
        
        self._resource_log[stage] = resource_data
        logger.info(f"Resource usage at {stage}: RAM={resource_data['peak_ram_mb']:.2f} MB, Device={resource_data['device']}")

    def infer(self, texts: List[str]) -> List[ClassificationResult]:
        """
        Run inference on a batch of texts.
        
        Args:
            texts: List of input strings.
        
        Returns:
            List of ClassificationResult objects.
        """
        if not texts:
            return []

        results = []
        
        # Batch processing to manage memory
        for i in range(0, len(texts), BATCH_SIZE):
            batch = texts[i:i + BATCH_SIZE]
            
            # Tokenize
            inputs = self.tokenizer(
                batch,
                padding=True,
                truncation=True,
                max_length=MAX_LENGTH,
                return_tensors="pt"
            )
            
            # Move to device
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            with torch.no_grad():
                outputs = self.model(**inputs)
                logits = outputs.logits
                probs = torch.softmax(logits, dim=1)
            
            # Decode
            for j, text in enumerate(batch):
                # Assuming binary classification: 0=Authorized, 1=Unauthorized
                # Adjust labels based on actual fine-tuned model if available
                score = probs[j, 1].item()
                label = "UNAUTHORIZED" if score > 0.5 else "AUTHORIZED"
                
                result = ClassificationResult(
                    label=label,
                    score=score,
                    timestamp=datetime.now().isoformat(),
                    resource_info=self._resource_log.get("initialization", {})
                )
                results.append(result)
        
        return results

def run_intent_classification(texts: List[str], classifier: Optional[FrozenDistilBERTClassifier] = None) -> List[ClassificationResult]:
    """
    Convenience wrapper to run intent classification.
    
    Args:
        texts: List of input strings.
        classifier: Optional pre-initialized classifier. If None, creates a new one.
    
    Returns:
        List of classification results.
    """
    if classifier is None:
        classifier = FrozenDistilBERTClassifier()
    
    return classifier.infer(texts)

def main():
    """
    Main entry point for testing the classifier independently.
    Runs a dummy inference to verify CPU-only execution and memory logging.
    """
    logger.info("Starting classifier verification test...")
    
    # Test data
    test_texts = [
        "Can I access the medical records of patient X?",
        "What is the weather today?",
        "Delete my account and all associated data.",
        "Show me the office meeting schedule."
    ]
    
    try:
        classifier = FrozenDistilBERTClassifier()
        results = classifier.infer(test_texts)
        
        logger.info(f"Classification complete. Processed {len(results)} items.")
        for i, res in enumerate(results):
            logger.info(f"  [{i}] Text: {test_texts[i][:30]}... -> {res.label} (score: {res.score:.4f})")
        
        # Verify resource log
        if "initialization" in classifier._resource_log:
            log = classifier._resource_log["initialization"]
            logger.info(f"Verification passed: Device={log['device']}, RAM={log['peak_ram_mb']:.2f} MB")
            if log['device'] != 'cpu':
                raise AssertionError("Verification failed: Device is not CPU.")
            if log['peak_ram_mb'] > 2048:
                logger.warning("Verification warning: RAM usage > 2GB.")
        
    except Exception as e:
        logger.error(f"Classifier test failed: {e}")
        raise

if __name__ == "__main__":
    main()