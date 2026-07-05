import csv
import os
from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "manual_validation"

def test_source_urls_exists():
    path = DATA_DIR / "source_urls.csv"
    assert path.exists(), "source_urls.csv must exist"
    with open(path, 'r') as f:
        reader = csv.reader(f)
        rows = list(reader)
        assert len(rows) >= 1, "source_urls.csv must have at least a header"
        # Check for Q19873191
        urls = [row[0] for row in rows[1:]]
        assert any("Q19873191" in url for url in urls), "Q19873191 must be in source_urls.csv"

def test_real_world_labels_exists_and_count():
    path = DATA_DIR / "real_world_labels.csv"
    assert path.exists(), "real_world_labels.csv must exist"
    with open(path, 'r') as f:
        reader = csv.reader(f)
        next(reader) # skip header
        count = sum(1 for _ in reader)
        assert count >= 100, f"real_world_labels.csv must have at least 100 rows, found {count}"

def test_real_world_labels_schema():
    path = DATA_DIR / "real_world_labels.csv"
    expected_fields = [
        "url", "source_type",
        "extracted_baseline_n", "extracted_variant_n", "extracted_baseline_rate", "extracted_variant_rate", "extracted_p_value",
        "annotator_1_baseline_n", "annotator_1_variant_n", "annotator_1_baseline_rate", "annotator_1_variant_rate", "annotator_1_p_value",
        "annotator_2_baseline_n", "annotator_2_variant_n", "annotator_2_baseline_rate", "annotator_2_variant_rate", "annotator_2_p_value",
        "ground_truth_baseline_n", "ground_truth_variant_n", "ground_truth_baseline_rate", "ground_truth_variant_rate", "ground_truth_p_value",
        "ground_truth_domain", "ground_truth_year"
    ]
    with open(path, 'r') as f:
        reader = csv.DictReader(f)
        assert reader.fieldnames == expected_fields, f"Schema mismatch. Expected {expected_fields}, got {reader.fieldnames}"
        # Check a row
        for row in reader:
            assert row['ground_truth_domain'] != '', "ground_truth_domain cannot be empty"
            break # just check one