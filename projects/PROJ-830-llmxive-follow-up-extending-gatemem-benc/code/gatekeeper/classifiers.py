"""
Intent classification module for GateMem benchmark.

Implements a frozen DistilBERT classifier for intent detection,
optimized for CPU-only execution with resource logging.
"""
import os
import json
import logging
from typing import List, Dict, Any, Optional, Tuple, NamedTuple
from datetime import datetime
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from transformers import pipeline

from logging_config import setup_logging
from utils.profiling import get_process_memory_mb, start_profiling, stop_profiling

# Initialize logger
logger = setup_logging(__name__)

# Constants
MODEL_NAME = "distilbert-base-uncased"
DEVICE = "cpu"
MAX_LENGTH = 512
BATCH_SIZE = 8
LABEL_MAP = {
    0: "safe",
    1: "leak_attempt",
    2: "deletion_request",
    3: "admin_access"
}

class ClassificationResult(NamedTuple):
    """Result of a classification inference."""
    episode_id: str
    label: str
    score: float
    raw_scores: Dict[str, float]
    inference_time_ms: float
    peak_memory_mb: float

class FrozenDistilBERTClassifier:
    """
    A frozen DistilBERT classifier for intent detection.
    
    This class loads a pre-trained model in inference mode,
    ensuring no gradients are computed and the model runs on CPU.
    """
    
    def __init__(self, model_name: str = MODEL_NAME, device: str = DEVICE):
        """
        Initialize the classifier.
        
        Args:
            model_name: HuggingFace model name or path
            device: Device to run inference on ('cpu' or 'cuda')
        """
        self.device = device
        self.model_name = model_name
        self.model = None
        self.tokenizer = None
        self.pipeline = None
        
        logger.info(f"Initializing {model_name} classifier on {device}")
        
        # Verify CPU-only constraint
        if device == "cuda" and not torch.cuda.is_available():
            logger.warning("CUDA requested but not available, falling back to CPU")
            self.device = "cpu"
        
        if self.device == "cpu":
            logger.info("Running in CPU-only mode (no CUDA)")
        
        self._load_model()
    
    def _load_model(self) -> None:
        """Load the model and tokenizer."""
        try:
            start_profiling()
            
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(
                self.model_name,
                num_labels=len(LABEL_MAP)
            )
            
            # Freeze model parameters
            for param in self.model.parameters():
                param.requires_grad = False
            
            # Set to evaluation mode
            self.model.eval()
            
            # Move to device
            self.model.to(self.device)
            
            # Create inference pipeline
            self.pipeline = pipeline(
                "text-classification",
                model=self.model,
                tokenizer=self.tokenizer,
                device=0 if self.device == "cpu" else -1,  # -1 for CPU in pipeline
                return_all_scores=False,
                max_length=MAX_LENGTH,
                truncation=True
            )
            
            peak_mem = stop_profiling()
            logger.info(f"Model loaded successfully. Peak memory: {peak_mem:.2f} MB")
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise
    
    def classify(self, text: str) -> Dict[str, Any]:
        """
        Classify a single text sample.
        
        Args:
            text: Input text to classify
            
        Returns:
            Dictionary with label, score, and timing info
        """
        if not self.pipeline:
            raise RuntimeError("Model not loaded. Call _load_model() first.")
        
        start_time = datetime.now()
        start_profiling()
        
        try:
            result = self.pipeline(text)[0]
            label = result['label']
            score = result['score']
        except Exception as e:
            logger.error(f"Classification failed: {e}")
            raise
        
        inference_time = (datetime.now() - start_time).total_seconds() * 1000
        peak_memory = stop_profiling()
        
        return {
            "label": label,
            "score": score,
            "inference_time_ms": inference_time,
            "peak_memory_mb": peak_memory
        }
    
    def classify_batch(self, texts: List[str]) -> List[Dict[str, Any]]:
        """
        Classify a batch of text samples.
        
        Args:
            texts: List of input texts
            
        Returns:
            List of classification results
        """
        if not self.pipeline:
            raise RuntimeError("Model not loaded. Call _load_model() first.")
        
        start_time = datetime.now()
        start_profiling()
        
        try:
            results = self.pipeline(texts, batch_size=BATCH_SIZE)
        except Exception as e:
            logger.error(f"Batch classification failed: {e}")
            raise
        
        inference_time = (datetime.now() - start_time).total_seconds() * 1000
        peak_memory = stop_profiling()
        
        # Add timing and memory to each result
        for i, result in enumerate(results):
            result["inference_time_ms"] = inference_time / len(texts)
            result["peak_memory_mb"] = peak_memory
        
        return results

def run_intent_classification(
    classifier: FrozenDistilBERTClassifier,
    episodes: List[Dict[str, Any]]
) -> List[ClassificationResult]:
    """
    Run intent classification on a list of episodes.
    
    Args:
        classifier: Initialized classifier instance
        episodes: List of episode dictionaries with 'text' field
        
    Returns:
        List of ClassificationResult objects
    """
    logger.info(f"Running intent classification on {len(episodes)} episodes")
    
    results = []
    texts = [ep.get("text", "") for ep in episodes]
    
    try:
        batch_results = classifier.classify_batch(texts)
        
        for i, (ep, res) in enumerate(zip(episodes, batch_results)):
            episode_id = ep.get("id", f"unknown_{i}")
            
            # Map label to our custom labels if needed
            label = res.get("label", "unknown")
            score = res.get("score", 0.0)
            
            # Create raw scores dict if available
            raw_scores = {label: score}
            
            result = ClassificationResult(
                episode_id=episode_id,
                label=label,
                score=score,
                raw_scores=raw_scores,
                inference_time_ms=res.get("inference_time_ms", 0.0),
                peak_memory_mb=res.get("peak_memory_mb", 0.0)
            )
            results.append(result)
            
            if (i + 1) % 100 == 0:
                logger.info(f"Processed {i + 1}/{len(episodes)} episodes")
        
        logger.info(f"Classification complete. Processed {len(results)} episodes")
        
    except Exception as e:
        logger.error(f"Classification pipeline failed: {e}")
        raise
    
    return results

def main():
    """Main entry point for standalone execution."""
    logger.info("Starting intent classification test")
    
    # Test with sample data
    test_episodes = [
        {
            "id": "test_001",
            "text": "Can you access the patient's medical records?"
        },
        {
            "id": "test_002",
            "text": "I need to delete my account and all associated data."
        },
        {
            "id": "test_003",
            "text": "What's the weather like today?"
        }
    ]
    
    try:
        # Initialize classifier
        classifier = FrozenDistilBERTClassifier()
        
        # Run classification
        results = run_intent_classification(classifier, test_episodes)
        
        # Log results
        for result in results:
            logger.info(
                f"Episode {result.episode_id}: "
                f"label={result.label}, "
                f"score={result.score:.4f}, "
                f"time={result.inference_time_ms:.2f}ms, "
                f"memory={result.peak_memory_mb:.2f}MB"
            )
        
        # Verify CPU-only execution
        if classifier.device == "cpu":
            logger.info("✓ Confirmed: Running on CPU only")
        else:
            logger.warning("✗ Warning: Not running on CPU")
        
        # Verify memory usage
        current_mem = get_process_memory_mb()
        logger.info(f"Current process memory: {current_mem:.2f} MB")
        
        if current_mem < 2000:  # 2GB limit
            logger.info("✓ Memory usage within 2GB limit")
        else:
            logger.warning(f"✗ Memory usage exceeds 2GB: {current_mem:.2f} MB")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        raise

if __name__ == "__main__":
    main()
