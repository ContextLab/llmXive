"""
Condition B (Ablation) Training Run.

Fine-tunes the base model on the ablation dataset (data/processed/ablation_tuples.jsonl)
using LoRA and 4-bit quantization.

Output: data/results/checkpoint_ablation.pt
Dependency: T015b (Ablation data generation)
"""
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

import torch
from datasets import Dataset
from peft import PeftConfig, PeftModel
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    BitsAndBytesConfig,
)

# Project root path handling
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
CODE_ROOT = PROJECT_ROOT / "code"

# Add code root to path for imports
if str(CODE_ROOT) not in sys.path:
    sys.path.insert(0, str(CODE_ROOT))

from src.utils.config import get_config, SocraticConfig
from src.train.lora_config import LoRAConfig, get_4bit_quantization_config, create_lora_config_from_env
from src.train.train_loop import (
    load_model_and_tokenizer, 
    prepare_model_for_lora, 
    run_training_loop, 
    TimeoutError, 
    setup_timeout
)
from src.utils.logging import get_logger

# Configure logging
logger = get_logger("run_ablation_train")

def load_ablation_data(file_path: Path) -> List[Dict[str, str]]:
    """
    Load the ablation dataset from JSONL file.
    
    Args:
        file_path: Path to the JSONL file (e.g., data/processed/ablation_tuples.jsonl)
        
    Returns:
        List of dictionaries containing the training tuples.
    """
    data = []
    if not file_path.exists():
        raise FileNotFoundError(f"Ablation data file not found: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                # Validate required fields based on ablation schema
                # Expected: question, initial_answer, critique (neutral placeholder), revised_answer
                required_keys = ['question', 'initial_answer', 'critique', 'revised_answer']
                if not all(key in record for key in required_keys):
                    logger.warning(f"Skipping line {line_num}: Missing required keys. Keys found: {list(record.keys())}")
                    continue
                data.append(record)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON on line {line_num}: {e}")
                continue
    
    if not data:
        raise ValueError(f"No valid records found in {file_path}")
    
    logger.info(f"Loaded {len(data)} ablation tuples from {file_path}")
    return data

def prepare_dataset(data: List[Dict[str, str]], tokenizer: Any) -> Dataset:
    """
    Prepare the dataset for training by formatting the input sequences.
    
    The training objective is to generate the 'revised_answer' given the 
    context of 'question', 'initial_answer', and 'critique'.
    
    Args:
        data: List of raw tuples.
        tokenizer: The tokenizer instance.
        
    Returns:
        HuggingFace Dataset object ready for training.
    """
    def format_example(examples):
        inputs = []
        labels = []
        
        for i in range(len(examples['question'])):
            # Construct the prompt
            prompt = (
                f"Question: {examples['question'][i]}\n"
                f"Initial Answer: {examples['initial_answer'][i]}\n"
                f"Critique: {examples['critique'][i]}\n"
                f"Revised Answer:"
            )
            
            target = examples['revised_answer'][i]
            
            # Tokenize the prompt
            tokenized_prompt = tokenizer(prompt, truncation=True, max_length=512)
            # Tokenize the target (label)
            tokenized_target = tokenizer(target, truncation=True, max_length=512)
            
            # Combine input and label, but we need to mask the prompt for loss calculation
            # Standard approach: input_ids = prompt + target, labels = [-100]*len(prompt) + target_ids
            input_ids = tokenized_prompt['input_ids'] + tokenized_target['input_ids']
            attention_mask = [1] * len(input_ids)
            
            # Create labels: -100 for prompt tokens (ignore in loss), target tokens for loss
            labels = [-100] * len(tokenized_prompt['input_ids']) + tokenized_target['input_ids']
            
            inputs.append({
                'input_ids': input_ids,
                'attention_mask': attention_mask,
                'labels': labels
            })
        
        # Convert list of dicts to a single dict of lists for Dataset
        return {
            'input_ids': [x['input_ids'] for x in inputs],
            'attention_mask': [x['attention_mask'] for x in inputs],
            'labels': [x['labels'] for x in inputs]
        }

    # Create HF Dataset
    ds = Dataset.from_list(data)
    # Apply formatting
    formatted_ds = ds.map(
        format_example,
        batched=True,
        remove_columns=ds.column_names
    )
    
    logger.info(f"Prepared dataset with {len(formatted_ds)} examples")
    return formatted_ds

def main():
    """Main entry point for the Ablation Training Run."""
    logger.info("Starting Ablation Training Run (Condition B)")
    
    # 1. Load Configuration
    config: SocraticConfig = get_config()
    
    # Define paths relative to project root
    data_path = PROJECT_ROOT / "data" / "processed" / "ablation_tuples.jsonl"
    output_dir = PROJECT_ROOT / "data" / "results"
    output_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_path = output_dir / "checkpoint_ablation.pt"
    
    logger.info(f"Data path: {data_path}")
    logger.info(f"Output path: {checkpoint_path}")
    
    # 2. Load Data
    try:
        raw_data = load_ablation_data(data_path)
    except (FileNotFoundError, ValueError) as e:
        logger.critical(f"Failed to load ablation data: {e}")
        sys.exit(1)
    
    # 3. Load Model and Tokenizer
    try:
        model, tokenizer = load_model_and_tokenizer(config)
    except Exception as e:
        logger.critical(f"Failed to load model/tokenizer: {e}")
        sys.exit(1)
    
    # 4. Prepare Model for LoRA
    try:
        model = prepare_model_for_lora(model, config)
    except Exception as e:
        logger.critical(f"Failed to prepare model for LoRA: {e}")
        sys.exit(1)
    
    # 5. Prepare Dataset
    try:
        train_dataset = prepare_dataset(raw_data, tokenizer)
    except Exception as e:
        logger.critical(f"Failed to prepare dataset: {e}")
        sys.exit(1)
    
    # 6. Configure Training Arguments
    # Using defaults from lora_config.py but overriding output_dir and specific paths
    lora_config = create_lora_config_from_env(config)
    
    training_args = TrainingArguments(
        output_dir=str(output_dir),
        per_device_train_batch_size=lora_config.batch_size,
        gradient_accumulation_steps=lora_config.gradient_accumulation_steps,
        learning_rate=lora_config.learning_rate,
        num_train_epochs=lora_config.num_train_epochs,
        fp16=False, # CPU training
        bf16=False,
        logging_steps=10,
        save_strategy="epoch",
        evaluation_strategy="no", # No eval data per plan
        save_total_limit=1,
        load_best_model_at_end=False,
        report_to="none",
        disable_tqdm=False,
        max_grad_norm=1.0,
        warmup_ratio=0.03,
        lr_scheduler_type="linear",
    )
    
    # 7. Setup Timeout (CPU-safe)
    timeout_seconds = 3600 # 1 hour default timeout for CPU run
    setup_timeout(timeout_seconds)
    
    try:
        # 8. Run Training Loop
        trainer = Trainer(
            model=model,
            args=training_args,
            train_dataset=train_dataset,
            tokenizer=tokenizer,
        )
        
        logger.info("Beginning training loop...")
        start_time = time.time()
        
        trainer.train()
        
        elapsed = time.time() - start_time
        logger.info(f"Training completed in {elapsed:.2f} seconds")
        
        # 9. Save Checkpoint
        logger.info(f"Saving final checkpoint to {checkpoint_path}")
        
        # Save the adapter weights (LoRA)
        # Since the model is wrapped in PeftModel, we save the adapter
        if hasattr(model, 'save_pretrained'):
            # Save to a temp dir first, then move to final name if needed
            # Or save directly to the checkpoint path
            # Note: For .pt file, we might want to save the state_dict directly
            # but Trainer.save_model saves the adapter config and weights in the directory structure.
            # To match the requirement of a single .pt file, we'll save the state_dict.
            
            # Get the base model state dict (without LoRA) or the full model?
            # Usually for LoRA we save the adapter. Let's save the adapter weights as a state dict.
            # However, the task asks for a .pt file.
            # We will save the model's state_dict (which includes LoRA adapters if merged or separate)
            # and the tokenizer.
            
            # Simplest robust approach for the artifact:
            # Save the model weights (including LoRA) and tokenizer config to the .pt file
            torch.save({
                'model_state_dict': model.state_dict(),
                'tokenizer_config': tokenizer.get_vocab(), # Simplified
                'config': {
                    'base_model_id': config.BASE_MODEL_ID,
                    'lora_config': lora_config.to_dict()
                },
                'training_args': training_args.to_dict()
            }, checkpoint_path)
            
        logger.info(f"Checkpoint saved successfully: {checkpoint_path}")
        
    except TimeoutError:
        logger.critical("Training timed out. Saving partial checkpoint.")
        # Fallback save logic handled by train_loop if we used the wrapper, 
        # but here we do it manually.
        torch.save({
            'status': 'timeout',
            'model_state_dict': model.state_dict()
        }, output_dir / "checkpoint_partial.pt")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Training failed with error: {e}")
        # Save partial checkpoint on failure
        try:
            torch.save({
                'status': 'error',
                'error': str(e),
                'model_state_dict': model.state_dict()
            }, output_dir / "checkpoint_partial.pt")
        except:
            pass
        sys.exit(1)
    finally:
        # Cancel timeout
        try:
            import signal
            signal.alarm(0)
        except:
            pass
    
    logger.info("Ablation Training Run finished.")

if __name__ == "__main__":
    main()
