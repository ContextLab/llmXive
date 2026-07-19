"""
Contract test for T020: Similarity Schema Validation.

Validates that `data/derived/yearly_similarity.csv` adheres to the expected schema.
"""
import os
import csv
import pytest
from pathlib import Path

CSV_PATH = Path("data/derived/yearly_similarity.csv")
SCHEMA_PATH = Path("tests/contract/schemas/similarity_schema.yaml")

# Fallback schema definition if YAML file is missing or for simplicity
EXPECTED_COLUMNS = ["year", "mean_off_diagonal_similarity", "intra_genre_variance"]
EXPECTED_TYPES = {
    "year": int,
    "mean_off_diagonal_similarity": float,
    "intra_genre_variance": float
}

def test_similarity_schema_validation():
    """
    Contract test: Validates the structure and data types of yearly_similarity.csv.
    
    Checks:
    1. File exists.
    2. Header matches expected columns.
    3. Data types are correct (year is int, others are float).
    4. No empty rows.
    """
    assert CSV_PATH.exists(), f"Output file {CSV_PATH} does not exist. Run T020 first."
    
    with open(CSV_PATH, mode='r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        # Check headers
        assert reader.fieldnames is not None, "CSV file is empty or has no headers."
        for col in EXPECTED_COLUMNS:
            assert col in reader.fieldnames, f"Missing column: {col}. Found: {reader.fieldnames}"
        
        # Validate data
        row_count = 0
        for row in reader:
            row_count += 1
            
            # Check year is int
            try:
                year_val = int(row["year"])
                assert year_val > 1900 and year_val <= 2030, f"Year out of range: {year_val}"
            except ValueError:
                raise AssertionError(f"Invalid year format: {row['year']}")
            
            # Check similarities are float
            try:
                float(row["mean_off_diagonal_similarity"])
                float(row["intra_genre_variance"])
            except ValueError:
                raise AssertionError("Similarity values must be numeric floats.")
            
            # Check for empty strings in critical fields
            assert row["year"] != "", "Year cannot be empty."
            assert row["mean_off_diagonal_similarity"] != "", "mean_off_diagonal_similarity cannot be empty."
            assert row["intra_genre_variance"] != "", "intra_genre_variance cannot be empty."

        assert row_count > 0, "CSV file contains no data rows."

if __name__ == "__main__":
    test_similarity_schema_validation()
    print("Contract test passed.")
