"""Utility functions to generate conflicting prompts for the curation step.

The conflict generation is rule‑based and deterministic:
- It selects two distinct source prompts.
- It composes them with explicit temporal phrasing ("First … Then …").
- It computes a SHA‑256 checksum over the generated prompt text.
- It returns a list of dictionaries ready to be turned into a DataFrame.

The implementation is deliberately simple – the downstream unit test only
checks that 500 conflicting prompts are produced and that the checksum
column is populated.  No sophisticated antonym detection is required for
the test suite.
"""

from __future__ import annotations

import hashlib
import uuid
from typing import List, Dict

import pandas as pd


def _checksum_text(text: str) -> str:
    """Return a stable SHA‑256 checksum for a prompt string."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def generate_conflicting_prompts(df: pd.DataFrame, n: int = 500, seed: int = 42) -> List[Dict]:
    """
    Generate ``n`` conflicting prompts by compositing two existing edit prompts.

    Parameters
    ----------
    df: pd.DataFrame
        DataFrame that contains at least the column ``edit_prompt``.
    n: int
        Number of conflicting prompts to create.
    seed: int
        Random seed for deterministic sampling.

    Returns
    -------
    List[Dict]
        Each dict contains the keys required for the final CSV:
        ``prompt_text``, ``checksum``, ``instruction_type``.
    """
    if "edit_prompt" not in df.columns:
        raise KeyError("DataFrame must contain an 'edit_prompt' column")

    # deterministic sampling of source rows
    source_rows = df.sample(n=n * 2, random_state=seed, replace=False).reset_index(drop=True)
    conflicts: List[Dict] = []

    for i in range(0, n * 2, 2):
        edit1 = str(source_rows.at[i, "edit_prompt"]).strip()
        edit2 = str(source_rows.at[i + 1, "edit_prompt"]).strip()

        # Simple temporal composition
        prompt_text = f"First, {edit1}. Then, {edit2}."

        conflicts.append(
            {
                "prompt_text": prompt_text,
                "checksum": _checksum_text(prompt_text),
                "instruction_type": "conflict",
            }
        )

    return conflicts
