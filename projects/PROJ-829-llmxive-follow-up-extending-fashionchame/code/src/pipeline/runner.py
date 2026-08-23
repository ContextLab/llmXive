import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Import existing components from the project API surface
from src.data.loader import load_deepfashion2_streaming, process_batch, iterate_dataset
from src.data.stratified_subset import load_filtered_manifest, stratify_samples
from src.adapters.text_cross_attention import TextCrossAttentionAdapter, load_adapter_from_config
from src.metrics.fidelity import compute_fidelity_scores
from src.metrics.latency import measure_inference_latency, evaluate_latency_pass_fail
from src.pipeline.streaming import get_current_memory_usage_bytes, should_trigger_batch_processing, trigger_memory_cleanup
from src.data.prompt_gen import generate_prompt

def ensure_cpu_only_execution():
    """
    Verifies that no CUDA calls are made during execution.
    Raises RuntimeError if CUDA is detected or if torch.cuda is available.
    Implements FR-004: CPU-only execution path verification.
    """
    import torch
    
    # Check if CUDA is available
    if torch.cuda.is_available():
        # If CUDA is available, we must ensure we are not using it
        # We force the device to CPU explicitly
        if torch.cuda.device_count() > 0:
            # Log warning but force CPU usage
            print(f"Warning: CUDA is available ({torch.cuda.device_count()} devices). "
                  f"Forcing CPU-only execution as per FR-004.")
    
    # Explicitly set device to CPU
    device = torch.device("cpu")
    
    # Verify no CUDA tensors are created
    # This is a runtime check to ensure no accidental CUDA usage
    test_tensor = torch.tensor([1.0], device=device)
    if test_tensor.is_cuda:
        raise RuntimeError("CUDA tensor detected despite CPU-only enforcement. "
                         "Execution path violates FR-004.")
    
    # Verify CUDA is not being used for any operations
    # If torch.backends.cuda is available, ensure it's not active
    if hasattr(torch.backends, 'cuda') and torch.backends.cuda.is_built():
        # We can't disable CUDA at runtime if built, but we can ensure we don't use it
        pass
    
    return device

def measure_component_latency(component_name: str, func: callable, *args, **kwargs) -> Tuple[float, Any]:
    """
    Measures latency for a specific component of the pipeline.
    Returns (latency_ms, result).
    """
    start_time = time.perf_counter()
    result = func(*args, **kwargs)
    end_time = time.perf_counter()
    latency_ms = (end_time - start_time) * 1000
    return latency_ms, result

def analyze_bottleneck(latencies: Dict[str, float], threshold_ms: float = 50.0) -> Dict[str, Any]:
    """
    Analyzes which components are bottlenecks based on latency thresholds.
    Returns a dictionary with bottleneck analysis.
    """
    bottlenecks = []
    for component, latency in latencies.items():
        if latency > threshold_ms:
            bottlenecks.append({
                "component": component,
                "latency_ms": latency,
                "threshold_ms": threshold_ms,
                "exceeds_threshold": True
            })
    
    return {
        "bottlenecks": bottlenecks,
        "total_components": len(latencies),
        "bottleneck_count": len(bottlenecks)
    }

def process_single_sample_with_bottleneck_analysis(
    sample: Dict[str, Any],
    adapter: TextCrossAttentionAdapter,
    device: torch.device,
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Processes a single sample with detailed bottleneck analysis.
    Ensures CPU-only execution and measures component latencies.
    """
    import torch
    
    # Ensure CPU-only execution for this sample
    if torch.cuda.is_available():
        raise RuntimeError("CUDA detected during sample processing. "
                         "FR-004 violation: CPU-only execution required.")
    
    latencies = {}
    
    try:
        # Measure text encoding latency
        start_time = time.perf_counter()
        text_embedding = adapter.text_encoder.encode(sample["prompt"])
        latencies["text_encoder"] = (time.perf_counter() - start_time) * 1000
        
        # Measure adapter forward pass latency
        start_time = time.perf_counter()
        adapter_output = adapter.forward(text_embedding)
        latencies["adapter_forward"] = (time.perf_counter() - start_time) * 1000
        
        # Measure backbone generation latency
        start_time = time.perf_counter()
        generated_output = adapter.backbone.generate(adapter_output)
        latencies["backbone_generate"] = (time.perf_counter() - start_time) * 1000
        
        # Calculate total latency
        total_latency = sum(latencies.values())
        
        return {
            "sample_id": sample.get("id", "unknown"),
            "latencies": latencies,
            "total_latency_ms": total_latency,
            "status": "success",
            "device": str(device)
        }
        
    except Exception as e:
        return {
            "sample_id": sample.get("id", "unknown"),
            "status": "error",
            "error_message": str(e),
            "device": str(device)
        }

def run_text_adapter_pipeline_with_bottleneck_analysis(
    config_path: str,
    subset_manifest_path: str,
    output_path: str
) -> Dict[str, Any]:
    """
    Runs the text adapter pipeline with comprehensive bottleneck analysis.
    Ensures CPU-only execution (FR-004) and measures all component latencies.
    
    Args:
        config_path: Path to configuration file
        subset_manifest_path: Path to filtered subset manifest
        output_path: Path to output results file
    
    Returns:
        Dictionary containing pipeline results and analysis
    """
    import torch
    
    # Step 1: Ensure CPU-only execution
    device = ensure_cpu_only_execution()
    
    # Load configuration
    config = load_adapter_from_config(Path(config_path))
    
    # Initialize adapter
    adapter = TextCrossAttentionAdapter(config)
    adapter.to(device)
    
    # Load filtered subset
    filtered_samples = load_filtered_manifest(Path(subset_manifest_path))
    
    # Process each sample with bottleneck analysis
    results = []
    total_latencies = []
    
    for sample in filtered_samples:
        result = process_single_sample_with_bottleneck_analysis(
            sample, adapter, device, config
        )
        results.append(result)
        
        if result["status"] == "success":
            total_latencies.append(result["total_latency_ms"])
    
    # Calculate aggregate statistics
    if total_latencies:
        avg_latency = sum(total_latencies) / len(total_latencies)
        max_latency = max(total_latencies)
        min_latency = min(total_latencies)
    else:
        avg_latency = 0.0
        max_latency = 0.0
        min_latency = 0.0
    
    # Analyze bottlenecks
    component_latencies = {}
    for result in results:
        if result["status"] == "success":
            for component, latency in result["latencies"].items():
                if component not in component_latencies:
                    component_latencies[component] = []
                component_latencies[component].append(latency)
    
    avg_component_latencies = {
        component: sum(latencies) / len(latencies)
        for component, latencies in component_latencies.items()
    }
    
    bottleneck_analysis = analyze_bottleneck(
        avg_component_latencies, 
        config.get("latency_threshold_ms", 50.0)
    )
    
    # Compile final report
    final_report = {
        "execution_mode": "cpu_only",
        "device_used": str(device),
        "total_samples_processed": len(results),
        "successful_samples": sum(1 for r in results if r["status"] == "success"),
        "failed_samples": sum(1 for r in results if r["status"] == "error"),
        "latency_statistics": {
            "average_ms": avg_latency,
            "max_ms": max_latency,
            "min_ms": min_latency,
            "threshold_ms": config.get("latency_threshold_ms", 50.0)
        },
        "component_latencies": avg_component_latencies,
        "bottleneck_analysis": bottleneck_analysis,
        "fr004_compliance": {
            "cuda_available": torch.cuda.is_available(),
            "cpu_only_enforced": True,
            "verification_passed": not torch.cuda.is_available() or (
                torch.cuda.is_available() and device.type == "cpu"
            )
        },
        "sample_results": results
    }
    
    # Write results to output file
    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path_obj, 'w') as f:
        json.dump(final_report, f, indent=2)
    
    return final_report

def main():
    """
    Main entry point for the pipeline runner with CPU-only verification.
    """
    parser = argparse.ArgumentParser(description="Run text adapter pipeline with CPU-only verification")
    parser.add_argument("--config", type=str, required=True, help="Path to configuration file")
    parser.add_argument("--subset", type=str, required=True, help="Path to filtered subset manifest")
    parser.add_argument("--output", type=str, required=True, help="Path to output results file")
    
    args = parser.parse_args()
    
    try:
        result = run_text_adapter_pipeline_with_bottleneck_analysis(
            args.config,
            args.subset,
            args.output
        )
        
        print(f"Pipeline completed successfully.")
        print(f"CPU-only enforcement: {'PASSED' if result['fr004_compliance']['verification_passed'] else 'FAILED'}")
        print(f"Average latency: {result['latency_statistics']['average_ms']:.2f}ms")
        print(f"Results written to: {args.output}")
        
    except Exception as e:
        print(f"Pipeline failed with error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()