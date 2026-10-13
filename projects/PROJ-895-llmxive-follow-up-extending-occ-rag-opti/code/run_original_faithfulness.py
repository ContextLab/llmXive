"""
Run inference on the original (unpruned) OCC-RAG-1.7B model and compute per-sample
faithfulness scores. The results are written to
`data/processed/original_faithfulness_scores.csv`.

This script is intended to be invoked as part of the quickstart pipeline
before statistical validation.
"""

import os
import csv
from llmxive_toolkit import paths, get_logger

# Config utilities
from code_00_config import Config, validate_config

# Dataset loader utilities
from utils.dataset_loader import load_and_cache_dataset

# Model loading utilities (layer‑wise, CPU‑only)
from utils.masking import load_model_layer_by_layer

# Faithfulness scoring utilities
from utils.faithfulness_score import compute_batch_faithfulness

log = get_logger(__name__)


def main():
    """
    Main entry point:
    1. Load configuration and validate it.
    2. Load the raw synthetic corpus (held‑out test set).
    3. Load a fresh copy of the frozen OCC‑RAG‑1.7B model.
    4. Iterate over samples with batch size = 1, compute faithfulness,
       and write results to CSV.
    """
    # ------------------------------------------------------------------
    # 1. Configuration
    # ------------------------------------------------------------------
    config = Config()
    validate_config(config)

    # ------------------------------------------------------------------
    # 2. Load dataset
    # ------------------------------------------------------------------
    raw_corpus_path = os.path.join("data", "raw", "occ_rag_corpus.jsonl")
    if not os.path.exists(raw_corpus_path):
        raise FileNotFoundError(
            f"Dataset not found at expected location: {raw_corpus_path}. "
            "Please ensure the synthetic corpus has been downloaded "
            "and placed in `data/raw/`."
        )

    # `load_and_cache_dataset` returns a list of dictionaries representing samples.
    # The function is designed to read a local JSONL file and return the parsed
    # objects; it will raise if the file cannot be read.
    dataset = load_and_cache_dataset(raw_corpus_path)

    if not isinstance(dataset, list):
        raise TypeError(
            f"Expected dataset to be a list of samples, got {type(dataset)}."
        )

    log.info(f"Loaded {len(dataset)} samples from the raw corpus.")

    # ------------------------------------------------------------------
    # 3. Load fresh model
    # ------------------------------------------------------------------
    # The configuration's MODEL_ID is a placeholder; the task explicitly
    # requires loading the OCC‑RAG‑1.7B frozen checkpoint.
    model_id = "nlp4research/occ-rag-1.7b-frozen"
    log.info(f"Loading fresh OCC‑RAG‑1.7B model from '{model_id}'.")
    model = load_model_layer_by_layer(model_id)

    if model is None:
        raise RuntimeError("Failed to load the OCC‑RAG model.")

    # ------------------------------------------------------------------
    # 4. Compute faithfulness per sample
    # ------------------------------------------------------------------
    output_path = paths.data("processed", "original_faithfulness_scores.csv")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(
            csvfile, fieldnames=["sample_id", "faithfulness_score"]
        )
        writer.writeheader()

        for idx, sample in enumerate(dataset):
            # Use the sample's own identifier if present; otherwise fall back to index.
            sample_id = sample.get("sample_id") or sample.get("id") or str(idx)

            # The scoring utility expects a list of samples; we pass a single‑item list
            # to respect the required batch size of 1.
            try:
                batch_score = compute_batch_faithfulness(model, [sample])
            except Exception as e:
                log.error(f"Faithfulness scoring failed for sample {sample_id}: {e}")
                raise

            # `compute_batch_faithfulness` returns a list of scores matching the batch.
            if not batch_score:
                raise RuntimeError(
                    f"No faithfulness score returned for sample {sample_id}."
                )
            faithfulness_score = float(batch_score[0])

            writer.writerow(
                {"sample_id": sample_id, "faithfulness_score": faithfulness_score}
            )

            if (idx + 1) % 100 == 0:
                log.info(f"Processed {idx + 1} samples...")

    log.info(
        f"Original model faithfulness scores written to '{output_path}'."
    )


if __name__ == "__main__":
    main()
