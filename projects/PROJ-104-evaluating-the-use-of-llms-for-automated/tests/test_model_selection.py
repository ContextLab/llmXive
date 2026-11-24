"""Test for model selection documentation.

This test validates that the markdown file
``docs/model_selection_and_limitations.md`` contains a table with the
required columns, that each listed model has ≤ 3 B parameters, and that
the document mentions the scale limitation.
"""
from __future__ import annotations

import re

from llmxive_toolkit import paths


def _read_markdown() -> str:
    """Read the model‑selection markdown document."""
    md_path = paths.docs("model_selection_and_limitations.md")
    assert md_path.is_file(), f"{md_path} does not exist"
    return md_path.read_text(encoding="utf-8")


def _extract_table(md: str) -> list[dict[str, str]]:
    """
    Extract the markdown table as a list of dictionaries.

    Returns a list where each element corresponds to a table row and maps
    column names to cell contents.
    """
    lines = md.splitlines()
    # Locate the first table header line (starts and ends with '|')
    header_idx = None
    for i, line in enumerate(lines):
        if line.strip().startswith("|") and line.strip().endswith("|"):
            header_idx = i
            break
    assert header_idx is not None, "No markdown table found in the document"

    # Header line and separator line
    header_line = lines[header_idx]
    separator_line = lines[header_idx + 1]
    assert re.fullmatch(r"\|[-\s|:]+\|", separator_line.strip()), "Table separator line malformed"

    # Parse column names
    headers = [h.strip().lower() for h in header_line.strip("|").split("|")]
    required_columns = {
        "model",
        "parameters (≈ b)",
        "4‑bit quantisation (bitsandbytes)",
        "expected per‑commit latency (cpu, s)",
    }
    missing = required_columns - set(headers)
    assert not missing, f"Missing required table columns: {missing}"

    rows: list[dict[str, str]] = []
    for line in lines[header_idx + 2 :]:
        if not line.strip().startswith("|"):
            # End of table
            break
        cells = [c.strip() for c in line.strip("|").split("|")]
        # Some rows may be empty (e.g., after the table); skip them
        if len(cells) != len(headers):
            continue
        row = dict(zip(headers, cells))
        rows.append(row)
    assert rows, "The markdown table contains no data rows"
    return rows


def test_models_parameter_limits():
    """Each listed model must have ≤ 3 B parameters."""
    md = _read_markdown()
    rows = _extract_table(md)

    for row in rows:
        param_str = row["parameters (≈ b)"]
        # Remove any non‑numeric characters (e.g., commas, spaces)
        param_clean = re.sub(r"[^\d.]", "", param_str)
        try:
            param_val = float(param_clean)
        except ValueError:
            raise AssertionError(f"Unable to parse parameter count '{param_str}'")
        assert param_val <= 3.0, f"Model {row['model']} exceeds 3 B parameters ({param_val})"


def test_scale_limitation_sentence():
    """Document must contain a sentence mentioning the scale limitation."""
    md = _read_markdown()
    # Look for a sentence that contains the phrase “scale limitation”
    # (case‑insensitive) and at least one verb to ensure it is a full sentence.
    pattern = re.compile(r"[^.]*\bscale limitation\b[^.]*\.", re.IGNORECASE)
    matches = pattern.findall(md)
    assert matches, "No sentence mentioning the scale limitation was found in the markdown"
    # Optionally, ensure the sentence discusses that models are of comparable size.
    sentence = matches[0]
    assert "comparable" in sentence.lower() or "similar" in sentence.lower(), (
        "The scale‑limitation sentence should note that the models are of comparable size."
    )