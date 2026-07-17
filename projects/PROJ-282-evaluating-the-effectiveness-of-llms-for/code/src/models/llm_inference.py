import os
import sys
import time
import gc
import json
import re
import psutil
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
import logging

from src.models.code_snippet import CodeSnippet
from src.models.prediction_result import PredictionResult, create_prediction_result
from src.utils.logger import get_logger
from src.utils.config import get_config

# Configure logger
logger = get_logger("llm_inference")

@dataclass
class InferenceConfig:
    """Configuration for LLM inference."""
    model_name: str
    quantization_bits: int = 4
    max_batch_size: int = 1
    memory_threshold_gb: float = 6.0  # Safety threshold below 7GB limit
    prompt_template: str = "Identify any security vulnerability in the following code: {code}"
    timeout_seconds: int = 21600  # 6 hours
    max_retries: int = 3

def get_available_ram_gb() -> float:
    """Get available RAM in GB using psutil."""
    try:
        process = psutil.Process(os.getpid())
        # Get available system memory
        mem_info = psutil.virtual_memory()
        available_gb = mem_info.available / (1024 ** 3)
        return available_gb
    except Exception as e:
        logger.warning(f"Could not determine available RAM: {e}. Defaulting to conservative estimate.")
        return 4.0  # Conservative default

def check_memory_constraint(config: InferenceConfig, batch_size: int) -> bool:
    """Check if current memory usage allows for the requested batch size."""
    available_gb = get_available_ram_gb()
    # Estimate memory usage: rough heuristic of 1GB per batch item for 4-bit models
    estimated_usage_gb = batch_size * 0.5 + 1.0  # Base overhead + per-item estimate
    if available_gb - estimated_usage_gb < config.memory_threshold_gb:
        logger.warning(f"Memory constraint would be violated: Available {available_gb:.2f}GB, "
                       f"Estimated usage {estimated_usage_gb:.2f}GB, Threshold {config.memory_threshold_gb}GB")
        return False
    return True

def load_model_4bit_cpu(model_name: str) -> Any:
    """
    Load a model in 4-bit quantized mode on CPU.
    Uses bitsandbytes and transformers.
    Falls back to a mock if the environment is not set up for real inference,
    but RAISES an error if the user expects real inference (as per task T013 requirements).
    """
    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
        import torch

        logger.info(f"Loading model {model_name} in 4-bit quantized mode on CPU...")

        # Configure 4-bit quantization
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float32
        )

        # Load tokenizer
        tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        # Load model
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            quantization_config=bnb_config,
            device_map="cpu",  # Force CPU as per requirement
            trust_remote_code=True,
            low_cpu_mem_usage=True
        )

        logger.info(f"Model {model_name} loaded successfully.")
        return model, tokenizer

    except ImportError as e:
        logger.error(f"Required libraries for real inference not installed: {e}")
        logger.error("This task requires REAL inference. The pipeline cannot proceed with synthetic mocks.")
        raise RuntimeError(
            f"Real LLM inference environment not configured. Missing: {e}. "
            "Install transformers, bitsandbytes, torch and ensure model is accessible."
        )
    except Exception as e:
        logger.error(f"Failed to load model {model_name}: {e}")
        raise RuntimeError(f"Failed to load model {model_name} for real inference: {e}")

def parse_llm_response(response_text: str) -> Tuple[bool, Optional[str], str]:
    """
    Parse LLM response to extract vulnerability label and category.
    Handles ambiguous responses by mapping them to 'uncertain' or negative.
    Returns: (is_vulnerable, category, parsed_confidence)
    """
    text_lower = response_text.lower()

    # Ambiguous patterns mapping to 'uncertain' or negative (treated as safe for binary label)
    ambiguous_patterns = [
        r"maybe", r"unclear", r"possibly", r"likely", r"might be",
        r"could be", r"uncertain", r"not sure", r"hard to tell"
    ]

    for pattern in ambiguous_patterns:
        if re.search(pattern, text_lower):
            logger.warning(f"Ambiguous response detected: '{response_text}' -> mapped to 'uncertain'")
            return False, "uncertain", "uncertain"

    # Positive vulnerability indicators
    vuln_patterns = [
        r"vulnerability", r"vulnerable", r"security issue", r"security flaw",
        r"buffer overflow", r"injection", r"sql injection", r"xss",
        r"cross-site scripting", r"command injection", r"path traversal",
        r"hardcoded password", r"weak cryptography", r"hardcoded secret"
    ]

    for pattern in vuln_patterns:
        if re.search(pattern, text_lower):
            # Try to extract category if mentioned
            category = "generic"
            if "sql" in text_lower:
                category = "injection"
            elif "buffer" in text_lower or "overflow" in text_lower:
                category = "memory_safety"
            elif "xss" in text_lower or "scripting" in text_lower:
                category = "injection"
            elif "password" in text_lower or "secret" in text_lower:
                category = "credential_exposure"
            elif "crypto" in text_lower or "encryption" in text_lower:
                category = "weak_cryptography"

            return True, category, "high"

    # Default to safe if no vulnerability found
    return False, None, "low"

def run_inference_batch(
    model: Any,
    tokenizer: Any,
    snippets: List[CodeSnippet],
    config: InferenceConfig
) -> List[PredictionResult]:
    """
    Run inference on a batch of snippets with memory safety checks.
    Dynamically adjusts batch size if memory constraints are detected.
    """
    results = []
    current_batch_size = config.max_batch_size

    for i in range(0, len(snippets), current_batch_size):
        batch = snippets[i:i + current_batch_size]
        
        # Memory check before processing batch
        if not check_memory_constraint(config, current_batch_size):
            if current_batch_size <= 1:
                raise MemoryError("Memory constraint violated even with batch size 1. Cannot proceed.")
            logger.warning(f"Reducing batch size from {current_batch_size} to {current_batch_size // 2} due to memory pressure.")
            current_batch_size = max(1, current_batch_size // 2)
            # Re-process this batch with smaller size
            batch = snippets[i:i + current_batch_size]

        batch_results = []
        for snippet in batch:
            start_time = time.time()
            
            try:
                prompt = config.prompt_template.format(code=snippet.source_code)
                inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512)
                
                # Log truncation events
                if len(inputs['input_ids'][0]) >= 512:
                    logger.warning(f"Truncation event for snippet {snippet.id}: input length exceeded max_length")

                with torch.no_grad():
                    outputs = model.generate(
                        **inputs,
                        max_new_tokens=100,
                        do_sample=False,
                        pad_token_id=tokenizer.pad_token_id
                    )
                
                response = tokenizer.decode(outputs[0], skip_special_tokens=True)
                # Extract just the model's generated part (after the prompt)
                generated_text = response[len(prompt):].strip()

                is_vuln, category, confidence = parse_llm_response(generated_text)
                
                inference_time_ms = (time.time() - start_time) * 1000
                
                result = create_prediction_result(
                    snippet=snippet,
                    predicted_label=is_vuln,
                    predicted_category=category,
                    inference_time_ms=inference_time_ms
                )
                batch_results.append(result)
                
            except Exception as e:
                logger.error(f"Error processing snippet {snippet.id}: {e}")
                # Create a failure result
                result = create_prediction_result(
                    snippet=snippet,
                    predicted_label=False,
                    predicted_category="error",
                    inference_time_ms=(time.time() - start_time) * 1000
                )
                batch_results.append(result)

        results.extend(batch_results)
        
        # Force garbage collection between batches
        gc.collect()
        time.sleep(0.1)  # Small pause to allow memory to stabilize

    return results

def process_snippets_zero_shot(
    snippets: List[CodeSnippet],
    config: InferenceConfig
) -> List[PredictionResult]:
    """
    Main entry point for zero-shot vulnerability detection.
    Enforces zero-shot methodology (no fine-tuning, no few-shot examples).
    """
    logger.info(f"Starting zero-shot inference for {len(snippets)} snippets.")
    
    # Load model
    model, tokenizer = load_model_4bit_cpu(config.model_name)
    
    start_time = time.time()
    results = run_inference_batch(model, tokenizer, snippets, config)
    
    total_time = time.time() - start_time
    logger.info(f"Inference complete. Processed {len(results)} snippets in {total_time:.2f} seconds.")
    
    # Check total time constraint
    if total_time > config.timeout_seconds:
        logger.error(f"TIMEOUT: Total inference time {total_time:.2f}s exceeded limit {config.timeout_seconds}s")
        # In a real pipeline, we might raise an exception or return partial results
        # For now, we log and continue with what we have
    
    return results

def main():
    """
    Main function to run the LLM inference pipeline.
    Reads snippets from data/processed/snippets.csv and writes predictions to data/processed/predictions.csv.
    """
    import pandas as pd
    from pathlib import Path

    # Load configuration
    cfg = get_config()
    
    # Determine model based on RAM (from T004 dynamic selection)
    # For now, use a default; in production, this would call the dynamic selection logic
    model_name = cfg.get("model_selection", {}).get("selected_model", "microsoft/Phi-3-mini-4k-instruct")
    
    config = InferenceConfig(
        model_name=model_name,
        max_batch_size=cfg.get("inference", {}).get("max_batch_size", 1),
        memory_threshold_gb=cfg.get("runtime", {}).get("memory_threshold_gb", 6.0),
        timeout_seconds=cfg.get("runtime", {}).get("hourly_limit", 21600)
    )

    # Load snippets
    snippets_path = Path("data/processed/snippets.csv")
    if not snippets_path.exists():
        logger.error(f"Snippets file not found: {snippets_path}")
        sys.exit(1)

    df = pd.read_csv(snippets_path)
    snippets = [
        CodeSnippet(
            id=row['id'],
            language=row['language'],
            source_code=row['source_code'],
            ground_truth_label=row['ground_truth_label'],
            ground_truth_category=row.get('ground_truth_category')
        )
        for _, row in df.iterrows()
    ]

    # Run inference
    results = process_snippets_zero_shot(snippets, config)

    # Save results
    output_path = Path("data/processed/predictions.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = pd.DataFrame([
            {
                'snippet_id': r.snippet_id,
                'predicted_label': r.predicted_label,
                'predicted_category': r.predicted_category,
                'is_correct': r.is_correct,
                'inference_time_ms': r.inference_time_ms
            }
            for r in results
        ]).to_csv(f, index=False)

    logger.info(f"Predictions saved to {output_path}")

if __name__ == "__main__":
    main()
