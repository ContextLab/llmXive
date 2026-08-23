"""Semantic Stability Analysis for Phenomenological Reports.

Computes embeddings for repeated generations of the same prompt/strategy,
calculates cosine similarity between pairs, and aggregates stability scores.
"""
from __future__ import annotations

import json
import logging
import os
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from sentence_transformers import SentenceTransformer

# Import shared logging utility
from code.utils.logging import get_logger, log_operation

logger = get_logger("stability_analysis")


class StabilityError(Exception):
    """Custom exception for stability analysis failures."""
    pass


def load_embedding_model(model_name: str = "all-MiniLM-L6-v2") -> SentenceTransformer:
    """Load a CPU-safe sentence transformer model.

    Args:
        model_name: HuggingFace model identifier.

    Returns:
        Loaded SentenceTransformer instance.
    """
    log_operation("load_embedding_model", model=model_name)
    try:
        # This model is small (~80MB) and CPU-safe
        model = SentenceTransformer(model_name)
        logger.info(f"Loaded embedding model: {model_name}")
        return model
    except Exception as e:
        raise StabilityError(f"Failed to load embedding model {model_name}: {e}")


def compute_embeddings(
    texts: List[str], model: SentenceTransformer, batch_size: int = 32
) -> np.ndarray:
    """Compute embeddings for a list of texts.

    Args:
        texts: List of text strings.
        model: Loaded SentenceTransformer model.
        batch_size: Number of texts to process in parallel.

    Returns:
        Numpy array of shape (len(texts), embedding_dim).
    """
    log_operation("compute_embeddings", count=len(texts), batch_size=batch_size)
    if not texts:
        return np.array([])
    try:
        embeddings = model.encode(texts, batch_size=batch_size, show_progress_bar=False)
        return np.array(embeddings)
    except Exception as e:
        raise StabilityError(f"Failed to compute embeddings: {e}")


def compute_cosine_similarity(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
    """Compute cosine similarity between two vectors.

    Args:
        vec_a: First vector.
        vec_b: Second vector.

    Returns:
        Cosine similarity score (float between -1 and 1).
    """
    if vec_a.shape != vec_b.shape:
        raise ValueError(f"Vector shapes mismatch: {vec_a.shape} vs {vec_b.shape}")

    norm_a = np.linalg.norm(vec_a)
    norm_b = np.linalg.norm(vec_b)

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return float(np.dot(vec_a, vec_b) / (norm_a * norm_b))


def group_generations_by_condition(
    data: List[Dict[str, Any]]
) -> Dict[Tuple[str, str], List[Dict[str, Any]]]:
    """Group generation results by (prompt_id, strategy).

    Args:
        data: List of generation records containing 'prompt_id', 'strategy', 'text'.

    Returns:
        Dictionary mapping (prompt_id, strategy) to list of records.
    """
    groups: Dict[Tuple[str, str], List[Dict[str, Any]]] = {}
    for record in data:
        prompt_id = record.get("prompt_id", "unknown")
        strategy = record.get("strategy", "unknown")
        key = (prompt_id, strategy)
        if key not in groups:
            groups[key] = []
        groups[key].append(record)
    return groups


def compute_stability_scores(
    groups: Dict[Tuple[str, str], List[Dict[str, Any]]],
    embeddings: Dict[Tuple[str, str], np.ndarray],
) -> List[Dict[str, Any]]:
    """Compute pairwise cosine similarities and aggregate stability scores.

    For each group (prompt, strategy), compute the mean cosine similarity
    of all pairs. If a group has < 2 samples, stability is NaN.

    Args:
        groups: Grouped generation data.
        embeddings: Pre-computed embeddings keyed by (prompt_id, strategy).

    Returns:
        List of stability records: {prompt_id, strategy, mean_similarity, count, std_similarity}.
    """
    results = []
    for (prompt_id, strategy), records in groups.items():
        if len(records) < 2:
            results.append({
                "prompt_id": prompt_id,
                "strategy": strategy,
                "mean_similarity": float('nan'),
                "std_similarity": float('nan'),
                "count": len(records),
                "n_pairs": 0,
            })
            continue

        vecs = embeddings.get((prompt_id, strategy))
        if vecs is None or len(vecs) != len(records):
            logger.warning(f"Embedding mismatch for {prompt_id}/{strategy}: {len(records)} vs {vecs.shape[0] if vecs is not None else 0}")
            continue

        similarities = []
        n = len(vecs)
        for i in range(n):
            for j in range(i + 1, n):
                sim = compute_cosine_similarity(vecs[i], vecs[j])
                similarities.append(sim)

        if not similarities:
            results.append({
                "prompt_id": prompt_id,
                "strategy": strategy,
                "mean_similarity": float('nan'),
                "std_similarity": float('nan'),
                "count": n,
                "n_pairs": 0,
            })
            continue

        mean_sim = float(np.mean(similarities))
        std_sim = float(np.std(similarities))
        results.append({
            "prompt_id": prompt_id,
            "strategy": strategy,
            "mean_similarity": mean_sim,
            "std_similarity": std_sim,
            "count": n,
            "n_pairs": len(similarities),
        })

    return results


def run_stability_analysis(
    input_path: str,
    output_path: str,
    model_name: str = "all-MiniLM-L6-v2",
    batch_size: int = 32,
) -> None:
    """Orchestrate the full stability analysis pipeline.

    1. Load generation data from input JSON.
    2. Group by (prompt_id, strategy).
    3. Compute embeddings for all texts.
    4. Compute pairwise cosine similarities.
    5. Aggregate and write results to output JSON.

    Args:
        input_path: Path to input JSON containing generation records.
        output_path: Path to write stability scores JSON.
        model_name: Sentence transformer model to use.
        batch_size: Batch size for encoding.
    """
    log_operation("run_stability_analysis", input=input_path, output=output_path)

    # Load data
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if not isinstance(data, list):
        data = [data]

    logger.info(f"Loaded {len(data)} generation records")

    # Group data
    groups = group_generations_by_condition(data)
    logger.info(f"Grouped into {len(groups)} unique (prompt, strategy) conditions")

    # Compute embeddings
    all_texts = []
    text_map: Dict[Tuple[int, int], str] = {}  # (group_idx, text_idx) -> text
    group_indices: List[Tuple[str, str]] = list(groups.keys())

    for group_idx, (pid, strat) in enumerate(group_indices):
        for text_idx, rec in enumerate(groups[(pid, strat)]):
            text = rec.get("text", "")
            if not text:
                continue
            all_texts.append(text)
            text_map[(group_idx, text_idx)] = text

    if not all_texts:
        logger.warning("No valid texts found for embedding.")
        # Write empty result
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump([], f, indent=2)
        return

    logger.info(f"Computing embeddings for {len(all_texts)} texts...")
    model = load_embedding_model(model_name)
    embeddings_all = compute_embeddings(all_texts, model, batch_size)

    # Map embeddings back to groups
    group_embeddings: Dict[Tuple[str, str], np.ndarray] = {}
    for group_idx, (pid, strat) in enumerate(group_indices):
        texts_in_group = groups[(pid, strat)]
        valid_indices = []
        for text_idx in range(len(texts_in_group)):
            if (group_idx, text_idx) in text_map:
                valid_indices.append(text_idx)

        if not valid_indices:
            continue

        group_vecs = embeddings_all[[
            all_texts.index(text_map[(group_idx, t)]) for t in valid_indices
        ]]
        # Actually, simpler: we just need to slice the flat embeddings array
        # We need to track which indices in all_texts belong to which group
        pass

    # Re-do mapping more simply
    # Flatten with group info
    flat_data = []
    for group_idx, (pid, strat) in enumerate(group_indices):
        for text_idx, rec in enumerate(groups[(pid, strat)]):
            text = rec.get("text", "")
            if text:
                flat_data.append({
                    "group_idx": group_idx,
                    "group_key": (pid, strat),
                    "text": text,
                })

    if not flat_data:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump([], f, indent=2)
        return

    flat_texts = [d["text"] for d in flat_data]
    logger.info(f"Re-computing embeddings for {len(flat_texts)} texts...")
    embeddings_flat = compute_embeddings(flat_texts, model, batch_size)

    # Re-group embeddings
    group_embeddings = {}
    for g_key in group_indices:
        group_embeddings[g_key] = []

    for i, d in enumerate(flat_data):
        group_embeddings[d["group_key"]].append(embeddings_flat[i])

    for k in group_embeddings:
        if group_embeddings[k]:
            group_embeddings[k] = np.array(group_embeddings[k])

    # Compute scores
    scores = compute_stability_scores(groups, group_embeddings)

    # Write output
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(scores, f, indent=2)

    logger.info(f"Wrote stability scores to {output_path}")


def main() -> None:
    """CLI entry point for stability analysis."""
    import argparse

    parser = argparse.ArgumentParser(description="Compute semantic stability scores.")
    parser.add_argument("--input", required=True, help="Path to input JSON (generation data).")
    parser.add_argument("--output", required=True, help="Path to output JSON (stability scores).")
    parser.add_argument("--model", default="all-MiniLM-L6-v2", help="Sentence transformer model.")
    parser.add_argument("--batch", type=int, default=32, help="Batch size for encoding.")

    args = parser.parse_args()

    try:
        run_stability_analysis(
            input_path=args.input,
            output_path=args.output,
            model_name=args.model,
            batch_size=args.batch,
        )
        log_operation("stability_analysis_complete", output=args.output)
    except Exception as e:
        log_operation("stability_analysis_failed", error=str(e))
        raise


if __name__ == "__main__":
    main()
