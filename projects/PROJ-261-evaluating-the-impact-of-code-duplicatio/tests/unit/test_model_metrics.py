import csv
from pathlib import Path

import pytest

from model_metrics import compute_perplexity_batch
from semantic_cloner import compute_semantic_distance_batch


@pytest.fixture
def raw_csv(tmp_path: Path) -> Path:
    """Create a tiny raw CSV with a single short Python snippet."""
    path = tmp_path / "github-code-sample.csv"
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["file_path", "content"])
        writer.writeheader()
        writer.writerow(
            {"file_path": "c.py", "content": "print('hello world')"}
        )
    return path


def test_compute_perplexity_batch_writes_file(tmp_path: Path, raw_csv: Path):
    out_path = tmp_path / "perplexity_scores.csv"
    rc = compute_perplexity_batch(
        raw_path=raw_csv,
        output_path=out_path,
        model_name="distilgpt2",
    )
    assert rc == 0
    with out_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    assert len(rows) == 1
    assert "perplexity" in rows[0]
    # Perplexity should be a finite positive number.
    ppl = float(rows[0]["perplexity"])
    assert ppl > 0 and ppl != float("inf")


def test_compute_semantic_distance_batch_basic():
    """
    Verify that the semantic distance calculation returns a list of floats,
    that identical snippets have distance 0.0, and that a different snippet
    yields a positive distance.
    """
    snippets = [
        "def foo():\n    return 1",
        "def foo():\n    return 1",
        "def bar():\n    return 2",
    ]
    distances = compute_semantic_distance_batch(snippets)
    assert isinstance(distances, list)
    assert len(distances) == len(snippets)
    # Identical snippets should have distance 0.0
    assert distances[0] == 0.0
    assert distances[1] == 0.0
    # Different snippet should have a positive distance
    assert distances[2] > 0.0