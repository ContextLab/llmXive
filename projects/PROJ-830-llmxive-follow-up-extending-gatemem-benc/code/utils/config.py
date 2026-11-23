"""
Configuration management for the GateMem benchmark pipeline.
Provides singleton access to shared resources like the LLM backbone.
"""
import logging
import uuid
from typing import Optional, Dict, Any
from threading import Lock

# Import profiling utilities to ensure standardized metrics if needed later
# Note: The actual LLM loading logic is deferred to the first call to ensure
# the model is only loaded when actually used, and to allow for CPU enforcement.
try:
    from transformers import AutoModelForCausalLM, AutoTokenizer
    import torch
except ImportError:
    # Handle cases where transformers/torch might not be installed in test environments
    # but the config module is imported. The actual error will surface on first use.
    AutoModelForCausalLM = None
    AutoTokenizer = None
    torch = None

from code.logging_config import setup_logging, pin_random_seed

logger = setup_logging(__name__)

# Configuration constants
LLM_MODEL_ID = "meta-llama/Llama-3-8B"  # Default backbone as per task description
# Fallback to a smaller open model if Llama-3 is not accessible, but we aim for the specified one.
# In a real run, if this ID is not available, the fetch will fail loudly as per data principles.
# For the sake of the singleton pattern implementation, we use the ID string.
# If the environment cannot resolve this, the initialization will raise an error.

# Singleton State
_llm_instance = None
_instance_id = None
_lock = Lock()
_initialized = False


class LLMConfig:
    """Configuration container for the LLM backbone."""
    def __init__(
        self,
        model_id: str = LLM_MODEL_ID,
        device: str = "cpu",
        max_length: int = 2048,
        temperature: float = 0.0, # Deterministic for benchmarking
        do_sample: bool = False,
        seed: int = 42
    ):
        self.model_id = model_id
        self.device = device
        self.max_length = max_length
        self.temperature = temperature
        self.do_sample = do_sample
        self.seed = seed
        self.tokenizer = None
        self.model = None

    def __repr__(self):
        return f"LLMConfig(model_id={self.model_id}, device={self.device})"


def get_llm_singleton() -> Dict[str, Any]:
    """
    Returns a singleton instance of the LLM backbone (Llama-3-8B).
    
    This function ensures that:
    1. The model is loaded only once across the entire process.
    2. CPU execution is enforced for reproducibility.
    3. A unique instance_id is generated and exposed for verification.
    4. Random seeds are pinned for deterministic behavior.
    
    Returns:
        Dict containing:
            - 'instance_id': Unique string ID for this singleton instance.
            - 'model': The loaded transformer model (if successful).
            - 'tokenizer': The loaded tokenizer.
            - 'config': The LLMConfig object.
            - 'status': 'initialized' or 'failed'.
            - 'error': Error message if initialization failed.
    
    Raises:
        RuntimeError: If the model cannot be loaded (e.g., missing dependencies, 
                      network issues, or model not found) and no synthetic fallback is allowed.
    """
    global _llm_instance, _instance_id, _initialized

    # Double-checked locking for thread safety
    if _initialized and _llm_instance is not None:
        return {
            "instance_id": _instance_id,
            "model": _llm_instance.model,
            "tokenizer": _llm_instance.tokenizer,
            "config": _llm_instance.config,
            "status": "initialized"
        }

    with _lock:
        if _initialized and _llm_instance is not None:
            return {
                "instance_id": _instance_id,
                "model": _llm_instance.model,
                "tokenizer": _llm_instance.tokenizer,
                "config": _llm_instance.config,
                "status": "initialized"
            }

        # Attempt initialization
        try:
            if AutoModelForCausalLM is None or torch is None:
                raise ImportError(
                    "Transformers or PyTorch not installed. "
                    "Install with: pip install transformers torch"
                )

            # Pin random seed for reproducibility
            pin_random_seed(42)

            # Create config
            config = LLMConfig(
                model_id=LLM_MODEL_ID,
                device="cpu", # Explicitly enforce CPU as per constraints
                temperature=0.0,
                do_sample=False,
                seed=42
            )

            logger.info(f"Initializing LLM Singleton: {config.model_id}")
            logger.info(f"Enforcing CPU execution: device={config.device}")

            # Load Tokenizer
            config.tokenizer = AutoTokenizer.from_pretrained(
                config.model_id,
                trust_remote_code=True
            )
            
            # Handle cases where tokenizer doesn't have a pad token
            if config.tokenizer.pad_token is None:
                config.tokenizer.pad_token = config.tokenizer.eos_token

            # Load Model
            # Using float32 for stability on CPU unless memory is extremely constrained.
            # If memory error occurs, this would typically require quantization, 
            # but the task specifies identical instance usage, implying standard loading first.
            config.model = AutoModelForCausalLM.from_pretrained(
                config.model_id,
                torch_dtype=torch.float32, # Explicit CPU dtype
                device_map="cpu"
            )
            
            # Ensure model is in eval mode
            config.model.eval()
            
            # Generate unique instance ID
            _instance_id = str(uuid.uuid4())
            _llm_instance = type('LLMWrapper', (), {'model': config.model, 'tokenizer': config.tokenizer, 'config': config})()
            _initialized = True

            logger.info(f"LLM Singleton initialized successfully with ID: {_instance_id}")

            return {
                "instance_id": _instance_id,
                "model": config.model,
                "tokenizer": config.tokenizer,
                "config": config,
                "status": "initialized"
            }

        except Exception as e:
            logger.critical(f"Failed to initialize LLM Singleton: {str(e)}")
            # Fail loudly: Do not return a mock or partial object.
            # The caller must handle this error or the process exits.
            raise RuntimeError(f"LLM Initialization Failed: {str(e)}") from e
