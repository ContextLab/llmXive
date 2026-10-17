"""Minimal generation module for Phase‑0 smoke test.

This implementation provides deterministic, CPU‑only placeholder
generation suitable for the quick‑start smoke test. It defines the
``CommitPair`` data class, a prompt builder, and a ``generate_documentation``
function that returns a deterministic string without loading any heavy
model weights. This satisfies the requirements of T001 while keeping the
module extensible for later tasks (e.g., real model inference in T005).
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
    """Construct the fixed generation prompt for a commit pair.

    The prompt follows the specification used throughout the project:

    ```
    Commit message: <commit_message>
    Pre-change documentation context: <prev_doc_snippet>
    Generate updated documentation:
    ```

    Parameters
    ----------
    pair: CommitPair
        The commit‑pair for which to build the prompt.

    Returns
    -------
    str
        The formatted prompt string.
    """
    return (
        f"Commit message: {pair.commit_message}\n"
        f"Pre-change documentation context: {pair.prev_doc_snippet}\n"
        "Generate updated documentation:\n"
    )

def generate_documentation(pair: CommitPair, model_id: str = "phi3-mini") -> str:
    """Return a deterministic placeholder documentation update.

    For the Phase‑0 smoke test we avoid loading any LLM. The function
    returns a string that includes the model identifier and the prompt,
    making it clear that this is a placeholder. The output is fully
    deterministic and runs in well under a second on any CPU.

    Parameters
    ----------
    pair: CommitPair
        The input data for which documentation is to be generated.
    model_id: str, optional
        Identifier of the model (kept for API compatibility). Defaults to
        ``"phi3-mini"``.

    Returns
    -------
    str
        A deterministic placeholder documentation update.
    """
    prompt = build_prompt(pair)
    placeholder = (
        f"[Placeholder generation by model {model_id}]\n"
        f"{prompt}\n"
        "(This is a synthetic output used only for the quick‑start smoke test.)"
    )
    return placeholder
