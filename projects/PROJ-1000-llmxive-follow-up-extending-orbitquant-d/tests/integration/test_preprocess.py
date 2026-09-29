"""
Integration test for the preprocessing pipeline (T006b).

This test verifies that running the preprocessing script generates
the expected output files with valid structure.
"""
import os
import sys
import csv
import json
import tempfile
import shutil
from pathlib import Path
import pytest

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from config import Config
from data.preprocess import split_data, write_csv, main

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test data."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)

def test_split_data():
    """Test the split_data function returns correct ratios."""
    data = [{"id": i} for i in range(100)]
    train, test = split_data(data, train_ratio=0.8, seed=42)
    assert len(train) == 80
    assert len(test) == 20
    # Verify no overlap
    train_ids = {d["id"] for d in train}
    test_ids = {d["id"] for d in test}
    assert train_ids.isdisjoint(test_ids)

def test_write_csv_empty():
    """Test writing empty data creates an empty file."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as f:
        temp_path = Path(f.name)
    try:
        write_csv([], temp_path)
        assert temp_path.exists()
        assert temp_path.stat().st_size == 0
    finally:
        temp_path.unlink()

def test_write_csv_with_data(temp_data_dir):
    """Test writing data to CSV creates valid file."""
    test_data = [
        {"prompt": "A cat", "source": "coco"},
        {"prompt": "A dog", "source": "diverse"}
    ]
    output_path = temp_data_dir / "test.csv"
    write_csv(test_data, output_path)

    assert output_path.exists()
    with open(output_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    assert len(rows) == 2
    assert rows[0]["prompt"] == "A cat"
    assert rows[0]["source"] == "coco"

def test_preprocess_main_creates_files(temp_data_dir, monkeypatch):
    """
    Test that main() creates the expected files.
    We mock the data loading functions to avoid network calls in this unit/integration test,
    but verify the file creation logic works.
    """
    # Mock Config to use temp directory
    class MockConfig:
        data_path = temp_data_dir
        seed = 42

    # Mock the external loaders
    def mock_load_coco(config):
        return [{"prompt": f"COCO caption {i}", "source": "coco"} for i in range(10)]

    def mock_fetch_diverse():
        return [{"prompt": f"Div prompt {i}", "source": "diverse"} for i in range(10)]

    def mock_merge(coco, diverse):
        return coco + diverse

    # Patch imports in the module under test
    import data.preprocess as preprocess_module
    preprocess_module.load_coco_captions = mock_load_coco
    preprocess_module.fetch_diverse_prompts = mock_fetch_diverse
    preprocess_module.merge_and_deduplicate = mock_merge
    preprocess_module.Config = MockConfig

    try:
        result = main()

        # Verify result structure
        assert "total" in result
        assert "train" in result
        assert "test" in result
        assert "files" in result

        # Verify files exist
        assert Path(result["files"]["full"]).exists()
        assert Path(result["files"]["train"]).exists()
        assert Path(result["files"]["test"]).exists()

        # Verify content validity
        with open(result["files"]["full"], 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            full_rows = list(reader)
        assert len(full_rows) == 20

        with open(result["files"]["train"], 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            train_rows = list(reader)
        assert len(train_rows) == 16

        with open(result["files"]["test"], 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            test_rows = list(reader)
        assert len(test_rows) == 4

    finally:
        # Restore original functions
        preprocess_module.load_coco_captions = None
        preprocess_module.fetch_diverse_prompts = None
        preprocess_module.merge_and_deduplicate = None
        preprocess_module.Config = Config