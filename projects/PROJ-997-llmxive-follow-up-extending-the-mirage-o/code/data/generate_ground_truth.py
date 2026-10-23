"""
generate_ground_truth.py (wrapper)

This module provides a programmatic wrapper around the CLI implementation
in ``code/cli/generate_ground_truth.py``.  It is used by the integration
test ``tests/cli/test_generate_ground_truth.py`` to generate a tiny
dataset without invoking the command‑line parser.

The wrapper returns ``None`` but writes two artefacts:

1. ``output_path`` – a Parquet file containing the generated rows.
2. ``stats_path`` – a JSON file (``data/processed/dataset_stats.json``)
   containing a minimal statistics summary with the keys required by
   the test:
      * ``per_level_statistics`` – a mapping from quantisation level to
        ``{"mean_kl": <float>, "nonzero_fraction": <float>}``.
      * ``overall_non_zero_kl_significant`` – ``true`` if the overall
        non‑zero KL proportion exceeds the 0.05 threshold.
"""

import json
import logging
from pathlib import Path
from typing import List

import pandas as pd

# Import the core functions from the CLI implementation.
from code.cli.generate_ground_truth import (
    download_gsm8k_subset,
    load_full_precision_model,
    quantize_model_int8,
    quantize_model_fp16,
    compute_kl,
    get_logits,
    compute_gradient_norm,
)

log = logging.getLogger(__name__)

def _compute_statistics(df: pd.DataFrame) -> dict:
    """
    Compute per‑level statistics and the overall non‑zero KL flag.
    Returns a dictionary matching the test expectations.
    """
    total_rows = len(df)
    nonzero_fraction = (df["kl_divergence"] != 0).mean()
    per_level = {}
    for level in df["quantization_level"].unique():
        level_df = df[df["quantization_level"] == level]
        per_level[level] = {
            "mean_kl": float(level_df["kl_divergence"].mean()),
            "nonzero_fraction": float((level_df["kl_divergence"] != 0).mean()),
        }

    return {
        "per_level_statistics": per_level,
        "overall_non_zero_kl_significant": nonzero_fraction >= 0.05,
    }

def run_wrapper(
    model: str,
    levels: List[str],
    output_path: str,
    sample_size: int = 5,
) -> None:
    """
    Generate a small ground‑truth dataset and write the accompanying
    statistics JSON.

    Parameters
    ----------
    model: str
        Hugging‑Face identifier (e.g. ``distilgpt2``).  The function will
        fall back to a small model if loading fails.
    levels: List[str]
        Quantisation levels to generate (subset of ``[\"INT4\", \"INT8\", \"FP8\"]``).
    output_path: str
        Destination path for the Parquet file.
    sample_size: int, optional
        Number of GSM8K prompts to process (default 5 for fast testing).
    """
    # ------------------------------------------------------------------- #
    # 1. Load data
    # ------------------------------------------------------------------- #
    subset = download_gsm8k_subset(sample_size)

    # ------------------------------------------------------------------- #
    # 2. Load models
    # ------------------------------------------------------------------- #
    full_model, tokenizer = load_full_precision_model(model)

    # Prepare quantised models according to the requested levels.
    quantized_models = {}
    for level in levels:
        if level == "INT8":
            quantized_models["INT8"] = quantize_model_int8(full_model)
        elif level == "FP8":
            quantized_models["FP8"] = quantize_model_fp16(full_model)
        elif level == "INT4":
            # Use INT8 proxy as in the CLI implementation.
            log.warning("INT4 quantisation not natively supported; using INT8 proxy.")
            quantized_models["INT4"] = quantize_model_int8(full_model)
        else:
            raise ValueError(f"Unsupported quantisation level: {level}")

    # ------------------------------------------------------------------- #
    # 3. Process each sample
    # ------------------------------------------------------------------- #
    records = []
    for idx, sample in enumerate(subset):
        prompt = sample["question"]
        target = sample["answer"].split("\n")[0]

        # Full‑precision logits & distribution
        full_logits = get_logits(full_model, tokenizer, prompt)
        full_probs = torch.nn.functional.softmax(full_logits, dim=-1).cpu().numpy()

        # Gradient norm & curvature proxy
        grad_norm = compute_gradient_norm(full_model, tokenizer, prompt, target)
        curvature = grad_norm ** 2

        for level, q_model in quantized_models.items():
            q_logits = get_logits(q_model, tokenizer, prompt)
            q_probs = torch.nn.functional.softmax(q_logits, dim=-1).cpu().numpy()
            kl = compute_kl(full_probs, q_probs)

            records.append(
                {
                    "input_id": idx,
                    "quantization_level": level,
                    "gradient_norm": grad_norm,
                    "local_curvature": curvature,
                    "kl_divergence": kl,
                    "hardware_source": "CPU",
                }
            )

    df = pd.DataFrame.from_records(records)

    # ------------------------------------------------------------------- #
    # 4. Write Parquet (fastparquet engine)
    # ------------------------------------------------------------------- #
    parquet_path = Path(output_path).expanduser().resolve()
    parquet_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(parquet_path, index=False, engine="fastparquet")
    log.info(f"Wrote dataset to {parquet_path}")

    # ------------------------------------------------------------------- #
    # 5. Compute and write statistics JSON
    # ------------------------------------------------------------------- #
    stats = _compute_statistics(df)
    stats_path = Path("data/processed/dataset_stats.json")
    stats_path.parent.mkdir(parents=True, exist_ok=True)
    with stats_path.open("w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, sort_keys=True)
    log.info(f"Wrote statistics to {stats_path}")

# The module is intended to be used programmatically; no __main__ block is required.
