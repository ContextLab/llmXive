import csv
from pathlib import Path

from ingestion.validate import main as validate_main
from utils.config import get_project_root

def test_validation_creates_count_and_validated_csv(tmp_path, monkeypatch):
    """
    Run the validation script on the existing raw dataset and verify that:
    - A validated CSV is created.
    - A valid_record_count.txt file is created.
    - The count matches the number of rows in the validated CSV (excluding header).
    """
    project_root = get_project_root()

    # Ensure we use the project's actual raw dataset
    raw_csv = project_root / "data" / "raw" / "dataset.csv"
    assert raw_csv.is_file(), "Raw dataset CSV must exist for the test."

    # Run the validation main function
    validate_main()

    # Paths to expected outputs
    validated_csv = project_root / "data" / "processed" / "validated.csv"
    count_file = project_root / "data" / "processed" / "valid_record_count.txt"

    # Check files exist
    assert validated_csv.is_file(), "Validated CSV was not created."
    assert count_file.is_file(), "Valid record count file was not created."

    # Read count
    with count_file.open("r", encoding="utf-8") as f:
        count = int(f.read().strip())

    # Count rows in validated CSV (skip header)
    with validated_csv.open(newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        rows = list(reader)
    validated_row_count = len(rows) - 1  # subtract header

    assert count == validated_row_count, (
        f"Count mismatch: count file={count} vs rows in CSV={validated_row_count}"
    )