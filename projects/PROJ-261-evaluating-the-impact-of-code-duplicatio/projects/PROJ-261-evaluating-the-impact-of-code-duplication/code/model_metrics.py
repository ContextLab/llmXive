"""Model metrics computation with NaN/infinite value validation.

This module loads LLM models in 8-bit quantization and computes perplexity
scores for code samples. It includes robust error handling for:
- NaN and infinite perplexity values
- Model loading failures
- Memory errors during inference

Per Constitution Principle III (Data Hygiene), all invalid metric values
are detected, logged, and handled appropriately.
"""
import logging
import math
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

# Module-level logger
_logger = None

def _get_logger() -> logging.Logger:
    """Get or create the module logger."""
    global _logger
    if _logger is None:
        _logger = logging.getLogger("model_metrics")
        _logger.setLevel(logging.INFO)
        if not _logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))
            _logger.addHandler(handler)
    return _logger

def load_model_and_tokenizer(
    model_name: str = "Salesforce/codegen-350M-mono",
    use_8bit: bool = True
) -> Tuple[AutoModelForCausalLM, AutoTokenizer]:
    """Load model and tokenizer with error handling.

    Args:
        model_name: HuggingFace model identifier
        use_8bit: If True, load in 8-bit quantization mode

    Returns:
        Tuple of (model, tokenizer)

    Raises:
        RuntimeError: If model cannot be loaded
    """
    logger = _get_logger()

    logger.info(f"Loading model: {model_name} (8-bit={use_8bit})")

    try:
        tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            trust_remote_code=True
        )

        # Ensure tokenizer has pad token
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
            logger.info("Set pad_token to eos_token")

    except Exception as e:
        error_msg = f"Failed to load tokenizer: {type(e).__name__}: {str(e)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e

    try:
        if use_8bit:
            try:
                import bitsandbytes
                model = AutoModelForCausalLM.from_pretrained(
                    model_name,
                    load_in_8bit=True,
                    device_map="auto",
                    trust_remote_code=True,
                    torch_dtype=torch.float16
                )
                logger.info("Model loaded in 8-bit quantization mode")
            except ImportError:
                logger.warning(
                    "bitsandbytes not available, loading in full precision"
                )
                model = AutoModelForCausalLM.from_pretrained(
                    model_name,
                    trust_remote_code=True,
                    torch_dtype=torch.float16
                )
            except Exception as e:
                logger.warning(
                    f"8-bit loading failed: {type(e).__name__}: {str(e)}, "
                    "falling back to full precision"
                )
                model = AutoModelForCausalLM.from_pretrained(
                    model_name,
                    trust_remote_code=True,
                    torch_dtype=torch.float16
                )
        else:
            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                trust_remote_code=True,
                torch_dtype=torch.float16
            )

        logger.info(f"Model loaded successfully: {model_name}")
        return model, tokenizer

    except Exception as e:
        error_msg = f"Failed to load model: {type(e).__name__}: {str(e)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e

def load_model_8bit(
    model_name: str = "Salesforce/codegen-350M-mono"
) -> Tuple[AutoModelForCausalLM, AutoTokenizer]:
    """Convenience function to load model in 8-bit mode.

    Args:
        model_name: HuggingFace model identifier

    Returns:
        Tuple of (model, tokenizer)
    """
    return load_model_and_tokenizer(model_name, use_8bit=True)

def validate_perplexity(perplexity: float) -> Tuple[bool, Optional[str]]:
    """Validate that perplexity value is valid.

    Checks for:
    - NaN values
    - Infinite values
    - Negative values (perplexity should always be >= 1.0)
    - Extremely large values (potential overflow)

    Args:
        perplexity: Perplexity value to validate

    Returns:
        Tuple of (is_valid, error_message). If invalid, error_message explains why.
    """
    if perplexity is None:
        return False, "Perplexity value is None"

    if math.isnan(perplexity):
        return False, "Perplexity is NaN"

    if math.isinf(perplexity):
        return False, "Perplexity is infinite"

    if perplexity < 1.0:
        return False, f"Perplexity {perplexity} < 1.0 (invalid)"

    if perplexity > 1e10:
        return False, f"Perplexity {perplexity} exceeds threshold (possible overflow)"

    return True, None

def compute_perplexity(
    model: AutoModelForCausalLM,
    tokenizer: AutoTokenizer,
    code: str,
    max_length: int = 512
) -> Tuple[Optional[float], Optional[str]]:
    """Compute perplexity for a code snippet.

    Args:
        model: Loaded transformer model
        tokenizer: Loaded tokenizer
        code: Code string to evaluate
        max_length: Maximum sequence length

    Returns:
        Tuple of (perplexity, error_message). If error, perplexity is None.
    """
    logger = _get_logger()

    if not code or not code.strip():
        logger.warning("Empty code provided for perplexity computation")
        return None, "Empty code"

    try:
        # Tokenize the code
        inputs = tokenizer(
            code,
            return_tensors="pt",
            truncation=True,
            max_length=max_length
        )

        # Move inputs to model device
        device = next(model.parameters()).device
        inputs = {k: v.to(device) for k, v in inputs.items()}

        # Get model outputs
        with torch.no_grad():
            outputs = model(**inputs, labels=inputs["input_ids"])
            loss = outputs.loss

        # Compute perplexity from cross-entropy loss
        perplexity = math.exp(loss.item())

        # Validate the result
        is_valid, error = validate_perplexity(perplexity)

        if not is_valid:
            logger.warning(f"Invalid perplexity computed: {error}")
            return None, error

        logger.debug(f"Computed perplexity: {perplexity:.4f}")
        return perplexity, None

    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}"
        logger.error(f"Error computing perplexity: {error_msg}")
        return None, error_msg

def compute_perplexity_batch(
    model: AutoModelForCausalLM,
    tokenizer: AutoTokenizer,
    codes: List[str],
    max_length: int = 512,
    batch_size: int = 8
) -> List[Tuple[Optional[float], Optional[str]]]:
    """Compute perplexity for a batch of code snippets.

    Args:
        model: Loaded transformer model
        tokenizer: Loaded tokenizer
        codes: List of code strings to evaluate
        max_length: Maximum sequence length
        batch_size: Batch size for processing

    Returns:
        List of (perplexity, error_message) tuples
    """
    logger = _get_logger()
    results = []

    logger.info(f"Processing {len(codes)} code snippets in batches of {batch_size}")

    for i in range(0, len(codes), batch_size):
        batch = codes[i:i + batch_size]
        logger.debug(f"Processing batch {i//batch_size + 1}")

        for code in batch:
            perplexity, error = compute_perplexity(
                model, tokenizer, code, max_length
            )
            results.append((perplexity, error))

    valid_count = sum(1 for p, e in results if p is not None)
    logger.info(
        f"Batch processing complete: {valid_count}/{len(codes)} valid perplexity values"
    )

    return results

def filter_invalid_perplexities(
    perplexity_scores: List[Tuple[Optional[float], Optional[str]]]
) -> Tuple[List[float], List[Tuple[Optional[float], Optional[str]]]]:
    """Filter out invalid perplexity values.

    Args:
        perplexity_scores: List of (perplexity, error) tuples

    Returns:
        Tuple of (valid_perplexities, invalid_entries)
    """
    logger = _get_logger()

    valid_scores = []
    invalid_entries = []

    for perplexity, error in perplexity_scores:
        if perplexity is not None:
            is_valid, validation_error = validate_perplexity(perplexity)
            if is_valid:
                valid_scores.append(perplexity)
            else:
                invalid_entries.append((perplexity, validation_error or "Invalid"))
        else:
            invalid_entries.append((perplexity, error or "No error message"))

    logger.info(
        f"Filtered perplexity scores: {len(valid_scores)} valid, "
        f"{len(invalid_entries)} invalid"
    )

    return valid_scores, invalid_entries
