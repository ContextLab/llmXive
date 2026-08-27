import argparse
import json
import os
import sys
import time
import torch
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import yaml
import gc

from src.adapters.text_cross_attention import TextCrossAttentionAdapter, load_adapter_from_config
from src.data.loader import load_deepfashion2_streaming, load_config
from src.data.stratified_subset import load_filtered_manifest, validate_subset_balance
from src.metrics.fidelity import compute_fidelity_scores
from src.metrics.latency import measure_inference_latency, evaluate_latency_pass_fail
from src.pipeline.streaming import process_batch_with_memory_check, get_current_memory_usage_bytes
from src.pipeline.reporter import generate_report

def ensure_cpu_only_execution():
    """Ensure execution is restricted to CPU only."""
    if torch.cuda.is_available():
        raise RuntimeError("CUDA is available but CPU-only execution is required. "
                         "Set CUDA_VISIBLE_DEVICES='' or use CPU-only environment.")
    device = torch.device('cpu')
    return device

def measure_component_latency(component_name: str, func, *args, **kwargs) -> Tuple[float, Any]:
    """Measure latency of a specific component."""
    start_time = time.perf_counter()
    result = func(*args, **kwargs)
    end_time = time.perf_counter()
    latency_ms = (end_time - start_time) * 1000
    return latency_ms, result

def analyze_bottleneck(latencies: Dict[str, float]) -> Dict[str, Any]:
    """Analyze which component is the bottleneck."""
    if not latencies:
        return {"status": "no_data"}
    
    max_component = max(latencies, key=latencies.get)
    total_time = sum(latencies.values())
    
    return {
        "bottleneck": max_component,
        "bottleneck_time_ms": latencies[max_component],
        "total_time_ms": total_time,
        "bottleneck_percentage": (latencies[max_component] / total_time) * 100 if total_time > 0 else 0,
        "all_latencies": latencies
    }

def process_single_sample_with_bottleneck_analysis(
    sample: Dict[str, Any],
    adapter: TextCrossAttentionAdapter,
    device: torch.device
) -> Dict[str, Any]:
    """
    Process a single sample with detailed bottleneck analysis.
    
    Args:
        sample: Dictionary containing sample data
        adapter: Initialized TextCrossAttentionAdapter
        device: Device to run on (must be CPU)
    
    Returns:
        Dictionary with results and latency breakdown
    """
    latencies = {}
    results = {}
    
    try:
        # 1. Text encoding latency
        text_embedding = sample.get('text_embedding')
        if text_embedding is None:
            # Generate from text if not present (in real pipeline, this comes from T008)
            raise ValueError("Text embedding required for adapter processing")
        
        text_embedding_tensor = torch.tensor(text_embedding, dtype=torch.float32, device=device)
        
        # 2. Adapter forward pass latency
        query = sample.get('query_features')
        if query is None:
            raise ValueError("Query features required for adapter processing")
        
        query_tensor = torch.tensor(query, dtype=torch.float32, device=device)
        
        latency, (output, attn_weights) = measure_component_latency(
            "adapter_forward",
            adapter.forward,
            text_embedding_tensor,
            query_tensor
        )
        latencies['adapter_forward'] = latency
        results['output'] = output.cpu().numpy().tolist()
        results['attention_weights'] = attn_weights.cpu().numpy().tolist()
        
        # 3. Fidelity calculation (if reference images available)
        if 'reference_image' in sample and 'generated_image' in sample:
            from src.metrics.fidelity import compute_lpips, compute_ssim
            ref_img = torch.tensor(sample['reference_image'], dtype=torch.float32, device=device)
            gen_img = torch.tensor(sample['generated_image'], dtype=torch.float32, device=device)
            
            lpips_score = compute_lpips(ref_img, gen_img)
            ssim_score = compute_ssim(ref_img, gen_img)
            
            results['lpips'] = float(lpips_score)
            results['ssim'] = float(ssim_score)
        
        # 4. Overall inference latency
        results['sample_id'] = sample.get('sample_id', 'unknown')
        results['latencies'] = latencies
        results['total_latency_ms'] = sum(latencies.values())
        results['status'] = 'success'
        
    except Exception as e:
        results['sample_id'] = sample.get('sample_id', 'unknown')
        results['error'] = str(e)
        results['status'] = 'failed'
        results['latencies'] = latencies
    
    return results

def run_text_adapter_pipeline_with_bottleneck_analysis(
    subset_size: int = 100,
    config_path: str = 'code/config/settings.yaml',
    output_dir: str = 'data/processed'
) -> Dict[str, Any]:
    """
    Execute the text-driven adapter on the stratified subset with bottleneck analysis.
    
    This is the main implementation for T019: Execute text-driven adapter pipeline.
    
    Args:
        subset_size: Number of samples to process
        config_path: Path to configuration file
        output_dir: Directory for output files
    
    Returns:
        Dictionary with aggregated results
    """
    # Ensure CPU-only execution
    device = ensure_cpu_only_execution()
    print(f"Running on device: {device}")
    
    # Load configuration
    config = load_config(config_path)
    
    # Initialize adapter
    adapter = load_adapter_from_config(config_path)
    adapter.eval()
    adapter.to(device)
    print(f"Adapter initialized: {type(adapter).__name__}")
    
    # Load stratified subset
    manifest_path = Path('data/processed/filtered_subset_manifest.json')
    if not manifest_path.exists():
        raise FileNotFoundError(f"Filtered subset manifest not found: {manifest_path}")
    
    samples = load_filtered_manifest(str(manifest_path))
    
    # Filter to requested subset size
    if len(samples) > subset_size:
        samples = samples[:subset_size]
    
    print(f"Processing {len(samples)} samples from stratified subset")
    
    # Process each sample
    all_results = []
    total_latencies = []
    
    for i, sample in enumerate(samples):
        if i % 10 == 0:
            print(f"Processing sample {i+1}/{len(samples)}")
        
        # Memory check
        mem_usage = get_current_memory_usage_bytes()
        if mem_usage > config.get('memory_trigger_mb', 14000) * 1024 * 1024:
            print(f"Memory threshold exceeded ({mem_usage / (1024*1024):.1f} MB), triggering cleanup")
            gc.collect()
        
        result = process_single_sample_with_bottleneck_analysis(sample, adapter, device)
        all_results.append(result)
        
        if result['status'] == 'success':
            total_latencies.append(result['total_latency_ms'])
        
        # Clear memory
        del sample
        gc.collect()
    
    # Aggregate results
    successful_results = [r for r in all_results if r['status'] == 'success']
    failed_results = [r for r in all_results if r['status'] == 'failed']
    
    # Calculate statistics
    if total_latencies:
        avg_latency = np.mean(total_latencies)
        std_latency = np.std(total_latencies)
        max_latency = np.max(total_latencies)
        min_latency = np.min(total_latencies)
    else:
        avg_latency = 0
        std_latency = 0
        max_latency = 0
        min_latency = 0
    
    # Analyze bottlenecks
    all_latencies_combined = {}
    for result in successful_results:
        for key, value in result['latencies'].items():
            all_latencies_combined[key] = all_latencies_combined.get(key, 0) + value
    
    bottleneck_analysis = analyze_bottleneck(all_latencies_combined)
    
    # Prepare final report
    report = {
        "pipeline": "text_adapter",
        "device": str(device),
        "total_samples": len(samples),
        "successful_samples": len(successful_results),
        "failed_samples": len(failed_results),
        "latency_statistics": {
            "mean_ms": float(avg_latency),
            "std_ms": float(std_latency),
            "max_ms": float(max_latency),
            "min_ms": float(min_latency)
        },
        "bottleneck_analysis": bottleneck_analysis,
        "per_sample_results": all_results
    }
    
    # Write output
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    output_file = output_path / 'text_adapter_results.json'
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"Results written to {output_file}")
    print(f"Success rate: {len(successful_results)}/{len(samples)} ({100*len(successful_results)/len(samples):.1f}%)")
    
    return report

def main():
    """Main entry point for the runner script."""
    parser = argparse.ArgumentParser(description='Run text-driven adapter pipeline')
    parser.add_argument('--subset-size', type=int, default=100,
                      help='Number of samples to process')
    parser.add_argument('--config', type=str, default='code/config/settings.yaml',
                      help='Path to configuration file')
    parser.add_argument('--output-dir', type=str, default='data/processed',
                      help='Output directory for results')
    
    args = parser.parse_args()
    
    try:
        report = run_text_adapter_pipeline_with_bottleneck_analysis(
            subset_size=args.subset_size,
            config_path=args.config,
            output_dir=args.output_dir
        )
        
        print("\n=== Pipeline Execution Complete ===")
        print(f"Total samples: {report['total_samples']}")
        print(f"Successful: {report['successful_samples']}")
        print(f"Failed: {report['failed_samples']}")
        print(f"Average latency: {report['latency_statistics']['mean_ms']:.2f} ms")
        print(f"Bottleneck: {report['bottleneck_analysis'].get('bottleneck', 'N/A')}")
        
    except Exception as e:
        print(f"Pipeline execution failed: {e}")
        raise

if __name__ == '__main__':
    main()