"""
Encoder Verification Utility (T008a)

Verifies the availability and memory footprint of:
1. distil-whisper/distil-large-v2
2. openai/whisper-distil-base

Runs on CPU only. Logs availability and peak RAM usage.
Addresses FR-001 (Flexibility) by ensuring fallback options are viable.
"""

import os
import gc
import time
import logging
import json
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

import torch
import psutil
from transformers import AutoModel, AutoProcessor, AutoConfig
from datasets import load_dataset

# Project imports
from config import set_seed, ensure_directories
from utils.memory_monitor import (
    get_current_memory_mb,
    get_peak_memory_mb,
    update_peak_memory,
    force_gc,
    MemoryWatcher
)

# Configuration
ENCODERS = [
    "distil-whisper/distil-large-v2",
    "openai/whisper-distil-base"
]

# Ensure we have a small test sample for memory profiling
# Using a tiny subset of a public dataset to avoid large downloads
TEST_DATASET_NAME = "audio_bench/jailbreak_v1"
# Fallback if specific dataset not available, use a generic small audio set
# We will attempt to load just 1 sample to measure model overhead
SAMPLE_SIZE = 1

def setup_logging(log_dir: str) -> logging.Logger:
    """Configure structured logging for the verification run."""
    logger = logging.getLogger("encoder_verify")
    logger.setLevel(logging.INFO)
    
    # File handler
    log_file = Path(log_dir) / "encoder_verification.log"
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.INFO)
    
    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    
    logger.addHandler(fh)
    logger.addHandler(ch)
    
    return logger

def get_model_memory_footprint(
    model_name: str,
    logger: logging.Logger,
    device: str = "cpu"
) -> Dict[str, Any]:
    """
    Loads a model on CPU, measures peak memory, and returns stats.
    Returns a dictionary with availability status and memory metrics.
    """
    result = {
        "model": model_name,
        "available": False,
        "device": device,
        "params_millions": 0.0,
        "peak_memory_mb": 0.0,
        "load_time_sec": 0.0,
        "error": None
    }

    force_gc()
    start_mem = get_current_memory_mb()
    peak_mem_before = get_peak_memory_mb()
    
    logger.info(f"Testing availability and memory for: {model_name}")
    
    try:
        # 1. Load Config to get parameter count
        config_start = time.time()
        config = AutoConfig.from_pretrained(model_name)
        config_time = time.time() - config_start
        
        # Estimate parameters (some models have hidden attributes, try standard approach)
        if hasattr(config, "num_parameters"):
            params = config.num_parameters()
        else:
            # Fallback estimation if method missing (rare)
            params = 0
            # We can't easily sum params without loading weights, so we load weights next
        
        # 2. Load Model (CPU only)
        load_start = time.time()
        model = AutoModel.from_pretrained(
            model_name,
            torch_dtype=torch.float32, # Force float32 for CPU compatibility
            local_files_only=False
        )
        model = model.to(device)
        model.eval()
        load_time = time.time() - load_start

        # Calculate actual parameters if not available from config
        if params == 0:
            params = sum(p.numel() for p in model.parameters())

        # 3. Measure Memory
        # Trigger a forward pass with dummy data to ensure memory is allocated
        # We need a dummy input matching the model's expected shape
        # For Whisper/Distil models, this is usually audio or hidden states.
        # To be safe and generic, we rely on the memory monitor's peak tracking
        # which captures allocation during load and any internal buffers.
        
        update_peak_memory()
        current_peak = get_peak_memory_mb()
        memory_delta = current_peak - peak_mem_before
        
        result["available"] = True
        result["params_millions"] = params / 1_000_000.0
        result["peak_memory_mb"] = memory_delta
        result["load_time_sec"] = load_time
        
        logger.info(
            f"SUCCESS: {model_name} loaded. "
            f"Params: {result['params_millions']:.2f}M, "
            f"Memory Delta: {result['peak_memory_mb']:.2f} MB, "
            f"Load Time: {result['load_time_sec']:.2f}s"
        )

    except Exception as e:
        result["error"] = str(e)
        logger.error(f"FAILED: {model_name} - {str(e)}")
    
    finally:
        # Cleanup
        del model
        del config
        force_gc()
    
    return result

def verify_encoder_availability(
    log_dir: Optional[str] = None
) -> Dict[str, Any]:
    """
    Main entry point for T008a.
    Verifies all encoders in ENCODERS list and logs results.
    """
    if log_dir is None:
        # Default to project results if not specified, but T008a is setup
        # Let's write to data/processed or a specific log dir
        log_dir = "data/processed" 
    
    ensure_directories([log_dir])
    logger = setup_logging(log_dir)
    
    logger.info("Starting Encoder Verification (T008a)...")
    logger.info(f"Target Device: CPU")
    logger.info(f"Encoders to test: {ENCODERS}")
    
    set_seed(42) # From config.py
    
    results = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "encoders": [],
        "summary": {
            "total_tested": len(ENCODERS),
            "available_count": 0,
            "failed_count": 0
        }
    }
    
    for encoder_name in ENCODERS:
        stats = get_model_memory_footprint(encoder_name, logger)
        results["encoders"].append(stats)
        if stats["available"]:
            results["summary"]["available_count"] += 1
        else:
            results["summary"]["failed_count"] += 1
    
    # Write JSON report
    report_path = Path(log_dir) / "encoder_verification_report.json"
    with open(report_path, "w") as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Verification complete. Report saved to: {report_path}")
    return results

def main():
    """CLI entry point."""
    verify_encoder_availability()

if __name__ == "__main__":
    main()