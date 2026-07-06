"""
Script to verify pilot batch feasibility (T010).

Calculates memory footprint and estimated runtime for N=1200 signals
(6 depths x 4 bins x 50 signals) to ensure it fits within:
- 7 GB RAM limit
- 6-hour CI time limit

Uses resource constraints defined in src/config.py (T009).
"""
import os
import sys
import json
import time
import numpy as np
from pathlib import Path
from typing import Dict, Any, Tuple

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config import get_resource_limits, calculate_batch_constraints, verify_pilot_feasibility
from src.state_manager import record_phase_state, load_state_file, save_state_file


def estimate_memory_per_signal(bit_depth: int = 16, num_samples: int = 4096) -> float:
    """
    Estimate memory usage per signal in GB.
    
    Args:
        bit_depth: Quantization bit depth (affects storage, but we process in float64)
        num_samples: Number of samples per waveform (typical for GW analysis)
        
    Returns:
        Estimated memory in GB
    """
    # Waveforms are processed in float64 (8 bytes) regardless of quantization depth
    # We store: waveform, noise, quantized_waveform, metadata, posterior samples
    # Conservative estimate: 10 arrays of size num_samples + overhead
    base_size_bytes = num_samples * 8 * 10  # 10 float64 arrays
    
    # Add overhead for metadata, posterior samples, etc.
    overhead_bytes = 1024 * 1024  # 1 MB overhead
    
    total_bytes = base_size_bytes + overhead_bytes
    return total_bytes / (1024**3)  # Convert to GB


def estimate_runtime_per_signal(target_snr: float = 20) -> float:
    """
    Estimate runtime per signal in seconds based on SNR.
    
    Lower SNR signals require more MCMC steps for convergence.
    Based on typical Bilby/PyCBC performance on 2 CPU cores.
    
    Args:
        target_snr: Target signal-to-noise ratio
        
    Returns:
        Estimated runtime in seconds
    """
    # Base runtime for high SNR (fast convergence)
    base_runtime = 60.0  # 1 minute for SNR > 30
    
    # Runtime increases for lower SNR (harder convergence)
    snr_factor = 1.0 + (40.0 / target_snr) if target_snr < 30 else 1.0
    
    return base_runtime * snr_factor


def calculate_batch_metrics() -> Dict[str, Any]:
    """
    Calculate detailed metrics for the pilot batch.
    
    Returns:
        Dictionary with memory, time, and feasibility metrics
    """
    # Configuration from T009
    depths = [1, 8, 10, 12, 14, 16]
    snr_bins = [(8, 14), (14, 20), (20, 30), (30, 50)]
    signals_per_bin = 50
    
    total_signals = len(depths) * len(snr_bins) * signals_per_bin
    
    # Memory estimation
    mem_per_signal = estimate_memory_per_signal()
    total_memory_gb = mem_per_signal * total_signals
    
    # Time estimation (weighted average across SNR bins)
    # Lower SNR bins take longer
    time_per_signal = 0.0
    for snr_min, snr_max in snr_bins:
        avg_snr = (snr_min + snr_max) / 2
        time_per_signal += estimate_runtime_per_signal(avg_snr) * signals_per_bin
    time_per_signal /= len(snr_bins)
    
    total_time_seconds = time_per_signal * total_signals
    total_time_hours = total_time_seconds / 3600
    
    # Parallel processing (2 cores as per T009)
    cores = 2
    parallel_time_hours = total_time_hours / cores
    
    return {
        "total_signals": total_signals,
        "depths": depths,
        "snr_bins": snr_bins,
        "signals_per_bin": signals_per_bin,
        "memory_per_signal_gb": mem_per_signal,
        "total_memory_gb": total_memory_gb,
        "time_per_signal_seconds": time_per_signal,
        "total_time_hours": total_time_hours,
        "parallel_time_hours": parallel_time_hours,
        "cores": cores,
        "constraints": {
            "max_memory_gb": 7.0,
            "max_time_hours": 6.0
        },
        "feasible": total_memory_gb < 7.0 and parallel_time_hours < 6.0
    }


def main():
    """
    Main entry point for T010 verification.
    
    Calculates batch feasibility and writes results to data/results/
    """
    print("=" * 60)
    print("T010: Verifying Pilot Batch Feasibility")
    print("=" * 60)
    
    # Get resource limits from config (T009)
    limits = get_resource_limits()
    constraints = calculate_batch_constraints()
    
    print(f"\nResource Limits (from T009):")
    print(f"  Max RAM: {limits['max_memory_gb']} GB")
    print(f"  Max Time: {limits['max_time_hours']} hours")
    print(f"  Cores: {limits['cores']}")
    
    # Calculate metrics
    metrics = calculate_batch_metrics()
    
    print(f"\nPilot Batch Configuration:")
    print(f"  Total Signals: {metrics['total_signals']}")
    print(f"  Bit Depths: {metrics['depths']}")
    print(f"  SNR Bins: {metrics['snr_bins']}")
    print(f"  Signals per Bin: {metrics['signals_per_bin']}")
    
    print(f"\nResource Estimates:")
    print(f"  Memory per Signal: {metrics['memory_per_signal_gb']:.4f} GB")
    print(f"  Total Memory: {metrics['total_memory_gb']:.4f} GB")
    print(f"  Time per Signal (avg): {metrics['time_per_signal_seconds']:.1f} seconds")
    print(f"  Total Time (sequential): {metrics['total_time_hours']:.2f} hours")
    print(f"  Total Time (parallel, {metrics['cores']} cores): {metrics['parallel_time_hours']:.2f} hours")
    
    # Feasibility check
    is_feasible = metrics['feasible']
    print(f"\nFeasibility Check:")
    print(f"  Memory < 7 GB: {metrics['total_memory_gb']:.4f} < 7.0 = {metrics['total_memory_gb'] < 7.0}")
    print(f"  Time < 6 hours (parallel): {metrics['parallel_time_hours']:.2f} < 6.0 = {metrics['parallel_time_hours'] < 6.0}")
    print(f"  OVERALL: {'FEASIBLE' if is_feasible else 'NOT FEASIBLE'}")
    
    # Save results to data/results/
    output_dir = project_root / "data" / "results"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / "pilot_feasibility.json"
    
    # Add verification metadata
    result = {
        "task_id": "T010",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "configuration": metrics,
        "resource_limits": limits,
        "batch_constraints": constraints,
        "verification_passed": is_feasible
    }
    
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"\nResults saved to: {output_file}")
    
    # Record state
    state_file = project_root / "state.yaml"
    record_phase_state("T010", [str(output_file)], state_file)
    
    if not is_feasible:
        print("\n" + "=" * 60)
        print("ERROR: Pilot batch does not fit within constraints!")
        print("=" * 60)
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("SUCCESS: Pilot batch is feasible within constraints.")
    print("=" * 60)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
