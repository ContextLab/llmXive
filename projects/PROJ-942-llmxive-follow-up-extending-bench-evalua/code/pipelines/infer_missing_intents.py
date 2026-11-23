"""
infer_missing_intents.py

Deterministic intent inference for missing ground‑truth intents.

This script reads a normalized CSV of π‑Bench interaction turns, identifies
turns where ``ground_truth_intent`` is missing, and uses a small deterministic
language model (google/flan‑t5‑small) to infer an intent label.  The inference
is fully deterministic:

* Fixed random seed (torch.manual_seed(42))
* Greedy decoding (do_sample=False)
* No stochastic sampling parameters

The output CSV contains one row per inferred intent with columns:
  - task_id
  - turn_index
  - inferred_intent
  - confidence (float in [0, 1]; set to 1.0 for deterministic output)

Running the script twice must produce identical CSV output, which is
enforced by sorting the rows by ``task_id`` and ``turn_index`` and by using
a deterministic model.
"""

import argparse
import logging
from pathlib import Path
from typing import List

import pandas as pd
import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer, pipeline

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _load_data(csv_path: Path) -> pd.DataFrame:
    """Load the normalized traces CSV."""
    if not csv_path.is_file():
        raise FileNotFoundError(f"Input CSV not found: {csv_path}")
    df = pd.read_csv(csv_path, dtype=str)
    # Ensure required columns exist
    required = {"task_id", "turn_index", "utterance", "ground_truth_intent"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns in {csv_path}: {missing}")
    return df

def _filter_missing_intents(df: pd.DataFrame) -> pd.DataFrame:
    """Return rows where ground_truth_intent is missing/NaN/empty."""
    # Treat empty strings and NaN as missing
    mask = df["ground_truth_intent"].isna() | (df["ground_truth_intent"].str.strip() == "")
    missing_df = df[mask].copy()
    if missing_df.empty:
        log.info("No missing ground_truth_intent entries found.")
    return missing_df

def _setup_deterministic_llm(model_name: str = "google/flan-t5-small") -> pipeline:
    """
    Load the model and tokenizer and return a text‑generation pipeline
    configured for deterministic (greedy) output.
    """
    # Set deterministic torch seeds
    torch.manual_seed(42)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

    # The pipeline will use the model and tokenizer; we explicitly set
    # do_sample=False to force greedy decoding.
    gen_pipe = pipeline(
        "text2text-generation",
        model=model,
        tokenizer=tokenizer,
        device=-1,  # CPU‑only
        clean_up_tokenization_spaces=True,
    )
    return gen_pipe

def _infer_intent(pipe: pipeline, utterance: str) -> str:
    """
    Generate an intent label for a single utterance.

    The prompt is deliberately simple to keep the inference deterministic
    and fast.  The model is expected to output a short phrase describing the
    intent.
    """
    prompt = f"Extract the user intent from the following utterance: \"{utterance}\""
    # Greedy decoding (no sampling)
    result = pipe(
        prompt,
        max_length=32,
        num_beams=1,
        do_sample=False,
        early_stopping=True,
    )
    # result is a list of dicts with key 'generated_text'
    generated = result[0]["generated_text"]
    # Clean up whitespace and line breaks
    intent = generated.strip()
    return intent

def _run_inference(df_missing: pd.DataFrame, pipe: pipeline) -> pd.DataFrame:
    """
    Perform deterministic inference on each missing turn.

    Returns a DataFrame with columns:
        task_id, turn_index, inferred_intent, confidence
    Confidence is set to 1.0 for all deterministic outputs.
    """
    records: List[dict] = []
    for _, row in df_missing.iterrows():
        task_id = row["task_id"]
        turn_index = int(row["turn_index"])
        utterance = row["utterance"] or ""
        inferred = _infer_intent(pipe, utterance)
        records.append(
            {
                "task_id": task_id,
                "turn_index": turn_index,
                "inferred_intent": inferred,
                "confidence": 1.0,
            }
        )
    inferred_df = pd.DataFrame(records)
    # Ensure deterministic ordering
    inferred_df.sort_values(by=["task_id", "turn_index"], inplace=True)
    inferred_df.reset_index(drop=True, inplace=True)
    return inferred_df

# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Deterministic intent inference for missing ground‑truth intents."
    )
    parser.add_argument(
        "--input-csv",
        type=str,
        required=True,
        help="Path to the normalized traces CSV (output of parse_traces).",
    )
    parser.add_argument(
        "--out-csv",
        type=str,
        required=True,
        help="Path where the inferred intents CSV will be written.",
    )
    args = parser.parse_args()

    input_path = Path(args.input_csv)
    out_path = Path(args.out_csv)

    log.info(f"Loading normalized traces from {input_path}")
    df = _load_data(input_path)

    log.info("Filtering turns with missing ground_truth_intent")
    df_missing = _filter_missing_intents(df)

    if df_missing.empty:
        # Still create an empty CSV with the correct header for downstream scripts
        out_path.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(
            columns=["task_id", "turn_index", "inferred_intent", "confidence"]
        ).to_csv(out_path, index=False)
        log.info(f"No missing intents – wrote empty file to {out_path}")
        return

    log.info(f"Running deterministic LLM on {len(df_missing)} missing turns")
    pipe = _setup_deterministic_llm()

    inferred_df = _run_inference(df_missing, pipe)

    # Write output
    out_path.parent.mkdir(parents=True, exist_ok=True)
    inferred_df.to_csv(out_path, index=False)
    log.info(f"Wrote inferred intents to {out_path}")

if __name__ == "__main__":
    # Configure a simple console logger if the toolkit logger is not already set up
    logging.basicConfig(level=logging.INFO)
    main()
