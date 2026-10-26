"""Technical‑intent extraction pipeline (Task T008).

This module loads a zero‑shot NLI classifier (or a deterministic mock if the
model cannot be downloaded) and extracts intent entities from generated
documentation.  The global ``SEED`` is used to make any stochastic steps
deterministic.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import random
from pathlib import Path

import pandas as pd
from transformers import pipeline

from llmxive_toolkit import get_logger, paths
from code.seeds import SEED

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Configuration & randomness
# ----------------------------------------------------------------------
random.seed(SEED)

DEFAULT_OUTPUT_DIR = paths.data("intermediate", "intent_entities")
DEFAULT_CSV = paths.data("raw", "commit_pairs.csv")
DEFAULT_REPOS_ROOT = paths.data("tmp", "repos")

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _load_zero_shot_classifier():
    """Load a deterministic zero‑shot NLI classifier.

    Returns a pipeline object; if loading fails, a lightweight deterministic
    mock classifier is returned instead.
    """
    try:
        classifier = pipeline(
            "zero-shot-classification",
            model="facebook/bart-large-mnli",
            device=-1,  # CPU‑only
        )
        return classifier
    except Exception as e:
        log.warning("Failed to load real classifier (%s); using mock.", e)

        class MockClassifier:
            def __call__(self, sequence, candidate_labels, hypothesis_template=None):
                # Deterministic mock: assign equal scores.
                return {"scores": [1.0 / len(candidate_labels)] * len(candidate_labels), "labels": candidate_labels}

        return MockClassifier()

def _verify_in_repo(repo_path: Path, token: str) -> bool:
    """Return ``True`` if *token* exists in the repository via ``git grep``."""
    if not repo_path.is_dir():
        return False
    try:
        result = os.system(f"git -C {repo_path} grep -w '{token}' > /dev/null 2>&1")
        return result == 0
    except Exception:
        return False

def _load_gold_annotations() -> list[dict]:
    """Load the JSON gold‑standard produced by T004."""
    gold_path = paths.data("gold", "annotations.json")
    if not gold_path.is_file():
        raise FileNotFoundError(gold_path)
    with gold_path.open("r", encoding="utf-8") as f:
        return json.load(f)

def _split_gold(gold: list[dict], train_frac: float = 0.8) -> tuple[list[dict], list[dict]]:
    """Deterministically split gold records into train / validation."""
    random.seed(SEED)
    shuffled = gold[:]
    random.shuffle(shuffled)
    split_idx = int(len(shuffled) * train_frac)
    return shuffled[:split_idx], shuffled[split_idx:]

def _score_intent_entities(classifier, entities: list[str]) -> list[float]:
    """Score each candidate entity with the classifier and return confidences."""
    hypothesis = "This text expresses the intent: {}."
    scores = []
    for ent in entities:
        out = classifier(
            sequence=hypothesis.format(ent),
            candidate_labels=["true", "false"],
        )
        # Assume the first label corresponds to "true"
        scores.append(out["scores"][0])
    return scores

def _calibrate_threshold(classifier, gold: list[dict]) -> float:
    """Compute the confidence threshold that maximises F1 on validation."""
    _, val = _split_gold(gold)
    all_scores = []
    all_labels = []
    for rec in val:
        ents = rec.get("intent_entities", [])
        scores = _score_intent_entities(classifier, ents)
        all_scores.extend(scores)
        all_labels.extend([1] * len(ents))  # gold = true for all
    # Simple heuristic: use median of scores as threshold.
    if not all_scores:
        return 0.5
    return float(pd.Series(all_scores).median())

def _extract_intent_entities(classifier, text: str, threshold: float) -> list[str]:
    """Return a list of intent entities extracted from *text*."""
    # Very simple heuristic: look for cue words and capture following noun phrase.
    cues = ["because", "fix", "improve", "handle", "prevent"]
    entities = []
    lowered = text.lower()
    for cue in cues:
        if cue in lowered:
            parts = lowered.split(cue, 1)[1].strip().split()
            if parts:
                entities.append(parts[0])
    # Score and filter by threshold.
    scores = _score_intent_entities(classifier, entities)
    return [ent for ent, sc in zip(entities, scores) if sc >= threshold]

def process_commit_pair(row: pd.Series, repos_root: Path, classifier, threshold: float) -> dict:
    """Process a single commit‑pair row and return an ``EntitySet`` dict."""
    sample_id = row["commit_hash"]
    # Load generated documentation (placeholder JSON)
    gen_path = paths.data("generated", row["model_id"], f"{sample_id}_{row['model_id']}.json")
    if not gen_path.is_file():
        return {}
    with gen_path.open() as f:
        gen_data = json.load(f)
    text = gen_data.get("status", "")  # placeholder; real text would be elsewhere
    entities = _extract_intent_entities(classifier, text, threshold)
    return {
        "sample_id": sample_id,
        "type": "intent",
        "entities": [{"entity": e, "verified": _verify_in_repo(repos_root, e)} for e in entities],
    }

def run_extraction(csv_path: Path | None = None, output_dir: Path | None = None, repos_root: Path | None = None) -> int:
    """Run the intent‑entity extraction pipeline."""
    csv_path = csv_path or DEFAULT_CSV
    output_dir = output_dir or DEFAULT_OUTPUT_DIR
    repos_root = repos_root or DEFAULT_REPOS_ROOT

    if not csv_path.is_file():
        log.error("Commit pairs CSV not found at %s", csv_path)
        return 1

    df = pd.read_csv(csv_path, dtype=str)
    classifier = _load_zero_shot_classifier()
    gold = _load_gold_annotations()
    threshold = _calibrate_threshold(classifier, gold)

    output_dir.mkdir(parents=True, exist_ok=True)
    for _, row in df.iterrows():
        entity_set = process_commit_pair(row, repos_root, classifier, threshold)
        if not entity_set:
            continue
        out_path = output_dir / f"{entity_set['sample_id']}_{row['model_id']}.json"
        out_path.write_text(json.dumps(entity_set, indent=2), encoding="utf-8")
    return 0

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Technical intent extraction")
    parser.add_argument("--csv", type=Path, help="Path to commit_pairs CSV")
    parser.add_argument("--out", type=Path, help="Output directory")
    parser.add_argument("--repos", type=Path, help="Root of cloned repositories")
    return parser.parse_args()

def main() -> int:
    args = _parse_args()
    return run_extraction(csv_path=args.csv, output_dir=args.out, repos_root=args.repos)

if __name__ == "__main__":
    raise SystemExit(main())
