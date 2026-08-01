import os
import json
import torch
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional
import time

# Constants
MAX_RAM_GB = 7.0
MAX_RUNTIME_HOURS = 6.0
RUNTIME_ESTIMATE_PER_SAMPLE_SEC = 0.5  # Conservative estimate: 0.5s per sample for VAE + OCR + Classifier overhead
BASE_OVERHEAD_SEC = 300  # 5 minutes base overhead for loading models, I/O, etc.

def estimate_peak_ram_usage(n_samples: int, latent_dim: int = 64, batch_size: int = 1) -> float:
    """
    Estimate peak RAM usage in GB for processing n_samples.
    
    Simplified model:
    - VAE model size (CPU): ~1GB (conservative for Qwen-Image-VAE-2.0)
    - Per-sample latent vector: latent_dim * 4 bytes (float32)
    - Overhead for OCR, image loading, classifier: ~0.5GB per batch
    - PyTorch/NumPy overhead: ~1GB base
    
    Args:
        n_samples: Number of samples to process
        latent_dim: Dimensionality of latent vectors (default 64)
        batch_size: Processing batch size
        
    Returns:
        Estimated peak RAM usage in GB
    """
    # Base model and library overhead
    base_overhead_gb = 3.0  # VAE model + PyTorch + NumPy + OCR engine
    
    # Per-sample memory (latent vectors, intermediate tensors)
    # Assuming we store latents for all samples
    latent_memory_gb = (n_samples * latent_dim * 4) / (1024**3)  # bytes to GB
    
    # Batch processing overhead
    batch_overhead_gb = (0.5 * (n_samples / batch_size)) / 10  # Scaled down for chunking
    
    total_gb = base_overhead_gb + latent_memory_gb + max(batch_overhead_gb, 0.5)
    
    return total_gb

def calculate_max_samples(peak_ram_limit_gb: float = MAX_RAM_GB) -> int:
    """
    Calculate maximum number of samples that can fit in memory.
    
    Args:
        peak_ram_limit_gb: RAM limit in GB (default 7.0)
        
    Returns:
        Maximum number of samples
    """
    # Reverse the estimation: solve for n_samples
    # peak_ram = base + n * latent_bytes / 1024^3 + batch_overhead
    # Simplified: assume 0.5GB per 1000 samples for latent storage + overhead
    samples_per_gb = 2000  # Conservative: 2000 samples per GB
    max_samples = int((peak_ram_limit_gb - 3.0) * samples_per_gb)
    
    return max(100, max_samples)  # At least 100 samples

def determine_chunk_size(n_samples: int, peak_ram_limit_gb: float = MAX_RAM_GB) -> int:
    """
    Determine optimal chunk size for processing given memory constraints.
    
    Args:
        n_samples: Total number of samples
        peak_ram_limit_gb: RAM limit in GB
        
    Returns:
        Chunk size for batch processing
    """
    max_samples = calculate_max_samples(peak_ram_limit_gb)
    
    # If total samples fit in memory, use all
    if n_samples <= max_samples:
        return n_samples
    
    # Otherwise, split into chunks that fit
    # Use 80% of max capacity for safety
    safe_max = int(max_samples * 0.8)
    return max(100, safe_max)

def estimate_runtime(n_samples: int) -> float:
    """
    Estimate total runtime in seconds for processing n_samples.
    
    Args:
        n_samples: Number of samples to process
        
    Returns:
        Estimated runtime in seconds
    """
    return BASE_OVERHEAD_SEC + (n_samples * RUNTIME_ESTIMATE_PER_SAMPLE_SEC)

def run_runtime_fallback_logic(power_analysis_path: str, output_path: str) -> Dict[str, Any]:
    """
    Implement runtime fallback logic (Task 0.4).
    
    Reads N_required from power_analysis.json, estimates runtime,
    and determines if N needs to be reduced to fit within 6h limit.
    
    Args:
        power_analysis_path: Path to power_analysis.json from T000
        output_path: Path to write runtime_fallback.json
        
    Returns:
        Dictionary with N_final, estimated_runtime, status
    """
    power_path = Path(power_analysis_path)
    if not power_path.exists():
        raise FileNotFoundError(f"Power analysis file not found: {power_analysis_path}")
    
    with open(power_path, 'r') as f:
        power_data = json.load(f)
    
    n_required = power_data.get('N_required')
    if n_required is None:
        raise ValueError("N_required not found in power analysis file")
    
    # Estimate runtime
    estimated_runtime_sec = estimate_runtime(n_required)
    estimated_runtime_hours = estimated_runtime_sec / 3600
    
    # Determine if we exceed the 6h limit
    max_runtime_sec = MAX_RUNTIME_HOURS * 3600
    
    result = {}
    if estimated_runtime_sec <= max_runtime_sec:
        # Runtime is acceptable
        result = {
            "N_final": n_required,
            "estimated_runtime_seconds": estimated_runtime_sec,
            "estimated_runtime_hours": estimated_runtime_hours,
            "status": "PASS",
            "runtime_inconclusive": False,
            "limitation_text": None
        }
    else:
        # Need to reduce N to fit within 6h
        # Calculate N_fallback that fits exactly in 6h
        # runtime = BASE + N * RATE
        # N = (max_runtime - BASE) / RATE
        n_fallback = int((max_runtime_sec - BASE_OVERHEAD_SEC) / RUNTIME_ESTIMATE_PER_SAMPLE_SEC)
        n_fallback = max(100, n_fallback)  # Ensure at least 100 samples
        
        # Recalculate actual runtime with fallback
        actual_runtime_sec = estimate_runtime(n_fallback)
        actual_runtime_hours = actual_runtime_sec / 3600
        
        result = {
            "N_final": n_fallback,
            "estimated_runtime_seconds": actual_runtime_sec,
            "estimated_runtime_hours": actual_runtime_hours,
            "status": "INCONCLUSIVE",
            "runtime_inconclusive": True,
            "N_original": n_required,
            "N_reduced_by": n_required - n_fallback,
            "limitation_text": f"Runtime constraint: Original N={n_required} would take {estimated_runtime_hours:.1f}h. "
                              f"Reduced to N={n_fallback} to fit within {MAX_RUNTIME_HOURS}h limit. "
                              f"Statistical power may be lower than target (0.8)."
        }
    
    # Write output
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)
    
    return result

def main():
    """Main entry point for runtime fallback logic."""
    # Paths relative to project root
    project_root = Path(__file__).resolve().parent.parent.parent
    power_analysis_path = project_root / "data" / "results" / "power_analysis.json"
    output_path = project_root / "data" / "results" / "runtime_fallback.json"
    
    print(f"Running runtime fallback logic...")
    print(f"Reading from: {power_analysis_path}")
    print(f"Writing to: {output_path}")
    
    try:
        result = run_runtime_fallback_logic(str(power_analysis_path), str(output_path))
        print(f"Runtime fallback status: {result['status']}")
        print(f"N_final: {result['N_final']}")
        print(f"Estimated runtime: {result['estimated_runtime_hours']:.2f} hours")
        
        if result.get('runtime_inconclusive'):
            print(f"WARNING: {result['limitation_text']}")
            
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        print("Ensure T000 (Power Analysis) has been completed first.")
        raise
    except Exception as e:
        print(f"ERROR during execution: {e}")
        raise

if __name__ == "__main__":
    main()
