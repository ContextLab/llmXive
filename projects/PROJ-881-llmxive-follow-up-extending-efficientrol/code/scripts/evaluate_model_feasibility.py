"""
Script to evaluate model feasibility for CPU inference.
This script benchmarks Qwen1.5-1.5B, Qwen1.5-7B-Int4, and Qwen1.5-0.5B
to determine the optimal choice based on RAM usage and inference speed.
"""
import json
import os
import sys
import time
import psutil
import torch
from pathlib import Path
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
RESULTS_DIR = PROJECT_ROOT / "results"
RESULTS_DIR.mkdir(exist_ok=True)

MODEL_CANDIDATES = {
    "qwen1.5-1.5b": "Qwen/Qwen1.5-1.5B",
    "qwen1.5-7b-int4": "Qwen/Qwen1.5-7B-Int4",
    "qwen1.5-0.5b": "Qwen/Qwen1.5-0.5B"
}

def get_peak_ram_gb():
    """Get current peak RAM usage in GB."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 ** 3)

def benchmark_model(model_id, model_name):
    """Load model and benchmark inference speed and RAM usage."""
    print(f"\n--- Benchmarking {model_name} ({model_id}) ---")
    try:
        # Quantization config for Int4 models
        quantization_config = None
        if "int4" in model_id.lower():
            quantization_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.float16
            )

        # Load tokenizer and model
        print(f"Loading tokenizer for {model_id}...")
        tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
        
        print(f"Loading model {model_id}...")
        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            trust_remote_code=True,
            quantization_config=quantization_config,
            torch_dtype=torch.float16 if quantization_config else torch.float32,
            device_map="auto" if torch.cuda.is_available() else "cpu"
        )

        # Warmup
        dummy_input = tokenizer("Hello", return_tensors="pt")
        if not torch.cuda.is_available():
            dummy_input = {k: v.to(model.device) for k, v in dummy_input.items()}
        
        with torch.no_grad():
            model(**dummy_input)

        # Benchmark inference
        print("Running inference benchmark (512 tokens)...")
        start_ram = get_peak_ram_gb()
        start_time = time.time()
        
        # Generate a fixed length sequence
        input_text = "The quick brown fox"
        inputs = tokenizer(input_text, return_tensors="pt")
        if not torch.cuda.is_available():
            inputs = {k: v.to(model.device) for k, v in inputs.items()}
        
        output = model.generate(
            **inputs,
            max_new_tokens=512,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id
        )
        
        end_time = time.time()
        end_ram = get_peak_ram_gb()

        tokens_generated = len(output[0]) - len(inputs["input_ids"][0])
        speed = tokens_generated / (end_time - start_time)
        peak_ram = end_ram

        print(f"  Speed: {speed:.2f} TPS")
        print(f"  Peak RAM: {peak_ram:.2f} GB")

        return {
            "model_id": model_id,
            "model_name": model_name,
            "speed_tps": round(speed, 2),
            "peak_ram_gb": round(peak_ram, 2),
            "feasible": peak_ram < 7.0
        }

    except Exception as e:
        print(f"  ERROR: {str(e)}")
        return {
            "model_id": model_id,
            "model_name": model_name,
            "error": str(e),
            "feasible": False
        }

def main():
    print("Starting Model Feasibility Evaluation...")
    results = []
    
    for model_id, model_name in MODEL_CANDIDATES.items():
        result = benchmark_model(model_id, model_name)
        results.append(result)
        
        # Save intermediate results
        report_path = RESULTS_DIR / "model_feasibility_report.json"
        with open(report_path, "w") as f:
            json.dump({"results": results, "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")}, f, indent=2)

    # Summary
    print("\n--- Summary ---")
    feasible_models = [r for r in results if r.get("feasible", False)]
    if feasible_models:
        # Prefer 1.5B, then 7B-Int4, then 0.5B
        priority = ["qwen1.5-1.5b", "qwen1.5-7b-int4", "qwen1.5-0.5b"]
        for p in priority:
            for r in feasible_models:
                if r["model_id"] == p:
                    print(f"Recommended: {r['model_name']} ({r['peak_ram_gb']} GB, {r['speed_tps']} TPS)")
                    break
    else:
        print("No feasible models found.")

    print(f"\nReport saved to: {RESULTS_DIR / 'model_feasibility_report.json'}")

if __name__ == "__main__":
    main()