"""
Metrics calculation for code snippets.

Calculates perplexity and functional correctness rate for code snippets
using a loaded language model and runtime validation.
"""

import ast
import logging
import sys
import time
import multiprocessing
import traceback
from concurrent.futures import TimeoutError as FuturesTimeoutError
from typing import Dict, Any, Optional, List, Tuple

from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logging import get_logger

logger = get_logger(__name__)

try:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False
    logger.warning("Transformers not available. Perplexity will be NaN.")

try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False
    logger.warning("NetworkX not available. Complexity calculation will fail.")

def _run_code_sandbox(code: str, timeout: int = 5) -> Tuple[bool, str]:
    """
    Runs code in a separate process with a timeout to prevent hanging.
    Returns (success, message).
    """
    def worker(queue):
        try:
            # Attempt to compile first to catch syntax errors quickly
            compile(code, '<sandbox>', 'exec')
            # Attempt execution with restricted builtins
            safe_globals = {
                "__builtins__": {
                    "len": len,
                    "str": str,
                    "int": int,
                    "float": float,
                    "list": list,
                    "dict": dict,
                    "tuple": tuple,
                    "set": set,
                    "range": range,
                    "True": True,
                    "False": False,
                    "None": None,
                    "print": lambda *args: None, # Suppress print
                }
            }
            # Execute the code
            exec(code, safe_globals, {})
            queue.put((True, "Execution successful"))
        except SyntaxError as e:
            queue.put((False, f"SyntaxError: {e}"))
        except Exception as e:
            queue.put((False, f"RuntimeError: {e}"))

    queue = multiprocessing.Queue()
    process = multiprocessing.Process(target=worker, args=(queue,))
    process.start()
    process.join(timeout=timeout)

    if process.is_alive():
        process.terminate()
        process.join()
        return False, "Timeout: Execution exceeded time limit"
    
    try:
        return queue.get_nowait()
    except Exception:
        return False, "Failed to retrieve result"

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
        Perplexity score (lower is better), or NaN if calculation fails.
    """
    if not HAS_TRANSFORMERS:
        logger.warning("Transformers not available, returning NaN for perplexity")
        return float('nan')
    
    if model is None or tokenizer is None:
        logger.warning("Model or tokenizer not provided, returning NaN for perplexity")
        return float('nan')

    try:
        # Tokenize
        inputs = tokenizer(
            snippet,
            return_tensors="pt",
            truncation=True,
            max_length=max_length
        )
        
        # Move to CPU explicitly
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
        logger.warning(f"Perplexity calculation failed for snippet: {str(e)}")
        return float('nan')

def validate_snippet_syntax(snippet: str) -> bool:
    """
    Validate Python syntax of a snippet.
    
    Args:
        snippet: The code snippet text
    
    Returns:
        True if syntax is valid, False otherwise.
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
    timeout_seconds: int = 5
) -> float:
    """
    Estimate functional correctness of a snippet.
    
    This function attempts to:
    1. Validate syntax.
    2. Execute the code in a sandboxed environment with a timeout.
    
    If the code compiles and executes without raising an exception
    (within the timeout and sandbox constraints), it returns 1.0.
    Otherwise, it returns 0.0.
    
    Args:
        snippet: The code snippet text
        timeout_seconds: Timeout for execution in seconds
    
    Returns:
        Correctness score (1.0 for valid execution, 0.0 otherwise).
    """
    try:
        # First, quick syntax check
        if not validate_snippet_syntax(snippet):
            return 0.0
        
        # If syntax is valid, attempt execution in sandbox
        success, msg = _run_code_sandbox(snippet, timeout=timeout_seconds)
        
        if success:
            return 1.0
        else:
            # Log specific failure reason for debugging if needed
            # logger.debug(f"Functional correctness failed: {msg}")
            return 0.0
            
    except Exception as e:
        logger.warning(f"Correctness validation failed unexpectedly: {str(e)}")
        return 0.0

def calculate_metrics(
    snippet: Dict[str, Any],
    model: Any,
    tokenizer: Any,
    timeout_seconds: int = 10
) -> Dict[str, Any]:
    """
    Calculate all metrics for a single snippet.
    
    Args:
        snippet: Dictionary containing snippet data (must include 'snippet_content')
        model: The loaded language model (or None)
        tokenizer: The loaded tokenizer (or None)
        timeout_seconds: Timeout for functional correctness check
    
    Returns:
        Dictionary with 'perplexity' and 'functional_correctness_rate'.
    """
    snippet_id = snippet.get('snippet_id', 'unknown')
    content = snippet.get('snippet_content', '')
    
    if not content:
        logger.warning(f"No content for snippet {snippet_id}")
        return {
            'perplexity': float('nan'),
            'functional_correctness_rate': float('nan')
        }
    
    perplexity = float('nan')
    correctness = 0.0 # Default to 0 if we can't even check syntax? No, let's try.

    try:
        # Calculate perplexity
        perplexity = calculate_perplexity(content, model, tokenizer)
        
        # Calculate functional correctness with timeout
        # This is the heavy part that might hang, so we wrap it or use the internal timeout
        correctness = calculate_functional_correctness(content, timeout_seconds)
        
    except Exception as e:
        logger.error(f"Error calculating metrics for {snippet_id}: {str(e)}")
        # Ensure we return NaNs or 0s on total failure
        if perplexity == float('nan') and 'perplexity' not in locals():
             perplexity = float('nan')
        if 'correctness' not in locals():
            correctness = float('nan')
    
    return {
        'perplexity': perplexity,
        'functional_correctness_rate': correctness
    }

def main():
    """
    Entry point for testing or running metrics calculation independently.
    In this context, it logs that the module is ready.
    Actual calculation happens via run_inference.py which loads model and snippets.
    """
    logger.info("Metrics calculator module loaded successfully.")
    if not HAS_TRANSFORMERS:
        logger.warning("Transformers library not found. Perplexity calculation will be skipped.")
    if not HAS_NETWORKX:
        logger.warning("NetworkX library not found. Complexity calculation (if needed here) will be skipped.")

if __name__ == '__main__':
    main()