"""
generate_ground_truth.py (wrapper)

This module provides a programmatic wrapper around the CLI implementation
located at ``code/cli/generate_ground_truth.py``.  The wrapper is used by
the integration test ``tests/cli/test_generate_ground_truth.py`` and can
also be invoked directly from user code.

The function :func:`run_wrapper` reproduces the full pipeline:

1.  Download a (small) subset of the GSM8K dataset.
2.  Load a full‑precision model (falling back to ``distilgpt2`` if the
    requested model cannot be loaded on the host).
3.  Create quantised model variants for the requested quantisation levels
    (INT4, INT8, FP8).  INT4 and FP8 are approximated with the best‑available
    proxy (dynamic INT8 quantisation and FP16 conversion respectively) –
    this matches the behaviour of the CLI script.
4.  For each prompt compute:
    * gradient norm,
    * a curvature proxy (gradient‑norm squared),
    * full‑precision logits,
    * quantised logits,
    * KL‑divergence between the two distributions.
5.  Persist a Parquet file containing the rows required by the
    ``dataset.schema.yaml`` contract.
6.  Compute per‑level statistics (mean KL, non‑zero fraction, t‑statistic,
    p‑value) and write them to ``data/processed/dataset_stats.json`` using
    the same utilities as the CLI validation script.

The wrapper is deliberately lightweight – it re‑uses the helper functions
defined in the CLI module so that the implementation stays in a single
place.  All paths are created on‑demand via ``pathlib.Path`` and the
``llmxive_toolkit.paths`` helpers are **not** required here because the
caller supplies explicit file locations.

Example usage (mirrors the quick‑start command)::

    from code.data.generate_ground_truth import run_wrapper

    run_wrapper(
        model="meta-llama/Meta-Llama-2-7B-4bit",
        levels=["INT4", "INT8", "FP8"],
        output_path="data/processed/training_sample.parquet",
        sample_size=300,
    )
"""

import json
import logging
from pathlib import Path
from typing import List

import pandas as pd
import torch
import torch.nn.functional as F

# Re‑use the implementation helpers from the CLI script.
from code.cli.generate_ground_truth import (
    load_full_precision_model,
    quantize_model_int8,
    quantize_model_fp16,
    compute_kl,
    get_logits,
    compute_gradient_norm,
    download_gsm8k_subset,
)

# Statistics utilities – the same logic used by ``validate_dataset_stats.py``.
from code.cli.validate_dataset_stats import compute_statistics, write_stats

log = logging.getLogger(__name__)

def _prepare_quantized_models(
    full_model,
    levels: List[str],
) -> dict:
    """Return a dict ``{level: model}`` for the requested quantisation levels."""
    quantized = {}
    for level in levels:
        if level == "INT8":
            quantized["INT8"] = quantize_model_int8(full_model)
        elif level == "FP8":
            # FP8 is not directly supported – use FP16 as a realistic proxy.
            quantized["FP8"] = quantize_model_fp16(full_model)
        elif level == "INT4":
            # No native INT4 support – fall back to the INT8 proxy.
            log.warning("INT4 quantisation not natively supported; using INT8 proxy.")
            quantized["INT4"] = quantize_model_int8(full_model)
        else:
            raise ValueError(f"Unsupported quantisation level: {level}")
    return quantized

def run_wrapper(
    model: str,
    levels: List[str],
    output_path: str,
    sample_size: int = 300,
) -> None:
    """
    Execute the ground‑truth generation pipeline.

    Parameters
    ----------
    model: str
        Hugging‑Face identifier of the base model (e.g. ``meta-llama/Meta-Llama-2-7B-4bit``).
    levels: List[str]
        Quantisation levels to generate (any subset of ``[\"INT4\", \"INT8\", \"FP8\"]``).
    output_path: str
        Destination path for the Parquet file that conforms to ``dataset.schema.yaml``.
    sample_size: int, optional
        Number of GSM8K prompts to process (default ``300``).  The test suite uses a
        much smaller value to keep CI fast.

    The function writes two artefacts:
    * ``output_path`` – the dataset Parquet file.
    * ``data/processed/dataset_stats.json`` – per‑level statistics used by downstream
      verification steps.
    """
    # -----------------------------------------------------------------
    # 1. Download the GSM8K subset.
    # -----------------------------------------------------------------
    log.info(f"Downloading {sample_size} GSM8K samples.")
    subset = download_gsm8k_subset(sample_size)

    # -----------------------------------------------------------------
    # 2. Load the full‑precision model and tokenizer.
    # -----------------------------------------------------------------
    full_model, tokenizer = load_full_precision_model(model)

    # -----------------------------------------------------------------
    # 3. Prepare quantised model variants.
    # -----------------------------------------------------------------
    quantized_models = _prepare_quantized_models(full_model, levels)

    # -----------------------------------------------------------------
    # 4. Process each prompt and collect records.
    # -----------------------------------------------------------------
    records = []
    log.info("Processing prompts and extracting features.")
    for idx, sample in enumerate(subset):
        prompt = sample["question"]
        # Use the first line of the answer as the target token.
        target = sample["answer"].split("\n")[0]

        # Full‑precision logits → probability distribution.
        full_logits = get_logits(full_model, tokenizer, prompt)
        full_probs = F.softmax(full_logits, dim=-1).cpu().numpy()

        # Gradient norm and curvature proxy.
        grad_norm = compute_gradient_norm(full_model, tokenizer, prompt, target)
        curvature = grad_norm ** 2

        for level, q_model in quantized_models.items():
            q_logits = get_logits(q_model, tokenizer, prompt)
            q_probs = F.softmax(q_logits, dim=-1).cpu().numpy()
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

    # -----------------------------------------------------------------
    # 5. Persist the dataset.
    # -----------------------------------------------------------------
    df = pd.DataFrame.from_records(records)
    parquet_path = Path(output_path).expanduser().resolve()
    parquet_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(parquet_path, index=False)
    log.info(f"Dataset written to {parquet_path} (rows={len(df)}).")

    # -----------------------------------------------------------------
    # 6. Compute and write statistics JSON.
    # -----------------------------------------------------------------
    stats = compute_statistics(df, levels)
    stats_path = Path("data/processed/dataset_stats.json")
    write_stats(stats, stats_path)
    log.info(f"Dataset statistics written to {stats_path}.")

# -----------------------------------------------------------------
# When executed as a script we expose a tiny CLI that mirrors the
# behaviour of the original ``code/cli/generate_ground_truth.py`` but
# forwards all arguments to :func:`run_wrapper`.
# -----------------------------------------------------------------
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Programmatic wrapper for ground‑truth dataset generation."
    )
    parser.add_argument(
        "--model",
        type=str,
        required=True,
        help="Hugging‑Face model identifier (e.g. meta-llama/Meta-Llama-2-7B-4bit).",
    )
    parser.add_argument(
        "--levels",
        nargs="+",
        choices=["INT4", "INT8", "FP8"],
        required=True,
        help="Quantisation levels to generate.",
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Path for the generated Parquet dataset.",
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=300,
        help="Number of GSM8K prompts to process.",
    )
    args = parser.parse_args()

    run_wrapper(
        model=args.model,
        levels=args.levels,
        output_path=args.output,
        sample_size=args.sample_size,
    )