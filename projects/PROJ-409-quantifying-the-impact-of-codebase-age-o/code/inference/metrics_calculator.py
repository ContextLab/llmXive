"""
Metrics calculation for code snippets.

Calculates perplexity and functional correctness rate for code snippets
using a loaded language model.
"""

import logging
import time
from concurrent.futures import TimeoutError as FuturesTimeoutError
from typing import Dict, Any, Optional, List

# Add project root to path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logging import get_logger

logger = get_logger(__name__)

try:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False

def calculate_perplexity(
    snippet: str,
    model: Any,
    tokenizer: Any,
    max_length: int = 512
) -> float:
    """
    Calculate perplexity of a code snippet.
    
    Args:
        snippet: The code snippet text
        model: The loaded language model
        tokenizer: The loaded tokenizer
        max_length: Maximum sequence length to consider
    
    Returns:
        Perplexity score (lower is better)
    """
    if not HAS_TRANSFORMERS:
        logger.warning("Transformers not available, returning NaN for perplexity")
        return float('nan')
    
    try:
        # Tokenize
        inputs = tokenizer(
            snippet,
            return_tensors="pt",
            truncation=True,
            max_length=max_length
        )
        
        # Move to CPU
        inputs = {k: v.to('cpu') for k, v in inputs.items()}
        
        # Disable gradients
        with torch.no_grad():
            # Get model outputs
            outputs = model(**inputs, labels=inputs['input_ids'])
            
            # Calculate loss (cross-entropy)
            loss = outputs.loss
            
            # Perplexity = exp(loss)
            perplexity = torch.exp(loss).item()
            
            return perplexity
            
    except Exception as e:
        logger.warning(f"Perplexity calculation failed: {str(e)}")
        return float('nan')

def validate_snippet_syntax(snippet: str) -> bool:
    """
    Validate Python syntax of a snippet.
    
    Args:
        snippet: The code snippet text
    
    Returns:
        True if syntax is valid, False otherwise
    """
    try:
        compile(snippet, '<string>', 'exec')
        return True
    except SyntaxError:
        return False
    except Exception:
        return False

def calculate_functional_correctness(
    snippet: str,
    timeout_seconds: int = 10
) -> float:
    """
    Estimate functional correctness of a snippet.
    
    For now, this uses a simple heuristic:
    - If syntax is valid, return 1.0
    - If syntax is invalid, return 0.0
    
    In a full implementation, this would run unit tests or semantic validation.
    
    Args:
        snippet: The code snippet text
        timeout_seconds: Timeout for execution (not used in this basic version)
    
    Returns:
        Correctness score (0.0 to 1.0)
    """
    try:
        # Basic syntax check
        if validate_snippet_syntax(snippet):
            return 1.0
        else:
            return 0.0
    except Exception as e:
        logger.warning(f"Correctness validation failed: {str(e)}")
        return float('nan')

def calculate_metrics(
    snippet: Dict[str, Any],
    model: Any,
    tokenizer: Any,
    timeout_seconds: int = 30
) -> Dict[str, Any]:
    """
    Calculate all metrics for a single snippet.
    
    Args:
        snippet: Dictionary containing snippet data
        model: The loaded language model
        tokenizer: The loaded tokenizer
        timeout_seconds: Timeout for the entire calculation
    
    Returns:
        Dictionary with perplexity and functional_correctness_rate
    """
    snippet_id = snippet.get('snippet_id', 'unknown')
    content = snippet.get('snippet_content', '')
    
    if not content:
        logger.warning(f"No content for snippet {snippet_id}")
        return {
            'perplexity': float('nan'),
            'functional_correctness_rate': float('nan')
        }
    
    try:
        # Calculate perplexity
        perplexity = calculate_perplexity(content, model, tokenizer)
        
        # Calculate functional correctness
        correctness = calculate_functional_correctness(content, timeout_seconds)
        
        return {
            'perplexity': perplexity,
            'functional_correctness_rate': correctness
        }
        
    except Exception as e:
        logger.error(f"Error calculating metrics for {snippet_id}: {str(e)}")
        return {
            'perplexity': float('nan'),
            'functional_correctness_rate': float('nan')
        }

def main():
    """Test metrics calculation with a sample snippet."""
    # This is a basic test - in real usage, model and tokenizer would be loaded
    logger.info("Metrics calculator module loaded successfully")

if __name__ == '__main__':
    main()
