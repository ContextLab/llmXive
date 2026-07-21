import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Set
import torch
import torch.nn as nn
from transformers import AutoModelForCausalLM, AutoTokenizer
from dataclasses import dataclass, field
import time

# Import from project utils
from src.utils.entropy_calc import calculate_entropy
from src.utils.validators import TokenSequence, ValidityLabel, validate_token_sequence, validate_validity_label
from src.config import Config

# Configure logging
def setup_logging(log_file: str = "logs/generation.log") -> logging.Logger:
    """Setup JSON-formatted logging to file and console."""
    logger = logging.getLogger("generation")
    logger.setLevel(logging.INFO)
    
    # Create logs directory if it doesn't exist
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Clear existing handlers
    logger.handlers = []
    
    # File handler with JSON formatter
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)
    
    class JSONFormatter(logging.Formatter):
        def format(self, record):
            log_obj = {
                "timestamp": self.formatTime(record, self.datefmt),
                "level": record.levelname,
                "message": record.getMessage(),
                "module": record.module,
                "function": record.funcName
            }
            # Add extra fields if present
            if hasattr(record, 'token_count'):
                log_obj['token_count'] = record.token_count
            if hasattr(record, 'validity_distribution'):
                log_obj['validity_distribution'] = record.validity_distribution
            return json.dumps(log_obj)
    
    file_handler.setFormatter(JSONFormatter())
    logger.addHandler(file_handler)
    
    # Console handler for visibility
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
    logger.addHandler(console_handler)
    
    return logger

@dataclass
class GenerationConfig:
    """Configuration for baseline generation."""
    model_name: str = "distilgpt2"
    temperature: float = 0.0
    max_new_tokens: int = 128
    batch_size: int = 1
    seed: int = 42
    dataset_name: str = "gsm8k"
    sample_size: int = 100

class LayerProbabilityHook:
    """Hook to capture layer-wise probability distributions."""
    def __init__(self):
        self.layer_outputs = []
        self.layer_logits = []
    
    def forward_hook(self, module, input, output):
        """Capture output logits from attention layers."""
        if isinstance(output, tuple) and len(output) > 0:
            self.layer_logits.append(output[0].detach().cpu())

def load_model_for_cpu_inference(model_name: str, logger: logging.Logger) -> Tuple[AutoModelForCausalLM, AutoTokenizer]:
    """Load a model optimized for CPU inference."""
    logger.info(f"Loading model {model_name} for CPU inference")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float32,
        device_map="cpu",
        low_cpu_mem_usage=True
    )
    model.eval()
    logger.info("Model loaded successfully")
    return model, tokenizer

def generate_single_pass(
    prompt: str,
    model: AutoModelForCausalLM,
    tokenizer: AutoTokenizer,
    config: GenerationConfig,
    logger: logging.Logger,
    hook: Optional[LayerProbabilityHook] = None
) -> Dict[str, Any]:
    """Generate a single sequence using greedy decoding (temperature=0.0)."""
    inputs = tokenizer(prompt, return_tensors="pt")
    input_ids = inputs["input_ids"]
    attention_mask = inputs["attention_mask"]
    
    if hook:
        # Register hook on transformer layers
        for name, module in model.named_modules():
            if isinstance(module, nn.Linear) and "lm_head" not in name:
                hook.forward_hook = module.register_forward_hook(hook.forward_hook)
    
    with torch.no_grad():
        outputs = model.generate(
            input_ids,
            attention_mask=attention_mask,
            max_new_tokens=config.max_new_tokens,
            temperature=config.temperature,
            do_sample=(config.temperature > 0),
            pad_token_id=tokenizer.eos_token_id,
            eos_token_id=tokenizer.eos_token_id
        )
    
    generated_ids = outputs[0][input_ids.shape[1]:]
    generated_text = tokenizer.decode(generated_ids, skip_special_tokens=True)
    
    tokens = tokenizer.convert_ids_to_tokens(generated_ids)
    
    return {
        "prompt": prompt,
        "generated_text": generated_text,
        "tokens": tokens,
        "token_ids": generated_ids.tolist(),
        "length": len(tokens)
    }

def generate_baseline(
    dataset: List[Dict[str, Any]],
    model_name: str,
    config: GenerationConfig,
    logger: logging.Logger,
    hook: Optional[LayerProbabilityHook] = None
) -> List[Dict[str, Any]]:
    """Generate baseline sequences for a dataset."""
    model, tokenizer = load_model_for_cpu_inference(model_name, logger)
    results = []
    
    logger.info(f"Starting baseline generation for {len(dataset)} examples")
    
    for idx, example in enumerate(dataset):
        prompt = example.get("prompt", example.get("question", ""))
        prompt_id = example.get("id", f"prompt_{idx}")
        
        try:
            generation_result = generate_single_pass(
                prompt, model, tokenizer, config, logger, hook
            )
            generation_result["prompt_id"] = prompt_id
            generation_result["original_example"] = example
            results.append(generation_result)
            
            if (idx + 1) % 10 == 0:
                logger.info(f"Generated {idx + 1}/{len(dataset)} sequences")
        except Exception as e:
            logger.error(f"Generation failed for prompt {prompt_id}: {str(e)}")
            continue
    
    logger.info(f"Baseline generation complete. Generated {len(results)} sequences.")
    return results

def label_validity(
    generated_sequences: List[Dict[str, Any]],
    dataset: List[Dict[str, Any]],
    logger: logging.Logger
) -> List[Dict[str, Any]]:
    """
    Label token sequences with ground truth validity flags.
    
    For GSM8K: Check if the generated answer matches the ground truth solution.
    For MiniGrid: Handle multiple valid paths - check if the generated action
    sequence matches ANY of the known valid ground-truth paths.
    
    If no match is found after checking all paths:
    - Log a warning to logs/generation.log with JSON format {"prompt_id": "...", "reason": "no_match"}
    - Retain the data point with validity=false
    """
    # Create a lookup map for ground truth answers
    gt_map = {}
    for example in dataset:
        prompt_id = example.get("id", f"prompt_{dataset.index(example)}")
        gt_map[prompt_id] = example
    
    labeled_results = []
    no_match_count = 0
    valid_count = 0
    invalid_count = 0
    
    for seq in generated_sequences:
        prompt_id = seq.get("prompt_id")
        generated_text = seq.get("generated_text", "")
        original_example = seq.get("original_example", {})
        
        # Determine dataset type and ground truth
        dataset_name = original_example.get("dataset", "gsm8k")
        ground_truth = None
        
        if dataset_name == "gsm8k":
            # GSM8K: Extract answer from generated text and compare to solution
            ground_truth = original_example.get("answer", "")
            # Extract the final answer from generation (usually after "####")
            generated_answer = ""
            if "####" in generated_text:
                generated_answer = generated_text.split("####")[-1].strip()
            else:
                # Try to extract last number
                import re
                numbers = re.findall(r'\d+', generated_text)
                if numbers:
                    generated_answer = numbers[-1]
            
            is_valid = generated_answer == ground_truth or (generated_answer and ground_truth and 
                    generated_answer.replace(',', '') == ground_truth.replace(',', ''))
            
        elif dataset_name == "minigrid":
            # MiniGrid: Check against multiple valid paths
            valid_paths = original_example.get("valid_paths", [])
            generated_actions = generated_text.strip().split()
            
            is_valid = False
            if valid_paths:
                # Check if generated actions match ANY valid path
                for path in valid_paths:
                    path_actions = path.strip().split()
                    # Check for exact match or prefix match
                    if generated_actions == path_actions or (len(generated_actions) > 0 and 
                        generated_actions[:len(path_actions)] == path_actions):
                        is_valid = True
                        break
            else:
                # No valid paths defined - treat as invalid
                is_valid = False
        else:
            # Unknown dataset type - default to invalid
            is_valid = False
        
        # Create validity label
        validity_label = {
            "prompt_id": prompt_id,
            "is_valid": is_valid,
            "ground_truth": ground_truth,
            "reason": "match" if is_valid else "no_match"
        }
        
        # Log warnings for no-match cases
        if not is_valid:
            no_match_count += 1
            logger.warning(json.dumps({
                "prompt_id": prompt_id,
                "reason": "no_match",
                "dataset": dataset_name
            }))
        else:
            valid_count += 1
        
        invalid_count = len(generated_sequences) - valid_count
        
        # Combine generation result with validity label
        labeled_seq = {
            **seq,
            "validity_label": validity_label,
            "validity": is_valid
        }
        labeled_results.append(labeled_seq)
    
    # Log distribution stats
    logger.info(json.dumps({
        "total": len(generated_sequences),
        "valid": valid_count,
        "invalid": invalid_count,
        "no_match_logged": no_match_count,
        "validity_distribution": {
            "valid": valid_count / len(generated_sequences) if generated_sequences else 0,
            "invalid": invalid_count / len(generated_sequences) if generated_sequences else 0
        }
    }))
    
    return labeled_results

def write_jsonl(
    data: List[Dict[str, Any]],
    output_path: str,
    logger: logging.Logger
) -> None:
    """Write labeled data to JSONL file."""
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for record in data:
            # Validate record before writing
            try:
                validate_token_sequence(record)
                if "validity_label" in record:
                    validate_validity_label(record["validity_label"])
            except Exception as e:
                logger.warning(f"Invalid record skipped: {str(e)}")
                continue
            
            f.write(json.dumps(record) + '\n')
    
    logger.info(f"Wrote {len(data)} records to {output_path}")

def write_labeled_dataset(
    labeled_data: List[Dict[str, Any]],
    output_path: str,
    logger: logging.Logger
) -> None:
    """Write labeled dataset to JSONL with standardized fields."""
    standardized_data = []
    
    for record in labeled_data:
        standardized_record = {
            "prompt_id": record.get("prompt_id"),
            "tokens": record.get("tokens", []),
            "validity": record.get("validity", False),
            "ground_truth": record.get("validity_label", {}).get("ground_truth"),
            "reason": record.get("validity_label", {}).get("reason")
        }
        standardized_data.append(standardized_record)
    
    write_jsonl(standardized_data, output_path, logger)

def load_and_merge_outputs(
    generation_output: str,
    dataset_path: str,
    logger: logging.Logger
) -> List[Dict[str, Any]]:
    """Load generated sequences and merge with ground truth labels."""
    # Load generated sequences
    generated_sequences = []
    with open(generation_output, 'r', encoding='utf-8') as f:
        for line in f:
            generated_sequences.append(json.loads(line))
    
    # Load original dataset for ground truth
    dataset = []
    with open(dataset_path, 'r', encoding='utf-8') as f:
        for line in f:
            dataset.append(json.loads(line))
    
    # Label validity
    labeled_data = label_validity(generated_sequences, dataset, logger)
    
    return labeled_data

def process_dataset(
    dataset: List[Dict[str, Any]],
    model_name: str,
    config: GenerationConfig,
    output_path: str,
    logger: logging.Logger
) -> None:
    """Process a complete dataset: generate, label, and write output."""
    # Generate baseline sequences
    generated_sequences = generate_baseline(dataset, model_name, config, logger)
    
    # Label validity
    labeled_data = label_validity(generated_sequences, dataset, logger)
    
    # Write output
    write_labeled_dataset(labeled_data, output_path, logger)

def process_batch(
    batch: List[Dict[str, Any]],
    model: AutoModelForCausalLM,
    tokenizer: AutoTokenizer,
    config: GenerationConfig,
    logger: logging.Logger,
    output_file: Path
) -> None:
    """Process a batch of examples and append to output file."""
    hook = LayerProbabilityHook()
    
    for example in batch:
        try:
            result = generate_single_pass(
                example.get("prompt", ""),
                model, tokenizer, config, logger, hook
            )
            result["prompt_id"] = example.get("id", f"prompt_{hash(example)}")
            result["original_example"] = example
            
            # Append to output file immediately
            with open(output_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(result) + '\n')
        except Exception as e:
            logger.error(f"Failed to process batch item: {str(e)}")

def main():
    """Main entry point for baseline generation."""
    config = GenerationConfig()
    logger = setup_logging()
    
    # Example usage - in practice, load from actual dataset
    logger.info("Generation module loaded successfully")
    logger.info(f"Default config: {config}")

if __name__ == "__main__":
    main()
