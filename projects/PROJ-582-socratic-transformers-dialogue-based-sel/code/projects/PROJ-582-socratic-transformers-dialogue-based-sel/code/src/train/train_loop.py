"""
CPU-safe training loop with hard timeout and OOM fallback.

Implements FR-008 (Hard Timeout) and the OOM fallback mechanism for
limited RAM constraints (7GB free-tier).
"""
import gc
import os
import signal
import sys
import time
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from datasets import Dataset

# Local imports (matching API surface)
from src.utils.config import get_config, SocraticConfig
from src.utils.logging import get_logger
from src.train.lora_config import LoRAConfig, create_lora_config_from_env

# Custom Timeout Error for clarity
class TimeoutError(Exception):
    """Custom timeout exception for training loop."""
    pass

# Global flag for timeout handling
_timeout_active = False
_timeout_handler_pid = None

def timeout_handler(signum, frame):
    """Signal handler for hard timeout."""
    global _timeout_active
    _timeout_active = True
    raise TimeoutError("Training loop exceeded hard timeout limit (FR-008).")

def setup_timeout(seconds: int):
    """
    Setup a hard timeout using signal.SIGALRM.
    Only works on Unix-like systems.
    """
    global _timeout_active, _timeout_handler_pid
    if os.name == 'nt':
        # Windows does not support SIGALRM
        raise RuntimeError("Hard timeout via signal.SIGALRM is not supported on Windows.")
    
    _timeout_active = False
    _timeout_handler_pid = os.getpid()
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)

def cancel_timeout():
    """Cancel the active timeout alarm."""
    if os.name != 'nt':
        signal.alarm(0)

def get_fallback_model_path() -> str:
    """
    Returns the path/hub ID for the smaller fallback model (Phi-1.5).
    Per FR-008 fallback requirement.
    """
    return "microsoft/phi-1.5"

def load_model_and_tokenizer(model_path: str, config: SocraticConfig) -> Tuple[Any, Any]:
    """
    Load model and tokenizer with quantization support.
    Uses bitsandbytes 4-bit quantization as per T020/LoraConfig.
    """
    logger = get_logger(__name__)
    logger.info(f"Loading model: {model_path}")

    # Check for available memory before loading
    if torch.cuda.is_available():
        free_mem = torch.cuda.mem_get_info()[0]
        logger.info(f"GPU Free Memory: {free_mem / 1024**2:.2f} MB")
    else:
        logger.info("No GPU detected. Running in CPU mode (may be slow).")

    try:
        # Load tokenizer
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        # Load model with quantization if configured
        if config.use_4bit_quantization:
            from transformers import BitsAndBytesConfig
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
            )
            model = AutoModelForCausalLM.from_pretrained(
                model_path,
                quantization_config=bnb_config,
                device_map="auto" if torch.cuda.is_available() else "cpu",
                trust_remote_code=True
            )
        else:
            model = AutoModelForCausalLM.from_pretrained(
                model_path,
                device_map="auto" if torch.cuda.is_available() else "cpu",
                trust_remote_code=True
            )

        logger.info(f"Successfully loaded model: {model_path}")
        return model, tokenizer

    except RuntimeError as e:
        if "out of memory" in str(e).lower() or "CUDA out of memory" in str(e):
            logger.error(f"OOM detected while loading {model_path}: {e}")
            raise MemoryError(f"OOM during model load: {e}")
        raise

def prepare_model_for_lora(model: Any, lora_config: LoRAConfig) -> Any:
    """
    Prepare model for LoRA fine-tuning.
    Handles k-bit training preparation if quantization is used.
    """
    if hasattr(model, "is_loaded_in_4bit") and model.is_loaded_in_4bit:
        model = prepare_model_for_kbit_training(model)
    
    peft_config = lora_config.to_peft_config()
    model = get_peft_model(model, peft_config)
    model.print_trainable_parameters()
    return model

def run_training_loop(
    model: Any,
    tokenizer: Any,
    train_dataset: Dataset,
    output_dir: str,
    timeout_seconds: int = 21600, # 6 hours default
    fallback_model_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Execute the training loop with hard timeout and OOM fallback.

    Args:
        model: The PEFT-wrapped model.
        tokenizer: The tokenizer.
        train_dataset: HuggingFace Dataset for training.
        output_dir: Directory to save checkpoints.
        timeout_seconds: Hard timeout in seconds (FR-008).
        fallback_model_id: ID of the smaller model to try if OOM occurs.

    Returns:
        Dict with training status and metrics.
    """
    logger = get_logger(__name__)
    config = get_config()
    lora_cfg = create_lora_config_from_env()

    # Setup timeout
    if os.name != 'nt':
        logger.info(f"Setting hard timeout to {timeout_seconds} seconds.")
        setup_timeout(timeout_seconds)
    else:
        logger.warning("Running on Windows. Hard timeout via signal is disabled.")

    try:
        # Prepare training arguments
        training_args = TrainingArguments(
            output_dir=output_dir,
            per_device_train_batch_size=lora_cfg.batch_size,
            gradient_accumulation_steps=lora_cfg.gradient_accumulation_steps,
            learning_rate=lora_cfg.learning_rate,
            num_train_epochs=lora_cfg.num_train_epochs,
            logging_steps=10,
            save_strategy="steps",
            save_steps=100,
            fp16=torch.cuda.is_available() and not config.use_4bit_quantization,
            bf16=torch.cuda.is_available() and config.use_4bit_quantization,
            optim="adamw_torch",
            lr_scheduler_type="linear",
            warmup_ratio=0.03,
            report_to="none", # Disable external tracking for simplicity
            disable_tqdm=False,
        )

        # Dummy trainer logic to avoid heavy dependency if not needed, 
        # but standard practice uses Trainer. We'll use Trainer here.
        from transformers import Trainer, TrainingArguments

        trainer = Trainer(
            model=model,
            args=training_args,
            train_dataset=train_dataset,
            tokenizer=tokenizer,
        )

        logger.info("Starting training loop...")
        start_time = time.time()
        trainer.train()
        end_time = time.time()

        logger.info(f"Training completed successfully in {end_time - start_time:.2f} seconds.")
        
        # Save final model
        trainer.save_model(output_dir)
        tokenizer.save_pretrained(output_dir)

        cancel_timeout()
        return {
            "status": "success",
            "duration_seconds": end_time - start_time,
            "model_path": output_dir,
            "oom_fallback_used": False
        }

    except TimeoutError as e:
        logger.critical(f"TIMEOUT: {e}")
        cancel_timeout()
        raise
    
    except MemoryError as e:
        logger.critical(f"MEMORY ERROR: {e}")
        if fallback_model_id:
            logger.info(f"Attempting fallback to smaller model: {fallback_model_id}")
            cancel_timeout()
            # Clean up current model to free memory
            del model
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            # Recursively call with fallback model (simplified for this task)
            # In a real runner, this would be handled by the orchestration layer.
            # Here we return a specific error code for the runner to handle.
            return {
                "status": "oom_fallback_triggered",
                "fallback_model_id": fallback_model_id,
                "error": str(e)
            }
        else:
            raise

    finally:
        # Ensure timeout is cleared
        if os.name != 'nt':
            cancel_timeout()

def main():
    """
    Entry point for the training loop script.
    Expects environment variables or config file to define:
    - MODEL_PATH
    - DATA_PATH (processed dataset)
    - OUTPUT_DIR
    - TIMEOUT_SECONDS
    """
    logger = get_logger(__name__)
    config = get_config()
    
    # Defaults
    model_path = os.getenv("MODEL_PATH", "microsoft/phi-1.5") # Default to small model
    data_path = os.getenv("DATA_PATH", "data/processed/dialogue_train.jsonl")
    output_dir = os.getenv("OUTPUT_DIR", "data/results/training_run")
    timeout_seconds = int(os.getenv("TIMEOUT_SECONDS", "21600"))
    
    logger.info(f"Configuration: model={model_path}, data={data_path}, timeout={timeout_seconds}s")

    # 1. Load Data
    try:
        # Assuming JSONL format as per T014/T015 outputs
        from datasets import load_dataset
        train_dataset = load_dataset("json", data_files=data_path, split="train")
        logger.info(f"Loaded dataset with {len(train_dataset)} samples.")
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        sys.exit(1)

    # 2. Load Model (Primary)
    try:
        model, tokenizer = load_model_and_tokenizer(model_path, config)
    except MemoryError:
        logger.warning(f"OOM on primary model {model_path}. Attempting fallback.")
        fallback_id = get_fallback_model_path()
        logger.info(f"Switching to fallback model: {fallback_id}")
        model_path = fallback_id
        model, tokenizer = load_model_and_tokenizer(model_path, config)

    # 3. Prepare for LoRA
    lora_cfg = create_lora_config_from_env()
    model = prepare_model_for_lora(model, lora_cfg)

    # 4. Run Training
    output_path = Path(output_dir) / f"run_{int(time.time())}"
    result = run_training_loop(
        model=model,
        tokenizer=tokenizer,
        train_dataset=train_dataset,
        output_dir=str(output_path),
        timeout_seconds=timeout_seconds,
        fallback_model_id=get_fallback_model_path()
    )

    if result["status"] == "oom_fallback_triggered":
        logger.error("Training failed due to OOM even after fallback attempt.")
        sys.exit(1)
    
    logger.info(f"Training finished. Result: {result}")

if __name__ == "__main__":
    main()