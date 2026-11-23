"""
Benchmark script for evaluating CPU feasibility of language models.

This script loads each specified model on CPU, measures peak RAM usage,
and records inference latency for generating a short sequence. The results
are written to a JSON file for downstream documentation (e.g., model_selection.md).

The script deliberately avoids any synthetic fall‑backs: if a model cannot be
loaded or the HuggingFace hub is unreachable, the exception is propagated
and the pipeline aborts, satisfying the project's data‑hygiene policy.
"""

import argparse
import json
import logging
import time
from pathlib import Path
from typing import List, Dict

import psutil
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def get_peak_ram_gb() -> float:
    """
    Return the current process RSS memory usage in gigabytes.
    """
    process = psutil.Process()
    rss_bytes = process.memory_info().rss
    return rss_bytes / (1024 ** 3)

def benchmark_model(model_id: str) -> Dict[str, object]:
    """
    Load a model on CPU, generate a short sequence, and measure RAM & latency.

    Args:
        model_id: HuggingFace model identifier.

    Returns:
        Dictionary with keys:
            - model_id
            - peak_ram_gb
            - avg_latency_s
            - notes (optional, e.g., quantization used)
    """
    logger.info(f"Benchmarking model {model_id}")

    # Load tokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_id, use_fast=True)

    # Load model on CPU.
    # We avoid using `low_cpu_mem_usage` and `device_map` to keep the
    # script free from the `accelerate` dependency.
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        torch_dtype=torch.float32,
        trust_remote_code=True  # Some models require this flag.
    )
    model.to("cpu")
    model.eval()

    # Measure RAM after loading
    ram_after_load = get_peak_ram_gb()
    logger.info(f"RAM after loading {model_id}: {ram_after_load:.2f} GB")

    # Prepare a short dummy input
    prompt = "Hello world."
    input_ids = tokenizer.encode(prompt, return_tensors="pt").to("cpu")

    # Warm‑up run (not timed) to mitigate any lazy initialization overhead
    with torch.no_grad():
        _ = model.generate(
            input_ids,
            max_new_tokens=5,
            do_sample=False,
            temperature=0.0,
            top_k=1,
            pad_token_id=tokenizer.eos_token_id,
        )

    # Timed generation of 10 tokens
    timings: List[float] = []
    num_trials = 5
    for _ in range(num_trials):
        start = time.time()
        with torch.no_grad():
            _ = model.generate(
                input_ids,
                max_new_tokens=10,
                do_sample=False,
                temperature=0.0,
                top_k=1,
                pad_token_id=tokenizer.eos_token_id,
            )
        end = time.time()
        timings.append(end - start)

    avg_latency = sum(timings) / len(timings)
    logger.info(f"Average latency for {model_id} (10 tokens): {avg_latency:.3f} s")

    # Final RAM measurement (should be similar to after load)
    final_ram = get_peak_ram_gb()
    peak_ram = max(ram_after_load, final_ram)

    return {
        "model_id": model_id,
        "peak_ram_gb": round(peak_ram, 2),
        "avg_latency_s": round(avg_latency, 3),
    }

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Benchmark CPU‑only language models for RAM usage and inference latency."
    )
    parser.add_argument(
        "--models",
        nargs="+",
        required=True,
        help="Space‑separated list of HuggingFace model identifiers to benchmark."
    )
    parser.add_argument(
        "--output",
        type=str,
        default="results/model_benchmarks.json",
        help="Path to write the JSON benchmark results."
    )
    args = parser.parse_args()

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    results: List[Dict[str, object]] = []
    for model_id in args.models:
        try:
            result = benchmark_model(model_id)
            results.append(result)
        except Exception as e:
            logger.error(f"Failed to benchmark {model_id}: {e}")
            # Propagate the exception to obey the no‑fallback policy
            raise

    # Write results
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    logger.info(f"Benchmark results written to {output_path}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())