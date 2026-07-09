import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
import pytest
import numpy as np
import pandas as pd

# Add parent to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from evaluation.visualize_results import validate_plot, plot_error_distribution, plot_model_comparison, plot_molecule_importance

class TestVisualizationValidation:
    @pytest.fixture
    def temp_dir(self):
        temp_path = tempfile.mkdtemp()
        yield temp_path
        shutil.rmtree(temp_path)

    def test_validate_plot_file_not_exists(self, temp_dir):
        """Test validation fails if file does not exist."""
        path = Path(temp_dir) / "nonexistent.png"
        assert not validate_plot(path)

    def test_validate_plot_file_too_small(self, temp_dir):
        """Test validation fails if file is smaller than 1KB."""
        path = Path(temp_dir) / "small.png"
        # Create a tiny file
        with open(path, 'wb') as f:
            f.write(b"tiny")
        assert not validate_plot(path)

    def test_validate_plot_file_valid(self, temp_dir):
        """Test validation passes if file is > 1KB."""
        path = Path(temp_dir) / "valid.png"
        # Create a file > 1KB
        with open(path, 'wb') as f:
            f.write(b"x" * 2048) # 2KB
        assert validate_plot(path)

class TestPlotGeneration:
    @pytest.fixture
    def temp_dir(self):
        temp_path = tempfile.mkdtemp()
        yield temp_path
        shutil.rmtree(temp_dir)

    def test_plot_error_distribution(self, temp_dir):
        """Test that error distribution plot is generated and valid."""
        rf_errors = np.random.rand(100)
        gnn_errors = np.random.rand(100)
        output_path = Path(temp_dir) / "error_dist.png"
        
        result = plot_error_distribution(rf_errors, gnn_errors, output_path)
        assert result is True
        assert output_path.exists()
        assert output_path.stat().st_size > 1024

    def test_plot_model_comparison(self, temp_dir):
        """Test that model comparison plot is generated and valid."""
        metrics_data = {
            "rf": {"rmse": 0.5, "r2": 0.8},
            "gnn": {"rmse": 0.4, "r2": 0.85}
        }
        metrics_path = Path(temp_dir) / "metrics.json"
        with open(metrics_path, 'w') as f:
            json.dump(metrics_data, f)
        
        output_path = Path(temp_dir) / "comparison.png"
        result = plot_model_comparison(metrics_path, output_path)
        
        assert result is True
        assert output_path.exists()
        assert output_path.stat().st_size > 1024

    def test_plot_molecule_importance(self, temp_dir):
        """Test that molecule importance plot is generated and valid."""
        smiles = "CCO" # Ethanol
        importance_scores = np.array([0.1, 0.5, 0.9])
        output_path = Path(temp_dir) / "mol_importance.png"
        
        result = plot_molecule_importance(smiles, importance_scores, output_path)
        
        assert result is True
        assert output_path.exists()
        assert output_path.stat().st_size > 1024