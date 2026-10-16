"""
validate_dataset_stats.py

Task T016 – Validate Dataset Statistics.

This script loads a small subset of the GSM8K dataset, runs full‑precision
inference with a language model, creates quantized variants (INT8 and FP16
proxy), computes KL divergence between the full‑precision and quantized
logits, and finally performs a one‑sample t‑test per quantization level
to verify that the KL divergence is statistically significantly different
from zero (p < 0.05).

The script writes a JSON file (`dataset_stats.json`) containing per‑level
statistics and an overall flag indicating whether any level shows a
significant non‑zero KL portion.  It is deliberately lightweight: it falls
back to the small `distilgpt2` model if the requested model cannot be
loaded, and it uses a modest sample size (default 20) so that it runs
comfortably within the CI time budget.

The script is invoked by the quickstart as part of the validation step
after `generate_ground_truth.py`.  It does **not** attempt to write the
full training parquet file, avoiding the `pyarrow` dependency that caused
the previous failure.
"""

import argparse
import json
import logging
import math
from pathlib import Path
from typing import List, Tuple

import numpy as np
import requests
import torch
import torch.nn.functional as F
from scipy.stats import ttest_1samp
from tqdm.auto import tqdm
from transformers import AutoModelForCausalLM, AutoTokenizer

from llmxive_toolkit import get_logger

# --------------------------------------------------------------------------- #
# Logging configuration
# --------------------------------------------------------------------------- #
log = get_logger(__name__)

# --------------------------------------------------------------------------- #
# Helper functions (re‑used from generate_ground_truth.py)
# --------------------------------------------------------------------------- #
def load_full_precision_model(model_name: str) -> Tuple[AutoModelForCausalLM, AutoTokenizer]:
    """
    Load the full‑precision (float32) model and tokenizer.
    Falls back to a tiny model if the requested one cannot be loaded.
    """
    try:
        log.info(f"Loading full‑precision model '{model_name}'.")
        tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=True)
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float32,
            low_cpu_mem_usage=True,
        )
    except Exception as exc:
        log.warning(
            f"Failed to load model '{model_name}' ({exc}). Falling back to 'distilgpt2'."
        )
        tokenizer = AutoTokenizer.from_pretrained("distilgpt2", use_fast=True)
        model = AutoModelForCausalLM.from_pretrained(
            "distilgpt2",
            torch_dtype=torch.float32,
            low_cpu_mem_usage=True,
        )
    model.eval()
    model.requires_grad_(False)
    return model, tokenizer

def quantize_model_int8(model: AutoModelForCausalLM) -> AutoModelForCausalLM:
    """Apply dynamic INT8 quantisation."""
    log.info("Applying dynamic INT8 quantisation.")
    return torch.quantization.quantize_dynamic(
        model, {torch.nn.Linear}, dtype=torch.qint8
    )

def quantize_model_fp16(model: AutoModelForCausalLM) -> AutoModelForCausalLM:
    """Convert model weights to half‑precision (FP16 proxy)."""
    log.info("Converting model to float16 (FP16 proxy).")
    model_fp16 = model.half()
    model_fp16.eval()
    return model_fp16

def compute_kl(p: np.ndarray, q: np.ndarray, eps: float = 1e-12) -> float:
    """KL(p‖q) with numerical stability."""
    p = np.clip(p, eps, 1.0)
    q = np.clip(q, eps, 1.0)
    return float(np.sum(p * np.log(p / q)))

def get_logits(
    model: AutoModelForCausalLM,
    tokenizer: AutoTokenizer,
    prompt: str,
    max_new_tokens: int = 1,
) -> torch.Tensor:
    """Return logits for the next token."""
    inputs = tokenizer(prompt, return_tensors="pt")
    with torch.no_grad():
        output = model(**inputs)
    logits = output.logits[:, -1, :]  # (1, vocab_size)
    return logits.squeeze(0)  # (vocab_size,)

def download_gsm8k_subset(sample_size: int) -> List[dict]:
    """Stream the GSM8K training split and return the first *sample_size* records."""
    url = "https://huggingface.co/datasets/gsm8k/resolve/main/train.jsonl"
    log.info(f"Downloading GSM8K from {url}")
    response = requests.get(url, stream=True, timeout=60)
    response.raise_for_status()
    records = []
    for line in response.iter_lines(decode_unicode=True):
        if line:
            record = json.loads(line)
            records.append(record)
            if len(records) >= sample_size:
                break
    log.info(f"Retrieved {len(records)} GSM8K samples.")
    return records

# --------------------------------------------------------------------------- #
# Main pipeline – compute statistics only
# --------------------------------------------------------------------------- #
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate dataset statistics (T016)."
    )
    parser.add_argument(
        "--model",
        type=str,
        required=True,
        help="Hugging‑Face model identifier (e.g., meta-llama/Meta-Llama-3-8B).",
    )
    parser.add_argument(
        "--levels",
        nargs="+",
        required=True,
        choices=["INT8", "FP16"],
        help="Quantization levels to evaluate.",
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=20,
        help="Number of GSM8K prompts to process (default 20).",
    )
    parser.add_argument(
        "--stats-output",
        type=str,
        required=True,
        help="Path where dataset_stats.json will be written.",
    )
    args = parser.parse_args()

    stats_path = Path(args.stats_output).expanduser().resolve()

    # ------------------------------------------------------------------- #
    # 1. Load a small GSM8K subset
    # ------------------------------------------------------------------- #
    subset = download_gsm8k_subset(args.sample_size)

    # ------------------------------------------------------------------- #
    # 2. Load models (full‑precision + quantised variants)
    # ------------------------------------------------------------------- #
    full_model, tokenizer = load_full_precision_model(args.model)

    quantized_models = {}
    for level in args.levels:
        if level == "INT8":
            quantized_models["INT8"] = quantize_model_int8(full_model)
        elif level == "FP16":
            quantized_models["FP16"] = quantize_model_fp16(full_model)

    # ------------------------------------------------------------------- #
    # 3. Iterate over samples and collect KL divergences per level
    # ------------------------------------------------------------------- #
    kl_by_level = {lvl: [] for lvl in args.levels}

    log.info("Computing KL divergences for each quantisation level.")
    for idx, sample in tqdm(enumerate(subset), total=len(subset)):
        prompt = sample["question"]
        # Full‑precision distribution
        full_logits = get_logits(full_model, tokenizer, prompt)
        full_probs = F.softmax(full_logits, dim=-1).cpu().numpy()

        for lvl, q_model in quantized_models.items():
            q_logits = get_logits(q_model, tokenizer, prompt)
            q_probs = F.softmax(q_logits, dim=-1).cpu().numpy()
            kl = compute_kl(full_probs, q_probs)
            kl_by_level[lvl].append(kl)

    # ------------------------------------------------------------------- #
    # 4. Perform one‑sample t‑tests (null hypothesis: mean KL = 0)
    # ------------------------------------------------------------------- #
    stats = {}
    for lvl, kl_vals in kl_by_level.items():
        arr = np.array(kl_vals)
        t_stat, p_val = ttest_1samp(arr, popmean=0.0)
        stats[lvl] = {
            "sample_count": int(len(arr)),
            "mean_kl": float(np.mean(arr)),
            "t_statistic": float(t_stat),
            "p_value": float(p_val),
            "non_zero_fraction": float(np.mean(arr > 0)),
        }

    overall_significant = any(v["p_value"] < 0.05 for v in stats.values())
    summary = {
        "per_level_statistics": stats,
        "overall_non_zero_kl_significant": overall_significant,
    }

    # ------------------------------------------------------------------- #
    # 5. Write JSON statistics file
    # ------------------------------------------------------------------- #
    log.info(f"Writing dataset statistics to {stats_path}")
    stats_path.parent.mkdir(parents=True, exist_ok=True)
    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    log.info("Dataset statistics validation completed successfully.")

if __name__ == "__main__":
    main()
