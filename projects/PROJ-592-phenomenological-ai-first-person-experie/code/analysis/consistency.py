"""Consistency analysis using NLI models."""
import os
import json
import logging
import warnings
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from utils.logging import log_operation, get_logger, retry_on_failure
from utils.io import safe_write_csv, load_json

logger = get_logger()


class ConsistencyError(Exception):
    """Custom exception for consistency analysis errors."""
    pass


def load_nli_model(model_name: str = "cross-encoder/stsb-distilroberta-base"):
    """Load NLI model for contradiction detection.

    Args:
        model_name: Name of the CrossEncoder model to load.

    Returns:
        Loaded CrossEncoder model instance.

    Raises:
        ConsistencyError: If model loading fails.
    """
    log_operation("load_nli_model", model=model_name)
    try:
        # Import here to avoid heavy dependency if not needed
        from sentence_transformers import CrossEncoder
        model = CrossEncoder(model_name)
        log_operation("load_nli_model_complete", model=model_name, status="success")
        return model
    except Exception as e:
        logger.error(f"Failed to load NLI model: {e}")
        raise ConsistencyError(f"Could not load NLI model: {e}")


def split_into_sentences(text: str) -> List[str]:
    """Split text into sentences using regex.

    Args:
        text: Input text to split.

    Returns:
        List of sentence strings.
    """
    import re
    # Split on . ! ? followed by whitespace or end of string
    # Filter out empty strings and very short fragments
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if len(s.strip()) > 10]


def compute_pairwise_contradictions(model, sentences: List[str]) -> int:
    """Compute contradiction count between sentence pairs.

    Uses the NLI model to score pairs. Scores < 0.5 are treated as contradictions.
    Skips pairs that exceed model length limits with a warning.

    Args:
        model: Loaded CrossEncoder model.
        sentences: List of sentences to compare.

    Returns:
        Count of contradictory pairs.
    """
    if len(sentences) < 2:
        return 0

    pairs = []
    for i in range(len(sentences)):
        for j in range(i+1, len(sentences)):
            pairs.append((sentences[i], sentences[j]))

    if not pairs:
        return 0

    # Process in batches to handle potential length issues
    # CrossEncoder.predict handles batching internally, but we wrap in try/except for length limits
    try:
        scores = model.predict(pairs)
    except Exception as e:
        # Log warning for length limit or other processing errors
        warnings.warn(f"Error processing sentence pairs: {e}. Skipping this batch.")
        log_operation("compute_pairwise_contradictions_warning", error=str(e))
        return 0

    # Assume score < 0.5 indicates contradiction (simplified heuristic)
    # In a real NLI setup, we might map specific labels (contradiction, entailment, neutral)
    contradictions = sum(1 for s in scores if s < 0.5)
    return contradictions


def compute_consistency_metric(text: str, model) -> float:
    """Compute consistency metric for a single text.

    Metric = 1 - (contradiction_count / total_pairs)
    Returns 1.0 if fewer than 2 sentences or no pairs.

    Args:
        text: The text to analyze.
        model: Loaded NLI model.

    Returns:
        Consistency score between 0.0 and 1.0.
    """
    sentences = split_into_sentences(text)
    if len(sentences) < 2:
        return 1.0

    contradictions = compute_pairwise_contradictions(model, sentences)
    total_pairs = len(sentences) * (len(sentences) - 1) / 2

    if total_pairs == 0:
        return 1.0

    return 1.0 - (contradictions / total_pairs)


def run_consistency_analysis(config: Dict[str, Any]) -> None:
    """Run consistency analysis on a dataset.

    Accepts a config dict with:
      - input_path: Path to input CSV (default: data/processed/merged_dataset.csv)
      - output_path: Path to output CSV (default: data/processed/consistency_scores.csv)
      - model_name: NLI model name (default: cross-encoder/stsb-distilroberta-base)

    Args:
        config: Configuration dictionary.

    Raises:
        ConsistencyError: If analysis fails critically.
    """
    # Handle flexible calling: dict or positional args (legacy)
    if isinstance(config, dict):
        input_path = config.get("input_path", "data/processed/merged_dataset.csv")
        output_path = config.get("output_path", "data/processed/consistency_scores.csv")
        model_name = config.get("model_name", "cross-encoder/stsb-distilroberta-base")
    else:
        # Fallback for direct calls with positional args (legacy support)
        # Assuming: run_consistency_analysis(input, output, model)
        input_path = str(config) if config else "data/processed/merged_dataset.csv"
        output_path = "data/processed/consistency_scores.csv"
        model_name = "cross-encoder/stsb-distilroberta-base"

    log_operation("run_consistency_analysis", input=input_path, model=model_name)

    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    # Load model
    model = load_nli_model(model_name)

    # Load data
    if not os.path.exists(input_path):
        logger.warning(f"Input file {input_path} not found. Skipping consistency analysis.")
        # Create empty output file to indicate completion (with no data)
        safe_write_csv([], output_path)
        return

    import pandas as pd
    try:
        df = pd.read_csv(input_path)
    except Exception as e:
        logger.error(f"Failed to load input file {input_path}: {e}")
        raise ConsistencyError(f"Could not load input data: {e}")

    if df.empty or 'text' not in df.columns:
        logger.warning("Input file is empty or lacks 'text' column.")
        safe_write_csv([], output_path)
        return

    results = []
    for idx, row in df.iterrows():
        text = row.get('text', '')
        if not text or not isinstance(text, str):
            logger.warning(f"Skipping row {idx}: invalid text.")
            continue

        try:
            score = compute_consistency_metric(text, model)
            results.append({
                "id": row.get('id', f"row_{idx}"),
                "consistency_score": score
            })
        except Exception as e:
            logger.error(f"Error processing row {idx}: {e}")
            # Continue processing other rows
            continue

    safe_write_csv(results, output_path)
    log_operation("run_consistency_analysis_complete", output=output_path, count=len(results))


def main():
    """CLI entry point for consistency analysis."""
    import argparse
    parser = argparse.ArgumentParser(description="Run consistency analysis on generated reports.")
    parser.add_argument("--input", default="data/processed/merged_dataset.csv", help="Input CSV path")
    parser.add_argument("--output", default="data/processed/consistency_scores.csv", help="Output CSV path")
    parser.add_argument("--model", default="cross-encoder/stsb-distilroberta-base", help="NLI model name")
    args = parser.parse_args()

    config = {
        "input_path": args.input,
        "output_path": args.output,
        "model_name": args.model
    }
    run_consistency_analysis(config)


if __name__ == "__main__":
    main()
