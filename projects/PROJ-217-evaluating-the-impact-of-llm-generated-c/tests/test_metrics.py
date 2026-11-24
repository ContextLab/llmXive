"""
Test suite for src/data/metrics.py

The tests use a tiny in‑memory fixture written to ``data/llm_comments.jsonl``.
They verify that:

* Identical strings yield BLEU, ROUGE‑L and semantic similarity scores of 1.0.
* The ``none`` condition produces null (empty) metric fields and zero comment length.
* The CSV header contains all required columns.
"""

import json
import csv
from pathlib import Path

import pytest

from llmxive_toolkit import paths
from src.data.metrics import main as metrics_main

@pytest.fixture
def tiny_fixture(tmp_path: Path):
    # Override the project's data directory for the test.
    data_dir = paths.root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    # Prepare a minimal llm_comments.jsonl with a single snippet.
    records = [
        {
            "snippet_id": "test-001",
            "code": "def add(a, b):\n    return a + b",
            "human_comment": "Adds two numbers together.",
            "llm_comment": "Adds two numbers together.",
            "no_comment": ""
        }
    ]
    llm_path = data_dir / "llm_comments.jsonl"
    with llm_path.open("w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec) + "\n")
    yield llm_path

def test_metrics_produce_expected_values(tiny_fixture):
    # Run the metrics script – it will write the CSV under data/
    metrics_main()

    csv_path = paths.data("readability_metrics.csv")
    assert csv_path.is_file(), "CSV output was not created"

    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Expect three rows (llm, human, none)
    assert len(rows) == 3

    # Helper to find a row by condition
    def get_row(cond):
        for r in rows:
            if r["condition"] == cond:
                return r
        raise KeyError(f"Condition {cond} not found")

    # Identical strings → scores of 1.0 (within tolerance)
    for cond in ("llm", "human"):
        row = get_row(cond)
        assert abs(float(row["BLEU_vs_source"]) - 1.0) < 0.001
        assert abs(float(row["BLEU_vs_human"]) - 1.0) < 0.001
        assert abs(float(row["ROUGE_L_vs_source"]) - 1.0) < 0.001
        assert abs(float(row["ROUGE_L_vs_human"]) - 1.0) < 0.001
        assert abs(float(row["Semantic_Similarity_vs_source"]) - 1.0) < 0.001
        assert abs(float(row["Semantic_Similarity_vs_human"]) - 1.0) < 0.001
        # Comment length should be > 0
        assert int(row["Comment_Length"]) > 0
        # Flesch‑Kincaid grade should be a float (non‑negative)
        assert float(row["Flesch_Kincaid_Grade"]) >= 0

    # ``none`` baseline
    none_row = get_row("none")
    metric_fields = [
        "BLEU_vs_source",
        "BLEU_vs_human",
        "ROUGE_L_vs_source",
        "ROUGE_L_vs_human",
        "Semantic_Similarity_vs_source",
        "Semantic_Similarity_vs_human",
    ]
    for mf in metric_fields:
        # Empty string in CSV is interpreted as None by the test
        assert none_row[mf] == "" or none_row[mf] is None
    assert int(none_row["Comment_Length"]) == 0
    assert float(none_row["Flesch_Kincaid_Grade"]) == 0.0

def test_csv_header_contains_all_columns():
    # Ensure the header matches the contract (order is not important)
    expected = {
        "snippet_id",
        "condition",
        "code",
        "human_comment",
        "llm_comment",
        "no_comment",
        "BLEU_vs_source",
        "BLEU_vs_human",
        "ROUGE_L_vs_source",
        "ROUGE_L_vs_human",
        "Semantic_Similarity_vs_source",
        "Semantic_Similarity_vs_human",
        "Comment_Length",
        "Flesch_Kincaid_Grade",
    }
    csv_path = paths.data("readability_metrics.csv")
    # If the CSV does not exist yet, generate it with an empty fixture.
    if not csv_path.is_file():
        # Write a minimal fixture so the script can run.
        dummy = paths.root / "data" / "llm_comments.jsonl"
        dummy.parent.mkdir(parents=True, exist_ok=True)
        dummy.write_text("")
        from src.data.metrics import main as metrics_main
        metrics_main()
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
    assert set(header) == expected, "CSV header missing required columns"