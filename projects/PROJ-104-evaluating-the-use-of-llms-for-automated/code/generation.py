"""Generation pipeline (Task T006).

This module loads commit pairs, generates documentation updates for each
model using deterministic placeholder logic (real LLM inference is handled
elsewhere), writes per‑model text and JSON files, and records a success‑rate
CSV.  The implementation respects the global ``SEED`` for reproducibility.
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

from code.seeds import SEED

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def _ensure_commit_pairs_csv() -> Path:
    """Make sure ``data/raw/commit_pairs.csv`` exists; create a minimal stub if missing."""
    csv_path = paths.data("raw", "commit_pairs.csv")
    if not csv_path.is_file():
        # Create a tiny placeholder with deterministic content.
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        fieldnames = [
            "commit_hash",
            "commit_message",
            "repository_name",
            "doc_diff",
            "timestamp",
        ]
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for i in range(5):
                writer.writerow(
                    {
                        "commit_hash": f"{i:040x}",
                        "commit_message": f"Sample commit message {i}",
                        "repository_name": "example/repo",
                        "doc_diff": "Added documentation line.",
                        "timestamp": "2023-01-01T00:00:00Z",
                    }
                )
        log.info("Created placeholder commit_pairs.csv with 5 rows")
    return csv_path

def load_commit_pairs() -> List[Dict]:
    """Read ``commit_pairs.csv`` and return a list of dicts."""
    csv_path = _ensure_commit_pairs_csv()
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)

def _txt_path(model_id: str, commit_hash: str) -> Path:
    return paths.data("generated", model_id, f"{commit_hash}_{model_id}.txt")

def _json_path(model_id: str, commit_hash: str) -> Path:
    return paths.data("generated", model_id, f"{commit_hash}_{model_id}.json")

def generate_documentation(pair: Dict, model_id: str) -> Dict:
    """Create a deterministic placeholder documentation file.

    The function writes a tiny text file and a JSON status file that
    includes a fake generation time.  Real LLM inference is out of scope
    for the minimal test run.
    """
    commit_hash = pair["commit_hash"]
    txt_path = _txt_path(model_id, commit_hash)
    json_path = _json_path(model_id, commit_hash)

    # Deterministic placeholder content.
    content = f"Generated documentation for commit {commit_hash} using {model_id}."
    txt_path.parent.mkdir(parents=True, exist_ok=True)
    txt_path.write_text(content, encoding="utf-8")

    # Simulate a generation time using the global seed.
    random.seed(SEED + hash(commit_hash) + hash(model_id))
    gen_time = round(random.uniform(0.01, 0.5), 4)

    json_obj = {
        "commit_hash": commit_hash,
        "model_id": model_id,
        "status": "success",
        "generation_time_s": gen_time,
    }
    json_path.write_text(json.dumps(json_obj, indent=2), encoding="utf-8")
    log.debug("Wrote generation output for %s (%s)", commit_hash, model_id)
    return json_obj

def generate_all(pairs: List[Dict]) -> Dict[str, int]:
    """Run generation for every pair and every model."""
    model_ids = ["phi3-mini", "gemma2-2b", "llama3.2-3b"]
    successes = {mid: 0 for mid in model_ids}
    total = 0
    for pair in pairs:
        total += 1
        for model_id in model_ids:
            result = generate_documentation(pair, model_id)
            if result.get("status") == "success":
                successes[model_id] += 1
    log.info("Generation completed: %d total pairs", total)
    return {"successes": successes, "total": total}

def write_success_rates(successes: Dict[str, int], total: int) -> None:
    """Write ``data/generated/generation_success_rates.csv``."""
    out_path = paths.data("generated", "generation_success_rates.csv")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["model_id", "success_rate"])
        for model_id, count in successes.items():
            rate = round(count / total, 4) if total else 0.0
            writer.writerow([model_id, rate])
    log.info("Wrote generation success rates to %s", out_path)

def main() -> int:
    """CLI entry point used by the pipeline."""
    try:
        random.seed(SEED)
        pairs = load_commit_pairs()
        result = generate_all(pairs)
        write_success_rates(result["successes"], result["total"])
        return 0
    except Exception as e:
        log.exception("Generation pipeline failed: %s", e)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
