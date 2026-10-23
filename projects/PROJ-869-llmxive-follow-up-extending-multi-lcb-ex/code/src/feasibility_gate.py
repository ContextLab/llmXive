"""
Feasibility gate script.

This script loads a small GGUF model using `llama_cpp`, runs a short
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

# Import the project configuration.  The config module is expected to
# expose a ``MODEL_PATH`` attribute that points to a GGUF model file.
try:
    from code.config import config
except ImportError as exc:
    raise ImportError(
        "Project configuration module `code.config` could not be imported. "
        "Make sure it defines a `MODEL_PATH` attribute."
    ) from exc

# ``llama_cpp`` is the official Python binding for GGUF models.
# It is listed in ``requirements.txt``.
from llama_cpp import Llama

logger = get_logger(__name__)

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
    # ``n_ctx`` is set to a modest value because we only need a few tokens.
    # ``n_threads`` defaults to the number of logical CPUs.
    return Llama(
        model_path=str(model_path),
        n_ctx=512,
        n_threads=0,          # 0 → auto‑detect
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
    output = model(
        prompt,
        max_tokens=num_tokens,
        temperature=0.0,
        stream=False,
    )
    elapsed = time.time() - start
    # ``output`` contains a ``choices`` list with generated text.
    # The exact token count is ``num_tokens`` (the request), which we
    # use for the TPS calculation.
    tps = num_tokens / elapsed if elapsed > 0 else float("inf")
    logger.debug(f"Sample completed in {elapsed:.4f}s → {tps:.2f} TPS")
    # Prevent unused‑variable warnings.
    _ = output
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
    try:
        model = _load_model(model_path)
    except RuntimeError as exc:
        # ``llama_cpp`` raises a ``RuntimeError`` on OOM.
        logger.error("Failed to load model – likely OOM.")
        raise exc

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
    # Resolve the model path from the project configuration.
    model_path = Path(config.MODEL_PATH)
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
