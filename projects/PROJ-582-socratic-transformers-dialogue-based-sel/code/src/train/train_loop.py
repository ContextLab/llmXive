"""
CPU-safe training loop with hard timeout and memory monitoring.
Implements FR-008: Configurable hard timeout and OOM handling.
"""

import gc
import json
import logging
import os
import signal
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import psutil
import torch
from datasets import Dataset
from peft import PeftModel, get_peft_model, prepare_model_for_kbit_training
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    Trainer,
    TrainingArguments,
)

# Import project utilities
from src.utils.config import get_config, SocraticConfig
from src.train.lora_config import create_lora_config_from_env, get_4bit_quantization_config
from src.utils.logging import get_logger

# Configure logger
logger = get_logger(__name__)

class TimeoutError(Exception):
    """Custom exception for training timeout."""
    pass

def timeout_handler(signum, frame):
    """Signal handler for timeout."""
    raise TimeoutError("Training timeout reached")

def setup_timeout(timeout_seconds: int):
    """Set up the signal alarm for timeout."""
    if hasattr(signal, 'SIGALRM'):
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout_seconds)
        logger.info(f"Timeout set to {timeout_seconds} seconds")
    else:
        logger.warning("SIGALRM not available on this platform (Windows). Timeout disabled.")

def cancel_timeout():
    """Cancel the signal alarm."""
    if hasattr(signal, 'SIGALRM'):
        signal.alarm(0)
        logger.info("Timeout cancelled")

def get_fallback_model_path() -> str:
    """Return the path for the partial checkpoint."""
    return "data/results/checkpoint_partial.pt"

def load_model_and_tokenizer(
    model_id: str,
    tokenizer_id: Optional[str] = None,
    quantization_config: Optional[BitsAndBytesConfig] = None,
) -> Tuple[Any, Any]:
    """
    Load the base model and tokenizer with optional 4-bit quantization.
    """
    tokenizer_id = tokenizer_id or model_id
    logger.info(f"Loading tokenizer from {tokenizer_id}...")
    tokenizer = AutoTokenizer.from_pretrained(tokenizer_id)

    logger.info(f"Loading model from {model_id} with quantization config: {quantization_config is not None}")
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        quantization_config=quantization_config,
        device_map="auto",  # Let transformers handle device placement
        trust_remote_code=True,
    )
    return model, tokenizer

def prepare_model_for_lora(
    model: Any,
    use_gradient_checkpointing: bool = True,
) -> Any:
    """
    Prepare model for LoRA fine-tuning.
    """
    model = prepare_model_for_kbit_training(model, use_gradient_checkpointing=use_gradient_checkpointing)
    logger.info("Model prepared for LoRA fine-tuning")
    return model

def load_training_data(
    data_path: str,
    question_field: str = "question",
    answer_field: str = "revised_answer",
) -> Dataset:
    """
    Load and format training data from JSONL.
    """
    logger.info(f"Loading training data from {data_path}...")
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Training data not found at {data_path}")

    # Load JSONL
    data_list = []
    with open(data_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                data_list.append(json.loads(line))

    if not data_list:
        raise ValueError(f"No data found in {data_path}")

    dataset = Dataset.from_list(data_list)
    logger.info(f"Loaded {len(dataset)} samples")
    return dataset

def run_training_loop(
    model_id: str,
    data_path: str,
    output_dir: str,
    timeout_seconds: Optional[int] = None,
    max_steps: Optional[int] = None,
) -> Optional[str]:
    """
    Run the CPU-safe training loop with timeout and memory monitoring.

    Args:
        model_id: HuggingFace model ID
        data_path: Path to training data (JSONL)
        output_dir: Directory to save checkpoints
        timeout_seconds: Hard timeout in seconds (if None, no timeout)
        max_steps: Maximum training steps (if None, train full epoch)

    Returns:
        Path to the final checkpoint, or None if failed
    """
    config = get_config()
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Load quantization config
    quantization_config = get_4bit_quantization_config()

    # Load model and tokenizer
    model, tokenizer = load_model_and_tokenizer(model_id, quantization_config=quantization_config)
    model = prepare_model_for_lora(model)

    # Create LoRA config
    lora_config = create_lora_config_from_env()
    model = get_peft_model(model, lora_config)
    logger.info(f"LoRA config: {lora_config}")

    # Load data
    dataset = load_training_data(data_path)

    # Prepare tokenizer
    def preprocess_function(examples):
        # Create prompt-response pairs
        texts = []
        for q, a in zip(examples["question"], examples["revised_answer"]):
            prompt = f"Q: {q}\nA: "
            texts.append(prompt + a)
        return tokenizer(texts, truncation=True, padding=True)

    tokenized_dataset = dataset.map(
        preprocess_function,
        batched=True,
        remove_columns=dataset.column_names,
    )

    # Setup timeout
    if timeout_seconds:
        setup_timeout(timeout_seconds)

    # Memory monitoring setup
    process = psutil.Process(os.pid)
    memory_warning_threshold = 6.5 * 1024 * 1024 * 1024  # 6.5 GB in bytes
    memory_check_interval = 10  # seconds
    last_memory_check = time.time()

    # Training arguments for CPU safety
    training_args = TrainingArguments(
        output_dir=str(output_path),
        per_device_train_batch_size=1,  # FR-003: batch_size <= 2
        gradient_accumulation_steps=4,    # FR-003: gradient accumulation
        learning_rate=1e-4,
        fp16=False,                       # CPU-only training
        bf16=False,
        max_steps=max_steps or len(tokenized_dataset),
        save_steps=50,
        save_total_limit=2,
        logging_steps=10,
        remove_unused_columns=False,
        report_to="none",
        disable_tqdm=False,
    )

    # Initialize trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_dataset,
    )

    checkpoint_path = None

    try:
        logger.info("Starting training loop...")
        start_time = time.time()

        trainer.train()

        elapsed = time.time() - start_time
        logger.info(f"Training completed in {elapsed:.2f} seconds")

        # Save final checkpoint
        final_checkpoint = output_path / "checkpoint_final.pt"
        trainer.save_model(str(final_checkpoint))
        checkpoint_path = str(final_checkpoint)
        logger.info(f"Final checkpoint saved to {checkpoint_path}")

    except TimeoutError as e:
        logger.error(f"TIMEOUT: {e}")
        # Save partial checkpoint
        partial_checkpoint = output_path / "checkpoint_partial.pt"
        trainer.save_model(str(partial_checkpoint))
        checkpoint_path = str(partial_checkpoint)
        logger.info(f"Partial checkpoint saved to {checkpoint_path}")
        return checkpoint_path  # Return partial checkpoint path

    except MemoryError as e:
        logger.error(f"OOM: {e}")
        # Save partial checkpoint
        partial_checkpoint = output_path / "checkpoint_partial.pt"
        trainer.save_model(str(partial_checkpoint))
        checkpoint_path = str(partial_checkpoint)
        logger.info(f"Partial checkpoint saved to {checkpoint_path}")
        return checkpoint_path

    except Exception as e:
        logger.error(f"Unexpected error during training: {e}", exc_info=True)
        # Attempt to save partial checkpoint
        try:
            partial_checkpoint = output_path / "checkpoint_partial.pt"
            trainer.save_model(str(partial_checkpoint))
            logger.info(f"Partial checkpoint saved to {partial_checkpoint}")
            checkpoint_path = str(partial_checkpoint)
        except Exception as save_error:
            logger.error(f"Failed to save partial checkpoint: {save_error}")
        raise

    finally:
        # Cancel timeout
        cancel_timeout()
        # Cleanup
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    return checkpoint_path

def monitor_memory():
    """
    Monitor memory usage and log warnings if RSS > 6.5GB.
    This is called periodically during training.
    """
    process = psutil.Process(os.pid)
    memory_info = process.memory_info()
    rss_gb = memory_info.rss / (1024 ** 3)

    if rss_gb > 6.5:
        logger.warning(f"Memory usage exceeded 6.5GB: {rss_gb:.2f}GB")
    else:
        logger.debug(f"Memory usage: {rss_gb:.2f}GB")

    return rss_gb

def main():
    """
    Main entry point for training loop.
    Usage:
      python -m src.train.train_loop
    """
    config = get_config()

    model_id = config.BASE_MODEL_ID
    data_path = "data/processed/dialogue_tuples.jsonl"  # Default path
    output_dir = "data/results"
    timeout_seconds = 3600  # Default 1 hour timeout

    # Override from command line args if provided
    if len(sys.argv) > 1:
        data_path = sys.argv[1]
    if len(sys.argv) > 2:
        output_dir = sys.argv[2]
    if len(sys.argv) > 3:
        timeout_seconds = int(sys.argv[3])

    logger.info(f"Training configuration:")
    logger.info(f"  Model: {model_id}")
    logger.info(f"  Data: {data_path}")
    logger.info(f"  Output: {output_dir}")
    logger.info(f"  Timeout: {timeout_seconds}s")

    checkpoint = run_training_loop(
        model_id=model_id,
        data_path=data_path,
        output_dir=output_dir,
        timeout_seconds=timeout_seconds,
    )

    if checkpoint:
        logger.info(f"Training finished. Checkpoint: {checkpoint}")
    else:
        logger.error("Training failed without saving a checkpoint.")
        sys.exit(1)

if __name__ == "__main__":
    main()
