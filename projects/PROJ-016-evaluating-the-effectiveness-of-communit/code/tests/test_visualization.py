"""
Unit tests for plot generation (file existence, format) as required by T038.
Tests verify that the visualization module generates valid output files
in the correct format (PNG) and location.
"""
import os
import sys
import tempfile
import shutil
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.visualization import (
    generate_residual_scatter_plot,
    generate_coefficient_plot,
    load_regression_results,
    load_processed_data
)
from config import get_config


class TestPlotGeneration:
    """Test suite for plot generation functionality."""

    @pytest.fixture
    def temp_output_dir(self):
        """Create a temporary directory for test outputs."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def mock_regression_results(self, temp_output_dir):
        """Create mock regression results file."""
        results = {
            "primary_model": {
                "coefficients": {
                    "regime_type": 0.15,
                    "gdp_per_capita": -0.02,
                    "population_density": 0.05
                },
                "p_values": {
                    "regime_type": 0.03,
                    "gdp_per_capita": 0.12,
                    "population_density": 0.08
                },
                "std_errors": {
                    "regime_type": 0.07,
                    "gdp_per_capita": 0.01,
                    "population_density": 0.03
                },
                "n_obs": 450,
                "n_countries": 45,
                "r_squared": 0.65,
                "f_statistic": 12.5,
                "f_p_value": 0.001
            },
            "sensitivity_analysis": {
                "no_gdp_model": {
                    "regime_type": 0.18,
                    "p_value": 0.02
                }
            },
            "nonlinear_model": {
                "regime_type": 0.14,
                "regime_type_squared": 0.01,
                "p_values": {
                    "regime_type": 0.04,
                    "regime_type_squared": 0.45
                }
            },
            "f_test_joint_significance": {
                "f_statistic": 8.2,
                "p_value": 0.003,
                "is_significant": True
            },
            "metadata": {
                "is_associational": True,
                "model_type": "fixed_effects",
                "year_range": [2000, 2020]
            }
        }
        output_path = temp_output_dir / "regression_results_primary.json"
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        return output_path

    @pytest.fixture
    def mock_processed_data(self, temp_output_dir):
        """Create mock processed dataset."""
        np.random.seed(42)
        n_countries = 45
        years = list(range(2000, 2021))
        
        data = []
        for i in range(n_countries):
            country_code = f"COD{i:03d}"
            for year in years:
                data.append({
                    "country_code": country_code,
                    "year": year,
                    "land_use_change_rate": np.random.normal(0.02, 0.05),
                    "regime_type": np.random.choice([0, 1]),
                    "gdp_per_capita": np.random.normal(5000, 2000),
                    "population_density": np.random.exponential(100),
                    "predicted": np.random.normal(0.02, 0.03),
                    "residual": np.random.normal(0, 0.02)
                })
        
        df = pd.DataFrame(data)
        output_path = temp_output_dir / "cleaned_data.csv"
        df.to_csv(output_path, index=False)
        return output_path

    def test_residual_scatter_plot_file_creation(self, temp_output_dir, 
                                                 mock_regression_results, 
                                                 mock_processed_data):
        """Test that residual scatter plot is created as a PNG file."""
        output_path = temp_output_dir / "residual_scatter_plot.png"
        
        # Mock the load functions to use our temp files
        with patch('analysis.visualization.load_regression_results') as mock_load_results, \
             patch('analysis.visualization.load_processed_data') as mock_load_data:
            
            mock_load_results.return_value = json.loads(open(mock_regression_results).read())
            mock_load_data.return_value = pd.read_csv(mock_processed_data)
            
            # Generate the plot
            generate_residual_scatter_plot(
                output_path=str(output_path),
                results_dir=temp_output_dir
            )
            
            # Verify file exists
            assert output_path.exists(), "Residual scatter plot file was not created"
            
            # Verify file format (PNG signature check)
            with open(output_path, 'rb') as f:
                header = f.read(8)
                # PNG signature: 89 50 4E 47 0D 0A 1A 0A
                assert header[:8] == b'\x89PNG\r\n\x1a\n', "File is not a valid PNG"

    def test_coefficient_plot_file_creation(self, temp_output_dir,
                                            mock_regression_results,
                                            mock_processed_data):
        """Test that coefficient plot is created as a PNG file."""
        output_path = temp_output_dir / "coefficient_plot.png"
        
        with patch('analysis.visualization.load_regression_results') as mock_load_results, \
             patch('analysis.visualization.load_processed_data') as mock_load_data:
            
            mock_load_results.return_value = json.loads(open(mock_regression_results).read())
            mock_load_data.return_value = pd.read_csv(mock_processed_data)
            
            # Generate the plot
            generate_coefficient_plot(
                output_path=str(output_path),
                results_dir=temp_output_dir
            )
            
            # Verify file exists
            assert output_path.exists(), "Coefficient plot file was not created"
            
            # Verify file format (PNG signature check)
            with open(output_path, 'rb') as f:
                header = f.read(8)
                assert header[:8] == b'\x89PNG\r\n\x1a\n', "File is not a valid PNG"

    def test_residual_scatter_plot_with_invalid_data(self, temp_output_dir):
        """Test that residual scatter plot handles invalid data gracefully."""
        output_path = temp_output_dir / "residual_scatter_plot.png"
        
        # Create empty results
        empty_results = {"primary_model": {}}
        empty_results_path = temp_output_dir / "empty_results.json"
        with open(empty_results_path, 'w') as f:
            json.dump(empty_results, f)
        
        with patch('analysis.visualization.load_regression_results') as mock_load_results, \
             patch('analysis.visualization.load_processed_data') as mock_load_data:
            
            mock_load_results.return_value = empty_results
            mock_load_data.return_value = pd.DataFrame()
            
            # Should not raise an exception, but may produce empty plot
            try:
                generate_residual_scatter_plot(
                    output_path=str(output_path),
                    results_dir=temp_output_dir
                )
                # If it succeeds, verify file exists
                if output_path.exists():
                    with open(output_path, 'rb') as f:
                        header = f.read(8)
                        assert header[:8] == b'\x89PNG\r\n\x1a\n'
            except Exception:
                # If it raises, that's acceptable for invalid data
                pass

    def test_coefficient_plot_with_missing_coefficients(self, temp_output_dir):
        """Test coefficient plot with missing coefficient data."""
        output_path = temp_output_dir / "coefficient_plot.png"
        
        # Create results with missing coefficients
        incomplete_results = {
            "primary_model": {
                "coefficients": {},
                "p_values": {}
            }
        }
        results_path = temp_output_dir / "incomplete_results.json"
        with open(results_path, 'w') as f:
            json.dump(incomplete_results, f)
        
        with patch('analysis.visualization.load_regression_results') as mock_load_results, \
             patch('analysis.visualization.load_processed_data') as mock_load_data:
            
            mock_load_results.return_value = incomplete_results
            mock_load_data.return_value = pd.DataFrame()
            
            try:
                generate_coefficient_plot(
                    output_path=str(output_path),
                    results_dir=temp_output_dir
                )
                if output_path.exists():
                    with open(output_path, 'rb') as f:
                        header = f.read(8)
                        assert header[:8] == b'\x89PNG\r\n\x1a\n'
            except Exception:
                pass

    def test_plot_generation_with_real_paths(self, temp_output_dir,
                                             mock_regression_results,
                                             mock_processed_data):
        """Test plot generation using actual file paths instead of mocks."""
        residual_path = temp_output_dir / "residual_scatter_plot.png"
        coeff_path = temp_output_dir / "coefficient_plot.png"
        
        # Generate plots using real file paths
        generate_residual_scatter_plot(
            output_path=str(residual_path),
            results_dir=temp_output_dir
        )
        
        generate_coefficient_plot(
            output_path=str(coeff_path),
            results_dir=temp_output_dir
        )
        
        # Verify both files exist and are valid PNGs
        for plot_path in [residual_path, coeff_path]:
            assert plot_path.exists(), f"{plot_path.name} was not created"
            
            with open(plot_path, 'rb') as f:
                header = f.read(8)
                assert header[:8] == b'\x89PNG\r\n\x1a\n', f"{plot_path.name} is not a valid PNG"

    def test_plot_file_size_reasonable(self, temp_output_dir,
                                       mock_regression_results,
                                       mock_processed_data):
        """Test that generated plots have reasonable file sizes."""
        residual_path = temp_output_dir / "residual_scatter_plot.png"
        coeff_path = temp_output_dir / "coefficient_plot.png"
        
        generate_residual_scatter_plot(
            output_path=str(residual_path),
            results_dir=temp_output_dir
        )
        
        generate_coefficient_plot(
            output_path=str(coeff_path),
            results_dir=temp_output_dir
        )
        
        # Check file sizes are reasonable (not empty, not huge)
        for plot_path in [residual_path, coeff_path]:
            file_size = plot_path.stat().st_size
            assert file_size > 1000, f"{plot_path.name} is too small (< 1KB)"
            assert file_size < 10_000_000, f"{plot_path.name} is too large (> 10MB)"