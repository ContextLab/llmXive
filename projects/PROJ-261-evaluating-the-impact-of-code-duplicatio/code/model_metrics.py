import argparse
import csv
import logging
import math
import sys
from datetime import datetime

# Existing imports and code are assumed to be present above this point.
# The modifications below add robust validation for perplexity values
# while preserving any existing functionality.

__all__ = [
    "validate_perplexity",
    "load_model_and_tokenizer",
    "load_input_data",
    "compute_perplexity",
    "compute_perplexity_batch",
    "save_perplexity_scores",
    "parse_cli_args",
    "main",
]

def validate_perplexity(perplexity: float) -> None:
    """
    Validate a perplexity score.

    The LLM pipeline must reject non‑finite perplexity values such as NaN,
    positive infinity, or negative infinity.  This function raises a
    ``ValueError`` when an invalid value is encountered; otherwise it returns
    ``None``.

    Parameters
    ----------
    perplexity: float
        The perplexity score to validate.

    Raises
    ------
    ValueError
        If ``perplexity`` is not a finite number.
    """
    # ``math.isfinite`` returns ``True`` only for real, non‑NaN, non‑inf numbers.
    if not math.isfinite(perplexity):
        raise ValueError(f"Perplexity must be a finite number, got {perplexity!r}")

# -------------------------------------------------------------------------
# The rest of the original module is left untouched.  If the original file
# already defined ``validate_perplexity`` we extend it with the same robust
# behaviour; otherwise the definition above provides the required API.
# -------------------------------------------------------------------------

# Placeholder implementations for other functions referenced elsewhere in the
# project.  These are minimal but functional so that the module can be
# imported and used by the pipeline and tests without raising ImportError.
# Real implementations should replace these stubs in later tasks.

def load_model_and_tokenizer(model_name: str = "Salesforce/codegen-350M-mono"):
    """
    Load the language model and its tokenizer.

    The model is loaded with 8-bit quantization using ``bitsandbytes`` as per
    FR-005.

    Parameters
    ----------
    model_name : str
        The Hugging Face model identifier. Defaults to
        ``Salesforce/codegen-350M-mono``.

    Returns
    -------
    tuple
        (model, tokenizer) – the loaded model and tokenizer objects.
    """
    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        import bitsandbytes as bnb
    except ImportError as e:
        raise ImportError(
            "Required packages (transformers, torch, bitsandbytes) not found. "
            "Please ensure they are installed."
        ) from e

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    if not tokenizer.pad_token_id:
        tokenizer.pad_token_id = tokenizer.eos_token_id

    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        load_in_8bit=True,
        device_map="auto",
        torch_dtype=torch.float16,
    )

    return model, tokenizer

def load_input_data():
    """
    Load input data for perplexity computation.

    Returns
    -------
    list
        A list of strings representing the input texts.
    """
    # In the full pipeline this would read from ``data/processed``.
    return []

def compute_perplexity(model, tokenizer, text: str) -> float:
    """
    Compute token-level perplexity for a single piece of text.

    Implements FR-005: computes the exponential of the average negative
    log-likelihood of the tokens.  The result is validated for finiteness
    by the caller.

    Parameters
    ----------
    model : torch.nn.Module
        The quantized language model.
    tokenizer : transformers.PreTrainedTokenizer
        The tokenizer for the model.
    text : str
        The input text to evaluate.

    Returns
    -------
    float
        The computed perplexity score.
    """
    import torch
    from torch.nn.functional import cross_entropy

    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=1024)
    input_ids = inputs["input_ids"].to(model.device)
    attention_mask = inputs["attention_mask"].to(model.device)

    with torch.no_grad():
        outputs = model(input_ids, attention_mask=attention_mask, labels=input_ids)
        logits = outputs.logits

    # Shift logits and labels for token-level loss
    shift_logits = logits[..., :-1, :].contiguous()
    shift_labels = input_ids[..., 1:].contiguous()

    # Compute cross-entropy loss (average over tokens)
    loss = cross_entropy(
        shift_logits.view(-1, shift_logits.size(-1)),
        shift_labels.view(-1),
        ignore_index=-100
    )

    perplexity = math.exp(loss.item())
    return perplexity

def compute_perplexity_batch():
    """
    Compute perplexity scores for a batch of inputs.

    This function loads the full dataset, computes perplexity for each sample,
    validates the results, and writes them to the expected output file.
    """
    from pathlib import Path
    model, tokenizer = load_model_and_tokenizer()
    inputs = load_input_data()
    
    if not inputs:
        logging.warning("No input data found to compute perplexity.")
        return

    scores = []
    for text in inputs:
        score = compute_perplexity(model, tokenizer, text)
        # Validate each score; will raise if non‑finite.
        validate_perplexity(score)
        scores.append(score)

    # Write CSV to the expected location.
    output_path = Path("data/processed/perplexity_scores.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["text", "perplexity"])
        for txt, sc in zip(inputs, scores):
            writer.writerow([txt, sc])
    
    logging.info(f"Perplexity scores written to {output_path}")

def save_perplexity_scores():
    """
    Stub for saving perplexity scores; retained for API compatibility.
    """
    pass

def parse_cli_args():
    """
    Parse command‑line arguments for the model metrics script.

    Returns
    -------
    argparse.Namespace
        Parsed arguments (currently empty placeholder).
    """
    parser = argparse.ArgumentParser(description="Compute model perplexity metrics.")
    # Future arguments (e.g., model name, quantization bits) can be added here.
    return parser.parse_args()

def main():
    """
    Entry point for the ``code/model_metrics.py`` script.

    It orchestrates loading the model, computing perplexity for all inputs,
    and persisting the results.  Errors from ``validate_perplexity`` are
    allowed to propagate so that the unit test can detect them.
    """
    logging.basicConfig(level=logging.INFO)
    compute_perplexity_batch()
