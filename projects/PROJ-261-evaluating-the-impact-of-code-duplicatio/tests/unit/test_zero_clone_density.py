import csv
import pathlib

from ast_cloner import compute_clone_density_batch

def test_zero_clone_density_handling(tmp_path):
    # Create a raw CSV with unique code snippets → zero clone pairs
    raw_path = tmp_path / "github-code-sample.csv"
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    with raw_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["file_path", "code"])
        writer.writeheader()
        writer.writerow({"file_path": "a.py", "code": "x = 1"})
        writer.writerow({"file_path": "b.py", "code": "y = 2"})
    compute_clone_density_batch(input_path=raw_path)

    out_csv = pathlib.Path("data/processed/clone_metrics.csv")
    with out_csv.open() as f:
        rows = list(csv.DictReader(f))
        for row in rows:
            assert float(row["clone_density"]) == 0.0
