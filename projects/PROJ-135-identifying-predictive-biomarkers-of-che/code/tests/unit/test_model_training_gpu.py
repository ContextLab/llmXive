"""
Unit tests for GPU-accelerated model training (T052).
Tests verify that the GPU module exists, imports correctly, and handles
missing GPU hardware gracefully.
"""

import pytest
import os
import sys
import tempfile
from pathlib import Path
import json
import numpy as np

# Import the module under test
# We use a try-except block to handle cases where GPU libs are not installed
try:
    from src.model_training_gpu import HAS_GPU, load_training_data_gpu, train_model_gpu, save_model_gpu
    GPU_AVAILABLE = True
except ImportError:
    GPU_AVAILABLE = False

@pytest.fixture
def temp_project_dir():
    """Create a temporary project structure for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        data_dir = root / "data" / "processed"
        results_dir = root / "results" / "models"
        meta_dir = root / "results" / "meta_analysis"

        data_dir.mkdir(parents=True)
        results_dir.mkdir(parents=True)
        meta_dir.mkdir(parents=True)

        # Create a mock gene panel
        panel_data = {
            "selected": [
                {"gene_symbol": "GENE_A", "meta_p_value": 0.001, "log2FC_mean": 1.5, "selected": True},
                {"gene_symbol": "GENE_B", "meta_p_value": 0.002, "log2FC_mean": 1.2, "selected": True},
                {"gene_symbol": "GENE_C", "meta_p_value": 0.003, "log2FC_mean": 1.1, "selected": True}
            ]
        }
        with open(meta_dir / "gene_panel.json", 'w') as f:
            json.dump(panel_data, f)

        # Create mock training data for a tumor type
        tumor_type = "TEST_TUMOR"
        # Wide format: Rows=Genes, Cols=Samples
        import pandas as pd
        expr_data = {
            "GENE_A": [1.0, 2.0, 3.0, 4.0, 5.0],
            "GENE_B": [2.0, 3.0, 4.0, 5.0, 6.0],
            "GENE_C": [3.0, 4.0, 5.0, 6.0, 7.0],
            "GENE_D": [4.0, 5.0, 6.0, 7.0, 8.0] # Extra gene to test filtering
        }
        df = pd.DataFrame(expr_data, index=["S1", "S2", "S3", "S4", "S5"]).T
        df.to_csv(data_dir / f"{tumor_type}_training_vst.csv")

        # Metadata
        meta_data = {
            "sample_id": ["S1", "S2", "S3", "S4", "S5"],
            "response_label": [0, 1, 0, 1, 1]
        }
        meta_df = pd.DataFrame(meta_data)
        meta_df.to_csv(data_dir / f"{tumor_type}_training_metadata.csv")

        yield root

def test_has_gpu_attribute():
    """Test that the module correctly detects GPU availability."""
    # If we imported, HAS_GPU should be a boolean
    if GPU_AVAILABLE:
        assert isinstance(HAS_GPU, bool)
    else:
        # If import failed, we can't test this directly, but the module should handle it
        pass

@pytest.mark.skipif(not GPU_AVAILABLE, reason="GPU libraries not available")
def test_load_training_data_gpu(temp_project_dir):
    """Test loading training data into GPU arrays."""
    from src.model_training_gpu import load_training_data_gpu
    import cupy as cp

    gene_panel = ["GENE_A", "GENE_B", "GENE_C"]
    X, y, sample_ids = load_training_data_gpu(
        tumor_type="TEST_TUMOR",
        gene_panel=gene_panel,
        data_dir=temp_project_dir / "data" / "processed"
    )

    # Check types
    assert isinstance(X, cp.ndarray), "X should be a CuPy array"
    assert isinstance(y, cp.ndarray), "y should be a CuPy array"
    assert len(X.shape) == 2, "X should be 2D"
    assert X.shape[0] == 5, "Should have 5 samples"
    assert X.shape[1] == 3, "Should have 3 genes (filtered)"
    assert len(sample_ids) == 5

@pytest.mark.skipif(not GPU_AVAILABLE, reason="GPU libraries not available")
def test_train_model_gpu(temp_project_dir):
    """Test GPU model training."""
    from src.model_training_gpu import load_training_data_gpu, train_model_gpu
    import cupy as cp

    gene_panel = ["GENE_A", "GENE_B", "GENE_C"]
    X, y, _ = load_training_data_gpu(
        tumor_type="TEST_TUMOR",
        gene_panel=gene_panel,
        data_dir=temp_project_dir / "data" / "processed"
    )

    result = train_model_gpu(X, y, alpha=0.1, l1_ratio=0.5)

    assert "coef" in result
    assert "intercept" in result
    assert "params" in result
    assert "training_time_sec" in result
    assert result["backend"] == "cuml_gpu"
    assert len(result["coef"]) == 3

def test_save_model_gpu(temp_project_dir):
    """Test saving model to disk."""
    import pickle
    from src.model_training_gpu import save_model_gpu

    model_data = {
        "coef": [0.1, 0.2, 0.3],
        "intercept": 0.5,
        "params": {"alpha": 0.1, "l1_ratio": 0.5},
        "training_time_sec": 1.0,
        "backend": "cuml_gpu"
    }
    output_path = temp_project_dir / "results" / "models" / "test_model.pkl"

    save_model_gpu(model_data, output_path)

    assert output_path.exists()
    with open(output_path, 'rb') as f:
        loaded = pickle.load(f)
    assert loaded["coef"] == model_data["coef"]
    assert loaded["backend"] == "cuml_gpu"