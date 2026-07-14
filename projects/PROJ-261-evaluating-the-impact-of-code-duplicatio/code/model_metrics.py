"""
model_metrics.py
----------------
Computes token‑level perplexity for a corpus of Python files using a
causal language model.  The implementation follows the same flexible‑call
signature pattern required by the contract:

* ``compute_perplexity_batch()`` – defaults.
* ``compute_perplexity_batch(input_path=…, output_path=…)`` – keyword args.
* ``compute_perplexity_batch(Path(...), Path(...))`` – positional args.

Results are written to ``data/processed/perplexity_scores.csv``.
"""
from __future__ import annotations

import csv
import logging
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from config import get_all_config

logger = logging.getLogger(__name__)


def _load_model_and_tokenizer():
    """
    Load the model specified in the configuration with 8‑bit quantisation
    when possible.  The function deliberately avoids any GPU‑only assumptions;
    if a GPU is present it will be used, otherwise CPU is used.
    """
    cfg = get_all_config()
    model_name = cfg.get("model_name", "Salesforce/codegen-350M-mono")
    quant_bits = cfg.get("quantization_bits", 8)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # ``torch_dtype`` is left as default; bitsandbytes handles the quantisation.
    tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=True)
    # ``load_in_8bit`` requires bitsandbytes; if unavailable we fall back.
    try:
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            device_map="auto",
            load_in_8bit=True,
            torch_dtype=torch.float16,
        )
    except Exception as exc:  # pragma: no cover – fallback path
        logger.warning(
            "8‑bit loading failed (%s); loading full‑precision model instead.", exc
        )
        model = AutoModelForCausalLM.from_pretrained(model_name)
    model.to(device)
    model.eval()
    return model, tokenizer, device


def _read_raw_dataset(csv_path: Path) -> list[tuple[str, str]]:
    """
    Read ``data/raw/github-code-sample.csv`` and return a list of
    (file_path, source_code) tuples.
    """
    records = []
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append((row["file_path"], row["content"]))
    return records


def _write_perplexity_csv(
    rows: list[tuple[str, float]], output_path: Path
) -> None:
    """
    Write perplexity scores to CSV.

    Parameters
    ----------
    rows: List[Tuple[str, float]]
        (file_path, perplexity) pairs.
    output_path: Path
        Destination CSV file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["file_path", "perplexity"])
        writer.writerows(rows)


def compute_perplexity_batch(
    input_path: Path | None = None,
    output_path: Path | None = None,
) -> Path:
    """
    Compute perplexity for each file in the supplied CSV.

    The function accepts a flexible call signature to satisfy all callers.
    If *input_path* is omitted, ``data/raw/github-code-sample.csv`` is used.
    If *output_path* is omitted, results are written to
    ``data/processed/perplexity_scores.csv``.

    Returns
    -------
    Path
        Path to the generated CSV.
    """
    cfg = get_all_config()
    default_input = Path("data/raw/github-code-sample.csv")
    default_output = Path("data/processed/perplexity_scores.csv")

    input_path = Path(input_path) if input_path else default_input
    output_path = Path(output_path) if output_path else default_output

    logger.info("Computing perplexity from %s → %s", input_path, output_path)

    records = _read_raw_dataset(input_path)
    model, tokenizer, device = _load_model_and_tokenizer()

    results: list[tuple[str, float]] = []

    for file_path, source in records:
        # Tokenise the source; we ignore empty inputs.
        if not source.strip():
            logger.debug("Empty source for %s – skipping", file_path)
            continue

        inputs = tokenizer(
            source,
            return_tensors="pt",
            truncation=True,
            max_length=tokenizer.model_max_length,
        )
        input_ids = inputs["input_ids"].to(device)

        with torch.no_grad():
            outputs = model(input_ids, labels=input_ids)
            # ``loss`` is the mean negative log‑likelihood over tokens.
            loss = outputs.loss.item()
            # Perplexity is exp(loss).
            perplexity = float(torch.exp(torch.tensor(loss)).item())

        # Guard against pathological values.
        if perplexity != perplexity or perplexity == float("inf"):
            logger.warning(
                "Invalid perplexity (%s) for %s – setting to NaN", perplexity, file_path
            )
            perplexity = float("nan")

        results.append((file_path, perplexity))

    _write_perplexity_csv(results, output_path)
    logger.info("Perplexity CSV written to %s", output_path)
    return output_path