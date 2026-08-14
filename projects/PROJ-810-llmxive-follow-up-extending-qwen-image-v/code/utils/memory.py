"""
Memory budget estimation and chunking strategy for VAE + OCR + Classifier pipeline.

Estimates peak RAM usage to determine safe chunk sizes and maximum sample counts
that fit within the 7GB RAM constraint.
"""
import os
import json
import torch
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional

# Constants
MAX_RAM_GB = 7.0
SAFETY_FACTOR = 0.8  # Use 80% of available RAM to be safe
VAE_MODEL_ID = "Qwen/Qwen-Image-VAE-2.0"
OCR_MODEL_ID = "PaddleOCR"

# Memory estimates in GB (approximate, based on model architecture)
# These are estimates that will be refined during runtime
MODEL_MEMORY_ESTIMATES = {
    "vae_encoder": 2.5,  # VAE encoder model
    "vae_decoder": 2.5,  # VAE decoder model  
    "ocr_engine": 1.5,   # PaddleOCR engine
    "classifier": 0.2,   # Linear SVM classifier
    "image_buffer": 0.5, # Image loading buffer per batch
    "overhead": 0.5      # General Python/NumPy overhead
}

def estimate_peak_ram_usage(n_samples: int, image_height: int = 512, image_width: int = 512) -> Dict[str, float]:
    """
    Estimate peak RAM usage for processing n_samples.
    
    Args:
        n_samples: Number of samples to process
        image_height: Height of images (default 512)
        image_width: Width of images (default 512)
        
    Returns:
        Dictionary with memory estimates for each component
    """
    # Estimate memory per image in latent space
    # Assuming latent dimensions ~ 64x64x4 = 16384 floats per image
    latent_per_image = 64 * 64 * 4 * 4 / (1024**3)  # bytes to GB (float32 = 4 bytes)
    
    # OCR processing memory per image (conservative estimate)
    ocr_per_image = 0.01  # ~10MB per image for OCR processing
    
    # Total per-sample memory
    per_sample_memory = latent_per_image + ocr_per_image
    
    # Peak memory = model memory + (per_sample * n_samples) + overhead
    model_memory = sum(MODEL_MEMORY_ESTIMATES.values())
    sample_memory = per_sample_memory * n_samples
    
    peak_ram_gb = model_memory + sample_memory
    
    return {
        "model_memory_gb": model_memory,
        "per_sample_memory_gb": per_sample_memory,
        "sample_memory_gb": sample_memory,
        "peak_ram_gb": peak_ram_gb,
        "n_samples": n_samples
    }

def calculate_max_samples(available_ram_gb: float = MAX_RAM_GB) -> int:
    """
    Calculate maximum number of samples that can be processed within RAM constraints.
    
    Args:
        available_ram_gb: Available RAM in GB (default 7.0)
        
    Returns:
        Maximum number of samples that fit in memory
    """
    safe_ram_gb = available_ram_gb * SAFETY_FACTOR
    model_memory = sum(MODEL_MEMORY_ESTIMATES.values())
    
    # Available for samples
    sample_budget_gb = safe_ram_gb - model_memory
    
    if sample_budget_gb <= 0:
        return 0
    
    # Per sample memory estimate
    per_sample = 0.011  # Combined latent + OCR estimate
    
    max_samples = int(sample_budget_gb / per_sample)
    return max(1, max_samples)

def determine_chunk_size(max_samples: int, target_max_samples: int = 1000) -> int:
    """
    Determine optimal chunk size for batched processing.
    
    Args:
        max_samples: Maximum samples that fit in memory
        target_max_samples: Target chunk size if memory allows
        
    Returns:
        Optimal chunk size
    """
    if max_samples <= 0:
        return 1
    
    # Use the smaller of target or max_samples
    chunk_size = min(target_max_samples, max_samples)
    
    # Ensure chunk size is at least 1
    return max(1, chunk_size)

def estimate_runtime(n_samples: int, samples_per_hour: int = 1000) -> Dict[str, float]:
    """
    Estimate runtime for processing n_samples.
    
    Args:
        n_samples: Number of samples to process
        samples_per_hour: Estimated processing rate (default 1000 samples/hour)
        
    Returns:
        Dictionary with runtime estimates
    """
    estimated_hours = n_samples / samples_per_hour
    estimated_seconds = estimated_hours * 3600
    
    return {
        "estimated_hours": estimated_hours,
        "estimated_seconds": estimated_seconds,
        "samples_per_hour": samples_per_hour
    }

def run_runtime_fallback_logic(n_required: int, max_runtime_hours: float = 6.0) -> Dict[str, Any]:
    """
    Determine if runtime fallback is needed based on N_required.
    
    Args:
        n_required: Required sample size from power analysis
        max_runtime_hours: Maximum acceptable runtime in hours (default 6)
        
    Returns:
        Dictionary with fallback strategy information
    """
    # Estimate samples per hour (conservative)
    samples_per_hour = 500  # Conservative estimate for CPU-only processing
    estimated_runtime_hours = n_required / samples_per_hour
    
    if estimated_runtime_hours > max_runtime_hours:
        # Calculate fallback N
        n_fallback = int(max_runtime_hours * samples_per_hour)
        return {
            "n_required": n_required,
            "n_fallback": n_fallback,
            "estimated_runtime_hours": estimated_runtime_hours,
            "max_runtime_hours": max_runtime_hours,
            "status": "runtime_inconclusive",
            "message": f"Required N ({n_required}) would exceed {max_runtime_hours}h runtime. Using N={n_fallback}."
        }
    else:
        return {
            "n_required": n_required,
            "n_fallback": n_required,
            "estimated_runtime_hours": estimated_runtime_hours,
            "max_runtime_hours": max_runtime_hours,
            "status": "pass",
            "message": "Runtime within acceptable limits."
        }

def main():
    """
    Main function to run memory budget analysis and generate memory_budget.json.
    
    This function:
    1. Estimates peak RAM for the full pipeline
    2. Calculates max samples that fit in 7GB RAM
    3. Determines optimal chunk size
    4. Checks against power analysis results (from T000)
    5. Generates memory_budget.json with fallback strategy
    """
    # Load power analysis results if available
    power_analysis_path = Path("data/results/power_analysis.json")
    n_required = 1000  # Default fallback
    n_audit = 50       # Default fallback
    
    if power_analysis_path.exists():
        try:
            with open(power_analysis_path, 'r') as f:
                power_data = json.load(f)
                n_required = power_data.get('N_required', 1000)
                n_audit = power_data.get('N_audit', 50)
        except Exception as e:
            print(f"Warning: Could not load power analysis: {e}. Using defaults.")
    
    # Calculate memory requirements
    memory_estimate = estimate_peak_ram_usage(n_required)
    
    # Calculate max samples and chunk size
    max_samples = calculate_max_samples(MAX_RAM_GB)
    chunk_size = determine_chunk_size(max_samples)
    
    # Determine fallback strategy
    if memory_estimate['peak_ram_gb'] > MAX_RAM_GB:
        fallback_strategy = "chunked_processing"
        status = "NEEDS_REDUCTION"
    else:
        fallback_strategy = "full_batch"
        status = "OK"
    
    # Check runtime constraints
    runtime_info = run_runtime_fallback_logic(n_required)
    
    # Prepare output
    output = {
        "chunk_size": chunk_size,
        "max_samples": max_samples,
        "fallback_strategy": fallback_strategy,
        "n_required": n_required,
        "n_audit": n_audit,
        "memory_required_gb": round(memory_estimate['peak_ram_gb'], 2),
        "max_ram_gb": MAX_RAM_GB,
        "status": status,
        "runtime_info": runtime_info
    }
    
    # Write output file
    output_path = Path("data/results/memory_budget.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"Memory budget analysis complete. Output written to {output_path}")
    print(f"  Chunk size: {chunk_size}")
    print(f"  Max samples: {max_samples}")
    print(f"  Estimated peak RAM: {output['memory_required_gb']} GB")
    print(f"  Status: {status}")
    
    return output

if __name__ == "__main__":
    main()
