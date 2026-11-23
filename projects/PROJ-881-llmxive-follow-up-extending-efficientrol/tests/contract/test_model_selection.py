"""
Test to verify that the model selection documentation exists and references a Llama‑2‑7B (or 1.5B) model,
as required by functional requirement FR‑002.
"""

import re
from pathlib import Path


def test_model_selection_documentation():
    """
    Ensure that `docs/model_selection.md` exists and mentions a Llama‑2‑7B (or Llama‑2‑1.5B) model.
    """
    doc_path = Path("docs/model_selection.md")
    assert doc_path.is_file(), f"Documentation file not found at {doc_path}"

    content = doc_path.read_text(encoding="utf-8")

    # Look for a mention of Llama‑2‑7B or Llama‑2‑1.5B (allowing different dash styles)
    pattern = re.compile(r"Llama[-\s]?2[-\s]?(7B|1\.5B)", re.IGNORECASE)
    assert pattern.search(content), (
        "The model selection document must reference a Llama‑2‑7B (or 1.5B) model. "
        "Found content does not contain such a reference."
    )