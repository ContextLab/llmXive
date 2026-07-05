"""
CPU-safe training loop with hard timeout and OOM fallback.

Implements FR-008 (Hard Timeout) and the adaptive fallback mechanism for
Out-of-Memory (OOM) errors, switching to a smaller model (Phi-1.5) when
the primary model fails on constrained RAM.
"""
import gc
import os
import signal
import sys
import time
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

import torch
from datasets import load_dataset
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments,
    Trainer,
)

from src.utils.config import get_config, SocraticConfig
from src.utils.logging import get_logger
from src.train.lora_config import create_lora_config_from_env

logger = get_logger(__name__)


class TimeoutError(Exception):
    """Custom exception for hard timeout enforcement."""

    pass


def timeout_handler(signum, frame):
    """Signal handler for hard timeout."""
    raise TimeoutError("Training loop exceeded hard timeout limit (FR-008).")


def setup_timeout(seconds: int):
    """
    Sets a hard timeout using signal.SIGALRM.
    Note: Only works on Unix-based systems.
    """
    if os.name == "nt":
        logger.warning("Hard timeout via SIGALRM not supported on Windows. Skipping timeout setup.")
        return

    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)
    logger.info(f"Hard timeout set to {seconds} seconds.")


def cancel_timeout():
    """Cancels the active timeout alarm."""
    if os.name != "nt":
        signal.alarm(0)


def get_fallback_model_path() -> str:
    """Returns the HuggingFace model path for the fallback model."""
    # Phi-1.5 is a 1.3B model, significantly smaller than typical 7B+ models,
    # designed to fit in constrained RAM environments.
    return "microsoft/phi-1.5"


def load_model_and_tokenizer(
    model_name: str,
    config: SocraticConfig,
    quantize: bool = True,
) -> Tuple[Any, Any]:
    """
    Loads a model and tokenizer with 4-bit quantization if enabled.
    """
    logger.info(f"Loading model: {model_name}")

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    if quantize:
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
        )
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            quantization_config=bnb_config,
            device_map="auto" if torch.cuda.is_available() else "cpu",
            trust_remote_code=True,
        )
    else:
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            device_map="auto" if torch.cuda.is_available() else "cpu",
            trust_remote_code=True,
        )

    if not torch.cuda.is_available():
        # For CPU, we might need to prepare for kbit training differently
        # but bitsandbytes 4bit is primarily for GPU.
        # If running on CPU with 4-bit, we might need to rely on CPU quantization
        # or fallback to 8-bit/16-bit if 4-bit is not supported on CPU in this env.
        # However, the spec asks for 4-bit. We attempt standard loading.
        # If bitsandbytes CPU backend is installed, it should work.
        pass

    return model, tokenizer


def prepare_model_for_lora(model: Any, config: SocraticConfig) -> Any:
    """Prepares model for LoRA training."""
    if torch.cuda.is_available():
        model = prepare_model_for_kbit_training(model)
    return model


def run_training_loop(
    model_name: str,
    dataset_name: str,
    output_dir: str,
    timeout_seconds: int = 21600,  # 6 hours default
) -> Dict[str, Any]:
    """
    Executes the training loop with hard timeout and OOM fallback.

    Args:
        model_name: Initial model identifier.
        dataset_name: HuggingFace dataset identifier.
        output_dir: Directory to save checkpoints and logs.
        timeout_seconds: Hard timeout limit in seconds.

    Returns:
        Dictionary with training status and metrics.
    """
    config = get_config()
    logger.info(f"Starting training loop for {model_name} with timeout {timeout_seconds}s")

    # Set up hard timeout
    setup_timeout(timeout_seconds)

    try:
        current_model_name = model_name
        attempt = 0
        max_attempts = 2  # Primary + 1 Fallback

        while attempt < max_attempts:
            attempt += 1
            logger.info(f"Training attempt {attempt} with model: {current_model_name}")

            try:
                # Load Model and Tokenizer
                model, tokenizer = load_model_and_tokenizer(current_model_name, config)

                # Load Dataset
                logger.info(f"Loading dataset: {dataset_name}")
                dataset = load_dataset(dataset_name, split="train[:100]") # Small subset for CPU demo

                # Prepare Data
                def preprocess_function(examples):
                    # Simple prompt construction for training
                    text = f"Question: {examples['question'][0]}\nAnswer: {examples['answer'][0]}"
                    return tokenizer(text, truncation=True, max_length=512)

                tokenized_dataset = dataset.map(
                    preprocess_function,
                    batched=True,
                    remove_columns=dataset.column_names
                )

                # Setup LoRA
                lora_config = create_lora_config_from_env()
                model = prepare_model_for_lora(model, config)
                model = get_peft_model(model, lora_config)
                model.print_trainable_parameters()

                # Training Arguments
                training_args = TrainingArguments(
                    output_dir=output_dir,
                    num_train_epochs=1,
                    per_device_train_batch_size=1, # FR-003: batch_size <= 2
                    gradient_accumulation_steps=4, # FR-003
                    learning_rate=1e-4,
                    fp16=False, # CPU safety
                    logging_steps=10,
                    save_strategy="no",
                    report_to="none",
                )

                # Trainer
                trainer = Trainer(
                    model=model,
                    args=training_args,
                    train_dataset=tokenized_dataset,
                )

                # Train
                logger.info("Starting training...")
                trainer.train()

                # Save
                logger.info("Saving model...")
                trainer.save_model(output_dir)
                tokenizer.save_pretrained(output_dir)

                cancel_timeout()
                return {
                    "status": "success",
                    "model_used": current_model_name,
                    "attempts": attempt,
                    "output_dir": output_dir,
                }

            except RuntimeError as e:
                if "out of memory" in str(e).lower():
                    logger.warning(f"OOM detected on attempt {attempt}: {e}")
                    gc.collect()
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()

                    if attempt < max_attempts:
                        logger.info("Switching to fallback model.")
                        current_model_name = get_fallback_model_path()
                        # Continue loop to retry with fallback
                    else:
                        cancel_timeout()
                        logger.error("OOM occurred on fallback model. Giving up.")
                        return {
                            "status": "failed",
                            "reason": "OOM on fallback model",
                            "attempts": attempt,
                        }
                else:
                    cancel_timeout()
                    raise

    except TimeoutError as e:
        logger.error(f"Hard timeout triggered: {e}")
        cancel_timeout()
        return {
            "status": "failed",
            "reason": "hard_timeout",
            "timeout_seconds": timeout_seconds,
        }
    except Exception as e:
        cancel_timeout()
        logger.error(f"Unexpected error during training: {e}")
        return {
            "status": "failed",
            "reason": str(e),
        }


def main():
    """
    Entry point for the training loop script.
    Reads environment variables for configuration.
    """
    # Default values if env vars not set
    model_name = os.getenv("TRAIN_MODEL_NAME", "Qwen/Qwen2.5-0.5B-Instruct") # Small model for demo
    dataset_name = os.getenv("TRAIN_DATASET_NAME", "gsm8k")
    output_dir = os.getenv("TRAIN_OUTPUT_DIR", "data/results/training_run")
    timeout_seconds = int(os.getenv("TRAIN_TIMEOUT_SECONDS", 21600))

    # Ensure output dir exists
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    result = run_training_loop(
        model_name=model_name,
        dataset_name=dataset_name,
        output_dir=output_dir,
        timeout_seconds=timeout_seconds,
    )

    # Log final result
    logger.info(f"Training completed with status: {result['status']}")
    if result["status"] == "success":
        logger.info(f"Model saved to: {result['output_dir']}")
    else:
        logger.error(f"Training failed: {result.get('reason', 'Unknown error')}")

    return result


if __name__ == "__main__":
    main()