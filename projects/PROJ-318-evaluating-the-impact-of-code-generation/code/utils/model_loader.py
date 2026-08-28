"""
Model loading utility with support for 4-bit quantization and strict abort on deviation.
Implements Constitution Principle VII: Strict adherence to specified model configuration.
"""
import logging
from typing import Optional, Tuple
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from transformers import BitsAndBytesConfig
import traceback

from code.utils.config import get_device_and_dtype, get_quantization_config, MODEL_PATH, logger

# Constitution Principle VII: Exact model path requirement
CONSTITUTION_MODEL_PATH = "Salesforce/codegen-350M-mono"

class ModelLoadException(Exception):
    """Custom exception for model loading failures."""
    pass

class ModelDeviationException(ModelLoadException):
    """Exception raised when the loaded model deviates from the Constitution Principle VII requirement."""
    pass

def load_model(
    model_path: str = MODEL_PATH,
    use_4bit: bool = True
) -> Tuple[AutoModelForCausalLM, AutoTokenizer]:
    """
    Loads the specified model with 4-bit quantization if possible.
    
    Implements the strict abort strategy:
    1. Verify the model_path matches Constitution Principle VII exactly.
    2. Attempt 4-bit quantization on GPU (if available).
    3. If 4-bit fails or GPU unavailable, abort (do not fallback to synthetic or incorrect model).
    
    Args:
        model_path: Path to the model on HuggingFace Hub.
        use_4bit: Flag to attempt 4-bit quantization.
        
    Returns:
        Tuple[AutoModelForCausalLM, AutoTokenizer]: The loaded model and tokenizer.
        
    Raises:
        ModelDeviationException: If the model_path does not match Constitution Principle VII.
        ModelLoadException: If the model cannot be loaded or 4-bit quantization fails.
    """
    # Constitution Principle VII Verification
    if model_path != CONSTITUTION_MODEL_PATH:
        raise ModelDeviationException(
            f"Model path '{model_path}' deviates from Constitution Principle VII "
            f"which requires exactly '{CONSTITUTION_MODEL_PATH}'. Aborting."
        )

    logger.info(f"Attempting to load model: {model_path} (Constitution Principle VII verified)")
    
    device, dtype = get_device_and_dtype()
    logger.info(f"Target device: {device}, dtype: {dtype}")

    try:
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        
        # Ensure tokenizer has a pad token for generation
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        if device.type == "cuda" and use_4bit:
            logger.info("Loading with 4-bit quantization on GPU.")
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
        else:
            # Strict abort logic: If we are not on CUDA or 4-bit is disabled,
            # we must abort if the task requires 4-bit on GPU specifically.
            if use_4bit and device.type != "cuda":
                raise ModelLoadException(
                    "4-bit quantization requested but GPU not available. "
                    "Strict abort triggered per Constitution Principle VII constraints."
                )
            
            logger.warning("Falling back to standard loading (CPU or 8-bit/Full Precision) - Deviation from 4-bit target.")
            model = AutoModelForCausalLM.from_pretrained(
                model_path,
                torch_dtype=dtype,
                device_map="auto" if device.type == "cuda" else None,
                load_in_8bit=(device.type == "cuda" and not use_4bit)
            )

        # Verify model integrity
        if model is None:
            raise ModelLoadException("Model failed to load (returned None).")

        # Verify model name matches expectation (internal check)
        if model.config._name_or_path != CONSTITUTION_MODEL_PATH:
            logger.warning(f"Loaded model config name '{model.config._name_or_path}' differs from expected '{CONSTITUTION_MODEL_PATH}'.")

        logger.info(f"Model loaded successfully on {device}.")
        return model, tokenizer

    except ModelDeviationException:
        # Re-raise deviation exceptions immediately
        raise
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        logger.error(traceback.format_exc())
        raise ModelLoadException(f"Model loading failed for {model_path}: {str(e)}")