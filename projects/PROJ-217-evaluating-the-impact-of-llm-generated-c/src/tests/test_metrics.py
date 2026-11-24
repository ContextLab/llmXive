"""
Test suite for src/data/metrics.py
"""
import json
import csv
from pathlib import Path
import pytest
from llmxive_toolkit import paths
from src.data.metrics import main as metrics_main

@pytest.fixture
def tiny_fixture(tmp_path: Path):
    data_dir = paths.root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
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
    metrics_main()
    csv_path = paths.data("readability_metrics.csv")
    assert csv_path.is_file()

    with csv_path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    assert len(rows) == 3
    
    def get_row(cond):
        return next(r for r in rows if r["condition"] == cond)

    # LLM and Human comments are identical in fixture
    for cond in ("llm", "human"):
        row = get_row(cond)
        # vs_human should be 1.0 because llm_comment == human_comment
        assert abs(float(row["BLEU_vs_human"]) - 1.0) < 0.001
        assert abs(float(row["ROUGE_L_vs_human"]) - 1.0) < 0.001
        assert abs(float(row["Semantic_Similarity_vs_human"]) - 1.0) < 0.001
        # vs_source should NOT be 1.0 because "Adds..." != "def add..."
        assert float(row["BLEU_vs_source"]) < 0.99
        assert int(row["Comment_Length"]) > 0
        assert float(row["Flesch_Kincaid_Grade"]) >= 0

    # None condition
    none_row = get_row("none")
    assert none_row["BLEU_vs_human"] == ""
    assert int(none_row["Comment_Length"]) == 0
    assert float(none_row["Flesch_Kincaid_Grade"]) == 0.0

def test_csv_header_contains_all_columns():
    expected = {
        "snippet_id", "condition", "code", "human_comment", "llm_comment", "no_comment",
        "BLEU_vs_source", "BLEU_vs_human", "ROUGE_L_vs_source", "ROUGE_L_vs_human",
        "Semantic_Similarity_vs_source", "Semantic_Similarity_vs_human",
        "Comment_Length", "Flesch_Kincaid_Grade",
    }
    csv_path = paths.data("readability_metrics.csv")
    if not csv_path.is_file():
        # Minimal run to generate file
        dummy = paths.root / "data" / "llm_comments.jsonl"
        dummy.parent.mkdir(parents=True, exist_ok=True)
        dummy.write_text('{"snippet_id":"1","code":"a","human_comment":"b","llm_comment":"c","no_comment":""}\n')
        metrics_main()
    
    with csv_path.open(newline="", encoding="utf-8") as f:
        header = next(csv.reader(f))
    assert set(header) == expected