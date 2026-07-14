"""
Model Metrics Module
--------------------
This module implements the functionality required by task **T020**:
- Load the `Salesforce/codegen-350M-mono` model using 8‑bit quantization via
  **bitsandbytes**.
- Compute token‑level perplexity for a sample of Python code snippets stored in
  ``data/raw/github-code-sample.csv``.
- Write the results to ``data/processed/perplexity_scores.csv``.
- Detect and log any NaN or infinite perplexity values (required by the
  unit test ``test_model_metrics.py``).

The implementation follows the existing project API surface:
- The public symbols ``ModelLoadingError``, ``load_model`` and
  ``compute_perplexity_batch`` are exported.
- The module can be executed directly (``python code/model_metrics.py``) and
  will produce the declared output file.
- No synthetic data is generated; all measurements are performed on real
  data loaded from the CSV produced by the data‑loader / AST cloner pipeline.
"""

from __future__ import annotations

import csv
import logging
import math
from pathlib import Path
from typing import List, Tuple

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

# --------------------------------------------------------------------------- #
# Logging configuration
# --------------------------------------------------------------------------- #
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# --------------------------------------------------------------------------- #
# Exceptions
# --------------------------------------------------------------------------- #
class ModelLoadingError(RuntimeError):
    """Raised when the language model cannot be loaded."""

# --------------------------------------------------------------------------- #
# Helper functions
# --------------------------------------------------------------------------- #
def _select_device() -> torch.device:
    """
    Choose the best available device.  If a CUDA‑capable GPU is present we use it;
    otherwise we fall back to CPU.  The model itself is loaded in 8‑bit mode,
    which works on both device types.
    """
    if torch.cuda.is_available():
        logger.info("CUDA device detected – using GPU.")
        return torch.device("cuda")
    logger.info("CUDA not available – using CPU.")
    return torch.device("cpu")

# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #
def load_model() -> Tuple[AutoModelForCausalLM, AutoTokenizer]:
    """
    Load the ``Salesforce/codegen-350M-mono`` model in 8‑bit quantization.

    Returns
    -------
    model : AutoModelForCausalLM
        The quantized language model.
    tokenizer : AutoTokenizer
        Tokenizer compatible with the model.

    Raises
    ------
    ModelLoadingError
        If the model cannot be loaded for any reason.
    """
    model_name = "Salesforce/codegen-350M-mono"
    try:
        logger.info("Loading tokenizer for %s", model_name)
        tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=True)
        # Ensure the tokenizer has a pad token (required for batching)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        logger.info("Loading model %s with 8‑bit quantization", model_name)
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            device_map="auto",
            load_in_8bit=True,
            trust_remote_code=True,
        )
        device = _select_device()
        model.to(device)
        model.eval()
        logger.info("Model loaded successfully on %s", device)
        return model, tokenizer
    except Exception as exc:  # pragma: no cover – explicit handling for clarity
        logger.exception("Failed to load model %s", model_name)
        raise ModelLoadingError(str(exc)) from exc

def _read_raw_snippets(
    raw_path: Path = Path("data/raw/github-code-sample.csv"),
    max_rows: int | None = None,
) -> List[Tuple[int, str]]:
    """
    Read Python code snippets from the raw CSV file.

    Parameters
    ----------
    raw_path : Path
        Path to the CSV file containing a column named ``code``.
    max_rows : int | None
        Optional limit on the number of rows to read (useful for quick tests).

    Returns
    -------
    List[Tuple[int, str]]
        List of ``(row_index, code_string)`` tuples.
    """
    if not raw_path.is_file():
        raise FileNotFoundError(f"Raw data file not found: {raw_path}")

    snippets: List[Tuple[int, str]] = []
    with raw_path.open(newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        if "code" not in reader.fieldnames:
            raise ValueError(
                f"Expected a 'code' column in {raw_path}, got {reader.fieldnames}"
            )
        for idx, row in enumerate(reader):
            if max_rows is not None and idx >= max_rows:
                break
            snippets.append((idx, row["code"]))
    logger.info("Loaded %d code snippets from %s", len(snippets), raw_path)
    return snippets

def _compute_perplexity(
    model: AutoModelForCausalLM,
    tokenizer: AutoTokenizer,
    text: str,
    device: torch.device,
) -> float:
    """
    Compute the perplexity of a single text string.

    The method tokenises ``text`` (including the EOS token), feeds the token
    IDs to the model with ``labels`` set to the same IDs, and extracts the
    mean loss.  Perplexity is ``exp(loss)``.

    Returns
    -------
    float
        Perplexity value (may be ``math.inf`` or ``math.nan`` if something goes
        wrong – the caller handles detection).
    """
    # Tokenise with truncation disabled to avoid silently dropping tokens.
    inputs = tokenizer(
        text,
        return_tensors="pt",
        truncation=False,
        add_special_tokens=True,
    )
    input_ids = inputs["input_ids"].to(device)

    with torch.no_grad():
        outputs = model(input_ids, labels=input_ids)
        # ``loss`` is the mean cross‑entropy over the sequence.
        loss = outputs.loss
        if loss is None:
            return float("nan")
        perplexity = torch.exp(loss).item()
        return perplexity

def compute_perplexity_batch(
    sample_size: int = 100,
    raw_path: Path = Path("data/raw/github-code-sample.csv"),
    output_path: Path = Path("data/processed/perplexity_scores.csv"),
) -> None:
    """
    Compute perplexity for a batch of code snippets and write the results to CSV.

    Parameters
    ----------
    sample_size : int
        Number of snippets to process.  The function reads up to ``sample_size``
        rows from ``raw_path``.
    raw_path : Path
        Input CSV containing a ``code`` column.
    output_path : Path
        Destination CSV where each row contains ``snippet_id`` and ``perplexity``.
    """
    logger.info(
        "Starting perplexity computation (sample_size=%d)", sample_size
    )
    device = _select_device()
    model, tokenizer = load_model()

    snippets = _read_raw_snippets(raw_path, max_rows=sample_size)

    # Ensure the output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["snippet_id", "perplexity"])

        for idx, code in snippets:
            try:
                ppl = _compute_perplexity(model, tokenizer, code, device)
            except Exception as exc:  # pragma: no cover – defensive
                logger.exception(
                    "Failed to compute perplexity for snippet %d", idx
                )
                ppl = float("nan")

            # Detect NaN / infinite values – required by unit test ``test_model_metrics.py``
            if math.isnan(ppl) or math.isinf(ppl):
                logger.warning(
                    "Perplexity for snippet %d is NaN or infinite (value=%s)",
                    idx,
                    ppl,
                )
            writer.writerow([idx, ppl])

    logger.info("Perplexity scores written to %s", output_path)

# --------------------------------------------------------------------------- #
# Command‑line entry point
# --------------------------------------------------------------------------- #
def main() -> None:
    """
    Entry point for ``python code/model_metrics.py``.

    The function respects the following environment variables (optional):
    - ``MODEL_METRICS_SAMPLE_SIZE`` – overrides the default sample size.
    - ``MODEL_METRICS_RAW_PATH`` – path to the raw CSV file.
    - ``MODEL_METRICS_OUTPUT_PATH`` – path where the CSV should be written.
    """
    import os

    sample_size_env = os.getenv("MODEL_METRICS_SAMPLE_SIZE")
    raw_path_env = os.getenv("MODEL_METRICS_RAW_PATH")
    output_path_env = os.getenv("MODEL_METRICS_OUTPUT_PATH")

    sample_size = int(sample_size_env) if sample_size_env else 100
    raw_path = Path(raw_path_env) if raw_path_env else Path(
        "data/raw/github-code-sample.csv"
    )
    output_path = Path(output_path_env) if output_path_env else Path(
        "data/processed/perplexity_scores.csv"
    )

    compute_perplexity_batch(
        sample_size=sample_size,
        raw_path=raw_path,
        output_path=output_path,
    )

if __name__ == "__main__":
    main()
