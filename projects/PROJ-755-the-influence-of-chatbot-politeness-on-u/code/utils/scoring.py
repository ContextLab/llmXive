import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import torch
import logging
from tqdm import tqdm

logger = logging.getLogger(__name__)

def score_utterances_batch(
    utterances: List[str],
    model_name: str = "jfiedler/politeness-bert",
    batch_size: int = 16,
    device: int = -1
) -> List[float]:
    """
    Scores a list of utterances using the specified BERT model for politeness.
    
    Implements robust batched inference with:
    - CPU-only execution (device=-1)
    - torch.no_grad() for memory efficiency
    - max_memory management
    - Error handling for ModelLoadingError and MemoryError
    - Fallback to batch_size=1 on failure
    
    Args:
        utterances: List of text strings to score
        model_name: HuggingFace model identifier
        batch_size: Initial batch size for inference
        device: Device ID (-1 for CPU)
        
    Returns:
        List of politeness scores (floats) corresponding to input utterances
        
    Raises:
        RuntimeError: If scoring fails after all retries
    """
    if not utterances:
        return []
    
    # Ensure CPU-only execution as per project constraints
    if device != -1:
        logger.warning("Device override requested, forcing CPU execution (device=-1)")
        device = -1
        
    current_batch_size = batch_size
    max_attempts = 3
    
    for attempt in range(max_attempts):
        try:
            logger.info(f"Attempting inference with batch_size={current_batch_size}, attempt {attempt+1}/{max_attempts}")
            
            # Load tokenizer and model
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModelForSequenceClassification.from_pretrained(model_name)
            
            # Move model to CPU explicitly
            model = model.to(device)
            model.eval()
            
            # Set up inference pipeline
            with torch.no_grad():
                scores = []
                for i in tqdm(range(0, len(utterances), current_batch_size), desc="Scoring utterances"):
                    batch = utterances[i:i + current_batch_size]
                    
                    # Tokenize
                    inputs = tokenizer(
                        batch,
                        padding=True,
                        truncation=True,
                        max_length=512,
                        return_tensors="pt"
                    )
                    
                    # Move inputs to device
                    inputs = {k: v.to(device) for k, v in inputs.items()}
                    
                    # Forward pass
                    outputs = model(**inputs)
                    logits = outputs.logits
                    
                    # Convert logits to probabilities (assuming binary classification)
                    probs = torch.nn.functional.softmax(logits, dim=1)
                    
                    # Extract politeness score (assuming index 1 is polite)
                    batch_scores = probs[:, 1].cpu().numpy().tolist()
                    scores.extend(batch_scores)
            
            logger.info(f"Successfully scored {len(scores)} utterances with batch_size={current_batch_size}")
            return scores
            
        except Exception as e:
            error_type = type(e).__name__
            logger.error(f"Inference failed: {error_type}: {str(e)}")
            
            # Check for specific error types
            if "ModelLoadingError" in error_type or "MemoryError" in error_type:
                if current_batch_size > 1:
                    logger.warning(f"Reducing batch size from {current_batch_size} to 1")
                    current_batch_size = 1
                    continue
                else:
                    logger.error("Memory error with batch_size=1. Cannot proceed.")
                    raise RuntimeError(f"Failed to score utterances: {str(e)}")
            else:
                # For other errors, try reducing batch size
                if current_batch_size > 1:
                    logger.warning(f"Reducing batch size from {current_batch_size} to 1")
                    current_batch_size = 1
                    continue
                else:
                    logger.error(f"Failed with batch_size=1: {str(e)}")
                    raise RuntimeError(f"Failed to score utterances: {str(e)}")
    
    raise RuntimeError("Failed to score utterances after all retry attempts")

def aggregate_dialogue_scores(
    utterance_scores: List[Dict[str, Any]],
    dialogue_id_col: str = "dialogue_id"
) -> Dict[str, float]:
    """
    Aggregates utterance-level scores into dialogue-level mean scores.
    
    Args:
        utterance_scores: List of dicts with 'dialogue_id' and 'politeness_score'
        dialogue_id_col: Column name for dialogue ID
        
    Returns:
        Dict mapping dialogue_id to mean politeness score
    """
    if not utterance_scores:
        return {}
        
    dialogue_scores = {}
    dialogue_counts = {}
    
    for item in utterance_scores:
        d_id = item[dialogue_id_col]
        score = item["politeness_score"]
        
        if d_id not in dialogue_scores:
            dialogue_scores[d_id] = 0.0
            dialogue_counts[d_id] = 0
            
        dialogue_scores[d_id] += score
        dialogue_counts[d_id] += 1
        
    # Calculate means
    return {
        d_id: total / dialogue_counts[d_id]
        for d_id, total in dialogue_scores.items()
    }

def standardize_scores(
    scores: List[float],
    method: str = "zscore"
) -> List[float]:
    """
    Standardizes scores using the specified method.
    
    Args:
        scores: List of raw scores
        method: Standardization method ('zscore' or 'minmax')
        
    Returns:
        List of standardized scores
    """
    if not scores:
        return []
        
    scores_array = np.array(scores)
    
    if method == "zscore":
        mean = np.mean(scores_array)
        std = np.std(scores_array)
        if std == 0:
            logger.warning("Standard deviation is zero, returning zeros")
            return [0.0] * len(scores)
        return ((scores_array - mean) / std).tolist()
        
    elif method == "minmax":
        min_val = np.min(scores_array)
        max_val = np.max(scores_array)
        if max_val == min_val:
            logger.warning("Min equals max, returning zeros")
            return [0.0] * len(scores)
        return ((scores_array - min_val) / (max_val - min_val)).tolist()
        
    else:
        raise ValueError(f"Unknown standardization method: {method}")
