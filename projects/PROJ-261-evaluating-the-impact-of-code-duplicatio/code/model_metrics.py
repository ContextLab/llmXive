"""Model metrics computation for code duplication analysis.

Provides functions to load models in 8-bit quantization and compute
perplexity scores for code segments.

Integrates memory monitoring to validate 7GB limit (SC-002).
"""

import logging
import math
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

# Import memory monitoring for SC-002 compliance
from memory_monitor import (
    check_memory_limit,
    validate_memory_within_limit,
    memory_monitor,
    setup_memory_monitoring,
    get_total_memory_mb
)

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

from transformers import AutoModelForCausalLM, AutoTokenizer

# Set up logging
logger = logging.getLogger(__name__)

# Default configuration
DEFAULT_MODEL_NAME = "Salesforce/codegen-350M-mono"
DEFAULT_DEVICE = "cuda" if TORCH_AVAILABLE and torch.cuda.is_available() else "cpu"


def load_model_and_tokenizer(
    model_name: str = DEFAULT_MODEL_NAME,
    device: str = DEFAULT_DEVICE,
    load_in_8bit: bool = True
) -> Tuple[Any, Any]:
    """Load model and tokenizer for perplexity computation.

    Args:
        model_name: HuggingFace model name to load.
        device: Device to load model on ('cuda' or 'cpu').
        load_in_8bit: Whether to use 8-bit quantization.

    Returns:
        Tuple of (model, tokenizer).

    Raises:
        MemoryError: If memory limit exceeded during loading.
    """
    logger.info(f"Loading model: {model_name} on {device}")

    # Check memory before loading
    pre_check = check_memory_limit()
    logger.info(f"Pre-load memory status: {pre_check['status']}, "
               f"current: {pre_check['current_mb']:.2f} MB")

    tokenizer = AutoTokenizer.from_pretrained(model_name)

    # Set up memory monitoring for model loading
    log_path = setup_memory_monitoring()

    with memory_monitor("model_loading", log_path=log_path) as monitor:
        if load_in_8bit and TORCH_AVAILABLE:
            try:
                import bitsandbytes
                model = AutoModelForCausalLM.from_pretrained(
                    model_name,
                    load_in_8bit=True,
                    device_map="auto" if device == "cuda" else None,
                    torch_dtype=torch.float16 if device == "cuda" else torch.float32,
                    low_cpu_mem_usage=True
                )
            except ImportError:
                logger.warning("bitsandbytes not available, falling back to 4-bit")
                model = AutoModelForCausalLM.from_pretrained(
                    model_name,
                    load_in_4bit=True,
                    device_map="auto" if device == "cuda" else None
                )
        else:
            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                device_map="auto" if device == "cuda" else None
            )

    # Validate memory after loading
    post_check = check_memory_limit()
    logger.info(f"Post-load memory status: {post_check['status']}, "
               f"current: {post_check['current_mb']:.2f} MB")

    # Validate we're within the 7GB limit
    validate_memory_within_limit(raise_on_exceed=True)

    logger.info(f"Model loaded successfully: peak memory {monitor['peak_mb']:.2f} MB")

    return model, tokenizer


def load_model_8bit(
    model_name: str = DEFAULT_MODEL_NAME,
    device: str = DEFAULT_DEVICE
) -> Any:
    """Load model in 8-bit quantization mode.

    Convenience wrapper for loading model with memory monitoring.

    Args:
        model_name: HuggingFace model name to load.
        device: Device to load model on.

    Returns:
        Loaded model.
    """
    model, _ = load_model_and_tokenizer(
        model_name=model_name,
        device=device,
        load_in_8bit=True
    )
    return model


def validate_perplexity(perplexity: float) -> bool:
    """Validate that perplexity value is valid (not NaN or infinite).

    Args:
        perplexity: Perplexity value to validate.

    Returns:
        True if valid, False otherwise.
    """
    if math.isnan(perplexity) or math.isinf(perplexity):
        return False
    if perplexity < 0:
        return False
    return True


def compute_perplexity(
    model: Any,
    tokenizer: Any,
    text: str,
    device: str = DEFAULT_DEVICE
) -> float:
    """Compute perplexity for a single text segment.

    Args:
        model: Loaded transformer model.
        tokenizer: Loaded tokenizer.
        text: Text to compute perplexity for.
        device: Device to use for computation.

    Returns:
        Perplexity score.

    Raises:
        MemoryError: If memory limit exceeded during inference.
    """
    # Check memory before computation
    pre_check = check_memory_limit()
    if pre_check['status'] == 'critical':
        raise MemoryError(
            f"Memory limit exceeded before inference: "
            f"{pre_check['current_mb']:.2f} MB"
        )

    # Set up memory monitoring for inference
    log_path = setup_memory_monitoring()

    with memory_monitor("perplexity_inference", log_path=log_path) as monitor:
        # Tokenize input
        inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
        inputs = {k: v.to(device) for k, v in inputs.items()}

        # Compute loss
        with torch.no_grad():
            outputs = model(**inputs, labels=inputs["input_ids"])
            loss = outputs.loss

        # Compute perplexity
        perplexity = torch.exp(loss).item()

    # Validate perplexity
    if not validate_perplexity(perplexity):
        logger.warning(f"Invalid perplexity value: {perplexity}")
        return float('nan')

    # Validate memory after computation
    post_check = check_memory_limit()
    logger.debug(f"Inference complete: peak memory {monitor['peak_mb']:.2f} MB, "
                f"status: {post_check['status']}")

    return perplexity


def compute_perplexity_batch(
    model: Any,
    tokenizer: Any,
    texts: List[str],
    device: str = DEFAULT_DEVICE,
    batch_size: int = 8
) -> List[float]:
    """Compute perplexity for a batch of text segments.

    Args:
        model: Loaded transformer model.
        tokenizer: Loaded tokenizer.
        texts: List of texts to compute perplexity for.
        device: Device to use for computation.
        batch_size: Batch size for processing.

    Returns:
        List of perplexity scores.

    Raises:
        MemoryError: If memory limit exceeded during inference.
    """
    logger.info(f"Computing perplexity for {len(texts)} texts in batches of {batch_size}")

    perplexities = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]

        # Check memory before each batch
        pre_check = check_memory_limit()
        if pre_check['status'] == 'critical':
            raise MemoryError(
                f"Memory limit exceeded before batch {i // batch_size}: "
                f"{pre_check['current_mb']:.2f} MB"
            )

        batch_perplexities = []
        for text in batch:
            pplx = compute_perplexity(model, tokenizer, text, device)
            batch_perplexities.append(pplx)

        perplexities.extend(batch_perplexities)

        logger.debug(f"Processed batch {i // batch_size + 1}: "
                    f"{len(batch)} texts, current memory: {get_total_memory_mb():.2f} MB")

    return perplexities
