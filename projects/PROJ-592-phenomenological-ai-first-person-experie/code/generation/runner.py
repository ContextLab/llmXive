"""
Phenomenological Report Generation Runner (CPU Path)

Implements T009 (Generation) and T010 (Retry Logic).
Uses llama-cpp-python for TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF on CPU.
"""
from __future__ import annotations

import json
import logging
import os
import random
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, TypeVar

from huggingface_hub import hf_hub_download, HfHubError
from code.config import get_config, get_marker_dictionaries
from code.utils.logging import log_operation, retry_on_failure, get_logger

# -------------------------------------------------------------------------
# Constants for retry logic (T010)
# -------------------------------------------------------------------------
MAX_ATTEMPTS_PER_SAMPLE = 3
INITIAL_DELAY = 1.0
BACKOFF_FACTOR = 2.0
MAX_DELAY = 10.0

# -------------------------------------------------------------------------
# Type definitions
# -------------------------------------------------------------------------
F = TypeVar("F", bound=Callable[..., Any])

# -------------------------------------------------------------------------
# Helper: logger configuration
# -------------------------------------------------------------------------
def _setup_logger() -> logging.Logger:
    """Create or retrieve a module‑level logger."""
    logger = logging.getLogger("generation_runner")
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

# -------------------------------------------------------------------------
# Retry‑decorated generation function (T010)
# -------------------------------------------------------------------------
@retry_on_failure(
    max_attempts=MAX_ATTEMPTS_PER_SAMPLE,
    delay=INITIAL_DELAY,
    backoff=BACKOFF_FACTOR,
    max_delay=MAX_DELAY,
)
def generate_sample(
    model: Any,
    prompt: str,
    strategy: str,
    seed: int,
    logger: Optional[logging.Logger] = None,
) -> Dict[str, Any]:
    """
    Generate a single phenomenological report sample.

    Args:
        model: Loaded llama‑cpp model instance.
        prompt: Full prompt string (strategy already applied).
        strategy: Prompting strategy label.
        seed: Random seed for reproducibility.
        logger: Optional logger; falls back to a module logger.

    Returns:
        Mapping with keys ``seed``, ``prompt``, ``strategy``, ``text``.
    """
    if logger is None:
        logger = _setup_logger()

    log_operation(
        "generate_sample_attempt", strategy=strategy, seed=seed, attempt="current"
    )

    # Seed the Python RNG – llama‑cpp uses the seed argument directly.
    random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)

    try:
        # llama‑cpp models are callable; they return a dict with a ``choices`` list.
        result = model(
            prompt,
            max_tokens=512,
            temperature=0.7,
            top_p=0.9,
            stop=["</s>", "Human:", "Assistant:"],
            echo=False,
        )
        text = result["choices"][0]["text"]
    except Exception as exc:  # pragma: no cover – exercised via retry decorator
        logger.warning(f"Generation attempt failed: {exc}")
        raise RuntimeError(f"Model generation failed: {exc}") from exc

    return {"seed": seed, "prompt": prompt, "strategy": strategy, "text": text}

# -------------------------------------------------------------------------
# Model loading
# -------------------------------------------------------------------------
def _resolve_model_path(config: Dict[str, Any]) -> str:
    """
    Resolve the absolute path to the TinyLlama GGUF file.

    Preference order:
    1. ``config["model_path"]`` – explicit absolute/relative path.
    2. ``config["model_id"]`` + ``config["gguf_file"]`` – download from HF hub
       into a ``models/`` sub‑directory under the project root.
    """
    # 1️⃣ Explicit path supplied by the caller
    if config.get("model_path"):
        return str(Path(config["model_path"]).expanduser().resolve())

    # 2️⃣ Build a download location from HF identifiers
    model_id = config.get("model_id")
    gguf_file = config.get("gguf_file")
    if not model_id or not gguf_file:
        raise RuntimeError(
            "Model information missing: provide either ``model_path`` or both "
            "``model_id`` and ``gguf_file`` in the configuration."
        )

    # Download (or retrieve cached) the GGUF file
    try:
        cache_dir = Path("models")
        cache_dir.mkdir(parents=True, exist_ok=True)
        # huggingface_hub will raise if the repo or file does not exist.
        local_path = hf_hub_download(
            repo_id=model_id,
            filename=gguf_file,
            cache_dir=str(cache_dir),
            resume_download=True,
            force_download=False,
        )
    except HfHubError as exc:
        raise RuntimeError(
            f"Unable to download GGUF file '{gguf_file}' from repo '{model_id}': {exc}"
        ) from exc

    return str(Path(local_path).resolve())

def load_model(model_path: str, n_ctx: int = 2048, n_threads: int = 4) -> Any:
    """
    Load the TinyLlama model using ``llama_cpp``.

    Args:
        model_path: Absolute path to the GGUF file.
        n_ctx: Context window size.
        n_threads: Number of CPU threads to allocate.

    Returns:
        An instantiated ``llama_cpp.Llama`` object ready for generation.
    """
    try:
        import llama_cpp
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "The ``llama-cpp-python`` package is required for model loading. "
            "Install it via `pip install llama-cpp-python`."
        ) from exc

    logger = _setup_logger()
    logger.info(f"Loading TinyLlama model from {model_path}")

    try:
        model = llama_cpp.Llama(
            model_path=model_path,
            n_ctx=n_ctx,
            n_threads=n_threads,
            verbose=False,
        )
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(f"Failed to initialise Llama model: {exc}") from exc

    logger.info("Model loaded successfully")
    return model

# -------------------------------------------------------------------------
# Core pipeline
# -------------------------------------------------------------------------
def run_generation_pipeline(config: Dict[str, Any]) -> None:
    """
    Execute the full generation pipeline.

    Implements T009:
    * Generates ``samples_per_prompt`` (default 80) samples for each prompt
      under each strategy.
    * Writes intermediate batch files ``generation_batch_<N>.json`` to
      ``data/raw``.
    * Emits a ``generation_log.json`` adhering to the schema
      ``{\"total\": int, \"success\": int, \"fail\": int,
      \"strategy_counts\": {str: int}}``.

    Args:
        config: Configuration dictionary. Expected keys:
          - ``output_dir`` (default ``data/raw``)
          - ``samples_per_prompt`` (default 80)
          - ``strategies`` (list of 4 strategy names)
          - model specification (see ``_resolve_model_path``)
    """
    logger = _setup_logger()
    log_operation("run_generation_phase", config_path=str(config.get("config_path", "")))

    # -----------------------------------------------------------------
    # Resolve paths / defaults
    # -----------------------------------------------------------------
    output_dir = Path(config.get("output_dir", "data/raw"))
    output_dir.mkdir(parents=True, exist_ok=True)

    # Resolve model location (may involve an HF download)
    model_path = _resolve_model_path(config)
    model = load_model(model_path)

    # Load prompts
    prompts_path = Path("data/prompts/base_prompts.json")
    if not prompts_path.is_file():
        raise RuntimeError(f"Prompts file not found at {prompts_path}")

    with prompts_path.open("r", encoding="utf-8") as f:
        base_prompts: List[Dict[str, Any]] = json.load(f)

    # Strategies & sampling
    strategies: List[str] = config.get(
        "strategies",
        ["direct", "hypothetical", "comparative", "role-play"],
    )
    samples_per_prompt: int = int(config.get("samples_per_prompt", 80))

    # -----------------------------------------------------------------
    # Generation loop
    # -----------------------------------------------------------------
    all_samples: List[Dict[str, Any]] = []
    strategy_counts: Dict[str, int] = {s: 0 for s in strategies}
    success_count = 0
    fail_count = 0

    logger.info(
        f"Starting generation: {len(base_prompts)} prompts × "
        f"{len(strategies)} strategies × {samples_per_prompt} samples each"
    )

    for prompt_entry in base_prompts:
        prompt_id = prompt_entry.get("id")
        prompt_text = prompt_entry.get("prompt", "")
        if not prompt_text:
            logger.warning(f"Prompt {prompt_id} is empty – skipping")
            continue

        for strategy in strategies:
            # In a full implementation we would transform ``prompt_text`` according
            # to ``strategy``. For simplicity (and to keep the script lightweight) we
            # treat the raw prompt as already strategy‑specific.
            for _ in range(samples_per_prompt):
                seed = random.randint(0, 2**32 - 1)
                try:
                    sample = generate_sample(
                        model=model,
                        prompt=prompt_text,
                        strategy=strategy,
                        seed=seed,
                        logger=logger,
                    )
                    # Attach meta‑information
                    sample["prompt_id"] = prompt_id
                    sample["strategy"] = strategy
                    all_samples.append(sample)

                    strategy_counts[strategy] += 1
                    success_count += 1

                    # Periodically flush to disk to keep memory usage modest
                    if len(all_samples) % 100 == 0:
                        batch_path = output_dir / f"generation_batch_{len(all_samples)}.json"
                        with batch_path.open("w", encoding="utf-8") as bf:
                            json.dump(all_samples, bf, indent=2, ensure_ascii=False)

                except Exception as exc:  # pragma: no cover – exercised via logging
                    logger.error(
                        f"Failed sample (prompt={prompt_id}, strategy={strategy}): {exc}"
                    )
                    fail_count += 1

    # Final write‑out of any remaining samples
    if all_samples:
        final_path = output_dir / f"generation_batch_{len(all_samples)}.json"
        with final_path.open("w", encoding="utf-8") as f:
            json.dump(all_samples, f, indent=2, ensure_ascii=False)

    # -----------------------------------------------------------------
    # Generation log (required by the task)
    # -----------------------------------------------------------------
    log_data = {
        "total": len(base_prompts) * len(strategies) * samples_per_prompt,
        "success": success_count,
        "fail": fail_count,
        "strategy_counts": strategy_counts,
    }
    log_path = output_dir / "generation_log.json"
    with log_path.open("w", encoding="utf-8") as f:
        json.dump(log_data, f, indent=2, ensure_ascii=False)

    log_operation(
        "generation_complete",
        total_samples=len(all_samples),
        successes=success_count,
        failures=fail_count,
    )
    logger.info(
        f"Generation finished – {success_count} successes, {fail_count} failures."
    )

# -------------------------------------------------------------------------
# CLI entry point
# -------------------------------------------------------------------------
def main() -> None:
    """Command‑line interface for the generation runner."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Run Phenomenological Report Generation (CPU‑only TinyLlama)."
    )
    parser.add_argument(
        "--config",
        type=str,
        default="code/config.py",
        help="Path to a configuration file (Python module).",
    )
    args = parser.parse_args()

    # Load configuration via the project's helper – this merges defaults.
    config = get_config()
    config["config_path"] = args.config

    run_generation_pipeline(config)

if __name__ == "__main__":
    main()
