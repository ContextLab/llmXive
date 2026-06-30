"""
Main script to run benchmark suite on multiple datasets with different quantizers.
Implements FR-007 by including KV-cache size reduction metrics in results.
"""
import json
import os
import argparse
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.inference.engine import create_quantized_generator
from src.benchmarks.evaluator import evaluate_multiple_benchmarks
from src.benchmarks.loader import load_dataset_by_name

def load_model_and_tokenizer(model_name: str):
    """
    Load model and tokenizer.
    
    Args:
        model_name: Name of the model to load
    
    Returns:
        Tuple of (model, tokenizer)
    """
    from transformers import AutoModelForCausalLM, AutoTokenizer
    import torch
    
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float16,
        device_map="auto" if torch.cuda.is_available() else "cpu"
    )
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    return model, tokenizer

def run_benchmark_suite(
    model_name: str,
    datasets: List[str],
    quantizer_types: List[str],
    output_dir: str = "data/processed"
) -> List[Dict[str, Any]]:
    """
    Run benchmark suite across datasets and quantizers.
    
    Args:
        model_name: Name of the model to use
        datasets: List of dataset names to evaluate
        quantizer_types: List of quantizer types to test
        output_dir: Directory to save results
    
    Returns:
        List of result dictionaries
    """
    results = []
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    for quantizer_type in quantizer_types:
        print(f"\n{'='*60}")
        print(f"Running benchmarks with {quantizer_type} quantizer")
        print(f"{'='*60}")
        
        # Create generator with size tracking enabled (FR-007)
        generator = create_quantized_generator(
            model_name=model_name,
            quantizer_type=quantizer_type,
            log_mse=True,
            track_size=True  # Enable FR-007 tracking
        )
        
        for dataset_name in datasets:
            print(f"\nEvaluating on {dataset_name}...")
            
            # Load dataset
            dataset = load_dataset_by_name(dataset_name)
            
            # Evaluate
            eval_results = evaluate_multiple_benchmarks(
                generator=generator,
                dataset=dataset,
                dataset_name=dataset_name
            )
            
            # Process results
            for item in eval_results:
                result_entry = {
                    "dataset": dataset_name,
                    "quantizer_type": quantizer_type,
                    "prompt": item.get("prompt", ""),
                    "generated_text": item.get("generated_text", ""),
                    "expected": item.get("expected", ""),
                    "correct": item.get("correct", False),
                    "input_length": item.get("input_length", 0),
                    "output_length": item.get("output_length", 0),
                }
                
                # Add KV-cache size reduction metrics (FR-007)
                if "kv_cache_reduction_percentage" in item:
                    result_entry["kv_cache_reduction_percentage"] = item["kv_cache_reduction_percentage"]
                if "kv_cache_original_bytes" in item:
                    result_entry["kv_cache_original_bytes"] = item["kv_cache_original_bytes"]
                if "kv_cache_quantized_bytes" in item:
                    result_entry["kv_cache_quantized_bytes"] = item["kv_cache_quantized_bytes"]
                
                # Add MSE summary if available
                if "mse_summary" in item:
                    result_entry["mse_summary"] = item["mse_summary"]
                
                results.append(result_entry)
                
                # Print summary for this item
                status = "✓" if item.get("correct", False) else "✗"
                print(f"  {status} {dataset_name[:20]:<20} | Acc: {item.get('correct', False)}")
                
                # Print size reduction if available (FR-007)
                if "kv_cache_reduction_percentage" in item:
                    reduction = item["kv_cache_reduction_percentage"]
                    print(f"      KV-cache reduction: {reduction:.2f}%")
        
        # Save intermediate results
        results_path = os.path.join(output_dir, f"benchmark_results_{quantizer_type}.jsonl")
        save_results(results, results_path)
        print(f"\nResults saved to {results_path}")
    
    return results

def save_results(results: List[Dict[str, Any]], output_path: str):
    """
    Save results to a JSONL file.
    
    Args:
        results: List of result dictionaries
        output_path: Path to output file
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        for result in results:
            f.write(json.dumps(result, ensure_ascii=False) + '\n')

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run benchmark suite with quantization")
    parser.add_argument("--model", type=str, default="microsoft/phi-2", help="Model name")
    parser.add_argument("--datasets", type=str, nargs="+", default=["math_dataset"], 
                      help="Datasets to evaluate")
    parser.add_argument("--quantizers", type=str, nargs="+", default=["uniform", "kvarn"],
                      help="Quantizer types to test")
    parser.add_argument("--output-dir", type=str, default="data/processed",
                      help="Output directory for results")
    
    args = parser.parse_args()
    
    print(f"Starting benchmark suite...")
    print(f"Model: {args.model}")
    print(f"Datasets: {args.datasets}")
    print(f"Quantizers: {args.quantizers}")
    
    results = run_benchmark_suite(
        model_name=args.model,
        datasets=args.datasets,
        quantizer_types=args.quantizers,
        output_dir=args.output_dir
    )
    
    # Save final combined results
    final_path = os.path.join(args.output_dir, "benchmark_results.jsonl")
    save_results(results, final_path)
    print(f"\nFinal results saved to {final_path}")
    
    # Print summary
    print(f"\n{'='*60}")
    print("BENCHMARK SUMMARY")
    print(f"{'='*60}")
    
    # Calculate accuracy per dataset/quantizer
    summary = {}
    for r in results:
        key = (r["dataset"], r["quantizer_type"])
        if key not in summary:
            summary[key] = {"total": 0, "correct": 0}
        summary[key]["total"] += 1
        if r.get("correct", False):
            summary[key]["correct"] += 1
    
    for (dataset, quantizer), stats in summary.items():
        acc = stats["correct"] / stats["total"] * 100 if stats["total"] > 0 else 0
        print(f"{dataset:<15} | {quantizer:<8} | Acc: {acc:.2f}% ({stats['correct']}/{stats['total']})")
        # Print size reduction if available
        for r in results:
            if r["dataset"] == dataset and r["quantizer_type"] == quantizer:
                if "kv_cache_reduction_percentage" in r:
                    print(f"                  |          | KV-cache reduction: {r['kv_cache_reduction_percentage']:.2f}%")
                    break

if __name__ == "__main__":
    main()