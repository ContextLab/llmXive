"""
Unit tests for the Study Counter module (T014a).
"""
import csv
import json
import os
import tempfile
from pathlib import Path
import sys

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from analysis.study_counter import count_unique_studies, save_study_count, load_extracted_studies

def test_count_unique_studies_basic():
    """Test counting unique (Author, Year) pairs."""
    studies = [
        {"Author": "Smith", "Year": "2020"},
        {"Author": "Jones", "Year": "2021"},
        {"Author": "Smith", "Year": "2020"},  # Duplicate
        {"Author": "Lee", "Year": "2022"},
    ]
    count = count_unique_studies(studies)
    assert count == 3, f"Expected 3 unique studies, got {count}"

def test_count_unique_studies_missing_fields():
    """Test handling of missing Author or Year."""
    studies = [
        {"Author": "Smith", "Year": "2020"},
        {"Author": "", "Year": "2021"},  # Missing author
        {"Author": "Lee", "Year": ""},   # Missing year
        {"Author": "Kim", "Year": "2022"},
    ]
    count = count_unique_studies(studies)
    # Should only count Smith and Kim
    assert count == 2, f"Expected 2 unique studies, got {count}"

def test_count_unique_studies_empty():
    """Test counting with empty list."""
    count = count_unique_studies([])
    assert count == 0, f"Expected 0 studies, got {count}"

def test_save_and_load_study_count():
    """Test saving to JSON and loading back."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_count.json"
        save_study_count(15, output_path)

        assert output_path.exists(), "Output file was not created"

        with open(output_path, 'r') as f:
            data = json.load(f)

        assert data["N"] == 15, f"Expected N=15, got {data['N']}"

def test_load_extracted_studies(tmp_path):
    """Test loading studies from a CSV file."""
    csv_path = tmp_path / "studies.csv"
    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["Author", "Year", "Tract"])
        writer.writeheader()
        writer.writerow({"Author": "Test", "Year": "2023", "Tract": "Arc"})
        writer.writerow({"Author": "Test2", "Year": "2024", "Tract": "Cing"})

    studies = load_extracted_studies(csv_path)
    assert len(studies) == 2, f"Expected 2 studies, got {len(studies)}"
    assert studies[0]["Author"] == "Test"
    assert studies[1]["Year"] == "2024"

def test_load_extracted_studies_missing_file():
    """Test that FileNotFoundError is raised for missing file."""
    try:
        load_extracted_studies(Path("/nonexistent/path/file.csv"))
        assert False, "Expected FileNotFoundError"
    except FileNotFoundError:
        pass  # Expected

if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])