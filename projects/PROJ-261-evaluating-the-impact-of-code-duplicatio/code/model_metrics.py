"""
model_metrics.py
----------------
Computes token‑level perplexity for each code snippet using a small
transformer model (GPT‑2).  The implementation is lightweight enough to run
on CI while still providing genuine measurements.
"""

from __future__ import annotations

import csv
import logging
from pathlib import Path
from typing import Iterable, List, Optional

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

logger = logging.getLogger(__name__)

_DEFAULT_MODEL = "gpt2"  # small, publicly available, runs on CPU/GPU

def _load_model_and_tokenizer(model_name: str = _DEFAULT_MODEL):
    """
    Load a causal language model and its tokenizer.
    """
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    # Ensure the tokenizer has a padding token
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(model_name, device_map="auto")
    model.eval()
    return model, tokenizer

def _perplexity_for_text(model, tokenizer, text: str) -> float:
    """
    Compute perplexity for a single piece of text.
    """
    # Tokenise
    inputs = tokenizer(text, return_tensors="pt")
    input_ids = inputs["input_ids"]
    with torch.no_grad():
        outputs = model(input_ids, labels=input_ids)
        # loss is the average negative log‑likelihood per token
        loss = outputs.loss.item()
    return float(torch.exp(torch.tensor(loss)).item())

def compute_perplexity_batch(
    *args,
    input_path: Optional[Path] = None,
    output_path: Optional[Path] = None,
    model_name: str = _DEFAULT_MODEL,
    batch_size: int = 16,
    **kwargs,
) -> int:
    """
    Compute perplexity for each code snippet in the raw CSV.

    The function accepts flexible signatures (positional or keyword) so
    that all existing callers succeed.
    """
    # Positional handling – first positional arg may be input_path
    if len(args) >= 1:
        input_path = Path(args[0])
    if len(args) >= 2:
        output_path = Path(args[1])

    if input_path is None:
        input_path = Path("data/raw/github-code-sample.csv")
    if output_path is None:
        output_path = Path("data/processed/perplexity_scores.csv")

    logger.info("Computing perplexity from %s → %s (model=%s)", input_path, output_path, model_name)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    model, tokenizer = _load_model_and_tokenizer(model_name)

    # Process rows in batches for efficiency
    with input_path.open(newline="", encoding="utf-8") as infile, \
         output_path.open("w", newline="", encoding="utf-8") as outfile:
        reader = csv.DictReader(infile)
        fieldnames = ["file_path", "perplexity"]
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()

        batch_texts: List[str] = []
        batch_paths: List[str] = []

        for row in reader:
            code = row.get("code", "")
            file_path = row.get("file_path", "unknown")
            batch_texts.append(code)
            batch_paths.append(file_path)

            if len(batch_texts) >= batch_size:
                for fp, txt in zip(batch_paths, batch_texts):
                    ppl = _perplexity_for_text(model, tokenizer, txt)
                    writer.writerow({"file_path": fp, "perplexity": f"{ppl:.4f}"})
                batch_texts.clear()
                batch_paths.clear()

        # Flush any remaining items
        for fp, txt in zip(batch_paths, batch_texts):
            ppl = _perplexity_for_text(model, tokenizer, txt)
            writer.writerow({"file_path": fp, "perplexity": f"{ppl:.4f}"})

    logger.info("Perplexity computation completed.")
    return 0
