import json
import os
import tempfile
from pathlib import Path

import pandas as pd
import pytest

from code.global_feature_injection import (
    inject_global_feature,
    load_dominant_eigenvalue,
    load_features,
    save_features,
)

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def sample_eigenvalue_file(temp_dir):
    path = temp_dir / "dominant_eigenvalue.json"
    data = {"dominant_eigenvalue": 12.345}
    with open(path, "w") as f:
        json.dump(data, f)
    return path

@pytest.fixture
def sample_features_file(temp_dir):
    path = temp_dir / "features.json"
    data = [
        {"id": 1, "variance": 0.5},
        {"id": 2, "variance": 0.8},
    ]
    df = pd.DataFrame(data)
    df.to_json(path, orient="records")
    return path

def test_load_dominant_eigenvalue_valid(sample_eigenvalue_file):
    import logging
    logger = logging.getLogger(__name__)
    val = load_dominant_eigenvalue(sample_eigenvalue_file, logger)
    assert val == 12.345

def test_load_dominant_eigenvalue_missing_key(temp_dir):
    path = temp_dir / "bad_eigenvalue.json"
    with open(path, "w") as f:
        json.dump({"other_key": 10}, f)
    import logging
    logger = logging.getLogger(__name__)
    with pytest.raises(ValueError):
        load_dominant_eigenvalue(path, logger)

def test_load_dominant_eigenvalue_file_not_found(temp_dir):
    path = temp_dir / "nonexistent.json"
    import logging
    logger = logging.getLogger(__name__)
    with pytest.raises(FileNotFoundError):
        load_dominant_eigenvalue(path, logger)

def test_load_features_valid(sample_features_file):
    import logging
    logger = logging.getLogger(__name__)
    df = load_features(sample_features_file, logger)
    assert len(df) == 2
    assert "variance" in df.columns

def test_load_features_file_not_found(temp_dir):
    path = temp_dir / "nonexistent.json"
    import logging
    logger = logging.getLogger(__name__)
    with pytest.raises(FileNotFoundError):
        load_features(path, logger)

def test_inject_global_feature():
    df = pd.DataFrame({"id": [1, 2], "val": [10, 20]})
    result = inject_global_feature(df, 99.9, None)
    assert "global_eigenvalue" in result.columns
    assert all(result["global_eigenvalue"] == 99.9)
    assert len(result) == 2

def test_save_and_reload_features(temp_dir, sample_features_file):
    import logging
    logger = logging.getLogger(__name__)
    
    df = load_features(sample_features_file, logger)
    df_injected = inject_global_feature(df, 5.5, logger)
    
    output_path = temp_dir / "output_features.json"
    save_features(df_injected, output_path, logger)
    
    assert output_path.exists()
    
    with open(output_path, "r") as f:
        loaded_data = json.load(f)
    
    assert len(loaded_data) == 2
    assert all(item["global_eigenvalue"] == 5.5 for item in loaded_data)
    assert loaded_data[0]["id"] == 1
    assert loaded_data[1]["variance"] == 0.8
