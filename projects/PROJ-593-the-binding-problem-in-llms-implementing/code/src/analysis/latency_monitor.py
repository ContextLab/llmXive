import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

import torch
from transformers import DistilBertTokenizerFast

# Import the base model wrapper and oscillatory module as per project API
from src.models.base_model import DistilBERTWrapper, load_distilbert_cpu
from src.models.oscillatory_attention import OscillatoryDistilBERTWrapper, create_oscillatory_attention

def measure_forward_pass_latency(
    model: torch.nn.Module,
    tokenizer: DistilBertTokenizerFast,
    texts: List[str],
    device: str = "cpu",
    warmup_runs: int = 2,
    measurement_runs: int = 5
) -> Dict[str, float]:
    """
    Measures the forward pass latency of a model on a batch of texts.
    
    Args:
        model: The model to measure.
        tokenizer: The tokenizer for the model.
        texts: List of input texts.
        device: Device to run inference on ('cpu' or 'cuda').
        warmup_runs: Number of warmup iterations to clear caches.
        measurement_runs: Number of iterations to average for timing.
    
    Returns:
        Dictionary containing total_time, avg_time_per_batch, and avg_time_per_token.
    """
    # Move model to device
    model.to(device)
    model.eval()
    
    # Tokenize inputs once
    inputs = tokenizer(texts, return_tensors="pt", padding=True, truncation=True)
    inputs = {k: v.to(device) for k, v in inputs.items()}
    total_tokens = sum(len(t) for t in inputs["input_ids"])
    
    # Warmup
    with torch.no_grad():
        for _ in range(warmup_runs):
            _ = model(**inputs)
    
    # Measurement
    start_time = time.perf_counter()
    for _ in range(measurement_runs):
        with torch.no_grad():
            _ = model(**inputs)
    end_time = time.perf_counter()
    
    total_time = end_time - start_time
    avg_time_per_batch = total_time / measurement_runs
    avg_time_per_token = (total_time / measurement_runs) / (total_tokens / len(texts))
    
    return {
        "total_time_seconds": total_time,
        "avg_time_per_batch_seconds": avg_time_per_batch,
        "avg_time_per_token_seconds": avg_time_per_token,
        "total_tokens_processed": total_tokens,
        "num_batches": len(texts),
        "measurement_runs": measurement_runs
    }

def check_latency_budget(
    metrics: Dict[str, float],
    max_total_seconds: float = 300.0,
    max_time_per_token_ms: float = 25.0
) -> Dict[str, Any]:
    """
    Checks if the measured latency metrics are within the specified budget.
    
    Args:
        metrics: Dictionary of latency metrics from measure_forward_pass_latency.
        max_total_seconds: Maximum allowed total time in seconds (default 300s).
        max_time_per_token_ms: Maximum allowed time per token in milliseconds (default 25ms).
    
    Returns:
        Dictionary with pass/fail status and details.
    """
    avg_time_per_token_ms = metrics["avg_time_per_token_seconds"] * 1000
    
    within_total_budget = metrics["total_time_seconds"] < max_total_seconds
    within_token_budget = avg_time_per_token_ms < max_time_per_token_ms
    
    return {
        "within_total_budget": within_total_budget,
        "within_token_budget": within_token_budget,
        "max_total_seconds": max_total_seconds,
        "max_time_per_token_ms": max_time_per_token_ms,
        "actual_avg_time_per_token_ms": avg_time_per_token_ms,
        "actual_total_time_seconds": metrics["total_time_seconds"],
        "passed": within_total_budget and within_token_budget
    }

def run_latency_analysis(
    texts: List[str],
    output_path: str,
    device: str = "cpu",
    frequency: float = 40.0,
    use_oscillation: bool = True
) -> Dict[str, Any]:
    """
    Runs a complete latency analysis for the oscillatory model (or baseline).
    
    Args:
        texts: List of input texts for inference.
        output_path: Path to save the latency report JSON.
        device: Device for inference.
        frequency: Relative frequency for oscillation (cycles per sequence).
        use_oscillation: Whether to use the oscillatory model or baseline.
    
    Returns:
        The full latency report dictionary.
    """
    print(f"Loading tokenizer and model...")
    tokenizer = DistilBertTokenizerFast.from_pretrained("distilbert-base-uncased")
    
    if use_oscillation:
        print("Initializing OscillatoryDistilBERTWrapper...")
        # Create base wrapper first
        base_wrapper = load_distilbert_cpu()
        # Inject oscillatory attention
        model = OscillatoryDistilBERTWrapper(base_wrapper.model, frequency=frequency)
        model_wrapper = model
    else:
        print("Initializing standard DistilBERTWrapper...")
        model_wrapper = load_distilbert_cpu()
    
    # Measure latency
    print(f"Measuring forward pass latency (use_oscillation={use_oscillation})...")
    latency_metrics = measure_forward_pass_latency(
        model_wrapper.model,
        tokenizer,
        texts,
        device=device
    )
    
    # Check budget
    budget_check = check_latency_budget(latency_metrics)
    
    # Compile report
    report = {
        "model_type": "OscillatoryDistilBERT" if use_oscillation else "DistilBERTBaseline",
        "frequency_cycles_per_sequence": frequency if use_oscillation else None,
        "device": device,
        "latency_metrics": latency_metrics,
        "budget_check": budget_check,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save report
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"Latency report saved to {output_path}")
    return report

def main():
    """
    Main entry point for the latency monitoring script.
    Loads configuration, runs analysis, and saves results.
    """
    # Define a sample set of texts for the latency test
    # In a real scenario, these might come from a config or dataset
    sample_texts = [
        "The quick brown fox jumps over the lazy dog.",
        "Synchronized oscillations in neural networks are a fascinating topic.",
        "The binding problem relates to how the brain integrates different features.",
        "Gamma band activity is often associated with cognitive binding.",
        "Transformer models use self-attention mechanisms to process sequences."
    ]
    
    # Configuration
    output_path = "data/final/latency_report.json"
    device = "cpu"
    frequency = 40.0  # Cycles per sequence
    
    # Run analysis for the oscillatory model
    print("=== Running Latency Analysis for Oscillatory Model ===")
    report = run_latency_analysis(
        texts=sample_texts,
        output_path=output_path,
        device=device,
        frequency=frequency,
        use_oscillation=True
    )
    
    # Print summary
    print("\n--- Latency Report Summary ---")
    print(f"Model: {report['model_type']}")
    print(f"Total Time: {report['latency_metrics']['total_time_seconds']:.4f} seconds")
    print(f"Avg Time per Batch: {report['latency_metrics']['avg_time_per_batch_seconds']:.4f} seconds")
    print(f"Avg Time per Token: {report['latency_metrics']['avg_time_per_token_seconds']*1000:.4f} ms")
    print(f"Within 300s Total Budget: {report['budget_check']['within_total_budget']}")
    print(f"Within 25ms/Token Budget: {report['budget_check']['within_token_budget']}")
    print(f"Overall Pass: {report['budget_check']['passed']}")

if __name__ == "__main__":
    main()
