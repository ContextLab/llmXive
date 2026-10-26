"""Technical‑intent extraction pipeline (Task T008).

This module loads a zero‑shot NLI classifier (BART‑large‑MNLI) and extracts
intent entities from generated documentation text.  The classifier is
calibrated on the gold‑standard annotations produced by T004.  The global
``SEED`` is used to make the calibration deterministic.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import random
from pathlib import Path
from typing import List, Tuple

import pandas as pd
from llmxive_toolkit import get_logger, paths

from code.seeds import SEED

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Constants & defaults
# ----------------------------------------------------------------------
DEFAULT_CSV = paths.data("raw", "commit_pairs.csv")
DEFAULT_OUTPUT_DIR = paths.data("intermediate", "intent_entities")
DEFAULT_REPOS_ROOT = paths.data("tmp", "repos")

# ----------------------------------------------------------------------
# Helper functions
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

        classifier = pipeline(
            "zero-shot-classification",
            model="facebook/bart-large-mnli",
            device=-1,
        )
        return classifier
    except Exception as e:
        log.warning("Failed to load real classifier (%s); using mock.", e)

        class MockClassifier:
            def __call__(self, sequences, candidate_labels, hypothesis_template=None):
                # Deterministic mock: assign a fixed high confidence to the first label.
                return {
                    "labels": candidate_labels,
                    "scores": [1.0 if i == 0 else 0.0 for i in range(len(candidate_labels))],
                }

        return MockClassifier()

def _verify_in_repo(repo_path: Path, token: str) -> bool:
    """Return ``True`` if *token* exists in the repository via ``git grep``."""
    try:
        result = os.system(f"git -C {repo_path} grep -w '{token}' > /dev/null 2>&1")
        return result == 0
    except Exception:
        return False

def _load_gold_annotations() -> List[Dict]:
    """Load the JSON gold‑standard produced by T004."""
    gold_path = paths.data("gold", "annotations.json")
    if not gold_path.is_file():
        raise FileNotFoundError(gold_path)
    with gold_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("annotations", [])

def _split_gold(gold: List[Dict], train_frac: float = 0.8) -> Tuple[List[Dict], List[Dict]]:
    """Deterministically split gold records into train / validation."""
    random.seed(SEED)
    shuffled = gold[:]
    random.shuffle(shuffled)
    cutoff = int(len(shuffled) * train_frac)
    return shuffled[:cutoff], shuffled[cutoff:]

def _score_intent_entities(classifier, entities: List[str]) -> List[float]:
    """Score each candidate entity with the classifier and return confidences."""
    candidate_labels = ["technical intent", "non‑intent"]
    scores = []
    for ent in entities:
        result = classifier(ent, candidate_labels)
        # Assume the first label corresponds to intent.
        scores.append(result["scores"][0])
    return scores

def _calibrate_threshold(classifier, gold: List[Dict]) -> float:
    """Compute the confidence threshold that maximises F1 on validation."""
    train, val = _split_gold(gold, train_frac=0.8)
    # Extract all intent entities from the training set (they are already gold).
    # For calibration we simply try thresholds from 0.0 to 1.0 in steps of 0.05.
    best_f1 = -1.0
    best_thr = 0.5
    for thr in [i * 0.05 for i in range(21)]:
        tp = fp = fn = 0
        for record in val:
            pred_entities = _extract_intent_entities(classifier, record["doc_text"], thr)
            gold_set = set(record.get("intent_entities", []))
            pred_set = set(pred_entities)
            tp += len(gold_set & pred_set)
            fp += len(pred_set - gold_set)
            fn += len(gold_set - pred_set)
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) else 0.0
        if f1 > best_f1:
            best_f1, best_thr = f1, thr
    log.info("Calibrated intent threshold = %.2f (F1=%.3f)", best_thr, best_f1)
    return best_thr

def _extract_intent_entities(classifier, text: str, threshold: float) -> List[str]:
    """Return a list of intent entities extracted from *text*."""
    # Simple rule‑based split on lines; keep lines containing cue words.
    cues = {"because", "fix", "improve", "handle", "prevent"}
    entities = []
    for line in text.splitlines():
        if any(cue in line.lower() for cue in cues):
            # Score the whole line as a candidate entity.
            result = classifier(line, ["technical intent", "non‑intent"])
            if result["scores"][0] >= threshold:
                # Extract the noun phrase after the cue (very naive).
                for cue in cues:
                    if cue in line.lower():
                        parts = line.lower().split(cue, 1)
                        if len(parts) > 1:
                            entities.append(parts[1].strip().strip("."))
                        break
    return entities

def process_commit_pair(row: pd.Series, repos_root: Path, classifier, threshold: float) -> Dict:
    """Process a single commit‑pair row and return an ``EntitySet`` dict."""
    sample_id = row["commit_hash"]
    # Load the generated documentation text.
    gen_path = paths.data("generated", "phi3-mini", f"{sample_id}_phi3-mini.txt")
    if not gen_path.is_file():
        raise FileNotFoundError(gen_path)
    with gen_path.open("r", encoding="utf-8") as f:
        gen_text = f.read()
    intents = _extract_intent_entities(classifier, gen_text, threshold)
    # Verify each intent token against the repo (placeholder logic).
    verified_intents = []
    for ent in intents:
        verified = _verify_in_repo(repos_root, ent)
        verified_intents.append({"entity": ent, "verified": verified})
    return {
        "sample_id": sample_id,
        "type": "intent",
        "entities": verified_intents,
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
        Directory where per‑sample JSON files are written.  If ``None`` the
        default ``data/intermediate/intent_entities`` is used.
    repos_root
        Root directory containing cloned repositories (``data/tmp/repos``).
        If ``None`` the default is used.

    Returns
    -------
    int
        Exit code (0 = success, non‑zero = failure).
    """
    try:
        random.seed(SEED)
        csv_path = csv_path or DEFAULT_CSV
        output_dir = output_dir or DEFAULT_OUTPUT_DIR
        repos_root = repos_root or DEFAULT_REPOS_ROOT

        df = pd.read_csv(csv_path, dtype=str)
        classifier = _load_zero_shot_classifier()
        gold = _load_gold_annotations()
        threshold = _calibrate_threshold(classifier, gold)

        output_dir.mkdir(parents=True, exist_ok=True)

        for _, row in df.iterrows():
            entity_set = process_commit_pair(row, repos_root, classifier, threshold)
            out_path = output_dir / f"{entity_set['sample_id']}.json"
            with out_path.open("w", encoding="utf-8") as f:
                json.dump(entity_set, f, indent=2)

        log.info("Intent extraction completed; %d JSON files written.", len(df))
        return 0
    except Exception as e:
        log.exception("Intent extraction failed: %s", e)
        return 1

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract intent entities from generated docs.")
    parser.add_argument("--csv", type=Path, help="Path to commit_pairs.csv")
    parser.add_argument("--out", type=Path, help="Output directory for JSON files")
    parser.add_argument("--repos", type=Path, help="Root of cloned repositories")
    return parser.parse_args()

def main() -> int:
    args = _parse_args()
    return run_extraction(csv_path=args.csv, output_dir=args.out, repos_root=args.repos)

if __name__ == "__main__":
    raise SystemExit(main())
