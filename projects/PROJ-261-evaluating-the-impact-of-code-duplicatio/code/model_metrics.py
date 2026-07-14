"""
model_metrics.py
-----------------
Computes token‑level perplexity for a collection of code snippets using a
causal language model. The public function ``compute_perplexity_batch`` is
now tolerant of a variety of call signatures required throughout the
project.
"""
from __future__ import annotations

import csv
import logging
from pathlib import Path
from typing import Iterable, List, Optional

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

logger = logging.getLogger(__name__)

# Default model configuration – a small, CPU‑friendly model.
_DEFAULT_MODEL_NAME = "gpt2"  # fits within the CI environment


def _load_model(model_name: str = _DEFAULT_MODEL_NAME):
    """
    Load a transformer model and its tokenizer.
    """
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    # GPT‑2 does not have a padding token; we set one for safety.
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(model_name).to(device)
    model.eval()
    return model, tokenizer, device


def _perplexity_of_text(text: str, model, tokenizer, device) -> float:
    """
    Compute the perplexity of a single string.
    """
    encodings = tokenizer(text, return_tensors="pt")
    input_ids = encodings.input_ids.to(device)
    with torch.no_grad():
        outputs = model(input_ids, labels=input_ids)
        # `loss` is the average negative log‑likelihood per token
        loss = outputs.loss.item()
    # Perplexity = exp(loss)
    return float(torch.exp(torch.tensor(loss)).item())


def compute_perplexity_batch(*args, **kwargs) -> None:
    """
    Compute perplexity for a batch of code snippets and write the result to
    ``data/processed/perplexity_scores.csv``.
    
    Accepted signatures (mirroring the flexibility required by the pipeline):
    
    * ``compute_perplexity_batch()`` – defaults to the standard input/output paths.
    * ``compute_perplexity_batch(input_path=Path(...))``
    * ``compute_perplexity_batch(output_path=Path(...))``
    * ``compute_perplexity_batch(input_path, output_path)`` (positional)
    
    Parameters
    ----------
    input_path : pathlib.Path, optional
        CSV containing a ``code`` column. Defaults to
        ``data/raw/github-code-sample.csv``.
    output_path : pathlib.Path, optional
        Destination CSV. Defaults to
        ``data/processed/perplexity_scores.csv``.
    """
    # Resolve arguments
    input_path = Path("data/raw/github-code-sample.csv")
    output_path = Path("data/processed/perplexity_scores.csv")

    if args:
        if isinstance(args[0], (str, Path)):
            input_path = Path(args[0])
        if len(args) > 1 and isinstance(args[1], (str, Path)):
            output_path = Path(args[1])

    if "input_path" in kwargs:
        input_path = Path(kwargs["input_path"])
    if "output_path" in kwargs:
        output_path = Path(kwargs["output_path"])

    logger.info("Computing perplexity from %s → %s", input_path, output_path)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Load model once
    model, tokenizer, device = _load_model()

    # Read input CSV
    codes: List[str] = []
    try:
        with input_path.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            if "code" not in reader.fieldnames:
                raise ValueError(f"Input CSV {input_path} must contain a 'code' column.")
            for row in reader:
                codes.append(row["code"])
    except FileNotFoundError as exc:
        logger.error("Input file not found: %s", exc)
        raise

    # Compute perplexities
    results: List[Tuple[int, float]] = []
    for idx, src in enumerate(codes):
        try:
            ppl = _perplexity_of_text(src, model, tokenizer, device)
        except Exception as exc:  # pragma: no cover – defensive
            logger.warning("Failed to compute perplexity for row %d: %s", idx, exc)
            ppl = float("nan")
        results.append((idx, ppl))

    # Write CSV
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["row_index", "perplexity"])
        writer.writeheader()
        for idx, ppl in results:
            writer.writerow({"row_index": idx, "perplexity": f"{ppl:.6f}"})

    logger.info("Perplexity scores written to %s", output_path)
