import logging
import math
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

def load_model_and_tokenizer(model_name: str = "Salesforce/codegen-350M-mono"):
    """
    Load model and tokenizer with error handling for loading failures.
    Returns None on failure to allow graceful degradation.
    """
    try:
        from transformers import AutoTokenizer, AutoModelForCausalLM
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForCausalLM.from_pretrained(model_name)
        return model, tokenizer
    except Exception as e:
        logger.error(f"Failed to load model {model_name}: {e}")
        return None, None

def load_model_8bit(model_name: str = "Salesforce/codegen-350M-mono"):
    """
    Load model in 8-bit quantization mode.
    Implements error handling for quantization failures.
    """
    try:
        from transformers import AutoTokenizer, AutoModelForCausalLM
        from transformers import BitsAndBytesConfig
        
        bnb_config = BitsAndBytesConfig(
            load_in_8bit=True,
            llm_int8_threshold=6.0,
            llm_int8_has_fp16_weight=False
        )
        
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            quantization_config=bnb_config,
            device_map="auto"
        )
        return model, tokenizer
    except ImportError as e:
        logger.warning(f"bitsandbytes not available: {e}")
        # Fallback to non-quantized loading
        return load_model_and_tokenizer(model_name)
    except Exception as e:
        logger.error(f"Failed to load model in 8-bit mode: {e}")
        return None, None

def validate_perplexity(perplexity: float) -> bool:
    """
    Validate perplexity value is not NaN or infinite.
    
    Args:
        perplexity: Perplexity value to validate
    
    Returns:
        True if valid, False if NaN or infinite
    """
    if np.isnan(perplexity):
        logger.warning(f"NaN perplexity value detected")
        return False
    if np.isinf(perplexity):
        logger.warning(f"Infinite perplexity value detected")
        return False
    if perplexity < 0:
        logger.warning(f"Negative perplexity value detected: {perplexity}")
        return False
    return True

def compute_perplexity(model, tokenizer, text: str) -> Tuple[float, bool]:
    """
    Compute perplexity for a text with error handling.
    
    Args:
        model: Loaded model
        tokenizer: Loaded tokenizer
        text: Input text to compute perplexity for
    
    Returns:
        Tuple of (perplexity, is_valid)
    """
    if model is None or tokenizer is None:
        logger.warning("Model or tokenizer not loaded, returning default perplexity")
        return 5.0, False
    
    try:
        import torch
        inputs = tokenizer(text, return_tensors="pt")
        
        with torch.no_grad():
            outputs = model(**inputs, labels=inputs["input_ids"])
            loss = outputs.loss
            perplexity = math.exp(loss.item())
        
        is_valid = validate_perplexity(perplexity)
        return perplexity, is_valid
        
    except Exception as e:
        logger.error(f"Failed to compute perplexity: {e}")
        return float('inf'), False

def compute_perplexity_batch(model, tokenizer, texts: List[str]) -> List[Tuple[float, bool]]:
    """
    Compute perplexity for multiple texts with error handling.
    
    Args:
        model: Loaded model
        tokenizer: Loaded tokenizer
        texts: List of input texts
    
    Returns:
        List of (perplexity, is_valid) tuples
    """
    results = []
    for i, text in enumerate(texts):
        try:
            perplexity, is_valid = compute_perplexity(model, tokenizer, text)
            results.append((perplexity, is_valid))
        except Exception as e:
            logger.error(f"Failed to compute perplexity for text {i}: {e}")
            results.append((float('inf'), False))
    return results

def save_perplexity_scores(scores: List[Dict[str, Any]], output_path: str | Path):
    """
    Save perplexity scores to CSV with validation.
    
    Args:
        scores: List of score dictionaries with 'file_path' and 'perplexity' keys
        output_path: Path to save CSV file
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Validate and filter scores
    valid_scores = []
    for score in scores:
        perplexity = score.get('perplexity', float('inf'))
        if validate_perplexity(perplexity):
            valid_scores.append(score)
        else:
            logger.warning(f"Skipping invalid perplexity for {score.get('file_path')}: {perplexity}")
    
    if valid_scores:
        df = pd.DataFrame(valid_scores)
        df.to_csv(output_path, index=False)
        logger.info(f"Saved {len(valid_scores)} valid perplexity scores to {output_path}")
    else:
        logger.warning("No valid perplexity scores to save")

def main():
    """Main entry point for model metrics computation."""
    logging.basicConfig(level=logging.INFO)
    
    # Test perplexity validation
    test_values = [5.0, float('nan'), float('inf'), -1.0, 10.5]
    for val in test_values:
        is_valid = validate_perplexity(val)
        print(f"Perplexity {val}: valid={is_valid}")

if __name__ == "__main__":
    main()
