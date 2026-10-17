"""CPU-only documentation generation module.

This module implements the prompt-construction and generation interface
used by the pipeline. The full quantized-model inference path (Phi-3-mini,
Gemma-2-2b, Llama-3.2-3B via ``transformers`` + ``bitsandbytes``) is added
in task T005; this file currently provides the shared, deterministic
plumbing (prompt construction and a CPU-only deterministic smoke-test
generator) so that the entry point in ``code/run_pipeline.py`` can be
exercised end-to-end without downloading model weights.

The smoke-test generator is deterministic (no sampling, no randomness)
and is used ONLY to validate the pipeline plumbing. It is never used to
produce analysis data.
"""

from __future__ import annotations

from dataclasses import dataclass

# Pinned seed (Constitution I). Real model decoding uses do_sample=False;
# the seed is still imported and recorded so all stochastic components
# share a single source of truth.
from code.seeds import SEED

MAX_NEW_TOKENS = 200
TIMEOUT_SECONDS = 60

# Canonical model identifiers (FR-002). All CPU-only (NFR-001).
MODEL_IDS = ("phi3-mini", "gemma2-2b", "llama3.2-3b")


@dataclass(frozen=True)
class CommitPair:
    """A single (commit_message, pre-change documentation context) pair."""

    commit_hash: str
    commit_message: str
    repository_name: str
    prev_doc_snippet: str


def build_prompt(pair: CommitPair) -> str:
    """Construct the fixed generation prompt (spec US-2, FR-002)."""
    return (
        f"Commit message: {pair.commit_message}\n"
        f"Pre-change documentation context: {pair.prev_doc_snippet}\n"
        "Generate updated documentation:"
    )


def generate_documentation(pair: CommitPair, model_id: str = "phi3-mini") -> str:
    """Generate a documentation update for ``pair`` on CPU.

    Full quantized-model inference arrives with T005. For the Phase-0
    smoke test this returns a deterministic, seed-pinned placeholder
    derived ONLY from the synthetic smoke-test input — it is plumbing
    validation, never analysis data. Decoding is deterministic
    (do_sample=False equivalent): no randomness is involved.
    """
    if model_id not in MODEL_IDS:
        raise ValueError(f"unknown model_id {model_id!r}; expected one of {MODEL_IDS}")
    prompt = build_prompt(pair)
    # Deterministic plumbing output: the prompt is echoed through a
    # fixed transformation. SEED is referenced for reproducibility
    # bookkeeping; no sampling occurs.
    _ = SEED
    return (
        "[SMOKE TEST OUTPUT - plumbing validation only, not analysis data]\n"
        f"model_id: {model_id}\n"
        f"commit_hash: {pair.commit_hash}\n"
        f"repository: {pair.repository_name}\n"
        f"prompt:\n{prompt}\n"
    )
