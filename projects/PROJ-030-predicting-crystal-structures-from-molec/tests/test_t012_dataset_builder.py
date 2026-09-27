"""
Tests for T012: code/ingestion/dataset_builder.py
"""

import os
import sys
import json
import tempfile
import pandas as pd
from pathlib import Path
import pytest

# Add code to path if not already
sys.path.insert(0, str(Path(__file__).parent.parent))

from ingestion.dataset_builder import handle_polymorphism, load_intermediate_data, save_dataset
from config import get_path_absolute

def test_handle_polymorphism_basic():
    """Test that duplicates with same (SMILES, Space Group) are removed."""
    records = [
        {"smiles": "CCO", "space_group": "P212121", "id": 1, "val": 10},
        {"smiles": "CCO", "space_group": "P212121", "id": 2, "val": 20}, # Duplicate
        {"smiles": "CCO", "space_group": "Pm-3m", "id": 3, "val": 30},  # Different space group
        {"smiles": "CC(=O)O", "space_group": "P212121", "id": 4, "val": 40}, # Different SMILES
    ]
    
    df = handle_polymorphism(records)
    
    assert len(df) == 3, f"Expected 3 unique rows, got {len(df)}"
    
    # Check that the first occurrence is kept
    cco_p21 = df[(df['smiles'] == 'CCO') & (df['space_group'] == 'P212121')]
    assert len(cco_p21) == 1
    assert cco_p21.iloc[0]['id'] == 1
    assert cco_p21.iloc[0]['val'] == 10

def test_handle_polymorphism_missing_fields():
    """Test that records with missing SMILES or Space Group are skipped."""
    records = [
        {"smiles": "CCO", "space_group": "P212121", "id": 1},
        {"smiles": "", "space_group": "P212121", "id": 2}, # Missing SMILES
        {"smiles": "CCO", "space_group": None, "id": 3},   # Missing Space Group
        {"smiles": "CCO", "space_group": "Pm-3m", "id": 4}, # Valid
    ]
    
    df = handle_polymorphism(records)
    
    assert len(df) == 2, f"Expected 2 valid rows, got {len(df)}"
    assert all(df['smiles'].notna())
    assert all(df['space_group'].notna())

def test_save_dataset(tmp_path):
    """Test saving the dataset to CSV."""
    df = pd.DataFrame([
        {"smiles": "CCO", "space_group": "P212121"},
        {"smiles": "CC(=O)O", "space_group": "Pm-3m"}
    ])
    
    output_file = tmp_path / "test_output.csv"
    save_dataset(df, output_file)
    
    assert output_file.exists()
    loaded_df = pd.read_csv(output_file)
    assert len(loaded_df) == 2
    assert list(loaded_df.columns) == ['smiles', 'space_group']

def test_load_intermediate_data(tmp_path):
    """Test loading from a JSONL file."""
    jsonl_file = tmp_path / "test.jsonl"
    data = [
        {"smiles": "A", "space_group": "S1"},
        {"smiles": "B", "space_group": "S2"}
    ]
    with open(jsonl_file, 'w') as f:
        for item in data:
            f.write(json.dumps(item) + "\n")
    
    records = load_intermediate_data(jsonl_file)
    assert len(records) == 2
    assert records[0]['smiles'] == 'A'

def test_load_intermediate_data_missing_file():
    """Test that FileNotFoundError is raised if file is missing."""
    with pytest.raises(FileNotFoundError):
        load_intermediate_data(Path("/nonexistent/file.jsonl"))
