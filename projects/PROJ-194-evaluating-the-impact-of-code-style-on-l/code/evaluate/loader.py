"""
Loader module for LLM models on CPU.

Implements memory-efficient loading of CodeGen-2B for CPU-only inference.
Uses 8-bit quantization via bitsandbytes (if available) or standard float16/float32
with memory optimization techniques to fit within CI runner constraints.
"""

import os
import torch
from typing import Optional, Dict, Any
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    PreTrainedModel,
    PreTrainedTokenizer
)
from transformers.utils import is_bitsandbytes_available

# Constants for model identification
MODEL_ID = "Salesforce/codegen-2B-mono"

# CPU-specific memory constraints
MAX_CPU_MEMORY_GB = 12  # Adjust based on CI runner specs
TORCH_DTYPE_CPU = torch.float32

# Logging helper
def _log(msg: str) -> None:
    print(f"[Loader] {msg}")

def load_codegen_2b_cpu(
    model_id: Optional[str] = None,
    max_memory: Optional[int] = None,
    use_quantization: bool = True
) -> tuple[PreTrainedModel, PreTrainedTokenizer]:
    """
    Load CodeGen-2B model optimized for CPU inference.
    
    Args:
        model_id: HuggingFace model ID (defaults to CodeGen-2B-mono).
        max_memory: Maximum CPU memory in GB to use.
        use_quantization: Whether to attempt 8-bit quantization if bitsandbytes is available.
    
    Returns:
        Tuple of (model, tokenizer)
    
    Raises:
        RuntimeError: If model cannot be loaded within memory constraints.
    """
    if model_id is None:
        model_id = MODEL_ID
    
    _log(f"Loading model: {model_id}")
    
    # Load tokenizer first
    _log("Loading tokenizer...")
    try:
        tokenizer = AutoTokenizer.from_pretrained(
            model_id,
            trust_remote_code=True,
            padding_side="left"
        )
        # Set pad token if not set
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
    except Exception as e:
        _log(f"Error loading tokenizer: {e}")
        raise RuntimeError(f"Failed to load tokenizer: {e}")
    
    # Determine device and dtype
    device = "cpu"
    
    # Attempt quantization if requested and available
    quantization_config = None
    if use_quantization and is_bitsandbytes_available():
        _log("Attempting 8-bit quantization via bitsandbytes...")
        try:
            quantization_config = BitsAndBytesConfig(
                load_in_8bit=True,
                llm_intest_threshold=0.0,
                llm_intest_enable_fp32_cpu=False
            )
        except Exception as e:
            _log(f"Quantization config creation failed: {e}, falling back to float32")
            quantization_config = None
    
    # Prepare model kwargs
    model_kwargs = {
        "trust_remote_code": True,
        "device_map": "auto",
        "torch_dtype": torch.float32,
        "low_cpu_mem_usage": True,
    }
    
    # If quantization is enabled and config exists, use it
    if quantization_config:
        model_kwargs["quantization_config"] = quantization_config
        # For 8-bit, we usually let device_map handle distribution, 
        # but ensure it works on CPU by not forcing GPU
        model_kwargs["device_map"] = "auto"
    else:
        # Standard float32 loading for CPU
        _log("Loading model in standard float32 (no quantization)...")
        model_kwargs["torch_dtype"] = torch.float32
        model_kwargs["device_map"] = "cpu"
        # Explicitly remove device_map if we are forcing CPU-only to avoid auto-placement issues
        # In strict CPU mode, we load onto CPU directly
        del model_kwargs["device_map"]
        model_kwargs["device_map"] = "cpu" 
        # Note: device_map="cpu" is not standard for CPU-only in older transformers, 
        # so we rely on default behavior + manual placement if needed.
        # Actually, for CPU, we just load normally.
        model_kwargs.pop("device_map", None)
    
    try:
        _log("Instantiating model...")
        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            **model_kwargs
        )
        
        # If not using device_map, ensure model is on CPU
        if not hasattr(model, 'hf_device_map') or model.hf_device_map is None:
            model = model.to("cpu")
        
        _log(f"Model loaded successfully. Dtype: {model.dtype}")
        return model, tokenizer
        
    except RuntimeError as e:
        _log(f"Model loading failed: {e}")
        # Fallback strategy: try without low_cpu_mem_usage if OOM
        if "out of memory" in str(e).lower() or "cannot allocate" in str(e).lower():
            _log("Retrying with reduced memory optimization settings...")
            model_kwargs.pop("low_cpu_mem_usage", None)
            try:
                model = AutoModelForCausalLM.from_pretrained(model_id, **model_kwargs)
                if not hasattr(model, 'hf_device_map') or model.hf_device_map is None:
                    model = model.to("cpu")
                return model, tokenizer
            except Exception as retry_e:
                raise RuntimeError(f"Failed to load model even with reduced optimization: {retry_e}")
        else:
            raise RuntimeError(f"Failed to load model: {e}")

def run_loader_test() -> None:
    """
    Simple test to verify the loader works without running full inference.
    Checks if the model can be instantiated and moved to CPU.
    """
    _log("Running loader self-test...")
    try:
        model, tokenizer = load_codegen_2b_cpu()
        _log("Loader test passed: Model and Tokenizer loaded successfully.")
        
        # Verify model is on CPU
        # Check if any parameter is on CUDA
        has_cuda = any(p.is_cuda for p in model.parameters())
        if has_cuda:
            _log("WARNING: Model parameters found on CUDA device!")
        else:
            _log("Confirmed: All model parameters are on CPU.")
            
        # Verify tokenizer works
        test_input = "def hello_world():\n    pass"
        tokens = tokenizer(test_input, return_tensors="pt")
        _log(f"Tokenizer test passed. Input tokens: {tokens['input_ids'].shape}")
        
    except Exception as e:
        _log(f"Loader test failed: {e}")
        raise

def main() -> None:
    """Entry point for running the loader test."""
    run_loader_test()

if __name__ == "__main__":
    main()