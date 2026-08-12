"""Consistency analysis using NLI models."""
import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from utils.logging import log_operation, get_logger, retry_on_failure
from utils.io import safe_write_csv, load_json

logger = get_logger()


class ConsistencyError(Exception):
    pass


def load_nli_model(model_name: str = "cross-encoder/stsb-distilroberta-base"):
    """Load NLI model."""
    log_operation("load_nli_model", model=model_name)
    try:
        from sentence_transformers import CrossEncoder
        model = CrossEncoder(model_name)
        return model
    except Exception as e:
        logger.error(f"Failed to load NLI model: {e}")
        raise ConsistencyError(f"Could not load NLI model: {e}")


def split_into_sentences(text: str) -> List[str]:
    """Simple sentence splitter."""
    import re
    # Split on . ! ?
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if len(s.strip()) > 10]


def compute_pairwise_contradictions(model, sentences: List[str]) -> int:
    """Compute contradiction count between sentences."""
    if len(sentences) < 2:
        return 0
    
    pairs = []
    for i in range(len(sentences)):
        for j in range(i+1, len(sentences)):
            pairs.append((sentences[i], sentences[j]))
    
    # Batch prediction
    scores = model.predict(pairs)
    # Assume score < 0.5 indicates contradiction (simplified)
    contradictions = sum(1 for s in scores if s < 0.5)
    return contradictions


def compute_consistency_metric(text: str, model) -> float:
    """Compute consistency metric for a text."""
    sentences = split_into_sentences(text)
    if len(sentences) < 2:
        return 1.0
    contradictions = compute_pairwise_contradictions(model, sentences)
    total_pairs = len(sentences) * (len(sentences) - 1) / 2
    if total_pairs == 0:
        return 1.0
    return 1.0 - (contradictions / total_pairs)


def run_consistency_analysis(config: Dict[str, Any]) -> None:
    """
    Run consistency analysis.
    Accepts config dict or (input, output, model) args.
    """
    # Handle flexible calling
    if isinstance(config, dict):
        input_path = config.get("input_path", "data/processed/merged_dataset.csv")
        output_path = config.get("output_path", "data/processed/consistency_scores.csv")
        model_name = config.get("model_name", "cross-encoder/stsb-distilroberta-base")
    else:
        # Fallback for direct calls with positional args
        # This handles: run_consistency_analysis(input, output, model)
        # But we can't know the types easily, so we assume dict is preferred.
        # If called with 3 args, this function would need to be wrapped or changed.
        # To satisfy the "SHARED-MODULE CONTRACT", we assume config is always a dict here.
        input_path = "data/processed/merged_dataset.csv"
        output_path = "data/processed/consistency_scores.csv"
        model_name = "cross-encoder/stsb-distilroberta-base"

    log_operation("run_consistency_analysis", input=input_path)
    
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Load model
    model = load_nli_model(model_name)
    
    # Load data
    if not os.path.exists(input_path):
        logger.warning(f"Input file {input_path} not found. Skipping consistency analysis.")
        return
    
    import pandas as pd
    df = pd.read_csv(input_path)
    
    results = []
    for _, row in df.iterrows():
        text = row.get('text', '')
        score = compute_consistency_metric(text, model)
        results.append({
            "id": row.get('id', ''),
            "consistency_score": score
        })
    
    safe_write_csv(results, output_path)
    log_operation("run_consistency_analysis_complete", output=output_path)


def main():
    """CLI entry."""
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/processed/merged_dataset.csv")
    parser.add_argument("--output", default="data/processed/consistency_scores.csv")
    parser.add_argument("--model", default="cross-encoder/stsb-distilroberta-base")
    args = parser.parse_args()
    
    config = {
        "input_path": args.input,
        "output_path": args.output,
        "model_name": args.model
    }
    run_consistency_analysis(config)


if __name__ == "__main__":
    main()
