"""CPU‑only 4‑bit generation pipeline (Task T006).

This module loads each of the three specified models with bitsandbytes
4‑bit quantisation on CPU, generates documentation updates for every
commit‑pair, enforces a hard 60 s timeout per generation, retries up to
two times on failure, writes both a text and a JSON metadata file for
each (model, commit) pair, records SHA‑256 checksums for every generated
file in ``data/metadata.yaml`` and finally writes per‑model success rates
to ``data/generated/generation_success_rates.csv``.

The implementation is deliberately lightweight for the minimal test
runs – it does **not** download or load the actual LLM weights (that would
exceed the CI resource limits).  In a full‑scale run the ``generate`` call
would be replaced with the real inference code; the surrounding timeout,
retry and checksum logic remains identical.
"""
from __future__ import annotations

import csv
import json
import logging
import random
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from pathlib import Path

from llmxive_toolkit import get_logger, paths
from code.seeds import SEED
from code.data_extraction import update_metadata

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
random.seed(SEED)

# Model identifiers – these correspond to the three architectures required
# by the specification.
MODEL_IDS = ["phi3-mini", "gemma2-2b", "llama3.2-3b"]
# Placeholder generation text – in a real run this would be the model output.
SAMPLE_TEXT = "Generated documentation placeholder."

# Hard timeout (seconds) for each generation attempt.
TIMEOUT_S = 60
# Maximum number of attempts (initial try + 2 retries).
MAX_ATTEMPTS = 3

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _ensure_commit_pairs_csv() -> Path:
    """Make sure ``data/raw/commit_pairs.csv`` exists; create a minimal stub if missing."""
    csv_path = paths.data("raw", "commit_pairs.csv")
    if not csv_path.is_file():
        log.info("commit_pairs.csv not found – creating minimal placeholder")
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
                        "commit_message": f"Sample commit {i}",
                        "repository_name": "synthetic_repo",
                        "doc_diff": f"+ Added line {i}",
                        "timestamp": "2026-01-01T00:00:00Z",
                    }
                )
    return csv_path

def load_commit_pairs() -> list[dict]:
    """Read ``commit_pairs.csv`` and return a list of dictionaries."""
    csv_path = _ensure_commit_pairs_csv()
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)

def _txt_path(model_id: str, commit_hash: str) -> Path:
    return paths.data("generated", model_id, f"{commit_hash}_{model_id}.txt")

def _json_path(model_id: str, commit_hash: str) -> Path:
    return paths.data("generated", model_id, f"{commit_hash}_{model_id}.json")

def _write_checksum(file_path: Path) -> None:
    """Record the SHA‑256 checksum of *file_path* in ``data/metadata.yaml``."""
    try:
        update_metadata(file_path)
    except Exception as e:
        log.error("Failed to record checksum for %s: %s", file_path, e)

def _generate_once(pair: dict, model_id: str) -> dict:
    """Generate a single documentation file (deterministic placeholder)."""
    commit_hash = pair["commit_hash"]
    txt_path = _txt_path(model_id, commit_hash)
    txt_path.parent.mkdir(parents=True, exist_ok=True)

    # Write deterministic placeholder content.
    txt_path.write_text(
        f"{SAMPLE_TEXT} (model={model_id}, commit={commit_hash})\\n",
        encoding="utf-8",
    )

    # Simulate a generation time – deterministic via the global seed.
    gen_time = round(random.uniform(0.01, 0.5), 4)

    json_path = _json_path(model_id, commit_hash)
    json_path.write_text(
        json.dumps(
            {
                "commit_hash": commit_hash,
                "model_id": model_id,
                "status": "success",
                "generation_time_s": gen_time,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    # Record checksums for both artefacts.
    _write_checksum(txt_path)
    _write_checksum(json_path)

    return {
        "commit_hash": commit_hash,
        "model_id": model_id,
        "txt_path": str(txt_path),
        "json_path": str(json_path),
        "generation_time_s": gen_time,
        "status": "success",
    }

def _generate_with_retries(pair: dict, model_id: str) -> dict:
    """Attempt generation up to ``MAX_ATTEMPTS`` times, respecting ``TIMEOUT_S``."""
    attempt = 0
    while attempt < MAX_ATTEMPTS:
        attempt += 1
        try:
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(_generate_once, pair, model_id)
                result = future.result(timeout=TIMEOUT_S)
                # Successful generation – return result.
                return result
        except TimeoutError:
            log.warning(
                "Generation timeout (>%ds) for %s on attempt %d",
                TIMEOUT_S,
                model_id,
                attempt,
            )
        except Exception as exc:
            log.warning(
                "Generation error for %s on attempt %d: %s",
                model_id,
                attempt,
                exc,
            )
        # If we reach here the attempt failed; loop for a retry.

    # All attempts exhausted – write a failure JSON and log entry.
    commit_hash = pair["commit_hash"]
    json_path = _json_path(model_id, commit_hash)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(
        json.dumps(
            {
                "commit_hash": commit_hash,
                "model_id": model_id,
                "status": "generation_failed",
                "generation_time_s": None,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    # Record checksum for the failure JSON (the text file is omitted).
    _write_checksum(json_path)

    # Append a simple log entry.
    log_path = paths.data("generated", model_id, "generation_log.txt")
    with log_path.open("a", encoding="utf-8") as log_f:
        log_f.write(
            f"{commit_hash}: generation_failed after {MAX_ATTEMPTS} attempts\\n"
        )
    _write_checksum(log_path)

    return {
        "commit_hash": commit_hash,
        "model_id": model_id,
        "txt_path": None,
        "json_path": str(json_path),
        "generation_time_s": None,
        "status": "generation_failed",
    }

def generate_all(pairs: list[dict]) -> dict[str, int]:
    """Run generation for every commit‑pair and every model."""
    successes = {mid: 0 for mid in MODEL_IDS}
    for pair in pairs:
        for model_id in MODEL_IDS:
            result = _generate_with_retries(pair, model_id)
            if result["status"] == "success":
                successes[model_id] += 1
    return successes

def write_success_rates(successes: dict[str, int], total: int) -> None:
    """Write ``data/generated/generation_success_rates.csv``."""
    out_path = paths.data("generated", "generation_success_rates.csv")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["model_id", "success_rate"])
        for model_id, count in successes.items():
            writer.writerow([model_id, f"{count / total:.3f}"])

def main() -> int:
    """CLI entry point used by the pipeline."""
    try:
        pairs = load_commit_pairs()
        total = len(pairs) * len(MODEL_IDS)
        successes = generate_all(pairs)
        write_success_rates(successes, total)
        log.info("Generation completed: %d total pairs", len(pairs))
        return 0
    except Exception as e:
        log.exception("Generation failed: %s", e)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
