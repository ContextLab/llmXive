"""
Model Loader Utility for Socratic Transformers Project.

Provides functionality to load base models with 4-bit quantization support
via bitsandbytes, optimized for CPU inference and low-memory environments.
"""

import gc
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, PreTrainedModel

# Ensure project root is in path for imports
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.utils.config import get_config

logger = logging.getLogger(__name__)


def get_4bit_quantization_config() -> BitsAndBytesConfig:
    """
    Configure 4-bit quantization using bitsandbytes.

    Returns:
        BitsAndBytesConfig: Configuration for 4-bit quantization.
    """
    return BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4",
        llm_int8_threshold=6.0,
    )


def load_model(
    model_id: str,
    device_map: Optional[Union[str, Dict[str, int]]] = None,
    quantization_config: Optional[BitsAndBytesConfig] = None,
    use_cache: bool = False,
    trust_remote_code: bool = False,
) -> Tuple[PreTrainedModel, AutoTokenizer]:
    """
    Load a pre-trained model and tokenizer with optional 4-bit quantization.

    Args:
        model_id: HuggingFace model identifier (e.g., 'TinyLlama/TinyLlama-1.1B-Chat-v1.0').
        device_map: Device mapping strategy ('auto', 'cpu', or a dict).
        quantization_config: Quantization configuration (default: 4-bit if not specified).
        use_cache: Whether to use KV cache during generation.
        trust_remote_code: Whether to trust remote code in the model.

    Returns:
        Tuple[PreTrainedModel, AutoTokenizer]: Loaded model and tokenizer.

    Raises:
        RuntimeError: If model loading fails due to memory or configuration issues.
        ImportError: If required dependencies (bitsandbytes) are missing.
    """
    logger.info(f"Loading model: {model_id}")

    # Default to 4-bit quantization if not specified
    if quantization_config is None:
        try:
            quantization_config = get_4bit_quantization_config()
            logger.info("Using 4-bit quantization (bitsandbytes)")
        except ImportError as e:
            logger.warning(f"bitsandbytes not available, falling back to standard loading: {e}")
            quantization_config = None

    # Set default device map for CPU if not specified
    if device_map is None:
        # Try auto first, fallback to cpu if OOM
        device_map = "auto"

    try:
        # Load tokenizer first
        tokenizer = AutoTokenizer.from_pretrained(
            model_id,
            trust_remote_code=trust_remote_code,
            padding_side="left",
        )
        if tokenizer.pad_token_id is None:
            tokenizer.pad_token = tokenizer.eos_token
            logger.info("Set pad token to eos token")

        # Load model
        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            device_map=device_map,
            quantization_config=quantization_config,
            use_cache=use_cache,
            trust_remote_code=trust_remote_code,
            torch_dtype=torch.float16,
        )

        # Freeze model parameters (inference mode)
        model.requires_grad_(False)
        model.eval()

        logger.info(f"Successfully loaded model: {model_id}")
        logger.info(f"Model device map: {model.hf_device_map}")

        return model, tokenizer

    except Exception as e:
        logger.error(f"Failed to load model {model_id}: {str(e)}")
        # Cleanup
        if 'model' in locals():
            del model
        if 'tokenizer' in locals():
            del tokenizer
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        raise RuntimeError(f"Model loading failed for {model_id}: {str(e)}") from e


def get_model_card(model_id: str) -> Dict[str, Any]:
    """
    Retrieve basic information about a model from HuggingFace.

    Args:
        model_id: HuggingFace model identifier.

    Returns:
        Dict containing model metadata.
    """
    from transformers import AutoConfig

    try:
        config = AutoConfig.from_pretrained(model_id)
        return {
            "model_id": model_id,
            "model_type": config.model_type,
            "vocab_size": getattr(config, "vocab_size", None),
            "hidden_size": getattr(config, "hidden_size", None),
            "num_attention_heads": getattr(config, "num_attention_heads", None),
            "num_hidden_layers": getattr(config, "num_hidden_layers", None),
        }
    except Exception as e:
        logger.warning(f"Could not retrieve model card for {model_id}: {e}")
        return {"model_id": model_id, "error": str(e)}


def validate_model_compatibility(
    model_id: str,
    max_memory_gb: float = 7.0,
    require_4bit: bool = True,
) -> bool:
    """
    Validate if a model is compatible with the current hardware constraints.

    Args:
        model_id: HuggingFace model identifier.
        max_memory_gb: Maximum available RAM in GB.
        require_4bit: Whether 4-bit quantization is required.

    Returns:
        bool: True if model is compatible, False otherwise.
    """
    model_card = get_model_card(model_id)

    if "error" in model_card:
        logger.error(f"Cannot validate model: {model_card['error']}")
        return False

    # Estimate memory requirements
    # Rough estimate: parameters * bytes_per_param
    # For 4-bit: 0.5 bytes per param (4 bits)
    # Add ~20% overhead for activations, KV cache, etc.

    params = None
    if hasattr(model_card.get("num_hidden_layers", 0), "__mul__"):
        # Approximate parameter count from config
        hidden_size = model_card.get("hidden_size", 0)
        num_layers = model_card.get("num_hidden_layers", 0)
        vocab_size = model_card.get("vocab_size", 0)

        if hidden_size and num_layers and vocab_size:
            # Rough estimate: embedding + transformer layers + lm_head
            # embedding: vocab_size * hidden_size
            # layers: num_layers * (2 * hidden_size^2 + hidden_size * hidden_size)
            # lm_head: hidden_size * vocab_size
            embedding_params = vocab_size * hidden_size
            layer_params = num_layers * (3 * hidden_size * hidden_size)
            lm_head_params = hidden_size * vocab_size
            params = embedding_params + layer_params + lm_head_params

    if params:
        if require_4bit:
            # 4-bit quantization: 0.5 bytes per param
            estimated_gb = (params * 0.5) / (1024**3)
        else:
            # FP16: 2 bytes per param
            estimated_gb = (params * 2) / (1024**3)

        estimated_gb *= 1.2  # 20% overhead

        logger.info(f"Estimated memory for {model_id}: {estimated_gb:.2f} GB")

        if estimated_gb > max_memory_gb:
            logger.warning(
                f"Model {model_id} requires ~{estimated_gb:.2f} GB, "
                f"exceeds available {max_memory_gb} GB"
            )
            return False

    return True


def main() -> None:
    """
    Main entry point for testing model loading.
    """
    config = get_config()

    # Default model for testing (TinyLlama fits in 7GB with 4-bit)
    model_id = config.get("model_id", "TinyLlama/TinyLlama-1.1B-Chat-v1.0")

    logger.info(f"Testing model loader with: {model_id}")

    # Validate compatibility
    if not validate_model_compatibility(model_id, max_memory_gb=7.0, require_4bit=True):
        logger.error(f"Model {model_id} is not compatible with current constraints")
        sys.exit(1)

    try:
        model, tokenizer = load_model(
            model_id=model_id,
            device_map="cpu",  # Force CPU for testing
            use_cache=False,
        )

        logger.info("Model loaded successfully!")
        logger.info(f"Model type: {type(model).__name__}")
        logger.info(f"Tokenizer type: {type(tokenizer).__name__}")

        # Test a simple forward pass
        test_input = "Hello, world!"
        inputs = tokenizer(test_input, return_tensors="pt")
        logger.info(f"Test input tokens: {inputs['input_ids'].shape}")

        with torch.no_grad():
            outputs = model(**inputs)
            logger.info(f"Output logits shape: {outputs.logits.shape}")

        logger.info("Forward pass successful!")

    except Exception as e:
        logger.error(f"Model loading or inference failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    main()
