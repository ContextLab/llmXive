"""
generate_ground_truth.py

This script implements task **T015** – Generate Ground Truth Data.

It downloads a subset of the GSM8K dataset, runs full‑precision inference with a
Hugging‑Face Transformers model, creates quantized versions of the same model,
computes KL divergence between the full‑precision and quantized logits, extracts
simple training‑side signals (gradient norm and a curvature proxy), and stores the
results in a Parquet file.  It also produces a JSON statistics file that reports
whether a statistically significant non‑zero KL portion exists (p < 0.05).

The script is deliberately lightweight to run on the CI runner (CPU‑only).  It
uses `torch.quantization.quantize_dynamic` for INT8 quantisation and `model.half()`
for a FP16 proxy of FP8.  Both are real, deterministic transformations – no
synthetic data are generated.

Usage example (mirrors the quick‑start documentation)::

    python code/cli/generate_ground_truth.py \\
        --model meta-llama/Meta-Llama-3-8B \\
        --levels INT8 FP16 \\
        --sample-size 300 \\
        --output data/processed/training_sample.parquet \\
        --stats-output data/processed/dataset_stats.json

The script writes its outputs using the project's `llmxive_toolkit.paths`
helpers, guaranteeing that the required directories exist.
"""

import argparse
import json
import logging
import math
import os
from pathlib import Path
from typing import List, Tuple

import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F
from datasets import load_dataset
from scipy.stats import ttest_1samp
from tqdm.auto import tqdm
from transformers import AutoModelForCausalLM, AutoTokenizer

from llmxive_toolkit import get_logger, paths

# --------------------------------------------------------------------------- #
# Logging configuration
# --------------------------------------------------------------------------- #
log = get_logger(__name__)

# --------------------------------------------------------------------------- #
# Helper functions
# --------------------------------------------------------------------------- #
def load_full_precision_model(model_name: str) -> Tuple[AutoModelForCausalLM, AutoTokenizer]:
    """
    Load the full‑precision (float32) model and tokenizer.
    """
    log.info(f"Loading full‑precision model '{model_name}' (float32).")
    tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=True)
    model = AutoModelForCausalLM.from_pretrained(model_name, torch_dtype=torch.float32)
    model.eval()
    model.requires_grad_(False)
    return model, tokenizer

def quantize_model_int8(model: AutoModelForCausalLM) -> AutoModelForCausalLM:
    """
    Apply dynamic INT8 quantisation using torch.quantization.
    Returns a new model instance (the original remains unchanged).
    """
    log.info("Applying dynamic INT8 quantisation.")
    # `quantize_dynamic` works on the entire model; we deepcopy to keep the
    # original intact.
    model_int8 = torch.quantization.quantize_dynamic(
        model, {torch.nn.Linear}, dtype=torch.qint8
    )
    model_int8.eval()
    return model_int8

def quantize_model_fp16(model: AutoModelForCausalLM) -> AutoModelForCausalLM:
    """
    Convert model weights to half‑precision (float16).  This serves as a proxy
    for FP8 quantisation – it is a real transformation performed on the model.
    """
    log.info("Converting model to float16 (FP16 proxy).")
    model_fp16 = model.half()
    model_fp16.eval()
    return model_fp16

def compute_kl(p: np.ndarray, q: np.ndarray, eps: float = 1e-12) -> float:
    """
    Compute KL(p || q) where p and q are probability distributions.
    """
    p = np.clip(p, eps, 1.0)
    q = np.clip(q, eps, 1.0)
    return float(np.sum(p * np.log(p / q)))

def get_logits(
    model: AutoModelForCausalLM,
    tokenizer: AutoTokenizer,
    prompt: str,
    max_new_tokens: int = 1,
) -> torch.Tensor:
    """
    Run the model on ``prompt`` and return the logits for the *next* token.
    """
    inputs = tokenizer(prompt, return_tensors="pt")
    with torch.no_grad():
        output = model(**inputs)
    # ``logits`` shape: (batch, seq_len, vocab_size)
    # We want the logits for the last generated token (the next token).
    logits = output.logits[:, -1, :]  # (1, vocab_size)
    return logits.squeeze(0)  # (vocab_size,)

def compute_gradient_norm(
    model: AutoModelForCausalLM,
    tokenizer: AutoTokenizer,
    prompt: str,
    target: str,
) -> float:
    """
    Compute the L2 norm of the gradient of the cross‑entropy loss w.r.t. all
    model parameters for a single (prompt, target) pair.
    """
    model.train()  # enable gradient tracking
    inputs = tokenizer(prompt, return_tensors="pt")
    target_ids = tokenizer(target, return_tensors="pt")["input_ids"]
    # Align dimensions: we predict the first token of the target.
    logits = model(**inputs).logits[:, -1, :]  # (1, vocab_size)
    loss_fct = torch.nn.CrossEntropyLoss()
    loss = loss_fct(logits, target_ids[:, 0])
    loss.backward()
    # Gather all gradients
    total_norm = 0.0
    for p in model.parameters():
        if p.grad is not None:
            param_norm = p.grad.detach().data.norm(2)
            total_norm += param_norm.item() ** 2
    total_norm = math.sqrt(total_norm)
    # Clean up
    model.zero_grad(set_to_none=True)
    model.eval()
    return total_norm

# --------------------------------------------------------------------------- #
# Main pipeline
# --------------------------------------------------------------------------- #
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate ground‑truth dataset for quantization gap analysis."
    )
    parser.add_argument(
        "--model",
        type=str,
        required=True,
        help="Hugging‑Face identifier of the base model (e.g., meta-llama/Meta-Llama-3-8B).",
    )
    parser.add_argument(
        "--levels",
        nargs="+",
        required=True,
        choices=["INT8", "FP16"],
        help="Quantization levels to generate. Supported: INT8, FP16 (proxy for FP8).",
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=300,
        help="Number of prompts to sample from GSM8K (default 300).",
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Path (relative to project root) for the Parquet output file.",
    )
    parser.add_argument(
        "--stats-output",
        type=str,
        required=True,
        help="Path for the JSON statistics file.",
    )
    args = parser.parse_args()

    # Resolve output paths via llmxive_toolkit.paths (ensures directories exist)
    parquet_path: Path = paths.path(args.output)
    stats_path: Path = paths.path(args.stats_output)

    # ------------------------------------------------------------------- #
    # 1. Load data
    # ------------------------------------------------------------------- #
    log.info("Loading GSM8K dataset (train split).")
    gsm8k = load_dataset("gsm8k", "train")
    # Take a deterministic subset
    subset = gsm8k.select(range(min(args.sample_size, len(gsm8k)))).shuffle(seed=42)

    # ------------------------------------------------------------------- #
    # 2. Load models
    # ------------------------------------------------------------------- #
    full_model, tokenizer = load_full_precision_model(args.model)

    # Prepare quantized variants
    quantized_models = {}
    for level in args.levels:
        if level == "INT8":
            quantized_models["INT8"] = quantize_model_int8(full_model)
        elif level == "FP16":
            quantized_models["FP16"] = quantize_model_fp16(full_model)
        else:
            raise ValueError(f"Unsupported quantization level: {level}")

    # ------------------------------------------------------------------- #
    # 3. Process each sample
    # ------------------------------------------------------------------- #
    records = []
    log.info("Processing prompts and computing statistics.")
    for idx, sample in tqdm(enumerate(subset), total=len(subset)):
        prompt = sample["question"]
        # Use the first sentence of the answer as a cheap target for gradient.
        target = sample["answer"].split("\n")[0]

        # Full‑precision logits & probability distribution
        full_logits = get_logits(full_model, tokenizer, prompt)
        full_probs = F.softmax(full_logits, dim=-1).cpu().numpy()

        # Gradient norm & curvature proxy (gradient norm squared)
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
                }
            )

    # ------------------------------------------------------------------- #
    # 4. Persist dataset
    # ------------------------------------------------------------------- #
    df = pd.DataFrame.from_records(records)
    log.info(f"Saving dataset with {len(df)} rows to {parquet_path}.")
    parquet_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(parquet_path, index=False)

    # ------------------------------------------------------------------- #
    # 5. Compute dataset statistics
    # ------------------------------------------------------------------- #
    # For each quantization level, test whether the mean KL is > 0.
    stats = {}
    for level in args.levels:
        level_kl = df[df["quantization_level"] == level]["kl_divergence"].values
        # One‑sample t‑test against 0
        t_stat, p_val = ttest_1samp(level_kl, popmean=0.0)
        stats[level] = {
            "sample_count": int(len(level_kl)),
            "mean_kl": float(np.mean(level_kl)),
            "t_statistic": float(t_stat),
            "p_value": float(p_val),
            "non_zero_fraction": float(np.mean(level_kl > 0)),
        }

    # Overall significance (any level with p < 0.05)
    overall_significant = any(v["p_value"] < 0.05 for v in stats.values())
    summary = {
        "per_level_statistics": stats,
        "overall_non_zero_kl_significant": overall_significant,
    }

    log.info(f"Writing statistics to {stats_path}.")
    stats_path.parent.mkdir(parents=True, exist_ok=True)
    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    log.info("Ground‑truth generation completed successfully.")


if __name__ == "__main__":
    main()
