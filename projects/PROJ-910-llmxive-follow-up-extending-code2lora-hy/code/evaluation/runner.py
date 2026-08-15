"""
Evaluation Runner for RepoPeftBench.

Implements Task T021: Load RepoPeftBench data, apply the AST-based adapter,
and compute BOTH exact-match scores AND inference latency.

Output: data/results/ast_scores.csv (columns: task_id, exact_match, latency_ms)
"""
import os
import csv
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

# Import local utilities
from utils.config import load_config, Config
from utils.logging import get_logger
from data.download_repopeftbench import download_dataset, verify_dataset_integrity
from evaluation.latency_monitor import measure_inference_latency, save_latency_results
from evaluation.failure_classifier import run_task_with_classification, classify_exception, FailureMode

logger = get_logger(__name__)

# Constants
RESULTS_DIR = Path("data/results")
RAW_DATA_DIR = Path("data/raw")
ADAPTER_DIR = Path("data/adapters")
OUTPUT_FILE = RESULTS_DIR / "ast_scores.csv"
LATENCY_LOG_FILE = RESULTS_DIR / "inference_latency_log.json"

def load_repopeftbench_data(config: Config) -> List[Dict[str, Any]]:
    """
    Load the RepoPeftBench dataset (Python subset).
    Uses streaming if available to handle large datasets, otherwise loads in memory.
    """
    if not RAW_DATA_DIR.exists():
        logger.error(f"Raw data directory {RAW_DATA_DIR} does not exist. Run download_repopeftbench.py first.")
        raise FileNotFoundError(f"Raw data directory {RAW_DATA_DIR} not found.")

    # Attempt to load the dataset
    # Assuming the download script has populated data/raw with the necessary files
    # or we use the datasets library directly if the HF ID is configured
    try:
        from datasets import load_dataset
        
        # Check if local path exists, otherwise try HF
        local_path = RAW_DATA_DIR / "python"
        if local_path.exists():
            logger.info(f"Loading local dataset from {local_path}")
            ds = load_dataset(str(local_path), split="test", streaming=False)
        else:
            # Fallback to HF ID if configured in config, else default
            hf_id = getattr(config, 'dataset_id', 'repo-peft-bench')
            logger.info(f"Loading dataset from HF: {hf_id}")
            ds = load_dataset(hf_id, "python", split="test", streaming=False)
        
        # Convert to list of dicts for easier processing
        data = []
        for item in ds:
            data.append(item)
        
        logger.info(f"Loaded {len(data)} samples from RepoPeftBench.")
        return data
    except Exception as e:
        logger.error(f"Failed to load RepoPeftBench: {e}")
        raise

def load_ast_adapter(config: Config) -> Tuple[AutoModelForCausalLM, AutoTokenizer]:
    """
    Load the base model and apply the AST-based adapter.
    """
    base_model_path = config.base_model_path
    adapter_path = ADAPTER_DIR / "ast_adapter.safetensors"
    
    if not adapter_path.exists():
        # Fallback to generic name if specific one doesn't exist
        alt_path = ADAPTER_DIR / "adapter.safetensors"
        if alt_path.exists():
            adapter_path = alt_path
        else:
            raise FileNotFoundError(f"AST adapter not found at {ADAPTER_DIR}. Run adapter generation first.")

    logger.info(f"Loading base model from {base_model_path}...")
    tokenizer = AutoTokenizer.from_pretrained(base_model_path)
    model = AutoModelForCausalLM.from_pretrained(
        base_model_path,
        torch_dtype=torch.float32, # Use float32 for CPU compatibility if needed
        device_map="auto" if torch.cuda.is_available() else None
    )
    
    logger.info(f"Applying AST adapter from {adapter_path}...")
    # Note: PeftModel.from_pretrained expects a folder usually, but safetensors can be loaded if structured correctly.
    # If the adapter was saved as a single safetensors file without config, we might need to load weights manually.
    # Assuming standard PEFT structure where the adapter folder contains adapter_model.safetensors and adapter_config.json.
    # If the task generated a single file, we treat the directory containing it as the adapter path.
    
    # Adjusting for the likely output of T015 which saves to data/adapters/ast_adapter.safetensors
    # PEFT usually expects a directory. Let's assume the directory 'ast_adapter' exists or we create a temp one.
    # However, to be robust, we try loading from the directory if it exists, or the file if it's a directory name.
    
    adapter_folder = ADAPTER_DIR / "ast_adapter"
    if not adapter_folder.exists():
        # If the file exists but not the folder, we might need to handle it differently or assume the file IS the adapter model
        # For this implementation, we assume the standard PEFT save structure (directory) was used or the file is placed in a folder.
        # If T015 saved a single file, we might need to reconstruct the folder structure or load weights directly.
        # Let's assume the standard PEFT directory structure for robustness, or adapt if T015 created a folder.
        # If the file is just 'ast_adapter.safetensors', we try to load it as a folder containing it? No.
        # Let's assume T015 created a folder 'ast_adapter' containing the files.
        # If the path is a file, we treat it as the model file inside a default folder structure or raise error.
        raise FileNotFoundError(f"Adapter directory {adapter_folder} not found. Expected standard PEFT folder structure.")

    model = PeftModel.from_pretrained(model, str(adapter_folder))
    model = model.merge_and_unload() # Merge for inference to avoid overhead
    
    logger.info("Adapter loaded and merged successfully.")
    return model, tokenizer

def compute_exact_match(prediction: str, reference: str) -> bool:
    """
    Compute exact match between prediction and reference.
    """
    return prediction.strip() == reference.strip()

def run_inference(
    model: AutoModelForCausalLM,
    tokenizer: AutoTokenizer,
    task: Dict[str, Any],
    timeout_sec: int = 30
) -> Tuple[Optional[str], float, Optional[FailureMode]]:
    """
    Run inference for a single task with latency measurement and timeout handling.
    Returns (prediction, latency_ms, failure_mode).
    """
    prompt = task.get("prompt", "")
    reference = task.get("reference", "")
    
    inputs = tokenizer(prompt, return_tensors="pt")
    input_len = inputs["input_ids"].shape[1]
    
    start_time = time.perf_counter()
    failure_mode = None
    prediction = None
    
    try:
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=128,
                do_sample=False,
                pad_token_id=tokenizer.eos_token_id
            )
        end_time = time.perf_counter()
        
        # Calculate latency (excluding input processing time roughly)
        latency_ms = (end_time - start_time) * 1000
        
        generated_ids = outputs[0][input_len:]
        prediction = tokenizer.decode(generated_ids, skip_special_tokens=True)
        
    except TimeoutError:
        failure_mode = FailureMode.TIMEOUT
        latency_ms = timeout_sec * 1000
    except Exception as e:
        failure_mode = classify_exception(e)
        latency_ms = (time.perf_counter() - start_time) * 1000
        prediction = None
        
    return prediction, latency_ms, failure_mode

def run_evaluation(config: Config) -> List[Dict[str, Any]]:
    """
    Run the full evaluation pipeline.
    """
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    
    logger.info("Loading RepoPeftBench data...")
    data = load_repopeftbench_data(config)
    
    logger.info("Loading AST Adapter...")
    model, tokenizer = load_ast_adapter(config)
    
    results = []
    latency_stats = []
    
    for i, task in enumerate(data):
        task_id = task.get("task_id", f"task_{i}")
        logger.info(f"Processing {task_id} ({i+1}/{len(data)})...")
        
        prediction, latency_ms, failure_mode = run_inference(model, tokenizer, task)
        
        if failure_mode:
            exact_match = False
            logger.warning(f"Task {task_id} failed with {failure_mode}")
        else:
            exact_match = compute_exact_match(prediction, task.get("reference", ""))
            logger.debug(f"Task {task_id}: {exact_match}")
        
        results.append({
            "task_id": task_id,
            "exact_match": 1 if exact_match else 0,
            "latency_ms": round(latency_ms, 3),
            "failure_mode": failure_mode.value if failure_mode else None
        })
        latency_stats.append(latency_ms)
        
        # Optional: Log progress
        if (i + 1) % 10 == 0:
            avg_lat = sum(latency_stats) / len(latency_stats)
            logger.info(f"Progress: {i+1}/{len(data)}, Avg Latency: {avg_lat:.2f}ms")
    
    return results

def save_results(results: List[Dict[str, Any]]) -> None:
    """
    Save results to CSV and latency stats to JSON.
    """
    if not results:
        logger.warning("No results to save.")
        return
    
    # Save CSV
    with open(OUTPUT_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["task_id", "exact_match", "latency_ms", "failure_mode"])
        writer.writeheader()
        writer.writerows(results)
    
    logger.info(f"Results saved to {OUTPUT_FILE}")
    
    # Save latency stats
    if latency_stats := [r["latency_ms"] for r in results if r.get("failure_mode") is None]:
        stats = {
            "count": len(latency_stats),
            "mean": sum(latency_stats) / len(latency_stats),
            "min": min(latency_stats),
            "max": max(latency_stats),
            "p50": sorted(latency_stats)[len(latency_stats)//2],
            "p99": sorted(latency_stats)[int(len(latency_stats)*0.99)]
        }
        with open(LATENCY_LOG_FILE, "w") as f:
            json.dump(stats, f, indent=2)
        logger.info(f"Latency stats saved to {LATENCY_LOG_FILE}")

def main():
    """
    Main entry point for the evaluation runner.
    """
    config = load_config()
    try:
        results = run_evaluation(config)
        save_results(results)
        logger.info("Evaluation completed successfully.")
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        raise

if __name__ == "__main__":
    main()