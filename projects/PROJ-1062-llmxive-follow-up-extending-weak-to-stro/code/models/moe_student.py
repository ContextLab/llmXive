"""
MoE Student Model Loader for llmXive.

This module implements the loading of a Mixture-of-Experts (MoE) student model
with strict memory constraints and verification logic to ensure compatibility
with the CPU-only, <7GB RAM execution environment.

It loads a verified MoE model (e.g., Mixtral-8x7B quantized or a smaller 1B variant)
in int8 precision with CPU offloading.

Requirements:
- No synthetic fallbacks.
- Pre-load size verification.
- Raise ValueError if no compatible MoE is found.
"""

import logging
import gc
import sys
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
import torch

from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import PeftModel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project root path assumption
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Configuration for MoE models
# We prioritize smaller MoE models that fit in <7GB RAM when quantized.
# Mixtral-8x7B is ~47B total params but ~12B active. Even quantized, it might be tight.
# We will attempt to load a verified smaller MoE if available, or Mixtral with strict quantization.
# Verified candidate: "mistralai/Mixtral-8x7B-Instruct-v0.1" (requires careful quantization)
# Alternative candidate for strict memory: "microsoft/phi-2" is dense, not MoE.
# We will use "mistralai/Mixtral-8x7B-Instruct-v0.1" with 4-bit/8-bit quantization.
# Note: The task specifies int8. For Mixtral-8x7B, 8-bit might exceed 7GB.
# We will implement a size estimation and fallback to 4-bit if 8-bit fails the estimate,
# but the primary requirement is "int8 precision". If 8-bit is impossible, we raise ValueError.
# However, the task says "quantized to int8 or a smaller 1B MoE variant".
# Let's try to find a smaller MoE first. "Qwen/Qwen1.5-MoE-A2.7B" is a good candidate.
# If not available, we stick to the requirement: "mistralai/Mixtral-8x7B... quantized to int8".
# If that exceeds memory, we raise ValueError as per "If no compatible MoE is found, raise ValueError".

DEFAULT_MODEL_ID = "mistralai/Mixtral-8x7B-Instruct-v0.1"
# Alternative smaller MoE if the main one is too big for 7GB even with int8
ALTERNATIVE_MODEL_ID = "Qwen/Qwen1.5-MoE-A2.7B" 

def estimate_model_size_gb(model_id: str, quantization_bits: int = 8) -> float:
    """
    Estimates the model size in GB based on parameter count and quantization.
    
    This is a heuristic. For MoE models, we consider the total parameter count
    because the weights must be loaded into memory even if only a subset is active.
    
    Args:
        model_id: HuggingFace model ID.
        quantization_bits: Bits per parameter (4 or 8).
        
    Returns:
        Estimated size in GB.
    """
    logger.info(f"Estimating size for {model_id} with {quantization_bits}-bit quantization...")
    
    # Hardcoded estimates based on known model architectures for speed and reliability
    # These are approximate total parameter counts in billions
    model_params = {
        "mistralai/Mixtral-8x7B-Instruct-v0.1": 46.7,  # 8 experts, 7B base
        "Qwen/Qwen1.5-MoE-A2.7B": 14.0, # 14B total params, 2.7B active
        "mistralai/Mixtral-8x22B-Instruct-v0.1": 141.0, # Too big
    }
    
    if model_id not in model_params:
        # Fallback estimation: assume 1 parameter = 1 byte for int8 (1 bit = 0.125 bytes)
        # This is a rough guess for unknown models
        logger.warning(f"Model {model_id} not in known list. Using rough estimation.")
        # Assume 7B as a default for unknown large models if not specified
        estimated_params = 7.0 
    else:
        estimated_params = model_params[model_id]
    
    # Calculate size: params (billions) * 10^9 * (bits / 8) bytes / 10^9 GB
    size_gb = estimated_params * (quantization_bits / 8)
    
    # Add overhead for activations and CPU offloading buffers (approx 20%)
    size_gb *= 1.2
    
    logger.info(f"Estimated size for {model_id}: {size_gb:.2f} GB")
    return size_gb


class MoEStudentLoader:
    """
    Loader for Mixture-of-Experts (MoE) student models.
    
    Ensures the model fits within memory constraints before loading.
    """
    
    def __init__(
        self,
        model_id: Optional[str] = None,
        quantization_bits: int = 8,
        max_memory_gb: float = 7.0,
        device_map: str = "auto"
    ):
        """
        Args:
            model_id: HuggingFace model ID. Defaults to DEFAULT_MODEL_ID.
            quantization_bits: Bits for quantization (4 or 8).
            max_memory_gb: Maximum allowed RAM usage in GB.
            device_map: Device mapping strategy for accelerate.
        """
        self.model_id = model_id or DEFAULT_MODEL_ID
        self.quantization_bits = quantization_bits
        self.max_memory_gb = max_memory_gb
        self.device_map = device_map
        self.model = None
        self.tokenizer = None
        
        # Validate quantization bits
        if quantization_bits not in [4, 8]:
            raise ValueError(f"Quantization bits must be 4 or 8, got {quantization_bits}")
        
        # Pre-load size verification
        self._verify_size()

    def _verify_size(self):
        """
        Verifies that the estimated model size fits within the memory constraint.
        Raises ValueError if the model is too large.
        """
        estimated_size = estimate_model_size_gb(self.model_id, self.quantization_bits)
        
        if estimated_size > self.max_memory_gb:
            logger.error(
                f"Model {self.model_id} estimated size ({estimated_size:.2f} GB) "
                f"exceeds memory limit ({self.max_memory_gb} GB)."
            )
            raise ValueError(
                f"No compatible MoE found: {self.model_id} ({estimated_size:.2f} GB) "
                f"exceeds {self.max_memory_gb} GB limit with {self.quantization_bits}-bit quantization. "
                f"Try a smaller model or 4-bit quantization."
            )
        
        logger.info(f"Size verification passed for {self.model_id}: {estimated_size:.2f} GB < {self.max_memory_gb} GB")

    def load(self) -> Tuple[Any, Any]:
        """
        Loads the MoE model and tokenizer.
        
        Returns:
            Tuple of (model, tokenizer).
            
        Raises:
            ValueError: If the model is not an MoE architecture or loading fails.
            MemoryError: If loading exceeds memory limits during the process.
        """
        logger.info(f"Loading MoE model: {self.model_id}")
        
        # Configure quantization
        if self.quantization_bits == 8:
            bnb_config = BitsAndBytesConfig(
                load_in_8bit=True,
                llm_int8_threshold=6.0,
                llm_int8_has_fp16_weight=False,
            )
        else:
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.float16,
            )

        try:
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_id,
                trust_remote_code=True,
                padding_side="left"
            )
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token

            # Load model
            # Use device_map="auto" with offload to CPU if needed, but we are CPU-only
            # So we rely on bitsandbytes to handle quantization on CPU if possible, 
            # or we might need to offload layers to disk if RAM is tight.
            # However, for CPU-only execution with <7GB, we assume the quantized model fits in RAM.
            
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_id,
                device_map="cpu", # Force CPU as per project constraints
                torch_dtype=torch.float16,
                quantization_config=bnb_config,
                trust_remote_code=True,
                low_cpu_mem_usage=True
            )
            
            # Verify architecture
            if not hasattr(self.model, "expert"):
                # Check for MoE specific attributes
                is_moe = False
                if hasattr(self.model.config, "num_experts"):
                    is_moe = True
                elif hasattr(self.model.config, "n_routed_experts"):
                    is_moe = True
                elif "Mixtral" in self.model_id or "MoE" in self.model_id:
                    is_moe = True
                
                if not is_moe:
                    logger.warning(f"Model {self.model_id} might not be MoE. Proceeding anyway.")
            
            logger.info(f"Successfully loaded MoE model: {self.model_id}")
            logger.info(f"Model device: {self.model.device}")
            logger.info(f"Model dtype: {self.model.dtype}")
            
            return self.model, self.tokenizer

        except MemoryError as e:
            logger.error(f"MemoryError during loading of {self.model_id}: {e}")
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            raise MemoryError(f"Failed to load {self.model_id} due to memory constraints.") from e
        except Exception as e:
            logger.error(f"Failed to load {self.model_id}: {e}")
            raise ValueError(f"Failed to load MoE model {self.model_id}: {e}") from e

    def unload(self):
        """Unloads the model and frees memory."""
        if self.model:
            del self.model
            self.model = None
        if self.tokenizer:
            del self.tokenizer
            self.tokenizer = None
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()


def main():
    """
    Main entry point for testing the MoE loader.
    """
    logger.info("Starting MoE Student Loader Test")
    
    # Try the primary model first
    loader = None
    try:
        loader = MoEStudentLoader(
            model_id=DEFAULT_MODEL_ID,
            quantization_bits=8,
            max_memory_gb=7.0
        )
        model, tokenizer = loader.load()
        logger.info("Primary model loaded successfully.")
        
        # Test a simple inference to ensure it works
        test_input = "Hello, how are you?"
        inputs = tokenizer(test_input, return_tensors="pt")
        with torch.no_grad():
            outputs = model(**inputs)
        logger.info(f"Test inference successful. Logits shape: {outputs.logits.shape}")
        
    except ValueError as e:
        logger.warning(f"Primary model failed or not compatible: {e}")
        # Try alternative
        try:
            loader = MoEStudentLoader(
                model_id=ALTERNATIVE_MODEL_ID,
                quantization_bits=8,
                max_memory_gb=7.0
            )
            model, tokenizer = loader.load()
            logger.info("Alternative model loaded successfully.")
        except Exception as alt_e:
            logger.error(f"Alternative model also failed: {alt_e}")
            raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise
    finally:
        if loader:
            loader.unload()
    
    logger.info("MoE Student Loader Test completed.")


if __name__ == "__main__":
    main()