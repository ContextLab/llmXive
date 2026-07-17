import os
import gc
import logging
from pathlib import Path
from typing import Optional, Union, Dict, Any, Tuple

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, PreTrainedModel, PreTrainedTokenizer
from peft import PeftModel

from src.utils.config import get_config

logger = logging.getLogger(__name__)

def _get_quantization_config() -> Optional[BitsAndBytesConfig]:
    """
    Constructs a BitsAndBytesConfig for 4-bit quantization to fit Limited RAM constraints.
    This configuration enables CPU offloading if GPU memory is insufficient,
    adhering to the project's compute constraints.
    """
    config = get_config()
    
    # Default to 4-bit quantization for memory efficiency
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        llm_int8_enable_fp32_cpu_offload=True, # Enable CPU offloading for layers that don't fit
        llm_int8_has_fp16_weight=False,
        llm_int8_skip_modules=["lm_head"], # Keep lm_head in fp16 for stability
    )
    return bnb_config

def load_model(
    model_id: str,
    adapter_id: Optional[str] = None,
    device_map: Optional[Union[str, Dict[str, Any]]] = None,
    trust_remote_code: bool = True
) -> Tuple[PreTrainedModel, PreTrainedTokenizer]:
    """
    Loads a base model and tokenizer with low-bit quantization support.
    
    This utility supports:
    1. 4-bit quantization via bitsandbytes (NF4) to reduce RAM usage.
    2. CPU offloading for models that exceed available GPU memory.
    3. Optional loading of LoRA adapters if provided.
    
    Args:
        model_id: HuggingFace model identifier (e.g., 'microsoft/phi-1.5').
        adapter_id: Optional path to LoRA adapter weights.
        device_map: Optional device mapping. If None, 'auto' is used with CPU offloading.
        trust_remote_code: Allow loading models with custom code.
    
    Returns:
        Tuple of (model, tokenizer).
    
    Raises:
        OSError: If the model cannot be loaded due to memory constraints or missing files.
        ValueError: If the model configuration is incompatible with the quantization settings.
    """
    config = get_config()
    model_path = model_id
    tokenizer_path = model_id

    logger.info(f"Loading model: {model_path} with 4-bit quantization...")
    
    # Prepare quantization config
    quantization_config = _get_quantization_config()

    # Determine device map
    if device_map is None:
        # Use 'auto' to let transformers handle placement, 
        # but rely on llm_int8_enable_fp32_cpu_offload for overflow
        device_map = "auto"
        logger.info("Using auto device map with CPU offloading enabled.")

    try:
        # Load tokenizer first
        tokenizer = AutoTokenizer.from_pretrained(
            tokenizer_path,
            trust_remote_code=trust_remote_code,
            padding_side="left"
        )
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        # Load base model with quantization
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            quantization_config=quantization_config,
            device_map=device_map,
            trust_remote_code=trust_remote_code,
            torch_dtype=torch.float16,
            low_cpu_mem_usage=True
        )
        
        logger.info(f"Base model loaded successfully on device: {model.device}")

        # Load LoRA adapter if provided
        if adapter_id:
            logger.info(f"Loading LoRA adapter from: {adapter_id}")
            model = PeftModel.from_pretrained(model, adapter_id)
            logger.info("LoRA adapter loaded and merged.")

        # Ensure model is in eval mode for inference/dialogue generation
        model.eval()
        
        return model, tokenizer

    except Exception as e:
        logger.error(f"Failed to load model {model_path}: {e}")
        # Force garbage collection to free memory before raising
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        raise

def get_model_card(model: PreTrainedModel) -> Dict[str, Any]:
    """
    Extracts metadata from the loaded model's config and card.
    
    Args:
        model: The loaded PreTrainedModel instance.
    
    Returns:
        Dictionary containing model metadata (name, type, parameters).
    """
    card_info = {
        "model_type": getattr(model.config, "model_type", "unknown"),
        "hidden_size": getattr(model.config, "hidden_size", None),
        "num_attention_heads": getattr(model.config, "num_attention_heads", None),
        "num_hidden_layers": getattr(model.config, "num_hidden_layers", None),
        "vocab_size": getattr(model.config, "vocab_size", None),
        "quantization": "4-bit NF4 (bitsandbytes)" if hasattr(model, "hf_quantizer") else "FP16/FP32",
    }
    return card_info

def validate_model_compatibility(
    model: PreTrainedModel,
    max_memory_gb: float = 7.0
) -> bool:
    """
    Validates if the loaded model is compatible with the specified memory constraint.
    
    This function estimates the memory footprint based on the model's parameter count
    and the quantization scheme. It does not measure runtime memory usage directly
    but provides a static check based on configuration.
    
    Args:
        model: The loaded PreTrainedModel instance.
        max_memory_gb: Maximum allowed RAM in GB (default 7.0 for free-tier).
    
    Returns:
        True if the model is estimated to fit, False otherwise.
    
    Note:
        With 4-bit quantization, the model weights occupy approximately 0.5 bytes per parameter.
        Activation memory is handled via CPU offloading if configured.
    """
    num_params = sum(p.numel() for p in model.parameters())
    # Estimate: 0.5 bytes per param for 4-bit + overhead
    estimated_weight_memory_gb = (num_params * 0.5) / (1024**3)
    
    # Add a conservative overhead factor for activations and CPU buffers
    # Even with offloading, we need some headroom
    estimated_total_memory_gb = estimated_weight_memory_gb * 1.5
    
    logger.info(f"Model parameter count: {num_params:,}")
    logger.info(f"Estimated memory footprint: {estimated_total_memory_gb:.2f} GB")
    
    if estimated_total_memory_gb > max_memory_gb:
        logger.warning(f"Model estimated memory ({estimated_total_memory_gb:.2f} GB) exceeds limit ({max_memory_gb} GB). "
                     "Proceed with caution; OOM may occur if CPU offloading is insufficient.")
        return False
    
    logger.info("Model compatibility check passed.")
    return True

def main():
    """
    Entry point for testing the model loader independently.
    Runs a small compatibility check and loads a small model to verify the pipeline.
    """
    from src.utils.config import init_project
    import sys

    # Initialize project structure if not done
    init_project()
    
    # Use a small model for testing (Phi-1.5 is ~1.3B params, fits 4-bit in <2GB)
    test_model_id = "microsoft/phi-1.5"
    
    try:
        model, tokenizer = load_model(test_model_id)
        
        card = get_model_card(model)
        print(f"Model Loaded: {card}")
        
        is_compatible = validate_model_compatibility(model, max_memory_gb=7.0)
        print(f"Compatibility (7GB limit): {is_compatible}")
        
        # Simple inference test to ensure the model is functional
        test_prompt = "Question: What is 2 + 2?\nAnswer:"
        inputs = tokenizer(test_prompt, return_tensors="pt").to(model.device)
        
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=20,
                do_sample=False,
                pad_token_id=tokenizer.pad_token_id
            )
        
        result = tokenizer.decode(outputs[0], skip_special_tokens=True)
        print(f"Test Inference Result: {result}")
        
        # Clean up
        del model, inputs, outputs
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            
        print("Model loader validation successful.")
        return 0

    except Exception as e:
        logger.error(f"Model loader test failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
