"""
Model Loader Utility for Socratic Transformers Project.

Implements 4-bit quantization loading via bitsandbytes for CPU/GPU backends.
Supports loading base models (Generator and Critic) as defined in config.
"""

import gc
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import PeftModel

# Import project configuration
try:
    from src.utils.config import get_config, SocraticConfig
except ImportError:
    # Fallback for direct execution or different path context
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from src.utils.config import get_config, SocraticConfig


# Configure logging
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def get_4bit_quantization_config() -> BitsAndBytesConfig:
    """
    Constructs a BitsAndBytesConfig for 4-bit quantization.

    Returns:
        BitsAndBytesConfig: Configuration object for 4-bit loading.
    """
    return BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4",
        llm_int8_enable_fp32_cpu_offload=False,  # Disabled for CPU backend constraint
        llm_int8_has_fp16_weight=False,
        llm_int8_skip_modules=["lm_head"],
    )


def load_model(
    model_id: Optional[str] = None,
    quantize: bool = True,
    device_map: Optional[str] = "auto",
    trust_remote_code: bool = False
) -> Tuple[Any, AutoTokenizer]:
    """
    Loads a transformer model and tokenizer with optional 4-bit quantization.

    Args:
        model_id: The HuggingFace model ID. Defaults to GENERATOR_MODEL_ID from config.
        quantize: Whether to apply 4-bit quantization.
        device_map: Device mapping strategy. Defaults to "auto" for GPU, "cpu" for CPU-only.
        trust_remote_code: Whether to trust remote code.

    Returns:
        Tuple[Model, Tokenizer]: The loaded model and its tokenizer.
    """
    config = get_config()
    if model_id is None:
        model_id = config.GENERATOR_MODEL_ID
        logger.info(f"No model_id provided, using config default: {model_id}")

    logger.info(f"Loading model: {model_id} with quantization={quantize}")

    # Prepare quantization config
    quantization_config = None
    if quantize:
        try:
            quantization_config = get_4bit_quantization_config()
            logger.info("4-bit quantization enabled via bitsandbytes")
        except Exception as e:
            logger.warning(f"Failed to initialize bitsandbytes quantization: {e}. "
                           "Falling back to standard loading (may OOM on large models).")
            quantization_config = None

    # Determine device map
    if device_map == "auto":
        if not torch.cuda.is_available():
            logger.warning("CUDA not available. Forcing device_map='cpu'.")
            device_map = "cpu"
            # Disable 4-bit on CPU if bitsandbytes doesn't support it well in this env
            if quantization_config:
                logger.warning("4-bit quantization requested on CPU. "
                               "Ensure bitsandbytes CPU backend is installed. "
                               "If this fails, set quantize=False.")

    try:
        tokenizer = AutoTokenizer.from_pretrained(
            model_id,
            trust_remote_code=trust_remote_code
        )
        
        # Ensure tokenizer has a pad token
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            quantization_config=quantization_config,
            device_map=device_map,
            trust_remote_code=trust_remote_code,
            torch_dtype=torch.float16 if quantize else torch.float32,
            low_cpu_mem_usage=True
        )

        logger.info(f"Model loaded successfully: {model_id}")
        logger.info(f"Model device: {model.device}")
        
        return model, tokenizer

    except Exception as e:
        logger.error(f"Failed to load model {model_id}: {e}")
        raise


def get_model_card(model_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieves basic metadata for a model from HuggingFace.

    Args:
        model_id: The HuggingFace model ID.

    Returns:
        Dict containing model metadata or None if unavailable.
    """
    try:
        from huggingface_hub import HfApi
        api = HfApi()
        model_info = api.model_info(model_id)
        return {
            "id": model_info.id,
            "author": model_info.author,
            "cardData": model_info.card_data.to_dict() if model_info.card_data else {}
        }
    except Exception as e:
        logger.warning(f"Could not fetch model card for {model_id}: {e}")
        return None


def validate_model_compatibility(model_id: str) -> bool:
    """
    Checks if a model is compatible with the current environment.

    Args:
        model_id: The HuggingFace model ID.

    Returns:
        bool: True if compatible, False otherwise.
    """
    try:
        # Attempt a lightweight config load
        from transformers import AutoConfig
        config = AutoConfig.from_pretrained(model_id)
        logger.info(f"Model config loaded: {config.model_type}")
        
        # Check for known incompatible architectures if necessary
        if hasattr(config, 'architectures'):
            logger.info(f"Architecture: {config.architectures}")
        
        return True
    except Exception as e:
        logger.error(f"Model compatibility check failed for {model_id}: {e}")
        return False


def main():
    """
    Main entry point for testing the model loader.
    Runs a basic load test on the configured Generator model.
    """
    config = get_config()
    model_id = config.GENERATOR_MODEL_ID
    
    print(f"Testing model loader with: {model_id}")
    
    try:
        # Load model (will fail loudly if real source is unreachable or env is wrong)
        model, tokenizer = load_model(model_id=model_id, quantize=True)
        print(f"SUCCESS: Model loaded. Type: {type(model)}")
        print(f"Tokenizer type: {type(tokenizer)}")
        
        # Quick inference test (optional, just to ensure pipeline works)
        test_input = "Hello, this is a test."
        inputs = tokenizer(test_input, return_tensors="pt")
        
        # Move inputs to model device
        inputs = {k: v.to(model.device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=10,
                do_sample=False
            )
        
        result = tokenizer.decode(outputs[0], skip_special_tokens=True)
        print(f"Sample generation: {result}")
        
    except Exception as e:
        print(f"FAILED: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()