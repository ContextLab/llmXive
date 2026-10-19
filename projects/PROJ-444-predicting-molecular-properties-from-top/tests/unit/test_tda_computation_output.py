"""
Unit test to ensure that the TDA computation script creates the expected output files.
"""
import pathlib
import json

def test_topological_features_file_exists():
    path = pathlib.Path("data/processed/topological_features_10x10.csv")
    assert path.is_file(), f"{path} does not exist"

def test_legacy_persistence_images_file_exists():
    path = pathlib.Path("data/processed/persistence_images_10x10.csv")
    assert path.is_file(), f"{path} does not exist"

def test_output_is_nonempty():
    path = pathlib.Path("data/processed/topological_features_10x10.csv")
    with path.open() as f:
        header = f.readline()
        first = f.readline()
    assert header.strip() != "", "CSV header is empty"
    assert first.strip() != "", "CSV contains no data rows"