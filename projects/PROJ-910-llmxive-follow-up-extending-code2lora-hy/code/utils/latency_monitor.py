"""
Latency monitoring utilities for adapter generation and inference.

Provides functions to measure baseline generation latency (T049a) and
compare it with AST-based generation (T049b).
"""
import os
import json
import time
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

from evaluation.baseline_loader import get_baseline_adapter_path
from utils.config import load_config

logger = logging.getLogger(__name__)

RESULTS_DIR = Path("data/results")

def ensure_results_dir() -> Path:
    """Ensure the results directory exists."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    return RESULTS_DIR

def measure_baseline_generation_latency() -> Dict[str, Any]:
    """
    Measure the time to load and initialize the baseline neural-encoder adapter.
    
    This simulates the "generation" time by measuring the time to:
    1. Load the base model
    2. Load the baseline adapter
    3. Prepare for inference (equivalent to generation setup)
    
    Returns:
        Dict with latency_ms and metadata
    """
    logger.info("Measuring baseline generation latency...")
    ensure_results_dir()
    
    config = load_config()
    base_model_path = config.get("base_model_path", "TinyLlama-1.1B-Chat-hf")
    
    start_time = time.perf_counter()
    
    try:
        # Load base model (this is the expensive part)
        logger.info(f"Loading base model: {base_model_path}")
        tokenizer = AutoTokenizer.from_pretrained(base_model_path)
        base_model = AutoModelForCausalLM.from_pretrained(
            base_model_path,
            torch_dtype=torch.float32,
            device_map="cpu"  # Force CPU for consistency
        )
        
        # Load baseline adapter
        baseline_adapter_path = get_baseline_adapter_path()
        logger.info(f"Loading baseline adapter from: {baseline_adapter_path}")
        
        if baseline_adapter_path and os.path.exists(baseline_adapter_path):
            model = PeftModel.from_pretrained(base_model, baseline_adapter_path)
            logger.info("Baseline adapter loaded successfully")
        else:
            logger.warning(f"Baseline adapter not found at {baseline_adapter_path}. Using base model only.")
            model = base_model
        
        end_time = time.perf_counter()
        elapsed_ms = (end_time - start_time) * 1000
        
        result = {
            "generation_latency_ms": round(elapsed_ms, 2),
            "base_model": base_model_path,
            "adapter_path": baseline_adapter_path,
            "device": "cpu",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
        
        logger.info(f"Baseline generation latency: {elapsed_ms:.2f} ms")
        return result
        
    except Exception as e:
        logger.error(f"Failed to measure baseline latency: {e}")
        raise

def save_latency_comparison(
    ast_latency_ms: float,
    baseline_latency_ms: float,
    ratio: float,
    meets_requirement: bool
) -> Path:
    """
    Save the latency comparison results to JSON.
    
    Args:
        ast_latency_ms: AST-based generation latency in ms
        baseline_latency_ms: Baseline generation latency in ms
        ratio: Reduction ratio (baseline / ast)
        meets_requirement: Whether ratio >= 10
        
    Returns:
        Path to the saved file
    """
    output_path = RESULTS_DIR / "generation_latency_comparison.json"
    ensure_results_dir()
    
    report = {
        "ast_generation_latency_ms": round(ast_latency_ms, 2),
        "baseline_generation_latency_ms": round(baseline_latency_ms, 2),
        "latency_reduction_ratio": round(ratio, 4),
        "meets_sc_001_requirement": meets_requirement,
        "sc_001_threshold": 10.0,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Latency comparison saved to: {output_path}")
    return output_path

def run_latency_analysis() -> Dict[str, Any]:
    """
    Run full latency analysis comparing AST and baseline generation.
    
    This function:
    1. Measures baseline latency (T049a)
    2. Reads AST latency from T040 results
    3. Computes ratio
    4. Saves comparison report
    
    Returns:
        Dict with all latency metrics
    """
    ensure_results_dir()
    
    # Measure baseline
    baseline_result = measure_baseline_generation_latency()
    baseline_latency_ms = baseline_result["generation_latency_ms"]
    
    # Read AST latency (assuming T040 already ran)
    ast_latency_path = RESULTS_DIR / "generation_latency.json"
    if not ast_latency_path.exists():
        raise FileNotFoundError(
            f"AST latency file not found: {ast_latency_path}. "
            "Please run the AST generation task (T040) first."
        )
    
    with open(ast_latency_path, 'r', encoding='utf-8') as f:
        ast_data = json.load(f)
    
    ast_latency_ms = ast_data.get("generation_latency_ms") or ast_data.get("latency_ms")
    if ast_latency_ms is None:
        raise ValueError(f"Could not find latency value in {ast_latency_path}")
    
    # Compute ratio
    ratio = baseline_latency_ms / ast_latency_ms
    meets_requirement = ratio >= 10.0
    
    # Save comparison
    save_latency_comparison(ast_latency_ms, baseline_latency_ms, ratio, meets_requirement)
    
    return {
        "ast_latency_ms": ast_latency_ms,
        "baseline_latency_ms": baseline_latency_ms,
        "ratio": ratio,
        "meets_requirement": meets_requirement
    }

def main() -> int:
    """CLI entry point for latency measurement."""
    try:
        result = run_latency_analysis()
        print(json.dumps(result, indent=2))
        return 0 if result["meets_requirement"] else 1
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 2
    except ValueError as e:
        logger.error(f"Invalid data: {e}")
        return 3
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 4

if __name__ == "__main__":
    import sys
    sys.exit(main())
