"""
test_ast_cloner_output.py
-------------------------
Integration test that verifies the AST‑clone detector creates the expected
CSV file when invoked via the pipeline entry‑point.
"""
import csv
from pathlib import Path

def test_clone_metrics_file_created(tmp_path, monkeypatch):
    # Ensure a clean workspace
    data_dir = Path("data")
    # Remove any pre‑existing processed directory
    processed_dir = data_dir / "processed"
    if processed_dir.exists():
        for p in processed_dir.iterdir():
            p.unlink()
        processed_dir.rmdir()

    # Run the pipeline
    from code.main import main as pipeline_main
    pipeline_main()

    # Verify the CSV exists and contains at least the header row
    output_file = data_dir / "processed" / "clone_metrics.csv"
    assert output_file.is_file(), "clone_metrics.csv was not created"

    with output_file.open(newline="") as f:
        reader = csv.reader(f)
        rows = list(reader)
        assert rows, "CSV file is empty"
        # Header must be present
        assert rows[0] == ["file_path", "clone_density"]
