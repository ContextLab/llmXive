"""
model_metrics.py
----------------
Computes token‑level perplexity for each code snippet using the
``Salesforce/codegen-350M-mono`` model loaded in 8‑bit mode via
``bitsandbytes``. The public function ``compute_perplexity_batch`` writes
``data/processed/perplexity_scores.csv``.
"""

from __future__ import annotations

import csv
import logging
from pathlib import Path
from typing import List

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

logger = logging.getLogger(__name__)

DEFAULT_DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

def _load_model_and_tokenizer():
    model_name = "Salesforce/codegen-350M-mono"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    # bitsandbytes 8‑bit loading
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        load_in_8bit=True,
        device_map="auto",
    )
    model.eval()
    return model, tokenizer

def _perplexity_of_text(text: str, model, tokenizer) -> float:
    """
    Compute perplexity for a single code snippet. Returns ``float('nan')``
    if the model cannot process the input.
    """
    try:
        inputs = tokenizer(text, return_tensors="pt")
        inputs = {k: v.to(model.device) for k, v in inputs.items()}
        with torch.no_grad():
            loss = model(**inputs, labels=inputs["input_ids"]).loss
        return torch.exp(loss).item()
    except Exception as e:
        logger.debug("Failed to compute perplexity for a snippet: %s", e)
        return float("nan")

def compute_perplexity_batch(*, input_path: Optional[Path] = None) -> None:
    """
    Compute perplexity for each row in ``data/raw/github-code-sample.csv``.
    Writes ``data/processed/perplexity_scores.csv`` with columns:

    ``file_path,perplexity``
    """
    raw_path = Path(input_path) if input_path else Path("data/raw/github-code-sample.csv")
    if not raw_path.is_file():
        raise FileNotFoundError(f"Raw data not found at {raw_path}")

    logger.info("Computing perplexity scores from %s", raw_path)

    model, tokenizer = _load_model_and_tokenizer()

    output_path = Path("data/processed/perplexity_scores.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with raw_path.open(newline="", encoding="utf-8") as rf, output_path.open(
        "w", newline="", encoding="utf-8"
    ) as wf:
        reader = csv.DictReader(rf)
        writer = csv.DictWriter(wf, fieldnames=["file_path", "perplexity"])
        writer.writeheader()
        for row in reader:
            file_path = row["file_path"]
            code = row["code"]
            perp = _perplexity_of_text(code, model, tokenizer)
            writer.writerow({"file_path": file_path, "perplexity": f"{perp:.6f}"})

    logger.info("Perplexity scores written to %s", output_path)
