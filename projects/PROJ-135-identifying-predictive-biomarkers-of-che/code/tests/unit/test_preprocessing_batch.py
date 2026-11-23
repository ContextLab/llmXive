import os
import sys
import json
import tempfile
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

from src.preprocessing import (
    load_batch_labels,
    apply_quantile_matching,
    write_batch_correction_config,
    update_summary_md
)
from src.config import get_project_root

@pytest.fixture
def sample_combined_df():
    """Create a mock VST matrix with 10 samples, 5 genes."""
    np.random.seed(42)
    data = np.random.randn(10, 5)
    index = pd.Index([
        'TCGA-01', 'TCGA-02', 'TCGA-03', 'TCGA-04', 'TCGA-05',
        'GSE12345-01', 'GSE12345-02', 'GSE12345-03', 'GSE12345-04', 'GSE12345-05'
    ], name='sample_id')
    columns = pd.Index(['GENE1', 'GENE2', 'GENE3', 'GENE4', 'GENE5'], name='gene')
    return pd.DataFrame(data, index=index, columns=columns)

@pytest.fixture
def temp_project_dir(tmp_path):
    """Create a temporary project structure."""
    # Mimic project root structure
    (tmp_path / "results").mkdir()
    (tmp_path / "data" / "processed").mkdir(parents=True)
    return tmp_path

def test_load_batch_labels_tcga_and_geo(sample_combined_df):
    """Test that batch labels are correctly inferred from sample IDs."""
    batches = load_batch_labels(sample_combined_df)
    assert len(batches) == 10
    assert (batches[:5] == 'TCGA').all()
    assert (batches[5:] == 'GSE12345').all()

def test_apply_quantile_matching(sample_combined_df):
    """Test that quantile matching runs without error and returns same shape."""
    batches = load_batch_labels(sample_combined_df)
    corrected = apply_quantile_matching(sample_combined_df, batches)
    assert corrected.shape == sample_combined_df.shape
    assert set(corrected.index) == set(sample_combined_df.index)
    assert set(corrected.columns) == set(sample_combined_df.columns)

def test_write_batch_correction_config(temp_project_dir):
    """Test that config file is written correctly."""
    # Temporarily override get_project_root
    original_root_func = get_project_root
    import src.preprocessing as prep_module
    prep_module.get_project_root = lambda: temp_project_dir

    config = {"method": "test", "param": 123}
    write_batch_correction_config("test_method", config)

    config_file = temp_project_dir / "results" / "batch_correction_config.json"
    assert config_file.exists()
    with open(config_file) as f:
        data = json.load(f)
    assert data["method"] == "test_method"
    assert data["parameters"]["method"] == "test"

    # Restore
    prep_module.get_project_root = original_root_func

def test_update_summary_md(temp_project_dir):
    """Test that summary.md is created/updated correctly."""
    import src.preprocessing as prep_module
    original_root_func = get_project_root
    prep_module.get_project_root = lambda: temp_project_dir

    update_summary_md("TestMethod", "Test note")

    summary_file = temp_project_dir / "results" / "summary.md"
    assert summary_file.exists()
    with open(summary_file) as f:
        content = f.read()
    assert "## Batch Correction" in content
    assert "TestMethod" in content
    assert "Test note" in content

    prep_module.get_project_root = original_root_func
