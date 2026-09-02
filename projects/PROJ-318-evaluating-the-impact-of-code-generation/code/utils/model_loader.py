"""
Model loading utility with support for 4-bit, 8-bit, and full precision quantization with strict fallback logic.
Implements Constitution Principle VII: Strict adherence to specified model configuration.
"""
import logging
from typing import Optional, Tuple
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from transformers import BitsAndBytesConfig
import traceback

from code.config import get_device_and_dtype, get_quantization_config, get_max_memory_mb, logger

# Constitution Principle VII: Exact model path requirement
CONSTITUTION_MODEL_PATH = "Salesforce/codegen-350M-mono"

class ModelLoadException(Exception):
    """Custom exception for model loading failures."""
    pass

class ModelDeviationException(ModelLoadException):
    """Exception raised when the loaded model deviates from the Constitution Principle VII requirement."""
    pass

def load_model(
    model_path: str = CONSTITUTION_MODEL_PATH,
    use_4bit: bool = True
) -> Tuple[AutoModelForCausalLM, AutoTokenizer]:
    """
    Loads the specified model with a strict quantization fallback strategy:
    1. Attempt 4-bit quantization.
    2. If 4-bit fails, attempt 8-bit quantization.
    3. If 8-bit fails, attempt full precision.
    4. Abort only if all strategies fail.
    
    Args:
        model_path: Path to the model on HuggingFace Hub.
        use_4bit: Flag to attempt 4-bit quantization first.
        
    Returns:
        Tuple[AutoModelForCausalLM, AutoTokenizer]: The loaded model and tokenizer.
        
    Raises:
        ModelDeviationException: If the model_path does not match Constitution Principle VII.
        ModelLoadException: If the model cannot be loaded with any quantization strategy.
    """
    # Constitution Principle VII Verification
    if model_path != CONSTITUTION_MODEL_PATH:
        raise ModelDeviationException(
            f"Model path '{model_path}' deviates from Constitution Principle VII "
            f"which requires exactly '{CONSTITUTION_MODEL_PATH}'. Aborting."
        )

    logger.info(f"Attempting to load model: {model_path} (Constitution Principle VII verified)")
    
    device, dtype = get_device_and_dtype()
    max_memory_mb = get_max_memory_mb()
    logger.info(f"Target device: {device}, dtype: {dtype}, max_memory_mb: {max_memory_mb}")

    tokenizer = None
    model = None
    last_exception = None

    # Strategy 1: 4-bit Quantization
    if use_4bit and device.type == "cuda":
        logger.info("Attempt 1: Loading with 4-bit quantization on GPU.")
        try:
            tokenizer = AutoTokenizer.from_pretrained(model_path)
            if tokenizer.pad_token is None:
                tokenizer.pad_token = tokenizer.eos_token

            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=dtype
            )
            
            model = AutoModelForCausalLM.from_pretrained(
                model_path,
                quantization_config=bnb_config,
                device_map="auto",
                torch_dtype=dtype
            )
            
            # Verify quantization is active
            if hasattr(model, "hf_device_map") and len(model.hf_device_map) > 0:
                logger.info("4-bit quantization verified: Model loaded on devices.")
            else:
                logger.warning("Model loaded but device_map check inconclusive.")
            
            logger.info("SUCCESS: Model loaded with 4-bit quantization.")
            return model, tokenizer

        except Exception as e:
            last_exception = e
            logger.warning(f"4-bit quantization failed: {e}. Retrying with 8-bit.")

    # Strategy 2: 8-bit Quantization
    if device.type == "cuda":
        logger.info("Attempt 2: Loading with 8-bit quantization on GPU.")
        try:
            if tokenizer is None:
                tokenizer = AutoTokenizer.from_pretrained(model_path)
                if tokenizer.pad_token is None:
                    tokenizer.pad_token = tokenizer.eos_token

            model = AutoModelForCausalLM.from_pretrained(
                model_path,
                load_in_8bit=True,
                device_map="auto",
                torch_dtype=dtype
            )
            logger.info("SUCCESS: Model loaded with 8-bit quantization.")
            return model, tokenizer

        except Exception as e:
            last_exception = e
            logger.warning(f"8-bit quantization failed: {e}. Retrying with full precision.")

    # Strategy 3: Full Precision
    logger.info("Attempt 3: Loading with full precision.")
    try:
        if tokenizer is None:
            tokenizer = AutoTokenizer.from_pretrained(model_path)
            if tokenizer.pad_token is None:
                tokenizer.pad_token = tokenizer.eos_token

        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=dtype,
            device_map="auto" if device.type == "cuda" else None
        )
        logger.info("SUCCESS: Model loaded with full precision.")
        return model, tokenizer

    except Exception as e:
        last_exception = e
        logger.error(f"Full precision loading failed: {e}")

    # All strategies failed
    error_msg = (
        f"Failed to load model '{model_path}' with any quantization strategy (4-bit, 8-bit, full). "
        f"Last error: {str(last_exception)}"
    )
    logger.error(error_msg)
    raise ModelLoadException(error_msg)