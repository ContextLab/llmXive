"""
src/data/metrics.py

Compute readability metrics for each comment condition (LLM-generated, human, none).

This script reads `data/llm_comments.jsonl` which contains, for each snippet,
the original source code, the human docstring, the LLM-generated comment and an
empty string for the no-comment baseline. For every snippet three rows are
written to `data/readability_metrics.csv` – one per condition.
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

log = get_logger(__name__)

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
    """BLEU score (0-1) between candidate and reference."""
    if not candidate or not reference:
        return 0.0
    if candidate == reference:
        return 1.0
    cand_tokens = _tokenize(candidate)
    ref_tokens = _tokenize(reference)
    smoothing = SmoothingFunction().method1
    return float(sentence_bleu([ref_tokens], cand_tokens, smoothing_function=smoothing))

def _rouge_l(candidate: str, reference: str) -> float:
    """ROUGE-L F-measure (0-1) between candidate and reference."""
    if not candidate or not reference:
        return 0.0
    if candidate == reference:
        return 1.0
    scorer = rouge_scorer.RougeScorer(["rougeL"], use_stemmer=True)
    scores = scorer.score(reference, candidate)
    return scores["rougeL"].fmeasure

def _load_sentence_transformer() -> SentenceTransformer:
    """Load Sentence-BERT model with OOM fallback."""
    primary = "sentence-transformers/multi-qa-mpnet-base-dot-v1"
    fallback = "sentence-transformers/all-MiniLM-L6-v2"
    try:
        log.info(f"Loading primary embedding model: {primary}")
        model = SentenceTransformer(primary)
        _ = model.encode(["test"], convert_to_numpy=True)
        return model
    except Exception as e:
        log.warning(f"Failed to load primary model ({primary}): {e}. Falling back to {fallback}.")
        return SentenceTransformer(fallback)

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

def main() -> None:
    """
    Entry-point for `python -m src.data.metrics`.
    Computes BLEU, ROUGE-L, and SBERT similarity against both source code
    and human comments.
    """
    llm_path = _load_llm_comments_stream()
    out_path = paths.data("readability_metrics.csv")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    embedder = _load_sentence_transformer()

    header = [
        "snippet_id", "condition", "code", "human_comment", "llm_comment", "no_comment",
        "BLEU_vs_source", "BLEU_vs_human", "ROUGE_L_vs_source", "ROUGE_L_vs_human",
        "Semantic_Similarity_vs_source", "Semantic_Similarity_vs_human",
        "Comment_Length", "Flesch_Kincaid_Grade",
    ]

    with out_path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=header)
        writer.writeheader()

        with llm_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line: continue
                rec = json.loads(line)

                snippet_id = rec.get("snippet_id")
                code = rec.get("code", "")
                human_comment = rec.get("human_comment", "")
                llm_comment = rec.get("llm_comment", "")
                no_comment = rec.get("no_comment", "")

                # Pre-compute embeddings for references
                code_emb = embedder.encode([code], convert_to_numpy=True)[0]
                human_emb = embedder.encode([human_comment], convert_to_numpy=True)[0] if human_comment else code_emb

                def compute_metrics(comment: str) -> Dict[str, Optional[float]]:
                    if comment == "":
                        return {
                            "BLEU_vs_source": None, "BLEU_vs_human": None,
                            "ROUGE_L_vs_source": None, "ROUGE_L_vs_human": None,
                            "Semantic_Similarity_vs_source": None, "Semantic_Similarity_vs_human": None,
                        }
                    
                    # Lexical metrics
                    b_src = _bleu(comment, code)
                    b_hum = _bleu(comment, human_comment) if human_comment else b_src
                    r_src = _rouge_l(comment, code)
                    r_hum = _rouge_l(comment, human_comment) if human_comment else r_src

                    # Semantic metrics
                    comment_emb = embedder.encode([comment], convert_to_numpy=True)[0]
                    s_src = _cosine_similarity(comment_emb, code_emb)
                    s_hum = _cosine_similarity(comment_emb, human_emb) if human_comment else s_src

                    return {
                        "BLEU_vs_source": b_src, "BLEU_vs_human": b_hum,
                        "ROUGE_L_vs_source": r_src, "ROUGE_L_vs_human": r_hum,
                        "Semantic_Similarity_vs_source": s_src, "Semantic_Similarity_vs_human": s_hum,
                    }

                for cond, comment_text in [("llm", llm_comment), ("human", human_comment), ("none", "")]:
                    metrics = compute_metrics(comment_text)
                    writer.writerow({
                        "snippet_id": snippet_id, "condition": cond, "code": code,
                        "human_comment": human_comment, "llm_comment": llm_comment, "no_comment": no_comment,
                        **metrics,
                        "Comment_Length": len(comment_text) if cond != "none" else 0,
                        "Flesch_Kincaid_Grade": flesch_kincaid_grade(comment_text) if (cond != "none" and comment_text) else 0,
                    })

    log.info(f"Readability metrics written to {out_path}")

if __name__ == "__main__":
    main()
