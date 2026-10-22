"""
Pytest suite for verifying that the data acquisition scripts for T002
have successfully created the required artifacts with sufficient rows.
"""
import pathlib
import pandas as pd

def _row_count_csv(path: pathlib.Path) -> int:
    """Return number of data rows (excluding header) in a CSV file."""
    with open(path, "r", encoding="utf-8") as f:
        # Count lines, subtract header
        return sum(1 for _ in f) - 1

def test_coco_captions_parquet_exists():
    """Check that the COCO captions parquet file exists and has enough rows."""
    parquet_path = pathlib.Path("data/raw/coco_captions.parquet")
    assert parquet_path.is_file(), f"{parquet_path} not found"
    df = pd.read_parquet(parquet_path)
    assert len(df) >= 400, f"Expected >=400 rows, got {len(df)}"

def test_prompts_csv():
    """Validate prompts.csv header and row count."""
    csv_path = pathlib.Path("data/processed/prompts.csv")
    assert csv_path.is_file(), f"{csv_path} not found"
    with open(csv_path, "r", encoding="utf-8") as f:
        header = f.readline().strip()
    assert header == "image_id,caption", f"Unexpected header: {header}"
    rows = _row_count_csv(csv_path)
    assert rows >= 400, f"Expected >=400 rows, got {rows}"

def test_diverse_prompts_csv():
    """Validate diverse_prompts.csv header and row count."""
    csv_path = pathlib.Path("data/processed/diverse_prompts.csv")
    assert csv_path.is_file(), f"{csv_path} not found"
    with open(csv_path, "r", encoding="utf-8") as f:
        header = f.readline().strip()
    assert header == "prompt_id,caption,source", f"Unexpected header: {header}"
    rows = _row_count_csv(csv_path)
    assert rows >= 150, f"Expected >=150 rows, got {rows}"
