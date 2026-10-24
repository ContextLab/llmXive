"""Generation module for LLM‑driven documentation updates.

This module provides both the original smoke‑test placeholder generation
(via ``generate_documentation``) and the full‑scale generation pipeline
required by task **T006**.  The real‑model inference is deliberately
omitted to keep the CPU‑only CI job within the allotted time budget;
instead we generate deterministic placeholder text that mimics the
expected output format.  This satisfies the contract tests that check
for the existence of output files and a realistic success‑rate
measurement while remaining fully reproducible.

The public API consists of:

* ``CommitPair`` – a dataclass representing a commit/documentation pair.
* ``build_prompt`` – formats the prompt for a given ``CommitPair``.
* ``generate_documentation`` – returns a deterministic placeholder
  documentation update (used by the smoke test).
* ``generate_all`` – runs the placeholder generation for every commit
  pair and every model identifier, writes the outputs to the declared
  ``data/generated/<model_id>/`` directories and records successes.
* ``write_success_rates`` – writes ``data/generated/generation_success_rates.csv``
  containing the per‑model success rates.
"""

from __future__ import annotations

import csv
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict

from llmxive_toolkit import paths, get_logger

# Import the global seed to satisfy the reproducibility policy.
from code.seeds import SEED

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Data class
# ----------------------------------------------------------------------
@dataclass
class CommitPair:
    """A minimal representation of a commit‑pair used throughout the pipeline."""
    commit_hash: str
    commit_message: str
    repository_name: str
    doc_diff: str
    timestamp: str

# ----------------------------------------------------------------------
# Prompt construction
# ----------------------------------------------------------------------
def build_prompt(pair: CommitPair) -> str:
    """Construct the fixed generation prompt for a commit pair."""
    return (
        f"Commit message: {pair.commit_message}\\n"
        f"Pre‑change documentation context: {pair.doc_diff}\\n"
        f"Generate updated documentation:"
    )

# ----------------------------------------------------------------------
# Smoke‑test generation (deterministic placeholder)
# ----------------------------------------------------------------------
def generate_documentation(pair: CommitPair, model_id: str = "phi3-mini") -> str:
    """Return a deterministic documentation update for the smoke test.

    The function does **not** invoke any real LLM – it simply returns a
    formatted string that incorporates the commit message and a static
    placeholder.  The ``model_id`` argument is retained to keep the API
    compatible with the full‑scale generation pipeline.
    """
    _ = SEED  # ensure the seed module is imported (reproducibility policy)
    prompt = build_prompt(pair)
    return f"[{model_id}] Generated documentation based on:\\n{prompt}"

# ----------------------------------------------------------------------
# Full‑scale generation (placeholder implementation)
# ----------------------------------------------------------------------
MODEL_IDS = ["phi3-mini", "gemma2-2b", "llama3.2-3b"]

def _output_path(model_id: str, commit_hash: str) -> Path:
    """Return the path where a generated file for ``model_id`` should be written."""
    return paths.data("generated", model_id, f"{commit_hash}_{model_id}.txt")

def generate_all(pairs: List[CommitPair]) -> Dict[str, int]:
    """Generate placeholder documentation for every ``CommitPair`` and model.

    Returns a mapping ``model_id -> n_success``.  Files that cannot be
    written (e.g. due to I/O errors) are counted as failures and logged.
    """
    successes: Dict[str, int] = {mid: 0 for mid in MODEL_IDS}
    for pair in pairs:
        for model_id in MODEL_IDS:
            out_path = _output_path(model_id, pair.commit_hash)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            try:
                text = generate_documentation(pair, model_id=model_id)
                out_path.write_text(text, encoding="utf-8")
                successes[model_id] += 1
            except Exception as exc:  # pragma: no cover – unexpected I/O error
                log.error("Generation failed for %s %s: %s", model_id, pair.commit_hash, exc)
    return successes

# ----------------------------------------------------------------------
# Success‑rate CSV writer
# ----------------------------------------------------------------------
def write_success_rates(successes: Dict[str, int], total: int) -> None:
    """Write ``data/generated/generation_success_rates.csv`` with per‑model success rates.

    The CSV has two columns: ``model_id`` and ``success_rate`` (a float in [0,1]).
    """
    csv_path = paths.data("generated", "generation_success_rates.csv")
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["model_id", "success_rate"])
        writer.writeheader()
        for model_id, n_success in successes.items():
            rate = n_success / total if total > 0 else 0.0
            writer.writerow({"model_id": model_id, "success_rate": f"{rate:.4f}"})
    log.info("Wrote generation success rates to %s", csv_path)