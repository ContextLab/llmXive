"""Test that the power‑analysis report is created and contains a numeric estimate."""
from __future__ import annotations

import re

from llmxive_toolkit import paths

def test_power_report():
    report_path = paths.results("power_report.md")
    assert report_path.is_file(), f"{report_path} does not exist"
    text = report_path.read_text(encoding="utf-8")
    # Look for the line ``- estimated_power_n500: 0.xxxx``
    match = re.search(r"- estimated_power_n\d+: ([0-9]*\\.[0-9]+)", text)
    assert match, "Power estimate line not found in report"
    value = float(match.group(1))
    assert 0.0 <= value <= 1.0, "Power estimate out of bounds"