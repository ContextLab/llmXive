"""
Integration tests for T027: Plot Saver functionality.

These tests verify that the plot saver correctly:
1. Creates the output directory
2. Generates and saves plots with correct filenames
3. Handles missing input files gracefully
"""
import os
import tempfile
import json
import csv
import pytest
from unittest.mock import patch, MagicMock
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for testing
import matplotlib.pyplot as plt

from code.visualization.saver import (
    ensure_output_directory,
    get_plot_filename,
    save_individual_plots,
    save_comparative_plots,
    main
)


class TestEnsureOutputDirectory:
    """Tests for ensure_output_directory function."""
    
    def test_creates_directory_if_not_exists(self, tmp_path):
        """Test that directory is created if it doesn't exist."""
        new_dir = tmp_path / "new_subdir"
        assert not new_dir.exists()
        
        ensure_output_directory(str(new_dir))
        
        assert new_dir.exists()
        assert new_dir.is_dir()
    
    def test_does_not_fail_if_exists(self, tmp_path):
        """Test that function doesn't fail if directory already exists."""
        existing_dir = tmp_path / "existing_dir"
        existing_dir.mkdir()
        
        # Should not raise any exception
        ensure_output_directory(str(existing_dir))
        
        assert existing_dir.exists()


class TestGetPlotFilename:
    """Tests for get_plot_filename function."""
    
    def test_basic_filename_generation(self):
        """Test basic filename generation."""
        filename = get_plot_filename("t_test", 0.5)
        assert filename == "error_rate_t_test_effect_0_50.png"
    
    def test_effect_size_formatting(self):
        """Test that effect sizes are formatted correctly."""
        filename = get_plot_filename("anova", 0.12345)
        assert filename == "error_rate_anova_effect_0_12.png"
    
    def test_different_plot_types(self):
        """Test different plot types."""
        filename = get_plot_filename("chi_squared", 0.8, "comparison")
        assert filename == "comparison_chi_squared_effect_0_80.png"


class TestSaveIndividualPlots:
    """Tests for save_individual_plots function."""
    
    @pytest.fixture
    def sample_error_rates(self):
        """Create sample error rates data."""
        return [
            {'sample_size': 10, 'test_type': 't_test', 'effect_size': 0.5, 
             'type_i_error_rate': 0.06, 'type_i_ci_lower': 0.04, 'type_i_ci_upper': 0.08,
             'power': 0.3, 'power_ci_lower': 0.25, 'power_ci_upper': 0.35},
            {'sample_size': 20, 'test_type': 't_test', 'effect_size': 0.5,
             'type_i_error_rate': 0.05, 'type_i_ci_lower': 0.03, 'type_i_ci_upper': 0.07,
             'power': 0.5, 'power_ci_lower': 0.45, 'power_ci_upper': 0.55},
            {'sample_size': 10, 'test_type': 'anova', 'effect_size': 0.5,
             'type_i_error_rate': 0.07, 'type_i_ci_lower': 0.05, 'type_i_ci_upper': 0.09,
             'power': 0.2, 'power_ci_lower': 0.15, 'power_ci_upper': 0.25},
        ]
    
    @pytest.fixture
    def sample_thresholds(self):
        """Create sample thresholds data."""
        return [
            {'test_type': 't_test', 'effect_size': 0.5, 'type_i_threshold_n': 25},
            {'test_type': 'anova', 'effect_size': 0.5, 'type_i_threshold_n': 30},
        ]
    
    def test_saves_plots_with_correct_filenames(self, tmp_path, sample_error_rates, sample_thresholds):
        """Test that plots are saved with correct filenames."""
        # Create temporary CSV and JSON files
        csv_path = tmp_path / "error_rates.csv"
        json_path = tmp_path / "thresholds.json"
        
        with open(csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=sample_error_rates[0].keys())
            writer.writeheader()
            writer.writerows(sample_error_rates)
        
        with open(json_path, 'w') as f:
            json.dump(sample_thresholds, f)
        
        # Mock the load functions to return our sample data
        with patch('code.visualization.saver.load_error_rates', return_value=sample_error_rates):
            with patch('code.visualization.saver.load_thresholds', return_value=sample_thresholds):
                with patch('matplotlib.pyplot.savefig') as mock_savefig:
                    saved_files = save_individual_plots(
                        str(tmp_path),
                        str(csv_path),
                        str(json_path),
                        ['t_test', 'anova'],
                        [0.5]
                    )
                    
                    # Verify savefig was called
                    assert mock_savefig.called
                    assert len(saved_files) == 2
                    
                    # Verify filenames
                    assert 'error_rate_t_test_effect_0_50.png' in saved_files
                    assert 'error_rate_anova_effect_0_50.png' in saved_files
    
    def test_handles_missing_data_gracefully(self, tmp_path):
        """Test that function handles missing data gracefully."""
        csv_path = tmp_path / "empty.csv"
        json_path = tmp_path / "empty.json"
        
        with open(csv_path, 'w') as f:
            f.write("")
        
        with open(json_path, 'w') as f:
            f.write("[]")
        
        with patch('code.visualization.saver.load_error_rates', return_value=[]):
            with patch('code.visualization.saver.load_thresholds', return_value=[]):
                saved_files = save_individual_plots(
                    str(tmp_path),
                    str(csv_path),
                    str(json_path),
                    ['t_test'],
                    [0.5]
                )
                
                # Should return empty list when no data
                assert saved_files == []


class TestSaveComparativePlots:
    """Tests for save_comparative_plots function."""
    
    def test_saves_comparative_plots(self, tmp_path):
        """Test that comparative plots are saved."""
        csv_path = tmp_path / "error_rates.csv"
        
        # Create minimal CSV
        with open(csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['sample_size', 'test_type', 'effect_size', 'type_i_error_rate'])
            writer.writeheader()
            writer.writerow({'sample_size': 10, 'test_type': 't_test', 'effect_size': 0.5, 'type_i_error_rate': 0.06})
        
        # Mock the load and generate functions
        mock_low_sample_data = [
            {
                'test_type': 't_test',
                'sample_sizes': [10, 20, 30],
                'error_rates': [0.06, 0.05, 0.05]
            }
        ]
        
        mock_fig, mock_ax = plt.subplots()
        
        with patch('code.visualization.saver.load_low_sample_data', return_value=mock_low_sample_data):
            with patch('code.visualization.saver.generate_comparative_plots', return_value=(mock_fig, [mock_ax])):
                with patch('matplotlib.pyplot.savefig'):
                    saved_files = save_comparative_plots(str(tmp_path), str(csv_path))
                    
                    assert len(saved_files) > 0
                    assert any('comparative' in f for f in saved_files)
        
        plt.close(mock_fig)
    
    def test_handles_empty_data(self, tmp_path):
        """Test that function handles empty data gracefully."""
        csv_path = tmp_path / "empty.csv"
        
        with open(csv_path, 'w') as f:
            f.write("")
        
        with patch('code.visualization.saver.load_low_sample_data', return_value=[]):
            saved_files = save_comparative_plots(str(tmp_path), str(csv_path))
            
            assert saved_files == []


class TestMain:
    """Tests for main function."""
    
    def test_main_with_valid_inputs(self, tmp_path):
        """Test main function with valid inputs."""
        # Create temporary directories and files
        data_dir = tmp_path / "data"
        simulation_dir = data_dir / "simulation"
        visualization_dir = data_dir / "visualization"
        
        simulation_dir.mkdir(parents=True)
        
        # Create mock error rates CSV
        error_rates_file = simulation_dir / "error_rates_summary.csv"
        with open(error_rates_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['sample_size', 'test_type', 'effect_size', 'type_i_error_rate'])
            writer.writeheader()
            writer.writerow({'sample_size': 10, 'test_type': 't_test', 'effect_size': 0.5, 'type_i_error_rate': 0.06})
        
        # Create mock thresholds JSON
        thresholds_file = simulation_dir / "thresholds.json"
        with open(thresholds_file, 'w') as f:
            json.dump([{'test_type': 't_test', 'effect_size': 0.5, 'type_i_threshold_n': 25}], f)
        
        # Mock the load functions
        mock_error_rates = [
            {'sample_size': 10, 'test_type': 't_test', 'effect_size': 0.5, 'type_i_error_rate': 0.06}
        ]
        mock_thresholds = [{'test_type': 't_test', 'effect_size': 0.5, 'type_i_threshold_n': 25}]
        
        with patch('code.visualization.saver.load_error_rates', return_value=mock_error_rates):
            with patch('code.visualization.saver.load_thresholds', return_value=mock_thresholds):
                with patch('code.visualization.saver.save_individual_plots', return_value=['plot1.png']):
                    with patch('code.visualization.saver.save_comparative_plots', return_value=['plot2.png']):
                        with patch('code.visualization.saver.ensure_output_directory'):
                            # Run main
                            main()
                            
                            # Verify output directory was created
                            assert visualization_dir.exists()


    def test_main_with_missing_error_rates(self, tmp_path):
        """Test main function with missing error rates file."""
        data_dir = tmp_path / "data"
        simulation_dir = data_dir / "simulation"
        simulation_dir.mkdir(parents=True)
        
        # Don't create the error rates file
        
        with patch('code.visualization.saver.load_error_rates') as mock_load:
            mock_load.side_effect = FileNotFoundError()
            
            # Should print error message and return
            main()
            
            # Verify load was attempted
            assert mock_load.called


    def test_main_with_missing_thresholds(self, tmp_path):
        """Test main function with missing thresholds file."""
        data_dir = tmp_path / "data"
        simulation_dir = data_dir / "simulation"
        simulation_dir.mkdir(parents=True)
        
        # Create error rates file but not thresholds
        error_rates_file = simulation_dir / "error_rates_summary.csv"
        with open(error_rates_file, 'w') as f:
            f.write("sample_size,test_type,effect_size,type_i_error_rate\n10,t_test,0.5,0.06\n")
        
        with patch('code.visualization.saver.load_error_rates', return_value=[{'sample_size': 10}]):
            with patch('code.visualization.saver.load_thresholds') as mock_load:
                mock_load.side_effect = FileNotFoundError()
                
                # Should print error message and return
                main()
                
                assert mock_load.called