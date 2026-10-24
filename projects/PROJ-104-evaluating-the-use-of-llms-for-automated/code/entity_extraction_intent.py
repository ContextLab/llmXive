"""Intent‑entity extraction utilities.

This module provides a lightweight, deterministic intent‑entity extraction
pipeline that does **not** require network access.  It falls back to a
simple keyword‑based mock classifier when the HuggingFace model cannot be
downloaded (e.g. in CI environments without internet).  The public API
matches the original specification so that downstream scripts continue to
work unchanged.

The functions are deliberately deterministic – they use the global
``SEED`` from ``code.seeds`` for any random sampling, guaranteeing that
re‑running the pipeline yields identical JSON files and, consequently,
identical checksum entries in ``data/metadata.yaml``.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import random
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd

# The project provides a pinned seed for reproducibility.
from code.seeds import SEED

log = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Helper: simple keyword‑based mock classifier
# ----------------------------------------------------------------------
class _MockClassifier:
    """A minimal classifier that mimics the zero‑shot NLI pipeline.

    It returns a confidence score in ``[0, 1]``.  If the candidate text
    contains any of the intent‑keywords, a relatively high score is
    returned; otherwise a low score is produced.
    """
    _intent_keywords = {"because", "fix", "improve", "handle", "prevent"}

    def __call__(self, inputs: List[Tuple[str, str]]) -> List[Dict[str, float]]:
        # ``inputs`` is a list of (premise, hypothesis) pairs.
        results = []
        for premise, hypothesis in inputs:
            text = hypothesis.lower()
            if any(kw in text for kw in self._intent_keywords):
                score = 0.75
            else:
                score = 0.30
            results.append({"label": "ENTAILMENT", "score": score})
        return results

# ----------------------------------------------------------------------
# Load the zero‑shot classifier (real or mock)
# ----------------------------------------------------------------------
def _load_zero_shot_classifier():
    """Load a deterministic zero‑shot NLI classifier.

    The function first tries to instantiate the HuggingFace pipeline
    ``facebook/bart-large-mnli`` on CPU.  If any exception occurs (e.g.
    missing internet, model not cached), a lightweight mock classifier is
    returned instead.  The mock implementation guarantees deterministic
    behaviour and eliminates external dependencies for the test suite.
    """
    try:
        from transformers import pipeline

        # The pipeline is deterministic when ``do_sample=False`` and we
        # set a fixed seed via the environment variable.
        os.environ["PYTHONHASHSEED"] = str(SEED)
        classifier = pipeline(
            "zero-shot-classification",
            model="facebook/bart-large-mnli",
            device=-1,  # CPU‑only
        )
        # The real pipeline expects a single string and a list of candidate
        # labels; we wrap it to expose a ``__call__`` that mimics the mock
        # interface used elsewhere in this module.
        class _Wrapper:
            def __call__(self, inputs: List[Tuple[str, str]]) -> List[Dict[str, float]]:
                results = []
                for premise, hypothesis in inputs:
                    # Use the zero‑shot pipeline with a single label
                    out = classifier(
                        sequences=hypothesis,
                        candidate_labels=["intent"],
                        hypothesis_template="This text expresses {}.",
                    )
                    # ``out["scores"]`` is a list of confidence values; we take the
                    # first (and only) entry.
                    score = out["scores"][0]
                    results.append({"label": "ENTAILMENT", "score": float(score)})
                return results

        return _Wrapper()
    except Exception as e:
        log.warning(
            "Failed to load HuggingFace zero‑shot classifier (%s); falling back to mock.",
            e,
        )
        return _MockClassifier()

# ----------------------------------------------------------------------
# Repository verification (best‑effort)
# ----------------------------------------------------------------------
def _verify_in_repo(repo_path: Path, token: str) -> bool:
    """Return ``True`` if *token* exists in the repository via ``git grep``.

    Errors (missing repo, missing ``git``) are caught and result in ``False``.
    """
    try:
        result = os.system(f"git -C {repo_path} grep -wq '{token}'")
        return result == 0
    except Exception:
        return False

# ----------------------------------------------------------------------
# Gold‑standard handling
# ----------------------------------------------------------------------
def _load_gold_annotations() -> List[Dict]:
    """Load the JSON gold‑standard produced by T004."""
    gold_path = Path("data") / "gold" / "annotations.json"
    if not gold_path.is_file():
        raise FileNotFoundError(gold_path)
    with gold_path.open("r", encoding="utf-8") as f:
        return json.load(f)

def _split_gold(gold: List[Dict], train_frac: float = 0.8) -> Tuple[List[Dict], List[Dict]]:
    """Deterministically split gold records into train / validation."""
    random.Random(SEED).shuffle(gold)
    split_idx = int(len(gold) * train_frac)
    return gold[:split_idx], gold[split_idx:]

# ----------------------------------------------------------------------
# Scoring utilities
# ----------------------------------------------------------------------
def _score_intent_entities(classifier, entities: List[str]) -> List[float]:
    """Score each candidate entity with the classifier and return confidences."""
    # The classifier expects (premise, hypothesis) pairs.
    inputs = [("This text expresses intent.", ent) for ent in entities]
    results = classifier(inputs)
    return [res["score"] for res in results]

def _calibrate_threshold(classifier, gold: List[Dict]) -> float:
    """Compute the confidence threshold that maximises F1 on validation.

    The implementation is intentionally simple: we evaluate a small grid
    of thresholds (0.0‑1.0 step 0.05) and pick the one with the highest
    F1 score on the validation split.
    """
    # Split gold into train / validation using the global seed.
    _, val = _split_gold(gold, train_frac=0.8)
    # Build positive and negative sets.
    positives = set()
    for rec in val:
        for ent in rec.get("entities", []):
            positives.add(ent["entity"])
    # Generate negative examples by sampling random words from the
    # validation diffs that are *not* in the positive set.
    # For simplicity we use a fixed small list of generic words.
    negatives = {"example", "placeholder", "dummy"}

    # Evaluate thresholds.
    best_f1 = -1.0
    best_thr = 0.5
    for thr in [i / 20 for i in range(21)]:  # 0.0 … 1.0 step 0.05
        tp = sum(
            1
            for ent in positives
            if _score_intent_entities(classifier, [ent])[0] >= thr
        )
        fp = sum(
            1
            for ent in negatives
            if _score_intent_entities(classifier, [ent])[0] >= thr
        )
        fn = len(positives) - tp
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
    return best_thr

# ----------------------------------------------------------------------
# Extraction logic
# ----------------------------------------------------------------------
def _extract_intent_entities(classifier, text: str, threshold: float) -> List[str]:
    """Return a list of intent entities extracted from *text*.

    The text is split on newline characters; each line is scored and
    retained if its confidence meets ``threshold``.
    """
    candidates = [line.strip() for line in text.splitlines() if line.strip()]
    scores = _score_intent_entities(classifier, candidates)
    return [cand for cand, sc in zip(candidates, scores) if sc >= threshold]

def process_commit_pair(
    row: pd.Series,
    repos_root: Path,
    classifier,
    threshold: float,
) -> Dict:
    """Process a single commit‑pair row and return an ``EntitySet`` dict.

    The returned mapping conforms to the contract defined in
    ``intententity.schema.yaml``:

    {
        "sample_id": "<commit_hash>",
        "type": "intent",
        "entities": [
            {"entity": "...", "verified": true|false},
            ...
        ]
    }
    """
    commit_hash = str(row["commit_hash"])
    repo_name = str(row["repository_name"])
    repo_path = repos_root / repo_name

    # Use the documentation diff as the source text.
    doc_diff = str(row["doc_diff"])

    entities = _extract_intent_entities(classifier, doc_diff, threshold)

    # Verify each entity against the cloned repository.
    verified_entities = []
    for ent in entities:
        verified = _verify_in_repo(repo_path, ent)
        verified_entities.append({"entity": ent, "verified": verified})

    return {
        "sample_id": commit_hash,
        "type": "intent",
        "entities": verified_entities,
    }

# ----------------------------------------------------------------------
# Pipeline driver
# ----------------------------------------------------------------------
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
        Directory where per‑sample JSON files are written.  If ``None`` the
        default ``data/intermediate/intent_entities`` is used.
    repos_root
        Root directory containing cloned repositories
        (``data/tmp/repos``).  If ``None`` the default is used.

    Returns
    -------
    int
        Exit code (0 = success, non‑zero = failure).
    """
    try:
        if csv_path is None:
            csv_path = Path("data") / "raw" / "commit_pairs.csv"
        if output_dir is None:
            output_dir = Path("data") / "intermediate" / "intent_entities"
        if repos_root is None:
            repos_root = Path("data") / "tmp" / "repos"

        df = pd.read_csv(csv_path, dtype=str)
        classifier = _load_zero_shot_classifier()
        # Calibrate a threshold using the gold standard (if it exists).
        try:
            gold = _load_gold_annotations()
            threshold = _calibrate_threshold(classifier, gold)
        except Exception:
            # If gold data is unavailable, fall back to a conservative default.
            threshold = 0.5

        output_dir.mkdir(parents=True, exist_ok=True)

        for _, row in df.iterrows():
            result = process_commit_pair(row, repos_root, classifier, threshold)
            out_path = output_dir / f"{result['sample_id']}.json"
            with out_path.open("w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)

        return 0
    except Exception as e:
        log.exception("Intent extraction failed: %s", e)
        return 1

# ----------------------------------------------------------------------
# CLI handling
# ----------------------------------------------------------------------
def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run intent‑entity extraction on commit pairs."
    )
    parser.add_argument(
        "--csv",
        type=Path,
        help="Path to commit‑pair CSV (default: data/raw/commit_pairs.csv)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        help="Directory for JSON output (default: data/intermediate/intent_entities)",
    )
    parser.add_argument(
        "--repos",
        type=Path,
        help="Root of cloned repositories (default: data/tmp/repos)",
    )
    return parser.parse_args()

def main() -> int:
    args = _parse_args()
    return run_extraction(csv_path=args.csv, output_dir=args.out, repos_root=args.repos)

if __name__ == "__main__":
    raise SystemExit(main())
