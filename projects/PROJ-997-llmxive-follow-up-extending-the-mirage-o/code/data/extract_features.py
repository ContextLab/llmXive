"""
extract_features.py

Task T019 – Extract training‑side features (gradient norms and local curvature)
from raw prompts using a full‑precision model. The script optionally applies PCA
to the two features.

The script can be invoked directly from the command line (as used in the
quick‑start / integration tests) or imported as a module. When imported,
the :func:`run_extraction` helper can be called programmatically.

Output
------
A Parquet file at the location specified by ``--output`` containing at least
the following columns:

* ``input_id`` – integer identifier of the sample (stable across runs)
* ``gradient_norm`` – L2 norm of the gradient of the cross‑entropy loss
  w.r.t. all model parameters for the (prompt, target) pair
* ``local_curvature`` – simple curvature proxy defined as ``gradient_norm ** 2``

If ``--pca`` is supplied, two additional columns ``pc1`` and ``pc2`` are
added, containing the first two principal components of the (gradient_norm,
local_curvature) matrix.

Determinism
-----------
The script sets the Python, NumPy and PyTorch RNG seeds to the user‑provided
``--seed`` value and forces deterministic CuDNN behaviour. This guarantees
that repeated executions with the same seed produce byte‑identical Parquet
files, satisfying the unit‑test requirement.

Dependencies
------------
* ``transformers`` – for model and tokenizer loading
* ``torch`` – for gradient computation
* ``pandas`` – for DataFrame handling and Parquet I/O
* ``numpy`` – numeric utilities
* ``requests`` – to download the GSM8K dataset
* ``tqdm`` – progress bar (optional but useful)
"""

import argparse
import json
import logging
import math
import random
from pathlib import Path
from typing import List, Tuple, Optional

import numpy as np
import pandas as pd
import requests
import torch
import torch.nn.functional as F
from tqdm.auto import tqdm
from transformers import AutoModelForCausalLM, AutoTokenizer

# --------------------------------------------------------------------------- #
# Logging configuration
# --------------------------------------------------------------------------- #
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# --------------------------------------------------------------------------- #
# Helper functions – re‑use implementations from generate_ground_truth where
# possible to avoid duplication.
# --------------------------------------------------------------------------- #
def set_deterministic(seed: int) -> None:
    """Make the whole pipeline deterministic."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False

def load_full_precision_model(model_name: str) -> Tuple[AutoModelForCausalLM, AutoTokenizer]:
    """
    Load the full‑precision (float32) model and tokenizer.
    Falls back to ``distilgpt2`` if the requested model cannot be loaded.
    """
    try:
        logger.info(f"Loading full‑precision model '{model_name}'.")
        tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=True)
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float32,
            low_cpu_mem_usage=True,
        )
    except Exception as exc:  # pragma: no cover – exercised only on CI when large model unavailable
        logger.warning(
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
    logits = model(**inputs).logits[:, -1, :]  # (1, vocab_size)
    loss_fct = torch.nn.CrossEntropyLoss()
    loss = loss_fct(logits, target_ids[:, 0])
    loss.backward()
    total_norm = 0.0
    for p in model.parameters():
        if p.grad is not None:
            param_norm = p.grad.detach().data.norm(2)
            total_norm += param_norm.item() ** 2
    total_norm = math.sqrt(total_norm)
    model.zero_grad(set_to_none=True)
    model.eval()
    return total_norm

def download_gsm8k_subset(sample_size: int) -> List[dict]:
    """
    Stream the GSM8K training split from the Hugging Face Hub and return
    the first ``sample_size`` records as a list of dictionaries.
    """
    url = "https://huggingface.co/datasets/gsm8k/resolve/main/train.jsonl"
    logger.info(f"Downloading GSM8K dataset from {url}")
    response = requests.get(url, stream=True, timeout=60)
    response.raise_for_status()
    records = []
    for line in response.iter_lines(decode_unicode=True):
        if line:
            record = json.loads(line)
            records.append(record)
            if len(records) >= sample_size:
                break
    logger.info(f"Retrieved {len(records)} GSM8K samples.")
    return records

# --------------------------------------------------------------------------- #
# Core extraction logic
# --------------------------------------------------------------------------- #
def run_extraction(
    model_name: str,
    sample_size: int,
    output_path: Path,
    seed: int = 42,
    apply_pca: bool = False,
) -> pd.DataFrame:
    """
    Perform a single forward‑backward pass for each prompt in the GSM8K
    subset, compute ``gradient_norm`` and ``local_curvature`` and write the
    results to ``output_path`` (Parquet).

    Parameters
    ----------
    model_name: str
        Hugging‑Face identifier of the model to load.
    sample_size: int
        Number of GSM8K training examples to process.
    output_path: Path
        Destination Parquet file.
    seed: int, optional
        Random seed for reproducibility.
    apply_pca: bool, optional
        If True, compute the first two principal components of the two‑dim
        feature matrix and store them as ``pc1`` and ``pc2`` columns.

    Returns
    -------
    pandas.DataFrame
        The DataFrame that was written to disk.
    """
    set_deterministic(seed)

    # 1️⃣ Load data
    subset = download_gsm8k_subset(sample_size)

    # 2️⃣ Load model
    model, tokenizer = load_full_precision_model(model_name)

    records = []
    logger.info("Computing training‑side features.")
    for idx, sample in tqdm(enumerate(subset), total=len(subset)):
        prompt = sample["question"]
        # Use the first line of the answer as the target token sequence.
        target = sample["answer"].split("\n")[0]

        grad_norm = compute_gradient_norm(model, tokenizer, prompt, target)
        curvature = grad_norm ** 2

        record = {
            "input_id": idx,
            "gradient_norm": float(grad_norm),
            "local_curvature": float(curvature),
        }
        records.append(record)

    df = pd.DataFrame.from_records(records)

    # Optional PCA
    if apply_pca:
        from sklearn.decomposition import PCA

        logger.info("Applying PCA to the two feature columns.")
        pca = PCA(n_components=2, random_state=seed)
        pcs = pca.fit_transform(df[["gradient_norm", "local_curvature"]].values)
        df["pc1"] = pcs[:, 0]
        df["pc2"] = pcs[:, 1]

    # 3️⃣ Persist
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, index=False)
    logger.info(f"Feature file written to {output_path} ({len(df)} rows).")
    return df

# --------------------------------------------------------------------------- #
# CLI entry point
# --------------------------------------------------------------------------- #
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract training‑side features (gradient norm & curvature) from GSM8K prompts."
    )
    parser.add_argument(
        "--model",
        type=str,
        required=True,
        help="Hugging‑Face model identifier (e.g. 'distilgpt2' or a larger model).",
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=300,
        help="Number of GSM8K training samples to process (default 300).",
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Path to the Parquet file that will store the extracted features.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for deterministic execution.",
    )
    parser.add_argument(
        "--pca",
        action="store_true",
        help="If set, compute the first two principal components and store them as pc1/pc2.",
    )
    args = parser.parse_args()

    output_path = Path(args.output).expanduser().resolve()
    run_extraction(
        model_name=args.model,
        sample_size=args.sample_size,
        output_path=output_path,
        seed=args.seed,
        apply_pca=args.pca,
    )

if __name__ == "__main__":
    main()
