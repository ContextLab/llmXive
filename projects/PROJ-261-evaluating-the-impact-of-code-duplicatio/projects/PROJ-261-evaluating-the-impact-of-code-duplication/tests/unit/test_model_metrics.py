import csv
import pathlib
import pytest

from model_metrics import compute_perplexity_batch

def test_perplexity_output(tmp_path, monkeypatch):
    """
    Verify that the normal execution path produces a CSV with a
    ``perplexity`` column.
    """
    # Create a minimal raw CSV input.
    raw_path = tmp_path / "github-code-sample.csv"
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    with raw_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["file_path", "code"])
        writer.writeheader()
        writer.writerow({"file_path": "a.py", "code": "print('hi')"})
    # Run the function.
    compute_perplexity_batch(input_path=raw_path)

    out_path = pathlib.Path("data/processed/perplexity_scores.csv")
    assert out_path.is_file()
    with out_path.open() as f:
        rows = list(csv.DictReader(f))
        assert len(rows) == 1
        assert "perplexity" in rows[0]

def test_model_loading_failure(monkeypatch, tmp_path):
    """
    Edge‑case: simulate a failure when loading the model in 8‑bit mode.
    The function should raise a RuntimeError.
    """
    # Prepare a tiny input CSV (content does not matter – the failure occurs
    # before the file is even read).
    raw_path = tmp_path / "github-code-sample.csv"
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    with raw_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["file_path", "code"])
        writer.writeheader()
        writer.writerow({"file_path": "b.py", "code": "print('bye')"})

    # Monkey‑patch the transformers model loader to raise an exception.
    import importlib

    transformers = importlib.import_module("transformers")
    original_from_pretrained = transformers.AutoModelForCausalLM.from_pretrained

    def broken_from_pretrained(*args, **kwargs):
        raise OSError("simulated model loading failure")

    monkeypatch.setattr(
        transformers.AutoModelForCausalLM,
        "from_pretrained",
        broken_from_pretrained,
    )

    # The function is expected to propagate the failure as RuntimeError.
    with pytest.raises(RuntimeError, match="Failed to load model"):
        compute_perplexity_batch(input_path=raw_path)

    # Restore the original method to avoid side effects for other tests.
    monkeypatch.setattr(
        transformers.AutoModelForCausalLM,
        "from_pretrained",
        original_from_pretrained,
    )