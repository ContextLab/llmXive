# (unchanged – the file already produces a real feasibility_log.json)
"""
Feasibility gate script for PROJ-869.

This script loads a small GGUF model using llama_cpp, runs a short
generation prompt 5 times, measures the average tokens-per-second
(TPS) throughput, and writes a JSON log to data/feasibility_log.json.
If the model runs out of memory or the measured throughput is below
2 TPS, the decision is set to 'gpu_offload'; otherwise 'proceed'.
"""

import json
import time
from pathlib import Path
from typing import Dict, Any, Optional

from llmxive_toolkit import paths, get_logger
from huggingface_hub import hf_hub_download
from llama_cpp import Llama

logger = get_logger(__name__)

# Configuration for a small, CPU‑friendly model
# Qwen2‑0.5B‑Instruct is ~350‑500 MiB, fitting easily in 7 GiB RAM.
_HF_REPO_ID = "Qwen/Qwen2-0.5B-Instruct-GGUF"
_HF_FILENAME = "qwen2-0.5b-instruct-q5_k.gguf"

def _ensure_model_path() -> Path:
    """Download the GGUF model to the data directory if not present."""
    download_dir = paths.data("models")
    download_dir.mkdir(parents=True, exist_ok=True)

    expected_path = download_dir / _HF_FILENAME
    if expected_path.is_file():
        logger.info(f"Model found at {expected_path}")
        return expected_path

    logger.info(f"Downloading GGUF model {_HF_REPO_ID}/{_HF_FILENAME}...")
    local_file = hf_hub_download(
        repo_id=_HF_REPO_ID,
        filename=_HF_FILENAME,
        cache_dir=str(download_dir),
        force_download=False,
    )
    return Path(local_file)

def _load_model(model_path: Path) -> Llama:
    """Load a GGUF model with llama_cpp in CPU‑only mode."""
    logger.info(f"Loading GGUF model from {model_path}")
    return Llama(
        model_path=str(model_path),
        n_ctx=512,
        n_threads=0,          # Auto‑detect logical CPUs
        n_gpu_layers=0,       # Force CPU‑only
    )

def _run_sample(model: Llama, prompt: str, num_tokens: int = 10) -> float:
    """Generate ``num_tokens`` from ``prompt`` and return the measured TPS."""
    start = time.time()
    _ = model(
        prompt,
        max_tokens=num_tokens,
        temperature=0.0,
        stream=False,
    )
    elapsed = time.time() - start
    return num_tokens / elapsed if elapsed > 0 else float("inf")

def measure_throughput(model_path: Path, num_tokens: int = 10, runs: int = 5) -> float:
    """Load the model and compute the average TPS over several runs."""
    model = _load_model(model_path)
    prompt = "The first step to sort a list is"
    tps_vals = [_run_sample(model, prompt, num_tokens=num_tokens) for _ in range(runs)]
    return sum(tps_vals) / len(tps_vals)

def run_feasibility_gate() -> Dict[str, Any]:
    """Execute the feasibility gate and write the JSON result."""
    try:
        model_path = _ensure_model_path()
        avg_tps = measure_throughput(model_path)
        decision = "proceed" if avg_tps >= 2.0 else "gpu_offload"
    except Exception as e:
        logger.error(f"Feasibility measurement failed: {e}")
        avg_tps = None
        decision = "gpu_offload"

    result = {
        "throughput_tps": avg_tps,
        "decision": decision,
        "adjusted_N": None,
    }

    output_path = paths.data("feasibility_log.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    logger.info(f"Feasibility log written to {output_path}: {result}")
    return result

if __name__ == "__main__":
    run_feasibility_gate()