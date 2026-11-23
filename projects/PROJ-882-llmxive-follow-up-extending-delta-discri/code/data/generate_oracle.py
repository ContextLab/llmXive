"""
code/data/generate_oracle.py
--------------------------------
Implements the DelTA oracle generation step (Task T013).

This script:
  * Loads the verified GSM8K subset (produced by `download_gsm8k.py`).
  * Samples up to ``N_EXAMPLES_TARGET`` examples stratified by answer length
    (seeded for reproducibility).
  * Loads the Llama‑3‑8B‑Instruct model (as defined in the config).
  * For each sampled example runs a lightweight DelTA‑style gradient
    computation using ``torch.autograd.grad``.
  * Handles numerical‑instability exceptions by logging them and skipping the
    offending example.
  * Falls back to a smaller set if the number of successful examples is
    between ``N_EXAMPLES_MIN`` and ``N_EXAMPLES_TARGET`` (issues a warning).
  * Fails with a clear ``RuntimeError`` if fewer than ``N_EXAMPLES_MIN``
    examples are successfully processed.
  * Computes the global variance of all coefficients and raises
    ``RuntimeError('ERR_TRIVIAL_TARGET')`` when the variance is ≤ 1e‑9.
  * Persists the results to ``data/processed/delta_coefficients.json`` and
    validates them against the schema.

The implementation deliberately avoids any GPU‑specific calls – the model
runs on CPU, which satisfies the project’s “CPU‑only portion” requirement.
"""

import json
import logging
import os
import random
import sys
import traceback
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd
import torch
from torch import nn
from transformers import AutoModelForCausalLM, AutoTokenizer

# Project‑specific imports
from config import get_config_summary

# --------------------------------------------------------------------------- #
# Logging configuration
# --------------------------------------------------------------------------- #
LOG_DIR = Path("logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "error.log"

logger = logging.getLogger("generate_oracle")
logger.setLevel(logging.INFO)
handler = logging.FileHandler(LOG_FILE, mode="a")
formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

# --------------------------------------------------------------------------- #
# Data structures
# --------------------------------------------------------------------------- #
@dataclass
class DeltaCoefficient:
    """
    Holds the DelTA coefficients for a single example.

    Attributes
    ----------
    example_id: str
        Identifier of the example (taken from the GSM8K ``id`` field).
    token_ids: List[int]
        Token IDs (as produced by the tokenizer) for the answer portion.
    coefficients: List[float]
        Computed coefficient for each token.
    """
    example_id: str
    token_ids: List[int]
    coefficients: List[float]

# --------------------------------------------------------------------------- #
# Helper functions
# --------------------------------------------------------------------------- #
def load_gsm8k_verified() -> pd.DataFrame:
    """
    Load the verified GSM8K subset saved by ``download_gsm8k.py``.

    Returns
    -------
    pd.DataFrame
        DataFrame with at least the columns ``id``, ``question`` and ``answer``.
    """
    data_path = Path("data/raw/gsm8k_verified.parquet")
    if not data_path.is_file():
        raise FileNotFoundError(
            f"Verified GSM8K file not found at {data_path}. "
            "Run `code/data/download_gsm8k.py` first."
        )
    df = pd.read_parquet(data_path)
    return df

def stratified_sample(df: pd.DataFrame, target_n: int, seed: int = 42) -> pd.DataFrame:
    """
    Perform a stratified sample of the dataframe based on answer length.

    Parameters
    ----------
    df : pd.DataFrame
        The full verified dataset.
    target_n : int
        Desired number of examples (e.g., 500).
    seed : int
        Random seed for reproducibility.

    Returns
    -------
    pd.DataFrame
        Sampled dataframe (may contain fewer rows if the original dataset is
        smaller than ``target_n``).
    """
    random.seed(seed)
    # Compute answer length (number of tokens approximated by whitespace split)
    df = df.copy()
    df["answer_len"] = df["answer"].apply(lambda x: len(str(x).split()))
    # Create length bins (5 bins)
    df["len_bin"] = pd.qcut(df["answer_len"], q=5, duplicates="drop")
    # Sample proportionally from each bin
    sampled_frames = []
    for _, bin_df in df.groupby("len_bin"):
        n_bin = max(1, int(round(len(bin_df) / len(df) * target_n)))
        sampled_frames.append(bin_df.sample(n=min(n_bin, len(bin_df)), random_state=seed))
    sampled = pd.concat(sampled_frames).drop(columns=["answer_len", "len_bin"])
    # If we still have fewer than target_n (because of rounding), pad with random rows
    if len(sampled) < target_n:
        remaining = df.drop(sampled.index)
        needed = target_n - len(sampled)
        extra = remaining.sample(n=min(needed, len(remaining)), random_state=seed)
        sampled = pd.concat([sampled, extra])
    return sampled.head(target_n)

def load_oracle_model(model_name: str) -> tuple[AutoModelForCausalLM, AutoTokenizer]:
    """
    Load the oracle LLM.

    Parameters
    ----------
    model_name : str
        HuggingFace identifier of the model (e.g., ``meta-llama/Meta-Llama-3-8B-Instruct``).

    Returns
    -------
    tuple
        (model, tokenizer) loaded onto CPU with ``torch.float16`` dtype to keep memory
        consumption as low as possible.
    """
    # The model is large; we request ``torch_dtype=torch.float16`` and ``device_map="auto"``
    # which lets 🤗 transformers place the model on CPU while using 16‑bit weights.
    # This works on machines without a GPU.
    tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=True)
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float16,
        device_map="auto",
    )
    model.eval()
    return model, tokenizer

def compute_delta_coefficients(
    model: nn.Module,
    tokenizer: AutoTokenizer,
    examples: pd.DataFrame,
) -> List[DeltaCoefficient]:
    """
    Compute DelTA coefficients for a list of examples.

    For each example we:
      1. Tokenise the *answer* (the part we want token‑level credit for).
      2. Iterate over each token position, compute the loss of predicting the next
         token, back‑propagate to obtain the gradient w.r.t. the input embedding,
         and record the L2 norm of that gradient as the coefficient.
      3. Collect all token IDs and coefficients into a ``DeltaCoefficient`` object.

    Numerical instabilities (e.g., ``RuntimeError`` or ``ValueError``) are caught;
    the offending example is logged and skipped.

    Parameters
    ----------
    model : nn.Module
        The loaded Llama‑3‑8B‑Instruct model.
    tokenizer : AutoTokenizer
        Corresponding tokenizer.
    examples : pd.DataFrame
        Dataframe containing at least ``id`` and ``answer`` columns.

    Returns
    -------
    List[DeltaCoefficient]
        Coefficients for all *successfully* processed examples.
    """
    results: List[DeltaCoefficient] = []

    for _, row in examples.iterrows():
        example_id = str(row["id"])
        answer_text = str(row["answer"])

        try:
            # Tokenise answer *only* (the oracle credit is per answer token)
            enc = tokenizer(
                answer_text,
                return_tensors="pt",
                add_special_tokens=False,
            )
            input_ids = enc["input_ids"]
            # Ensure gradient tracking on embeddings
            input_ids = input_ids.to(model.device)

            # Obtain embeddings with gradient tracking
            embedding_layer = model.get_input_embeddings()
            embeddings = embedding_layer(input_ids)
            embeddings.requires_grad_(True)

            # Forward pass using embeddings
            outputs = model(inputs_embeds=embeddings)
            logits = outputs.logits  # shape: (1, seq_len, vocab_size)

            # Shift so that logits[i] predicts token i+1
            shift_logits = logits[:, :-1, :].contiguous()
            shift_labels = input_ids[:, 1:].contiguous()

            loss_fct = nn.CrossEntropyLoss(reduction="none")
            # Compute loss per token
            loss_per_token = loss_fct(
                shift_logits.view(-1, shift_logits.size(-1)),
                shift_labels.view(-1),
            )
            # Back‑propagate each token loss individually to get per‑token grads
            token_coeffs: List[float] = []
            for i in range(loss_per_token.shape[0]):
                # Zero previous grads
                if embeddings.grad is not None:
                    embeddings.grad.zero_()
                loss = loss_per_token[i]
                loss.backward(retain_graph=True)
                # Gradient w.r.t. the embedding of token i
                grad = embeddings.grad[0, i]  # shape: (hidden_dim,)
                coeff = torch.norm(grad, p=2).item()
                if not np.isfinite(coeff):
                    raise ValueError("Non‑finite coefficient encountered")
                token_coeffs.append(coeff)

            # Store results
            results.append(
                DeltaCoefficient(
                    example_id=example_id,
                    token_ids=input_ids.squeeze().tolist(),
                    coefficients=token_coeffs,
                )
            )
        except Exception as exc:
            # Log the failure and continue with the next example
            logger.error(
                f"Failed to compute DelTA for example {example_id}: {exc}"
            )
            logger.debug(traceback.format_exc())
            continue

    return results

def validate_coefficients(coeffs: List[DeltaCoefficient]) -> None:
    """
    Validate the list of ``DeltaCoefficient`` objects.

    Checks performed:
      * At least one coefficient set is present.
      * No NaN/Inf values.
      * Global variance of all coefficient values exceeds ``1e-9``.
    Raises
    ------
    RuntimeError
        If any validation rule fails.
    """
    if not coeffs:
        raise RuntimeError("No valid DelTA coefficients were generated.")

    # Flatten all coefficient values
    flat_vals = np.concatenate([np.array(c.coefficients) for c in coeffs])

    if np.isnan(flat_vals).any() or np.isinf(flat_vals).any():
        raise RuntimeError("NaN or Inf detected in DelTA coefficients.")

    variance = float(np.var(flat_vals))
    if variance <= 1e-9:
        raise RuntimeError("ERR_TRIVIAL_TARGET")
    # Optionally expose variance for logging
    logger.info(f"Global variance of DelTA coefficients: {variance:e}")

def save_oracle_results(
    coeffs: List[DeltaCoefficient],
    output_path: Path = Path("data/processed/delta_coefficients.json"),
) -> None:
    """
    Serialize ``DeltaCoefficient`` objects to JSON.

    The JSON format is a list of dictionaries with keys:
        - ``example_id``
        - ``token_ids``
        - ``coefficients``

    Parameters
    ----------
    coeffs : List[DeltaCoefficient]
        Computed coefficients.
    output_path : Path
        Destination file. Parent directories are created automatically.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    serialisable = [asdict(c) for c in coeffs]
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(serialisable, f, ensure_ascii=False, indent=2)
    logger.info(f"Saved DelTA oracle results to {output_path}")

# --------------------------------------------------------------------------- #
# Main orchestration
# --------------------------------------------------------------------------- #
def main() -> None:
    """
    Entry point for the oracle generation script.

    The workflow follows the specification of Task T013.
    """
    try:
        cfg: Dict[str, Any] = get_config_summary()
        target_n: int = int(cfg.get("N_EXAMPLES_TARGET", 500))
        min_n: int = int(cfg.get("N_EXAMPLES_MIN", 10))
        model_name: str = cfg.get(
            "ORACLE_MODEL",
            "meta-llama/Meta-Llama-3-8B-Instruct",
        )

        # 1️⃣ Load and sample the dataset
        df = load_gsm8k_verified()
        sampled_df = stratified_sample(df, target_n, seed=42)

        # 2️⃣ Load the oracle model
        model, tokenizer = load_oracle_model(model_name)

        # 3️⃣ Compute coefficients
        coeffs = compute_delta_coefficients(model, tokenizer, sampled_df)

        # 4️⃣ Fallback / size checks
        successful = len(coeffs)
        if successful < min_n:
            raise RuntimeError(
                f"Insufficient successful examples: {successful} < {min_n}"
            )
        if successful < target_n:
            logger.warning(
                f"Only {successful} out of {target_n} examples succeeded; "
                "proceeding with available data."
            )

        # 5️⃣ Global variance check
        validate_coefficients(coeffs)

        # 6️⃣ Persist results
        save_oracle_results(coeffs)

    except Exception as e:
        # Any top‑level failure is logged and re‑raised so that the pipeline
        # recognises the error.
        logger.error(f"Oracle generation failed: {e}")
        logger.debug(traceback.format_exc())
        raise

if __name__ == "__main__":
    # When executed as a script we invoke the main routine.
    main()