import csv
import pathlib

from model_metrics import compute_perplexity_batch

def test_perplexity_output(tmp_path, monkeypatch):
    # Prepare a tiny raw CSV
    raw_path = tmp_path / "github-code-sample.csv"
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    with raw_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["file_path", "code"])
        writer.writeheader()
        writer.writerow({"file_path": "a.py", "code": "print('hi')"})
    # Force the function to read our temporary file
    compute_perplexity_batch(input_path=raw_path)

    out_path = pathlib.Path("data/processed/perplexity_scores.csv")
    assert out_path.is_file()
    with out_path.open() as f:
        rows = list(csv.DictReader(f))
        assert len(rows) == 1
        assert "perplexity" in rows[0]
