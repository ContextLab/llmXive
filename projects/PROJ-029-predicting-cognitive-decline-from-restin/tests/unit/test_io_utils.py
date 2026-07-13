"""
Unit tests for I/O utilities.
"""
import pytest
import pandas as pd
import json
from pathlib import Path
from utils.io import save_csv, load_csv, save_json, load_json, ensure_dir

def test_save_load_csv(tmp_path):
    """Test CSV save and load."""
    df = pd.DataFrame({'a': [1, 2], 'b': [3, 4]})
    path = tmp_path / "test.csv"
    
    save_csv(df, path)
    loaded = load_csv(path)
    
    assert loaded.equals(df)

def test_save_load_json(tmp_path):
    """Test JSON save and load."""
    data = {'key': 'value', 'num': 123}
    path = tmp_path / "test.json"
    
    save_json(data, path)
    loaded = load_json(path)
    
    assert loaded == data

def test_ensure_dir(tmp_path):
    """Test directory creation."""
    new_dir = tmp_path / "new" / "nested"
    ensure_dir(new_dir)
    assert new_dir.exists()
