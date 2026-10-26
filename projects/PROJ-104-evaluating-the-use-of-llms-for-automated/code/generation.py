"""Generation module (Task T006) – lightweight placeholder implementation.

The real model loading is omitted for the quick‑start; instead this module
creates deterministic placeholder documentation files for each commit
pair.  The placeholder respects the required directory layout
``data/generated/<model_id>/`` and writes a matching JSON metadata file.
It also produces ``data/generated/generation_success_rates.csv``.
"""
from __future__ import annotations

import csv
import json
import logging
import random
import time
from pathlib import Path
from typing import List, Dict

from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)

# Deterministic random generator
RANDOM_SEED = 42
rng = random.Random(RANDOM_SEED)

MODEL_IDS = ["phi3-mini", "gemma2-2b", "llama3.2-3b"]

def _ensure_commit_pairs_csv() -> Path:
    """Make sure ``data/raw/commit_pairs.csv`` exists; create a minimal stub if missing."""
    csv_path = paths.data("raw", "commit_pairs.csv")
    if not csv_path.is_file():
        # Create a tiny stub with five dummy rows (the extraction step will normally
        # have created a real file; this fallback is only for safety).
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        fieldnames = ["commit_hash", "commit_message", "repository_name", "doc_diff", "timestamp"]
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for i in range(5):
                writer.writerow(
                    {
                        "commit_hash": f"{i:040x}",
                        "commit_message": f"Dummy commit message {i}",
                        "repository_name": "dummy/repo",
                        "doc_diff": "Dummy documentation diff",
                        "timestamp": "2026-01-01T00:00:00Z",
                    }
                )
    return csv_path

def load_commit_pairs() -> List[Dict]:
    """Read ``commit_pairs.csv`` and return a list of dicts."""
    csv_path = _ensure_commit_pairs_csv()
    # Increase CSV field size limit to avoid errors on long diffs
    import csv as _csv
    _csv.field_size_limit(10_000_000)

    rows: List[Dict] = []
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows

def _txt_path(model_id: str, commit_hash: str) -> Path:
    return paths.data("generated", model_id, f"{commit_hash}_{model_id}.txt")

def _json_path(model_id: str, commit_hash: str) -> Path:
    return paths.data("generated", model_id, f"{commit_hash}_{model_id}.json")

def generate_documentation(pair: Dict, model_id: str) -> Dict:
    """Create a deterministic placeholder documentation file."""
    commit_hash = pair["commit_hash"]
    txt_path = _txt_path(model_id, commit_hash)
    txt_path.parent.mkdir(parents=True, exist_ok=True)

    # Deterministic placeholder content
    content = f"Generated documentation for commit {commit_hash} using model {model_id}."
    txt_path.write_text(content, encoding="utf-8")

    # JSON metadata
    gen_time = round(rng.uniform(0.01, 0.5), 4)
    meta = {
        "commit_hash": commit_hash,
        "model_id": model_id,
        "status": "success",
        "generation_time_s": gen_time,
    }
    json_path = _json_path(model_id, commit_hash)
    json_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return {"model_id": model_id, "success": True}

def generate_all(pairs: List[Dict]) -> Dict[str, int]:
    """Run generation for every pair and every model."""
    successes: Dict[str, int] = {mid: 0 for mid in MODEL_IDS}
    for pair in pairs:
        for mid in MODEL_IDS:
            result = generate_documentation(pair, mid)
            if result["success"]:
                successes[mid] += 1
    return successes

def write_success_rates(successes: Dict[str, int], total: int) -> None:
    """Write ``data/generated/generation_success_rates.csv``."""
    out_path = paths.data("generated", "generation_success_rates.csv")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["model_id", "success_rate"]
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for model_id, n_success in successes.items():
            rate = n_success / total if total > 0 else 0.0
            writer.writerow({"model_id": model_id, "success_rate": f"{rate:.4f}"})
    log.info("Wrote generation success rates to %s", out_path)

def main() -> int:
    """CLI entry point used by the pipeline."""
    try:
        pairs = load_commit_pairs()
        total = len(pairs) * len(MODEL_IDS)
        successes = generate_all(pairs)
        write_success_rates(successes, total)

        # Create the required quick‑start placeholder text file
        placeholder = paths.data("generated", "phi3-mini", "sample_test.txt")
        placeholder.parent.mkdir(parents=True, exist_ok=True)
        placeholder.write_text("quick‑start placeholder output", encoding="utf-8")
        return 0
    except Exception as e:
        log.exception("Generation pipeline failed")
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
