"""
model_metrics.py
-----------------
Computes token‑level perplexity for each source file using the
``Salesforce/codegen-350M-mono`` model. The function writes a CSV with the
per‑file perplexity values.
"""

from __future__ import annotations

import csv
import logging
from pathlib import Path
from typing import Iterable, Tuple

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

logger = logging.getLogger(__name__)


def _default_input_path() -> Path:
    """Default path for the raw sample CSV."""
    return Path("data/raw/github-code-sample.csv")


def _default_output_path() -> Path:
    """Default path for the perplexity CSV."""
    return Path("data/processed/perplexity_scores.csv")


def _read_samples(csv_path: Path) -> Iterable[Tuple[str, str]]:
    """
    Yield ``(file_path, content)`` rows from the raw CSV.
    """
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            file_path = row.get("path") or row.get("repo") or "unknown"
            content = row.get("content", "")
            yield file_path, content


def _load_model() -> Tuple[AutoModelForCausalLM, AutoTokenizer]:
    """
    Load the CodeGen model in the most resource‑efficient way.

    The function first attempts an 8‑bit quantised load via bitsandbytes.
    If that fails (e.g. no GPU), it falls back to a regular FP16 CPU load.
    """
    model_name = "Salesforce/codegen-350M-mono"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    try:
        # 8‑bit quantisation requires bitsandbytes and (preferably) a GPU.
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            load_in_8bit=True,
            device_map="auto",
        )
        logger.info("Loaded model with 8‑bit quantisation.")
    except Exception as e:  # pragma: no cover – fallback path
        logger.warning(
            "8‑bit load failed (%s). Falling back to FP16 CPU load.", e
        )
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16,
        )
        model.to("cpu")
    model.eval()
    return model, tokenizer


def _perplexity_of_text(
    model: AutoModelForCausalLM,
    tokenizer: AutoTokenizer,
    text: str,
) -> float:
    """
    Compute the (negative‑log‑likelihood) perplexity of a single string.

    The implementation tokenises the text, shifts the inputs to obtain
    ``labels`` and computes the mean loss over the sequence.  Perplexity is
    ``exp(loss)``.
    """
    if not text.strip():
        return float("nan")

    inputs = tokenizer(text, return_tensors="pt")
    with torch.no_grad():
        outputs = model(**inputs, labels=inputs["input_ids"])
        # ``loss`` is the mean negative log‑likelihood.
        loss = outputs.loss.item()
    return float(torch.exp(torch.tensor(loss)).item())


def compute_perplexity_batch(
    input_path: Path | None = None,
    output_path: Path | None = None,
) -> Path:
    """
    Compute perplexity for each file in the sample and write a CSV.

    Parameters
    ----------
    input_path: Path | None
        Path to the raw CSV (default ``data/raw/github-code-sample.csv``).
    output_path: Path | None
        Destination CSV (default ``data/processed/perplexity_scores.csv``).

    Returns
    -------
    Path
        Path to the written CSV.
    """
    if input_path is None:
        input_path = _default_input_path()
    else:
        input_path = Path(input_path)

    if output_path is None:
        output_path = _default_output_path()
    else:
        output_path = Path(output_path)

    logger.info("Computing perplexity from %s", input_path)

    model, tokenizer = _load_model()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["file_path", "perplexity"])

        for file_path, content in _read_samples(input_path):
            try:
                ppl = _perplexity_of_text(model, tokenizer, content)
            except Exception as exc:  # pragma: no cover – unexpected model error
                logger.error("Failed to compute perplexity for %s: %s", file_path, exc)
                ppl = float("nan")
            writer.writerow([file_path, f"{ppl:.6f}"])

    logger.info("Perplexity CSV written to %s", output_path)
    return output_path
