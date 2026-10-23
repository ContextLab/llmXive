"""
Feasibility gate script.

This script loads a small GGUF model using ``llama_cpp``, runs a short
generation prompt five times, measures the average tokens‑per‑second
(TPS) throughput, and writes a JSON log to ``data/feasibility_log.json``.
If the model runs out of memory or the measured throughput is below
2 TPS, the decision is set to ``gpu_offload``; otherwise it is ``proceed``.
The ``adjusted_N`` field is reserved for future use and is set to ``null``.
"""

import json
import time
from pathlib import Path

from llmxive_toolkit import paths, get_logger
from huggingface_hub import hf_hub_download
from llama_cpp import Llama

logger = get_logger(__name__)

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
# Name of a small GGUF model on the Hugging Face Hub.  The chosen model
# (Qwen2‑0.5B‑Instruct) is ~500 MiB and fits comfortably within the
# 7 GiB RAM limit of the free‑tier CI runner.
_HF_REPO_ID = "Qwen/Qwen2-0.5B-Instruct-GGUF"
_HF_FILENAME = "qwen2-0.5b-instruct-q5_k.gguf"

def _ensure_model_path() -> Path:
    """
    Ensure that a GGUF model file is present locally.

    The function first checks the ``MODEL_PATH`` attribute of the
    project configuration.  If that attribute is missing or the file does
    not exist, it falls back to downloading a known small model from
    Hugging Face Hub into the project's ``data`` directory and returns
    that path.
    """
    # Try to read a custom path from config, if it exists.
    try:
        from code.config import config
        model_path = Path(getattr(config, "MODEL_PATH", ""))
    except Exception:
        model_path = Path()

    if model_path.is_file():
        logger.info(f"Using model path from config: {model_path}")
        return model_path

    # Download the fallback model into the data directory.
    download_dir = paths.data("models")
    download_dir.mkdir(parents=True, exist_ok=True)
    logger.info(
        f"Downloading fallback GGUF model {_HF_REPO_ID}/{_HF_FILENAME} ..."
    )
    local_file = hf_hub_download(
        repo_id=_HF_REPO_ID,
        filename=_HF_FILENAME,
        cache_dir=str(download_dir),
        force_download=False,
    )
    logger.info(f"Model downloaded to {local_file}")
    return Path(local_file)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _load_model(model_path: Path) -> Llama:
    """
    Load a GGUF model with ``llama_cpp`` in CPU‑only mode.

    Parameters
    ----------
    model_path: Path
        Path to the GGUF model file.

    Returns
    -------
    Llama
        An instance of the loaded model.
    """
    logger.info(f"Loading GGUF model from {model_path}")
    # ``n_ctx`` is modest because we only need a few tokens.
    return Llama(
        model_path=str(model_path),
        n_ctx=512,
        n_threads=0,          # 0 → auto‑detect logical CPUs
        n_gpu_layers=0,       # CPU‑only
    )

def _run_sample(model: Llama, prompt: str, num_tokens: int = 10) -> float:
    """
    Generate ``num_tokens`` tokens from ``prompt`` and return the TPS.

    Parameters
    ----------
    model: Llama
        Loaded model instance.
    prompt: str
        Prompt string (should be short; we only care about timing).
    num_tokens: int, default 10
        Number of tokens to generate.

    Returns
    -------
    float
        Tokens‑per‑second for this single run.
    """
    logger.debug(f"Running sample generation ({num_tokens} tokens).")
    start = time.time()
    # ``max_tokens`` limits the generation length.
    # ``temperature=0.0`` makes the output deterministic.
    _ = model(
        prompt,
        max_tokens=num_tokens,
        temperature=0.0,
        stream=False,
    )
    elapsed = time.time() - start
    tps = num_tokens / elapsed if elapsed > 0 else float("inf")
    logger.debug(f"Sample completed in {elapsed:.4f}s → {tps:.2f} TPS")
    return tps

def measure_throughput(model_path: Path, num_tokens: int = 10, runs: int = 5) -> float:
    """
    Load the model and compute the average tokens‑per‑second over ``runs``.

    Parameters
    ----------
    model_path: Path
        Path to the GGUF model.
    num_tokens: int, default 10
        Number of tokens to request per generation.
    runs: int, default 5
        How many times to repeat the measurement.

    Returns
    -------
    float
        Average tokens‑per‑second across all runs.
    """
    model = _load_model(model_path)

    prompt = "Explain the steps to sort a list."
    tps_values = []
    for i in range(runs):
        logger.info(f"Running throughput measurement {i + 1}/{runs}")
        tps = _run_sample(model, prompt, num_tokens=num_tokens)
        tps_values.append(tps)

    average_tps = sum(tps_values) / len(tps_values)
    logger.info(f"Average throughput: {average_tps:.2f} TPS")
    return average_tps

def run_feasibility_gate() -> dict:
    """
    Execute the feasibility gate and write the JSON log.

    Returns
    -------
    dict
        The JSON payload that was written to disk.
    """
    model_path = _ensure_model_path()
    if not model_path.is_file():
        raise FileNotFoundError(f"Model file not found at {model_path}")

    try:
        avg_tps = measure_throughput(model_path)
    except Exception as exc:
        # Any exception (including OOM) forces the GPU‑offload decision.
        logger.warning(f"Feasibility measurement failed: {exc}")
        decision = "gpu_offload"
        avg_tps = None
    else:
        decision = "proceed" if avg_tps >= 2.0 else "gpu_offload"

    result = {
        "throughput_tps": avg_tps if avg_tps is not None else None,
        "decision": decision,
        "adjusted_N": None,   # Reserved for future use.
    }

    # Write the JSON file to ``data/feasibility_log.json``.
    output_path = paths.data("feasibility_log.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as fp:
        json.dump(result, fp, indent=2)

    logger.info(f"Wrote feasibility log to {output_path}")
    return result

if __name__ == "__main__":
    # When executed as a script, run the gate and exit with status 0.
    run_feasibility_gate()
