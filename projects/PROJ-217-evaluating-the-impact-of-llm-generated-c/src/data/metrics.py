"""
src/data/metrics.py

Compute readability metrics for each comment condition (LLM‐generated, human, none).

This script reads ``data/llm_comments.jsonl`` which contains, for each snippet,
the original source code, the human docstring, the LLM‑generated comment and an
empty string for the no‑comment baseline.  For every snippet three rows are
written to ``data/readability_metrics.csv`` – one per condition – with the
following columns:

    snippet_id
    condition               # "llm", "human", "none"
    code
    human_comment
    llm_comment
    no_comment
    BLEU_vs_source
    BLEU_vs_human
    ROUGE_L_vs_source
    ROUGE_L_vs_human
    Semantic_Similarity_vs_source
    Semantic_Similarity_vs_human
    Comment_Length
    Flesch_Kincaid_Grade

All metric values are normalised to the range [0, 1]; for the ``none`` condition
the metric fields are ``null`` (written as empty cells in the CSV), the comment
length is ``0`` and the Flesch‑Kincaid grade is ``0``.
"""

import csv
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional

import numpy as np
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
from rouge_score import rouge_scorer
from sentence_transformers import SentenceTransformer
from textstat import flesch_kincaid_grade

from llmxive_toolkit import paths, get_logger

# --------------------------------------------------------------------------- #
# Logging
# --------------------------------------------------------------------------- #
log = get_logger(__name__)

# --------------------------------------------------------------------------- #
# Helper functions
# --------------------------------------------------------------------------- #

def _load_llm_comments() -> List[Dict]:
    """Load ``data/llm_comments.jsonl`` and return a list of records."""
    in_path = paths.data("llm_comments.jsonl")
    if not in_path.is_file():
        raise FileNotFoundError(f"LLM comments file not found: {in_path}")
    records = []
    with in_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records

def _tokenize(text: str) -> List[str]:
    """Very light tokenisation – split on whitespace."""
    return text.split()

def _bleu(candidate: str, reference: str) -> float:
    """BLEU score (0‑1) between ``candidate`` and ``reference``."""
    if not candidate or not reference:
        return 0.0
    cand_tokens = _tokenize(candidate)
    ref_tokens = _tokenize(reference)
    # Smoothing to avoid zero scores for very short texts.
    smoothing = SmoothingFunction().method1
    return float(
        sentence_bleu([ref_tokens], cand_tokens, smoothing_function=smoothing)
    )

def _rouge_l(candidate: str, reference: str) -> float:
    """ROUGE‑L F‑measure (0‑1) between ``candidate`` and ``reference``."""
    if not candidate or not reference:
        return 0.0
    scorer = rouge_scorer.RougeScorer(["rougeL"], use_stemmer=True)
    scores = scorer.score(reference, candidate)
    return scores["rougeL"].fmeasure

def _load_sentence_transformer() -> SentenceTransformer:
    """
    Load the primary Sentence‑BERT model, falling back to a smaller model on
    OOM or any other exception. The chosen model is cached for the script run.
    """
    primary = "sentence-transformers/multi-qa-mpnet-base-dot-v1"
    fallback = "sentence-transformers/all-MiniLM-L6-v2"
    try:
        log.info(f"Loading primary embedding model: {primary}")
        model = SentenceTransformer(primary)
        # A quick forward pass to provoke OOM early (if it will happen).
        _ = model.encode(["test"], convert_to_numpy=True)
        return model
    except Exception as e:
        log.warning(
            f"Failed to load primary model ({primary}): {e}. "
            f"Falling back to smaller model {fallback}."
        )
        fallback_model = SentenceTransformer(fallback)
        return fallback_model

def _cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """Cosine similarity scaled to [0, 1]."""
    if vec1.shape != vec2.shape:
        raise ValueError("Embedding vectors must have the same shape")
    dot = np.dot(vec1, vec2)
    norm = np.linalg.norm(vec1) * np.linalg.norm(vec2)
    if norm == 0:
        return 0.0
    cosine = dot / norm
    # Scale from [-1, 1] to [0, 1]
    return float((cosine + 1.0) / 2.0)

# --------------------------------------------------------------------------- #
# Main processing
# --------------------------------------------------------------------------- #

def main() -> None:
    """
    Entry‑point for ``python -m src.data.metrics``.

    The function streams the input JSON‑Lines file, computes the required
    metrics for each condition and writes a CSV with one row per
    ``(snippet_id, condition)``.
    """
    records = _load_llm_comments()
    if not records:
        log.warning("No records found in llm_comments.jsonl – an empty CSV will be written.")
    out_path = paths.data("readability_metrics.csv")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Prepare the embedding model once.
    embedder = _load_sentence_transformer()

    # CSV header according to the contract.
    header = [
        "snippet_id",
        "condition",
        "code",
        "human_comment",
        "llm_comment",
        "no_comment",
        "BLEU_vs_source",
        "BLEU_vs_human",
        "ROUGE_L_vs_source",
        "ROUGE_L_vs_human",
        "Semantic_Similarity_vs_source",
        "Semantic_Similarity_vs_human",
        "Comment_Length",
        "Flesch_Kincaid_Grade",
    ]

    with out_path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=header)
        writer.writeheader()

        for rec in records:
            snippet_id = rec.get("snippet_id")
            code = rec.get("code", "")
            human_comment = rec.get("human_comment", "")
            llm_comment = rec.get("llm_comment", "")
            no_comment = rec.get("no_comment", "")

            # Pre‑compute embeddings for the two references once.
            code_emb = embedder.encode([code], convert_to_numpy=True)[0]
            human_emb = embedder.encode([human_comment], convert_to_numpy=True)[0]

            # Helper to compute all metrics for a given comment.
            def compute_metrics(comment: str) -> Dict[str, Optional[float]]:
                if comment == "":
                    # No‑comment baseline – metrics are null.
                    return {
                        "BLEU_vs_source": None,
                        "BLEU_vs_human": None,
                        "ROUGE_L_vs_source": None,
                        "ROUGE_L_vs_human": None,
                        "Semantic_Similarity_vs_source": None,
                        "Semantic_Similarity_vs_human": None,
                    }
                # BLEU
                bleu_src = _bleu(comment, code)
                bleu_hum = _bleu(comment, human_comment)

                # ROUGE‑L
                rouge_src = _rouge_l(comment, code)
                rouge_hum = _rouge_l(comment, human_comment)

                # Semantic similarity
                comment_emb = embedder.encode([comment], convert_to_numpy=True)[0]
                sim_src = _cosine_similarity(comment_emb, code_emb)
                sim_hum = _cosine_similarity(comment_emb, human_emb)

                return {
                    "BLEU_vs_source": bleu_src,
                    "BLEU_vs_human": bleu_hum,
                    "ROUGE_L_vs_source": rouge_src,
                    "ROUGE_L_vs_human": rouge_hum,
                    "Semantic_Similarity_vs_source": sim_src,
                    "Semantic_Similarity_vs_human": sim_hum,
                }

            # ------------------------------------------------------------------- #
            # Condition: LLM
            # ------------------------------------------------------------------- #
            llm_metrics = compute_metrics(llm_comment)
            writer.writerow(
                {
                    "snippet_id": snippet_id,
                    "condition": "llm",
                    "code": code,
                    "human_comment": human_comment,
                    "llm_comment": llm_comment,
                    "no_comment": no_comment,
                    **llm_metrics,
                    "Comment_Length": len(llm_comment),
                    "Flesch_Kincaid_Grade": flesch_kincaid_grade(llm_comment)
                    if llm_comment
                    else 0,
                }
            )

            # ------------------------------------------------------------------- #
            # Condition: Human
            # ------------------------------------------------------------------- #
            human_metrics = compute_metrics(human_comment)
            writer.writerow(
                {
                    "snippet_id": snippet_id,
                    "condition": "human",
                    "code": code,
                    "human_comment": human_comment,
                    "llm_comment": llm_comment,
                    "no_comment": no_comment,
                    **human_metrics,
                    "Comment_Length": len(human_comment),
                    "Flesch_Kincaid_Grade": flesch_kincaid_grade(human_comment)
                    if human_comment
                    else 0,
                }
            )

            # ------------------------------------------------------------------- #
            # Condition: None (baseline)
            # ------------------------------------------------------------------- #
            none_metrics = compute_metrics("")
            writer.writerow(
                {
                    "snippet_id": snippet_id,
                    "condition": "none",
                    "code": code,
                    "human_comment": human_comment,
                    "llm_comment": llm_comment,
                    "no_comment": no_comment,
                    **none_metrics,
                    "Comment_Length": 0,
                    "Flesch_Kincaid_Grade": 0,
                }
            )

    log.info(f"Readability metrics written to {out_path}")

if __name__ == "__main__":
    main()
