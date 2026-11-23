"""
CPU-safe training loop for Socratic Transformers project.

Implements hard timeout enforcement (FR-008) and fallback to smaller model
(Phi-1.5) if OOM occurs, adhering to compute constraints.
"""
import gc
import os
import signal
import sys
import time
import json
import traceback
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from datetime import datetime

import torch
from datasets import Dataset
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    BitsAndBytesConfig,
)
from src.utils.config import get_config, SocraticConfig
from src.utils.logging import get_logger
from src.train.lora_config import create_lora_config_from_env

# Custom exception for timeout
class TimeoutError(Exception):
    """Raised when training exceeds the hard timeout limit."""
    pass

def timeout_handler(signum, frame):
    """Signal handler for timeout enforcement."""
    raise TimeoutError("Training exceeded the hard timeout limit (FR-008).")

def setup_timeout(seconds: int):
    """Setup a hard timeout using signal alarms (Unix only)."""
    if os.name == 'nt':
        # Windows doesn't support signal.alarm in the same way
        # We'll use a thread-based timeout fallback in run_training_loop if needed
        return
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)

def cancel_timeout():
    """Cancel any active timeout alarm."""
    if os.name != 'nt':
        signal.alarm(0)

def get_fallback_model_path() -> str:
    """
    Returns the path for the fallback model (Phi-1.5) as per FR-008.
    Uses the smaller 1.5B parameter model for CPU/OOM fallback.
    """
    return "microsoft/phi-1.5"

def load_model_and_tokenizer(
    model_name: str,
    config: SocraticConfig,
    use_lora: bool = True,
) -> Tuple[Any, Any]:
    """
    Loads model and tokenizer with 4-bit quantization for CPU efficiency.
    
    Args:
        model_name: HuggingFace model identifier.
        config: SocraticConfig instance.
        use_lora: Whether to apply LoRA configuration.
        
    Returns:
        Tuple of (model, tokenizer)
    """
    logger = get_logger()
    logger.info(f"Loading model: {model_name}")
    
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        
        # Configure 4-bit quantization for memory efficiency
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
        )
        
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            quantization_config=bnb_config,
            device_map="auto", # Let transformers handle device placement
            trust_remote_code=True,
        )
        
        if use_lora:
            lora_config = create_lora_config_from_env(config)
            model = prepare_model_for_kbit_training(model)
            model = get_peft_model(model, lora_config)
            model.print_trainable_parameters()
            
        return model, tokenizer
        
    except Exception as e:
        logger.error(f"Failed to load model {model_name}: {e}")
        raise

def prepare_model_for_lora(model: Any, config: SocraticConfig) -> Any:
    """
    Prepares model for LoRA training by enabling gradient checkpointing
    and preparing for k-bit training.
    """
    model = prepare_model_for_kbit_training(model)
    return model

def run_training_loop(
    model: Any,
    tokenizer: Any,
    train_dataset: Dataset,
    eval_dataset: Optional[Dataset] = None,
    timeout_seconds: int = 21600, # 6 hours default
) -> Dict[str, Any]:
    """
    Executes the training loop with hard timeout and OOM handling.
    
    Args:
        model: The PEFT model.
        tokenizer: The tokenizer.
        train_dataset: Training dataset.
        eval_dataset: Optional evaluation dataset.
        timeout_seconds: Maximum training duration in seconds.
        
    Returns:
        Dictionary containing training results and metrics.
    """
    logger = get_logger()
    config = get_config()
    results = {
        "status": "unknown",
        "model_used": config.model_name,
        "start_time": datetime.now().isoformat(),
        "end_time": None,
        "error": None,
        "metrics": {}
    }
    
    try:
        # Setup hard timeout
        setup_timeout(timeout_seconds)
        
        # Prepare training arguments
        training_args = TrainingArguments(
            output_dir=str(config.output_dir),
            num_train_epochs=config.num_epochs,
            per_device_train_batch_size=config.batch_size,
            per_device_eval_batch_size=config.batch_size,
            gradient_accumulation_steps=config.gradient_accumulation_steps,
            learning_rate=config.learning_rate,
            weight_decay=config.weight_decay,
            warmup_steps=config.warmup_steps,
            logging_steps=config.logging_steps,
            save_steps=config.save_steps,
            evaluation_strategy="steps" if eval_dataset else "no",
            save_strategy="steps",
            load_best_model_at_end=True,
            metric_for_best_model="loss",
            report_to="none", # Disable external reporting for privacy/speed
            fp16=False, # Use bf16 or no mixed precision on CPU
            bf16=False, # Explicitly disable bf16 for CPU safety unless available
            max_grad_norm=config.max_grad_norm,
            remove_unused_columns=False,
        )
        
        # Initialize Trainer
        trainer = Trainer(
            model=model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=eval_dataset,
            tokenizer=tokenizer,
        )
        
        logger.info("Starting training loop...")
        trainer.train()
        
        # Evaluate if dataset provided
        if eval_dataset:
            logger.info("Running evaluation...")
            eval_results = trainer.evaluate()
            results["metrics"] = eval_results
        else:
            # Basic loss from last checkpoint if no eval set
            results["metrics"] = {"final_loss": trainer.state.log_history[-1].get("loss", None)}
        
        results["status"] = "completed"
        logger.info("Training completed successfully.")
        
    except TimeoutError as e:
        results["status"] = "timeout"
        results["error"] = str(e)
        logger.error(f"Training timed out: {e}")
        
    except RuntimeError as e:
        if "CUDA out of memory" in str(e) or "OOM" in str(e):
            results["status"] = "oom_fallback_triggered"
            results["error"] = str(e)
            logger.error(f"OOM error detected: {e}")
            # The caller should handle the fallback logic
            # We raise a specific exception to signal this
            raise RuntimeError(f"OOM: {e}")
        else:
            results["status"] = "failed"
            results["error"] = str(e)
            logger.error(f"Training failed with RuntimeError: {e}")
            raise
            
    except Exception as e:
        results["status"] = "failed"
        results["error"] = str(e)
        logger.error(f"Training failed with unexpected error: {e}")
        traceback.print_exc()
        raise
        
    finally:
        cancel_timeout()
        results["end_time"] = datetime.now().isoformat()
        
        # Log results
        logger.info(f"Training results: {json.dumps(results, indent=2)}")
        
        # Save results to file
        output_file = Path(config.output_dir) / "training_results.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)
            
        return results

def main():
    """
    Main entry point for the training loop script.
    Handles OOM fallback to Phi-1.5 if the primary model fails.
    """
    logger = get_logger()
    logger.info("Starting Socratic Transformers Training Loop (T021)")
    
    config = get_config()
    
    # Try primary model first
    primary_model_name = config.model_name
    fallback_model_name = get_fallback_model_path()
    
    current_model_name = primary_model_name
    max_retries = 1 # Primary + 1 fallback
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            logger.info(f"Attempting to load and train with model: {current_model_name}")
            
            # Load model and tokenizer
            model, tokenizer = load_model_and_tokenizer(current_model_name, config)
            
            # Load data (using static extractor output or downloaded dataset)
            # Assuming data is prepared in data/processed/
            train_path = Path(config.data_dir) / "processed" / "train.json"
            eval_path = Path(config.data_dir) / "processed" / "eval.json"
            
            if not train_path.exists():
                raise FileNotFoundError(f"Training data not found at {train_path}")
            
            train_dataset = Dataset.from_json(str(train_path))
            eval_dataset = Dataset.from_json(str(eval_path)) if eval_path.exists() else None
            
            # Run training
            results = run_training_loop(
                model, 
                tokenizer, 
                train_dataset, 
                eval_dataset,
                timeout_seconds=config.timeout_seconds
            )
            
            logger.info(f"Training finished with status: {results['status']}")
            
            # If we hit OOM on primary, switch to fallback and retry once
            if results['status'] == 'oom_fallback_triggered' and current_model_name == primary_model_name:
                logger.warning("Primary model OOM. Switching to fallback model.")
                current_model_name = fallback_model_name
                retry_count += 1
                gc.collect()
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                continue
            
            # If successful or other error, break
            break
            
        except FileNotFoundError as e:
            logger.error(f"Data file error: {e}")
            raise
        except RuntimeError as e:
            if "OOM" in str(e) and current_model_name == primary_model_name:
                logger.warning("OOM on primary model. Retrying with fallback.")
                current_model_name = fallback_model_name
                retry_count += 1
                gc.collect()
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                continue
            else:
                logger.error(f"Critical error: {e}")
                raise
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise
    
    logger.info("Training process complete.")

if __name__ == "__main__":
    main()