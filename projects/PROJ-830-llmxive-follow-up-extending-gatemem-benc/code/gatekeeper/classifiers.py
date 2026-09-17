import os
import json
import logging
import time
from typing import List, Dict, Any, Optional, Tuple, NamedTuple
from datetime import datetime

import torch
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
from transformers import set_seed

# Enforce CPU usage globally as per task requirements
torch.set_default_device('cpu')
# Ensure no GPU is used even if available
if torch.cuda.is_available():
    logging.warning("CUDA is available but will not be used. Forcing CPU execution.")
    torch.cuda.is_available = lambda: False

from code.utils.profiling import profile_execution, get_results_summary
from code.logging_config import setup_logging

# Setup logging
logger = setup_logging("gatekeeper_classifiers")

class ClassificationResult(NamedTuple):
    label: str
    score: float
    inference_time_ms: float
    peak_ram_mb: float

class FrozenDistilBERTClassifier:
    """
    Zero-Shot Intent Classifier using facebook/bart-large-mnli.
    Enforces CPU execution.
    """
    
    def __init__(self, model_id: str = "facebook/bart-large-mnli", cache_dir: Optional[str] = None):
        self.model_id = model_id
        self.pipeline = None
        self.cache_dir = cache_dir
        self._load_model()

    def _load_model(self, retry: bool = False):
        """
        Load the zero-shot classification pipeline.
        Implements retry logic for cache corruption.
        """
        attempt = 1 if not retry else 2
        try:
            logger.info(f"Loading zero-shot model: {self.model_id} (Attempt {attempt})")
            
            # Explicitly set device to CPU
            self.pipeline = pipeline(
                "zero-shot-classification",
                model=self.model_id,
                device=0 if torch.cuda.is_available() else "cpu", # Fallback logic, but we force CPU
                cache_dir=self.cache_dir
            )
            
            # Double check device
            if hasattr(self.pipeline.model, 'device'):
                if str(self.pipeline.model.device).startswith('cuda'):
                    logger.error("Model loaded on GPU despite CPU enforcement. Forcing reload on CPU.")
                    raise RuntimeError("Model loaded on GPU")

            logger.info("Model loaded successfully.")
            
        except Exception as e:
            if not retry:
                logger.error(f"Critical: Model Unavailable on first attempt: {e}. Retrying once...")
                self._load_model(retry=True)
            else:
                logger.critical(f"Critical: Model Unavailable after retry: {e}")
                # Exit with code 1 as per requirements
                import sys
                sys.exit(1)

    def classify(self, candidate_labels: List[str], hypothesis_template: Optional[str] = None) -> Tuple[List[str], List[float]]:
        """
        Perform zero-shot classification.
        """
        if not self.pipeline:
            raise RuntimeError("Model not loaded.")
        
        # We expect a single hypothesis or a list. 
        # For zero-shot, we usually pass the text and candidate labels.
        # The pipeline handles the hypothesis template internally if not provided, 
        # or we can construct it.
        
        # The task requires classifying against 'leak-target' schema labels (e.g., "allowed", "denied").
        # The BART model expects a hypothesis template like "This text is {}."
        # However, the pipeline function signature is:
        # (sequences, candidate_labels, hypothesis_template=None, ...)
        
        return self.pipeline, candidate_labels

    def run_inference(self, text: str, candidate_labels: List[str]) -> Dict[str, Any]:
        """
        Run inference on a single text sample.
        Returns dict with inference_time_ms and peak_ram_mb using profile_execution.
        """
        
        def inference_core():
            if not self.pipeline:
                raise RuntimeError("Model not initialized.")
            
            # Run classification
            # The pipeline returns a dict with 'labels' and 'scores'
            result = self.pipeline(text, candidate_labels=candidate_labels)
            return result

        # Use the profiling utility from code/utils/profiling.py
        # profile_execution expects a callable and returns a dict with standardized keys
        profile_result = profile_execution(inference_core)
        
        if profile_result['success']:
            inference_data = profile_result['data']
            # Extract the top label and score
            # The pipeline returns a dict with 'labels' (list) and 'scores' (list) sorted by score
            top_label = inference_data['labels'][0]
            top_score = inference_data['scores'][0]
            
            return {
                'inference_time_ms': profile_result['latency_ms'],
                'peak_ram_mb': profile_result['peak_ram_mb'],
                'label': top_label,
                'score': top_score,
                'all_labels': inference_data['labels'],
                'all_scores': inference_data['scores']
            }
        else:
            logger.error(f"Inference failed: {profile_result['error']}")
            raise RuntimeError(f"Inference failed: {profile_result['error']}")

def run_inference(text: str, candidate_labels: List[str], model_id: str = "facebook/bart-large-mnli") -> Dict[str, Any]:
    """
    Convenience function to run inference using the default classifier instance.
    """
    classifier = FrozenDistilBERTClassifier(model_id=model_id)
    return classifier.run_inference(text, candidate_labels)

def main():
    """
    Main entry point for testing the classifier directly.
    """
    logger.info("Starting classifier test...")
    
    # Test data
    test_text = "The user is requesting to delete their medical records."
    labels = ["allowed", "denied", "review_required"]
    
    try:
        result = run_inference(test_text, labels)
        logger.info(f"Classification Result: {result}")
    except Exception as e:
        logger.critical(f"Test failed: {e}")
        import sys
        sys.exit(1)

if __name__ == "__main__":
    main()
