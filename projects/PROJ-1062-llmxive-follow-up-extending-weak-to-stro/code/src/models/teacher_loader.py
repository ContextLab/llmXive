"""
Teacher Loader Module for llmXive.

Implements loading of dense Transformer teacher models (pre-RL and post-RL)
using low-precision integer quantization (int8) and CPU offloading to
satisfy the 7GB RAM constraint.
"""
import logging
import gc
from typing import Optional, Tuple, Dict, Any
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

# Import local project utilities
from core.config_validator import load_config
from core.memory_monitor import MemoryMonitor

logger = logging.getLogger(__name__)


class TeacherLoader:
    """
    Handles the loading of dense Transformer teacher models with strict
    memory constraints (int8 quantization + CPU offloading).
    """

    def __init__(self, config_path: str = "config/hyperparams.yaml"):
        """
        Initialize the loader with configuration.

        Args:
            config_path: Path to the hyperparameters YAML file.
        """
        self.config = load_config(config_path)
        self.model_cache: Dict[str, torch.nn.Module] = {}
        self.tokenizer_cache: Dict[str, AutoTokenizer] = {}

    def _get_quantization_config(self) -> BitsAndBytesConfig:
        """
        Constructs the BitsAndBytesConfig for int8 quantization.
        Ensures CPU offloading is enabled to fit within 7GB RAM.
        """
        return BitsAndBytesConfig(
            load_in_8bit=True,
            llm_int8_enable_fp32_cpu_offload=True,
            llm_int8_has_fp16_weight=False,
            llm_int8_skip_modules=["lm_head"], # Keep lm_head in FP32 for stability
            llm_int8_threshold=6.0,
        )

    def load_teacher(
        self,
        model_id: str,
        model_type: str = "pre-rl"
    ) -> Tuple[AutoModelForCausalLM, AutoTokenizer]:
        """
        Loads a teacher model and tokenizer from HuggingFace Hub.

        Args:
            model_id: The HuggingFace model identifier (e.g., "meta-llama/Llama-2-7b").
            model_type: Type of model, either "pre-rl" or "post-rl". Used for logging.

        Returns:
            Tuple of (model, tokenizer).

        Raises:
            ValueError: If model_id is invalid or loading fails.
            RuntimeError: If memory constraints are violated.
        """
        cache_key = f"{model_id}_{model_type}"
        if cache_key in self.model_cache:
            logger.info(f"Returning cached {model_type} model: {model_id}")
            return self.model_cache[cache_key], self.tokenizer_cache[cache_key]

        logger.info(f"Loading {model_type} teacher model: {model_id} (int8 + CPU offload)...")

        # 1. Load Tokenizer
        try:
            tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
            if tokenizer.pad_token is None:
                tokenizer.pad_token = tokenizer.eos_token
            logger.info(f"Tokenizer loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load tokenizer for {model_id}: {e}")
            raise ValueError(f"Tokenizer load failed: {e}")

        # 2. Prepare Quantization Config
        quant_config = self._get_quantization_config()

        # 3. Load Model
        try:
            # Monitor memory before loading
            mem_monitor = MemoryMonitor()
            initial_mem = mem_monitor.get_memory_usage_gb()
            logger.info(f"Initial memory usage: {initial_mem:.2f} GB")

            model = AutoModelForCausalLM.from_pretrained(
                model_id,
                quantization_config=quant_config,
                device_map="auto", # Allows automatic distribution (CPU offload)
                trust_remote_code=True,
                torch_dtype=torch.float16, # Base dtype for non-quantized parts
            )

            final_mem = mem_monitor.get_memory_usage_gb()
            logger.info(f"Model loaded. Memory usage increased by: {final_mem - initial_mem:.2f} GB")

            # Validate model is on correct device map (mixed CPU/GPU)
            if not model.device_map:
                logger.warning("Model device_map is empty. Check CPU offload configuration.")

        except RuntimeError as e:
            if "out of memory" in str(e).lower():
                logger.critical(f"OOM detected during {model_type} model load. "
                                "This exceeds the 7GB RAM constraint even with offloading.")
                raise RuntimeError(f"Memory constraint violation: {e}") from e
            raise

        # Cache results
        self.model_cache[cache_key] = model
        self.tokenizer_cache[cache_key] = tokenizer

        logger.info(f"Successfully loaded {model_type} teacher model: {model_id}")
        return model, tokenizer

    def unload_teacher(self, model_type: str = None):
        """
        Unloads a specific model type or all models to free memory.

        Args:
            model_type: "pre-rl", "post-rl", or None for all.
        """
        keys_to_remove = []
        for key in self.model_cache:
            if model_type is None or key.endswith(model_type):
                keys_to_remove.append(key)

        for key in keys_to_remove:
            logger.info(f"Unloading model: {key}")
            del self.model_cache[key]
            del self.tokenizer_cache[key]

        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        mem_monitor = MemoryMonitor()
        logger.info(f"Memory after unload: {mem_monitor.get_memory_usage_gb():.2f} GB")


def main():
    """
    Entry point for testing the TeacherLoader.
    Loads a dummy/small config to verify the loader works without crashing.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    loader = TeacherLoader()

    # Example usage (commented out to prevent accidental large downloads in test envs)
    # model_id = "HuggingFaceH4/zephyr-7b-beta" # Example small teacher
    # model, tokenizer = loader.load_teacher(model_id, "pre-rl")
    # print(f"Model loaded: {model.__class__.__name__}")

    logger.info("TeacherLoader module initialized successfully.")


if __name__ == "__main__":
    main()