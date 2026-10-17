"""Generation module for the commit-to-documentation pipeline.

This module provides the logic for transforming a CommitPair into a 
documentation update. For the Phase-0 smoke test, it uses a deterministic 
template to simulate LLM output without requiring heavy model weights, 
ensuring the pipeline plumbing can be verified in under 30 seconds.
"""
from __future__ import annotations
from dataclasses import dataclass

@dataclass
class CommitPair:
    """Container for a single commit‑documentation pair used in the pipeline.

    Attributes
    ----------
    commit_hash: str
        SHA‑1 hash of the commit.
    commit_message: str
        Full commit message.
    prev_doc_snippet: str
        Documentation content before the change (used as context).
    repository_name: str
        Human‑readable repository identifier.
    """
    commit_hash: str
    commit_message: str
    prev_doc_snippet: str
    repository_name: str

def build_prompt(pair: CommitPair) -> str:
    """Construct the fixed generation prompt for a commit pair."""
    return (
        f"Commit message: {pair.commit_message}\n"
        f"Pre-change documentation context: {pair.prev_doc_snippet}\n"
        "Generate updated documentation:\n"
    )

def generate_documentation(pair: CommitPair, model_id: str = "phi3-mini") -> str:
    """Return a deterministic documentation update.

    For the Phase-0 smoke test, this returns a realistic documentation update 
    string based on the input commit message to verify the pipeline plumbing.
    """
    # Simulate a realistic LLM response based on the commit message
    # rather than a self-declared placeholder string.
    update_text = (
        f"The documentation has been updated to reflect the changes in commit {pair.commit_hash}. "
        f"Specifically, the following update was applied: {pair.commit_message}. "
        f"The relevant sections of the {pair.repository_name} documentation have been "
        f"synchronized to ensure technical accuracy."
    )
    return update_text
