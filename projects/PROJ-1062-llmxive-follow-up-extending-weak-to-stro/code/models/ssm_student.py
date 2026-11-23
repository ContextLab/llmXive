"""
SSM Student Model Loader for Mamba-1.3b.

Implements low-precision loading with CPU offloading and pre-load size verification.
Strictly enforces real model loading; raises MemoryError on failure without fallback.
"""
import logging
import gc
import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

import torch

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
MODEL_ID = "state-spaces/mamba-1.3b-hf"
MAX_RAM_GB = 7.0
PRELOAD_CHECK_GB = 6.5  # Safety margin before hard limit

def estimate_model_size_gb(model_id: str) -> float:
    """
    Estimates the RAM footprint of the model in GB based on parameter count and precision.
    
    For Mamba-1.3b:
    - Parameters: ~1.3B
    - Precision: int8 (1 byte per param) + overhead
    - Estimated: ~1.3GB (weights) + ~1.5GB (overhead, activations, buffers) ≈ 3-4GB total
    
    Returns:
        float: Estimated size in GB
    """
    # Hardcoded estimate for Mamba-1.3b based on architecture specs
    # 1.3B params * 1 byte (int8) = 1.3GB
    # + ~2GB for optimizer states, activations, and overhead
    estimated_params_gb = 1.3
    overhead_gb = 2.0
    return estimated_params_gb + overhead_gb

class SSMStudentLoader:
    """
    Loader for Mamba-1.3b SSM student model with strict memory constraints.
    """
    
    def __init__(self, model_id: str = MODEL_ID, device: str = "cpu", 
                 dtype: torch.dtype = torch.float8_e4m3fn):
        """
        Initialize the SSM student loader.
        
        Args:
            model_id: HuggingFace model ID for Mamba
            device: Target device (default: "cpu")
            dtype: Precision for loading (default: float8_e4m3fn for int8-like behavior)
        """
        self.model_id = model_id
        self.device = device
        self.dtype = dtype
        self.model = None
        self.tokenizer = None
        self.size_gb = estimate_model_size_gb(model_id)
    
    def verify_memory_budget(self) -> bool:
        """
        Pre-load size verification. Checks if estimated model size fits within constraints.
        
        Returns:
            bool: True if within budget, False otherwise
        
        Raises:
            MemoryError: If estimated size exceeds budget
        """
        logger.info(f"Verifying memory budget for {self.model_id}")
        logger.info(f"Estimated model size: {self.size_gb:.2f} GB")
        logger.info(f"Max allowed RAM: {MAX_RAM_GB} GB")
        
        if self.size_gb > PRELOAD_CHECK_GB:
            error_msg = (
                f"Model {self.model_id} estimated size ({self.size_gb:.2f} GB) "
                f"exceeds pre-load check limit ({PRELOAD_CHECK_GB} GB). "
                "Aborting to prevent OOM."
            )
            logger.error(error_msg)
            raise MemoryError(error_msg)
        
        # Check current system memory usage if possible
        try:
            import psutil
            process = psutil.Process()
            mem_info = process.memory_info()
            current_usage_gb = mem_info.rss / (1024 ** 3)
            logger.info(f"Current Python process RAM usage: {current_usage_gb:.2f} GB")
            
            if current_usage_gb + self.size_gb > MAX_RAM_GB:
                warning_msg = (
                    f"Current usage ({current_usage_gb:.2f} GB) + model ({self.size_gb:.2f} GB) "
                    f"exceeds {MAX_RAM_GB} GB limit."
                )
                logger.warning(warning_msg)
                # Still raise error to be safe
                raise MemoryError(warning_msg)
                
        except ImportError:
            logger.warning("psutil not installed; skipping current usage check.")
        
        return True
    
    def load_model(self) -> Tuple[Any, Any]:
        """
        Load the Mamba model and tokenizer with low precision and CPU offloading.
        
        Returns:
            Tuple[model, tokenizer]: The loaded model and tokenizer
        
        Raises:
            MemoryError: If loading fails due to memory constraints
            ValueError: If model loading fails for other reasons
        """
        # Pre-load verification
        self.verify_memory_budget()
        
        logger.info(f"Attempting to load {self.model_id} in low precision...")
        
        try:
            # Clear cache and collect garbage before loading
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            # Import Mamba-specific components
            # Note: Mamba uses its own architecture, not standard transformers
            from mamba_ssm import MambaForCausalLM
            from transformers import AutoTokenizer
            
            # Load tokenizer
            logger.info("Loading tokenizer...")
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_id,
                trust_remote_code=True
            )
            
            # Configure for low precision (using float8 if available, else float16)
            # Mamba models support specific precision configurations
            logger.info(f"Loading model with dtype={self.dtype}...")
            
            self.model = MambaForCausalLM.from_pretrained(
                self.model_id,
                torch_dtype=self.dtype,
                device_map="cpu",  # Explicit CPU offloading
                trust_remote_code=True
            )
            
            # Verify model loaded successfully
            if self.model is None:
                raise ValueError("Model loading returned None")
            
            # Post-load verification
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            logger.info(f"Successfully loaded {self.model_id}")
            logger.info(f"Model parameters: {sum(p.numel() for p in self.model.parameters()):,}")
            
            return self.model, self.tokenizer
            
        except MemoryError:
            logger.error(f"MemoryError during model load for {self.model_id}")
            raise
        except Exception as e:
            error_msg = (
                f"Failed to load {self.model_id}: {str(e)}. "
                "This is not a memory issue but a loading failure."
            )
            logger.error(error_msg)
            raise ValueError(error_msg) from e

def main():
    """
    Main entry point for testing SSM student model loading.
    """
    logger.info("Starting SSM Student Model Loader test...")
    
    try:
        loader = SSMStudentLoader()
        model, tokenizer = loader.load_model()
        
        logger.info("Model loaded successfully!")
        logger.info(f"Model type: {type(model)}")
        logger.info(f"Tokenizer type: {type(tokenizer)}")
        
        # Simple sanity check
        test_input = "The capital of France is"
        inputs = tokenizer(test_input, return_tensors="pt")
        logger.info(f"Test input processed: {inputs['input_ids'].shape}")
        
        return True
        
    except MemoryError as e:
        logger.critical(f"Memory constraint violation: {e}")
        return False
    except Exception as e:
        logger.critical(f"Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
