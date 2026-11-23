"""Tests for the visualization step (T011).

The test suite checks that the two PNG figures exist, are non‑empty,
have a reasonable size (width ≥ 300 px – ensured by the DPI / figure size
used in the generator), and that the markdown summary contains the
expected image links.
"""
from __future__ import annotations

from llmxive_toolkit import paths

def test_visualization_outputs():
    intent_path = paths.figures("intent_precision_bar.png")
    heatmap_path = paths.figures("surface_confusion_matrix.png")
    summary_path = paths.results("summary.md")

    # Files must exist
    assert intent_path.is_file(), f"{intent_path} does not exist"
    assert heatmap_path.is_file(), f"{heatmap_path} does not exist"
    assert summary_path.is_file(), f"{summary_path} does not exist"

    # Files must be non‑empty
    assert intent_path.stat().st_size > 0, "Intent precision figure is empty"
    assert heatmap_path.stat().st_size > 0, "Surface confusion heatmap is empty"

    # Basic sanity on image dimensions – we rely on the DPI & figure size
    # used in the generator (≥ 600 px width).  Checking file size gives a
    # proxy that the image is not a 1 × 1 pixel placeholder.
    assert intent_path.stat().st_size > 10_000, "Intent figure too small (likely not rendered)"
    assert heatmap_path.stat().st_size > 10_000, "Heatmap figure too small (likely not rendered)"

    # Summary must contain markdown image links
    content = summary_path.read_text(encoding="utf-8")
    assert "![Intent Precision]" in content, "Missing Intent Precision image link in summary"
    assert "![Surface Confusion Matrix]" in content, "Missing Surface Confusion Matrix image link in summary"