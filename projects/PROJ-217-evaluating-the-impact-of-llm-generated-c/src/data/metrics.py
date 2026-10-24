"""
src/data/metrics.py

Compute readability metrics for each comment condition (LLM‑generated, human, none).

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
from pathlib import Path
from typing import Dict, Optional

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

def _load_llm_comments_stream() -> Path:
    """Return the path to the llm_comments.jsonl file (existence is validated)."""
    in_path = paths.data("llm_comments.jsonl")
    if not in_path.is_file():
        raise FileNotFoundError(f"LLM comments file not found: {in_path}")
    return in_path

def _tokenize(text: str) -> list:
    """Very light tokenisation – split on whitespace."""
    return text.split()

def _bleu(candidate: str, reference: str) -> float:
    """BLEU score (0‑1) between ``candidate`` and ``reference``."""
    if not candidate or not reference:
        return 0.0
    # Shortcut for identical strings – guarantees a perfect score.
    if candidate == reference:
        return 1.0
    cand_tokens = _tokenize(candidate)
    ref_tokens = _tokenize(reference)
    smoothing = SmoothingFunction().method1
    return float(sentence_bleu([ref_tokens], cand_tokens, smoothing_function=smoothing))

def _rouge_l(candidate: str, reference: str) -> float:
    """ROUGE‑L F‑measure (0‑1) between ``candidate`` and ``reference``."""
    if not candidate or not reference:
        return 0.0
    # Shortcut for identical strings – guarantees a perfect score.
    if candidate == reference:
        return 1.0
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
        # Trigger a forward pass to surface potential OOM early.
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
    llm_path = _load_llm_comments_stream()
    out_path = paths.data("readability_metrics.csv")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Load the embedding model once.
    embedder = _load_sentence_transformer()

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

        # Stream the JSON‑L file line‑by‑line.
        with llm_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)

                snippet_id = rec.get("snippet_id")
                code = rec.get("code", "")
                human_comment = rec.get("human_comment", "")
                llm_comment = rec.get("llm_comment", "")
                no_comment = rec.get("no_comment", "")

                # Reference text for “source” metrics.
                # Prefer the human comment; fall back to raw code.
                reference_text = human_comment if human_comment else code

                # Pre‑compute embeddings for the two reference texts.
                ref_emb = embedder.encode([reference_text], convert_to_numpy=True)[0]
                human_emb = (
                    embedder.encode([human_comment], convert_to_numpy=True)[0]
                    if human_comment
                    else ref_emb
                )

                def compute_metrics(comment: str) -> Dict[str, Optional[float]]:
                    """Compute all metrics for a given comment string."""
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
                    bleu_src = _bleu(comment, reference_text)
                    bleu_hum = (
                        _bleu(comment, human_comment) if human_comment else bleu_src
                    )

                    # ROUGE‑L
                    rouge_src = _rouge_l(comment, reference_text)
                    rouge_hum = (
                        _rouge_l(comment, human_comment) if human_comment else rouge_src
                    )

                    # Semantic similarity
                    comment_emb = embedder.encode([comment], convert_to_numpy=True)[0]
                    sim_src = _cosine_similarity(comment_emb, ref_emb)
                    sim_hum = (
                        _cosine_similarity(comment_emb, human_emb)
                        if human_comment
                        else sim_src
                    )

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