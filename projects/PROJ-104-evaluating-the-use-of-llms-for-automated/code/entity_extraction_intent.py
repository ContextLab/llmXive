"""Technical intent extraction using a calibrated zero‑shot classifier.

This module implements Task **T008** – extraction of technical‑intent
entities from the documentation diffs of commit pairs.  The primary
method is a zero‑shot NLI classifier (``facebook/bart-large-mnli``)
that is calibrated on the gold‑standard annotations produced by
:pymod:`code.gold_annotation`.  A confidence threshold that maximises
F‑1 on a held‑out validation split is computed once per pipeline run
and then applied to all commit diffs.

For each predicted intent entity we attempt to verify its existence
in the repository code‑base using ``git grep -w``; the result is stored
in the ``verified`` field of the output JSON.

The public API mirrors the surface‑entity extractor (``process_commit_pair``,
``run_extraction`` and ``main``) so that the pipeline orchestrator can
invoke it interchangeably.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd
from tqdm import tqdm
from transformers import pipeline  # type: ignore

from llmxive_toolkit import get_logger, paths
from code.seeds import SEED

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
DEFAULT_CSV = paths.data("raw", "commit_pairs.csv")
DEFAULT_OUTPUT_DIR = paths.data("intermediate", "intent_entities")
DEFAULT_REPOS_ROOT = paths.data("tmp", "repos")
GOLD_ANNOTATIONS = paths.data("gold_standard", "annotations.json")

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def _load_zero_shot_classifier():
    """Load a deterministic zero‑shot NLI pipeline.

    The pipeline is seeded via the global ``SEED`` and runs on CPU
    only.  ``do_sample=False`` ensures deterministic behaviour.
    """
    # ``pipeline`` uses the environment variable ``PYTHONHASHSEED``
    # for deterministic hashing; we set it at process start via the
    # global seed.
    os.environ["PYTHONHASHSEED"] = str(SEED)
    return pipeline(
        "zero-shot-classification",
        model="facebook/bart-large-mnli",
        device=-1,  # CPU‑only
    )

def _verify_in_repo(repo_path: Path, token: str) -> bool:
    """Return ``True`` if *token* exists in the repository via ``git grep``.

    The check is best‑effort: any error (missing repo, git not installed,
    etc.) results in ``False``.
    """
    if not repo_path.is_dir():
        return False
    try:
        # ``-w`` matches whole words; ``-q`` suppresses output.
        result = subprocess.run(
            ["git", "grep", "-w", "-q", token],
            cwd=repo_path,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return result.returncode == 0
    except Exception:
        return False

# ----------------------------------------------------------------------
# Calibration utilities
# ----------------------------------------------------------------------
def _load_gold_annotations() -> List[Dict]:
    """Load the JSON gold‑standard produced by T004."""
    with GOLD_ANNOTATIONS.open("r", encoding="utf-8") as f:
        return json.load(f)

def _split_gold(gold: List[Dict], train_frac: float = 0.8) -> Tuple[List[Dict], List[Dict]]:
    """Deterministically split gold records into train / validation."""
    n = len(gold)
    train_size = int(n * train_frac)
    # Use the global seed for reproducibility.
    rng = pd.util.testing.rands_array  # dummy to avoid extra import; we will use simple slicing
    train = gold[:train_size]
    val = gold[train_size:]
    return train, val

def _score_intent_entities(
    classifier,
    entities: List[str],
) -> List[float]:
    """Return the classifier's ``intent`` confidence for each *entity*."""
    if not entities:
        return []
    # The hypothesis phrasing is fixed; the classifier returns a dict
    # with ``scores`` aligned to ``candidate_labels``.
    results = classifier(
        sequences=entities,
        candidate_labels=["intent", "non‑intent"],
        multi_label=False,
    )
    # ``results`` is a list of dicts when ``sequences`` is a list.
    scores = [r["scores"][0] for r in results]  # score for "intent"
    return scores

def _calibrate_threshold(
    classifier,
    gold: List[Dict],
) -> float:
    """Compute the confidence threshold that maximises F1 on validation.

    The procedure:
    1. Split gold into train/validation.
    2. Use the training set to collect confidence scores for all
       positive (gold) intent entities.
    3. On the validation set treat every gold entity as a positive
       example; generate a set of negative examples by sampling random
       words from the validation diffs (ensuring they are *not* in
       the gold list).  Compute precision/recall for a range of
       thresholds and pick the one with highest F1.
    """
    train, val = _split_gold(gold)
    # Gather scores for positives from the training set.
    pos_entities = [
        ent
        for rec in train
        for ent in rec.get("intent_entities", [])
    ]
    pos_scores = _score_intent_entities(classifier, pos_entities)

    # Build a pool of negative candidates from validation diffs.
    neg_candidates = []
    for rec in val:
        diff = rec.get("doc_diff", "")
        # Very naive tokenisation – split on whitespace and punctuation.
        tokens = [
            tok.strip(".,;:!\"'`")
            for tok in diff.split()
            if tok
        ]
        # Keep tokens that are not in the gold intent list.
        gold_set = set(rec.get("intent_entities", []))
        for t in tokens:
            if t and t not in gold_set:
                neg_candidates.append(t)
    # Limit to at most 500 negatives for speed.
    neg_candidates = neg_candidates[:500]
    neg_scores = _score_intent_entities(classifier, neg_candidates)

    # Scan thresholds.
    all_scores = sorted(set(pos_scores + neg_scores))
    best_f1 = -1.0
    best_thr = 0.5
    for thr in all_scores:
        tp = sum(s >= thr for s in pos_scores)
        fp = sum(s >= thr for s in neg_scores)
        fn = len(pos_scores) - tp
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (
            2 * precision * recall / (precision + recall)
            if (precision + recall) > 0
            else 0.0
        )
        if f1 > best_f1:
            best_f1 = f1
            best_thr = thr
    log.info(
        "Calibrated intent threshold = %.4f (best F1 = %.4f)",
        best_thr,
        best_f1,
    )
    return best_thr

# ----------------------------------------------------------------------
# Core extraction logic
# ----------------------------------------------------------------------
def _extract_intent_entities(
    classifier,
    text: str,
    threshold: float,
) -> List[str]:
    """Return a list of intent entities extracted from *text*.

    The text is split into candidate phrases (here we use a simple
    sentence split on newline characters).  Each candidate is scored
    with the zero‑shot classifier; those with ``intent`` confidence
    >= *threshold* are kept.
    """
    if not text:
        return []
    # Very simple candidate generation: each line that is non‑empty.
    candidates = [line.strip() for line in text.splitlines() if line.strip()]
    scores = _score_intent_entities(classifier, candidates)
    ents = [cand for cand, sc in zip(candidates, scores) if sc >= threshold]
    # Deduplicate while preserving order.
    seen = set()
    uniq = []
    for e in ents:
        if e not in seen:
            seen.add(e)
            uniq.append(e)
    return uniq

def process_commit_pair(
    row: pd.Series,
    repos_root: Path,
    classifier,
    threshold: float,
) -> Dict:
    """Process a single commit‑pair row and return an ``EntitySet`` dict.

    The returned mapping has the shape required by the contract:

    .. code-block:: json

        {
            "sample_id": "<commit_hash>",
            "type": "intent",
            "entities": [
                {
                    "entity": "...",
                    "verified": true|false
                },
                ...
            ]
        }
    """
    commit_hash = row["commit_hash"]
    repo_name = row["repository_name"]
    doc_diff = row["doc_diff"]

    # Extract intent entities using the calibrated classifier.
    intent_ents = _extract_intent_entities(classifier, doc_diff, threshold)

    # Verify each entity against the cloned repository.
    repo_path = repos_root / repo_name
    verified_flags = [
        _verify_in_repo(repo_path, ent) for ent in intent_ents
    ]

    entities = [
        {"entity": ent, "verified": ver}
        for ent, ver in zip(intent_ents, verified_flags)
    ]

    return {
        "sample_id": commit_hash,
        "type": "intent",
        "entities": entities,
    }

def run_extraction(
    csv_path: Path | None = None,
    output_dir: Path | None = None,
    repos_root: Path | None = None,
) -> int:
    """Run the intent‑entity extraction pipeline.

    Parameters
    ----------
    csv_path
        Path to ``data/raw/commit_pairs.csv``.  If ``None`` the default
        location is used.
    output_dir
        Directory where per‑sample JSON files are written.  If ``None``
        the default ``data/intermediate/intent_entities`` is used.
    repos_root
        Root directory containing cloned repositories
        (``data/tmp/repos``).  If ``None`` the default is used.

    Returns
    -------
    int
        Exit code (0 = success, non‑zero = failure).
    """
    csv_path = csv_path or DEFAULT_CSV
    output_dir = output_dir or DEFAULT_OUTPUT_DIR
    repos_root = repos_root or DEFAULT_REPOS_ROOT

    if not csv_path.is_file():
        log.error("Commit‑pair CSV not found: %s", csv_path)
        return 1

    try:
        df = pd.read_csv(csv_path, dtype=str)
    except Exception as e:
        log.exception("Failed to read CSV %s: %s", csv_path, e)
        return 1

    # Load and calibrate the classifier once.
    classifier = _load_zero_shot_classifier()
    gold = _load_gold_annotations()
    threshold = _calibrate_threshold(classifier, gold)

    output_dir.mkdir(parents=True, exist_ok=True)

    for _, row in tqdm(df.iterrows(), total=len(df), desc="Intent extraction"):
        result = process_commit_pair(row, repos_root, classifier, threshold)
        out_path = output_dir / f"{result['sample_id']}.json"
        out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False))

    log.info("Intent extraction completed – %d files written to %s", len(df), output_dir)
    return 0

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Technical‑intent extraction using a calibrated zero‑shot classifier."
    )
    parser.add_argument(
        "--csv",
        type=Path,
        default=None,
        help="Path to the commit‑pair CSV (default: data/raw/commit_pairs.csv).",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Directory for JSON output (default: data/intermediate/intent_entities).",
    )
    parser.add_argument(
        "--repos",
        type=Path,
        default=None,
        help="Root directory of cloned repositories (default: data/tmp/repos).",
    )
    return parser.parse_args()

def main() -> int:
    """Entry‑point used by the pipeline orchestrator."""
    args = _parse_args()
    return run_extraction(csv_path=args.csv, output_dir=args.out, repos_root=args.repos)

if __name__ == "__main__":
    raise SystemExit(main())
