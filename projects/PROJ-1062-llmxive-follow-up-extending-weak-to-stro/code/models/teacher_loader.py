"""
Teacher model loader for dense Transformer models (pre-RL and post-RL).

Loads models in int8 precision with CPU offloading to fit within memory constraints.
Supports both pre-RL and post-RL teacher checkpoints.
"""

import logging
import gc
from typing import Optional, Tuple, Dict, Any
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import PeftModel

# Import existing utilities from project
from core.memory_monitor import MemoryMonitor
from core.hard_floor_enforcer import HardFloorEnforcer

logger = logging.getLogger(__name__)

# Memory constraints (from FR-007)
MAX_RAM_GB = 7.0
HARD_FLOOR_BATCH_SIZE = 1


class TeacherLoader:
    """
    Loader for dense Transformer teacher models with int8 quantization and CPU offloading.
    
    Supports:
    - Pre-RL teacher models (base models)
    - Post-RL teacher models (fine-tuned with adapters)
    - Automatic memory monitoring and fallback to hard floor
    """
    
    def __init__(
        self,
        model_id: str,
        checkpoint_path: Optional[str] = None,
        use_post_rl: bool = False,
        max_memory_gb: float = MAX_RAM_GB,
        device_map: str = "auto",
        offload_folder: str = "offload"
    ):
        """
        Initialize teacher loader.
        
        Args:
            model_id: HuggingFace model ID (e.g., 'mistralai/Mistral-7B-v0.1')
            checkpoint_path: Path to post-RL checkpoint (PEFT adapters) if applicable
            use_post_rl: Whether to load post-RL adapters
            max_memory_gb: Maximum RAM usage in GB
            device_map: Device mapping strategy ('auto', 'cpu', etc.)
            offload_folder: Folder for CPU offloading
        """
        self.model_id = model_id
        self.checkpoint_path = checkpoint_path
        self.use_post_rl = use_post_rl
        self.max_memory_gb = max_memory_gb
        self.device_map = device_map
        self.offload_folder = offload_folder
        
        self.model = None
        self.tokenizer = None
        self.memory_monitor = MemoryMonitor()
        self.hard_floor = HardFloorEnforcer(
            hard_floor_batch_size=HARD_FLOOR_BATCH_SIZE
        )
        
    def _compute_quantization_config(self) -> BitsAndBytesConfig:
        """
        Configure int8 quantization for memory efficiency.
        
        Returns:
            BitsAndBytesConfig for int8 quantization with CPU offloading
        """
        return BitsAndBytesConfig(
            load_in_8bit=True,
            llm_int8_threshold=6.0,
            llm_int8_has_fp16_weight=False,
            llm_int8_skip_modules=["lm_head"],
            llm_int8_enable_fp32_cpu_offload=True,
        )
    
    def _verify_model_size(self, estimated_params: int) -> bool:
        """
        Verify model size fits within memory constraints before loading.
        
        Args:
            estimated_params: Estimated number of parameters in the model
        
        Returns:
            True if model should fit, False otherwise
        
        Raises:
            RuntimeError: If model is too large for available memory
        """
        # Int8 quantization: 1 byte per parameter + overhead (~20%)
        estimated_size_gb = (estimated_params * 1.2) / (1024 ** 3)
        
        if estimated_size_gb > self.max_memory_gb:
            raise RuntimeError(
                f"Model {self.model_id} estimated size ({estimated_size_gb:.2f} GB) "
                f"exceeds memory constraint ({self.max_memory_gb} GB). "
                f"Consider using a smaller model or increasing memory."
            )
        
        logger.info(
            f"Model size verification passed: {estimated_size_gb:.2f} GB "
            f"< {self.max_memory_gb} GB constraint"
        )
        return True
    
    def load(self) -> Tuple[Any, Any]:
        """
        Load the teacher model and tokenizer.
        
        Returns:
            Tuple of (model, tokenizer)
        
        Raises:
            FileNotFoundError: If model checkpoint not found
            RuntimeError: If model loading fails or memory constraints violated
        """
        logger.info(f"Loading teacher model: {self.model_id}")
        logger.info(f"Post-RL checkpoint: {self.checkpoint_path if self.use_post_rl else 'None'}")
        
        # Pre-load verification
        try:
            from transformers import AutoConfig
            config = AutoConfig.from_pretrained(self.model_id)
            estimated_params = config.hidden_size * config.num_attention_heads * config.num_hidden_layers
            # Rough estimate for decoder-only models
            estimated_params = config.to_dict().get('num_parameters', estimated_params * 2)
            
            if not self._verify_model_size(estimated_params):
                raise RuntimeError("Model size verification failed")
        except Exception as e:
            logger.warning(f"Pre-load size check failed: {e}")
            # Continue with loading, let memory monitor handle OOM
        
        # Configure quantization
        quantization_config = self._compute_quantization_config()
        
        try:
            # Load tokenizer
            logger.info("Loading tokenizer...")
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_id,
                trust_remote_code=True
            )
            
            # Set pad token if not set
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            # Load base model
            logger.info("Loading base model with int8 quantization...")
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_id,
                quantization_config=quantization_config,
                device_map=self.device_map,
                offload_folder=self.offload_folder,
                torch_dtype=torch.float16,
                trust_remote_code=True,
                low_cpu_mem_usage=True
            )
            
            # Load post-RL adapters if specified
            if self.use_post_rl and self.checkpoint_path:
                logger.info(f"Loading post-RL adapters from: {self.checkpoint_path}")
                if not Path(self.checkpoint_path).exists():
                    raise FileNotFoundError(
                        f"Post-RL checkpoint not found at: {self.checkpoint_path}"
                    )
                
                self.model = PeftModel.from_pretrained(
                    self.model,
                    self.checkpoint_path,
                    device_map=self.device_map
                )
            
            # Post-load memory check
            gc.collect()
            torch.cuda.empty_cache() if torch.cuda.is_available() else None
            
            current_ram_gb = self.memory_monitor.get_current_ram_usage_gb()
            logger.info(f"Model loaded. Current RAM usage: {current_ram_gb:.2f} GB")
            
            if current_ram_gb > self.max_memory_gb * 0.9:
                logger.warning(
                    f"RAM usage ({current_ram_gb:.2f} GB) approaching limit "
                    f"({self.max_memory_gb} GB). Enforcing hard floor."
                )
                self.hard_floor.enforce_hard_floor()
            
            logger.info(f"Successfully loaded teacher model: {self.model_id}")
            return self.model, self.tokenizer
            
        except Exception as e:
            logger.error(f"Failed to load teacher model: {e}")
            # Clean up partial loads
            if self.model:
                del self.model
            if self.tokenizer:
                del self.tokenizer
            gc.collect()
            raise RuntimeError(f"Model loading failed: {e}") from e
    
    def unload(self) -> None:
        """Unload the model to free memory."""
        if self.model:
            del self.model
            self.model = None
        if self.tokenizer:
            del self.tokenizer
            self.tokenizer = None
        gc.collect()
        torch.cuda.empty_cache() if torch.cuda.is_available() else None
        logger.info("Teacher model unloaded")
    
    @staticmethod
    def load_pre_rl_teacher(
        model_id: str,
        max_memory_gb: float = MAX_RAM_GB
    ) -> Tuple[Any, Any]:
        """
        Convenience method to load a pre-RL teacher model.
        
        Args:
            model_id: HuggingFace model ID
            max_memory_gb: Maximum RAM usage in GB
        
        Returns:
            Tuple of (model, tokenizer)
        """
        loader = TeacherLoader(
            model_id=model_id,
            use_post_rl=False,
            max_memory_gb=max_memory_gb
        )
        return loader.load()
    
    @staticmethod
    def load_post_rl_teacher(
        model_id: str,
        checkpoint_path: str,
        max_memory_gb: float = MAX_RAM_GB
    ) -> Tuple[Any, Any]:
        """
        Convenience method to load a post-RL teacher model.
        
        Args:
            model_id: HuggingFace base model ID
            checkpoint_path: Path to post-RL checkpoint
            max_memory_gb: Maximum RAM usage in GB
        
        Returns:
            Tuple of (model, tokenizer)
        """
        loader = TeacherLoader(
            model_id=model_id,
            checkpoint_path=checkpoint_path,
            use_post_rl=True,
            max_memory_gb=max_memory_gb
        )
        return loader.load()


def main():
    """
    Main function to demonstrate teacher model loading.
    
    Usage:
        python -m models.teacher_loader --model_id mistralai/Mistral-7B-v0.1
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Load teacher model")
    parser.add_argument(
        "--model_id",
        type=str,
        default="mistralai/Mistral-7B-v0.1",
        help="HuggingFace model ID"
    )
    parser.add_argument(
        "--checkpoint",
        type=str,
        default=None,
        help="Path to post-RL checkpoint (optional)"
    )
    parser.add_argument(
        "--post_rl",
        action="store_true",
        help="Load as post-RL model"
    )
    parser.add_argument(
        "--max_memory_gb",
        type=float,
        default=MAX_RAM_GB,
        help=f"Maximum RAM usage in GB (default: {MAX_RAM_GB})"
    )
    
    args = parser.parse_args()
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        if args.post_rl and not args.checkpoint:
            raise ValueError("--checkpoint required for post-RL model")
        
        loader = TeacherLoader(
            model_id=args.model_id,
            checkpoint_path=args.checkpoint,
            use_post_rl=args.post_rl,
            max_memory_gb=args.max_memory_gb
        )
        
        model, tokenizer = loader.load()
        
        logger.info("Model loaded successfully!")
        logger.info(f"Model type: {type(model)}")
        logger.info(f"Tokenizer type: {type(tokenizer)}")
        
        # Test inference
        test_prompt = "Hello, how are you?"
        inputs = tokenizer(test_prompt, return_tensors="pt")
        
        logger.info(f"Test inference: '{test_prompt}'")
        logger.info(f"Input shape: {inputs['input_ids'].shape}")
        
        # Unload to free memory
        loader.unload()
        
    except Exception as e:
        logger.error(f"Error: {e}")
        raise


if __name__ == "__main__":
    main()
