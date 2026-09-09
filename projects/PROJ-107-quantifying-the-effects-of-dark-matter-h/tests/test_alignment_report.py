"""
Tests for the alignment report generation (T038).

This module contains tests to verify the alignment angles generation
process, including data loading, angle computation, and output validation.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import tempfile
import shutil
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from utils.config import get_project_root, get_data_processed_path
from analysis.generate_alignment_report import (
    load_halo_shapes,
    compute_alignment_angles,
    save_alignment_results,
    apply_associational_flag
)

class TestAlignmentReportGeneration:
    """Tests for the alignment report generation pipeline."""

    @pytest.fixture
    def temp_data_dir(self):
        """Create a temporary directory for test data."""
        temp_dir = tempfile.mkdtemp()
        processed_dir = Path(temp_dir) / "data" / "processed"
        processed_dir.mkdir(parents=True)
        
        # Create mock halo shapes data
        halo_data = {
            'halo_id': [1, 2, 3, 4, 5],
            'mass': [1e12, 1e13, 1e14, 1e12, 1e13],
            'c_a_ratio': [0.6, 0.7, 0.8, 0.5, 0.9],
            'b_a_ratio': [0.7, 0.8, 0.9, 0.6, 0.85],
            'triaxiality': [0.3, 0.2, 0.1, 0.4, 0.15],
            'x_pos': [10.0, 20.0, 30.0, 40.0, 50.0],
            'y_pos': [15.0, 25.0, 35.0, 45.0, 55.0],
            'z_pos': [5.0, 10.0, 15.0, 20.0, 25.0]
        }
        halo_df = pd.DataFrame(halo_data)
        halo_df.to_csv(processed_dir / "halo_shapes.csv", index=False)
        
        # Create mock galaxy properties data
        galaxy_data = {
            'galaxy_id': [1, 2, 3, 4, 5],
            'halo_id': [1, 2, 3, 4, 5],
            'sfr': [1.0, 2.0, 3.0, 4.0, 5.0],
            'radius': [5.0, 6.0, 7.0, 8.0, 9.0],
            'x_pos': [10.1, 20.1, 30.1, 40.1, 50.1],
            'y_pos': [15.1, 25.1, 35.1, 45.1, 55.1],
            'z_pos': [5.1, 10.1, 15.1, 20.1, 25.1],
            'spin_x': [0.1, 0.2, 0.3, 0.4, 0.5],
            'spin_y': [0.2, 0.3, 0.4, 0.5, 0.6],
            'spin_z': [0.3, 0.4, 0.5, 0.6, 0.7],
            'major_axis_x': [0.8, 0.7, 0.6, 0.9, 0.5],
            'major_axis_y': [0.5, 0.6, 0.7, 0.4, 0.8],
            'major_axis_z': [0.3, 0.4, 0.5, 0.6, 0.7]
        }
        galaxy_df = pd.DataFrame(galaxy_data)
        galaxy_df.to_csv(processed_dir / "galaxy_properties.csv", index=False)
        
        yield temp_dir
        
        # Cleanup
        shutil.rmtree(temp_dir)

    def test_load_halo_shapes(self, temp_data_dir):
        """Test loading halo shapes data."""
        # Patch the get_data_processed_path function to return our temp directory
        with patch('analysis.generate_alignment_report.get_data_processed_path') as mock_path:
            mock_path.return_value = Path(temp_data_dir) / "data" / "processed"
            
            halo_df = load_halo_shapes()
            
            assert isinstance(halo_df, pd.DataFrame)
            assert len(halo_df) == 5
            assert 'halo_id' in halo_df.columns
            assert 'c_a_ratio' in halo_df.columns
            assert 'b_a_ratio' in halo_df.columns

    def test_compute_alignment_angles(self, temp_data_dir):
        """Test computing alignment angles."""
        # Load mock data
        halo_df = pd.read_csv(Path(temp_data_dir) / "data" / "processed" / "halo_shapes.csv")
        galaxy_df = pd.read_csv(Path(temp_data_dir) / "data" / "processed" / "galaxy_properties.csv")
        
        # Mock the align_halo_galaxy_pairs function
        with patch('analysis.generate_alignment_report.align_halo_galaxy_pairs') as mock_align:
            # Create mock result
            mock_result = pd.DataFrame({
                'halo_id': [1, 2, 3],
                'galaxy_id': [1, 2, 3],
                'spin_spin_angle': [10.0, 20.0, 30.0],
                'major_major_angle': [15.0, 25.0, 35.0],
                'associational_only': [True, True, True]
            })
            mock_align.return_value = mock_result
            
            alignment_results = compute_alignment_angles(halo_df, galaxy_df)
            
            assert isinstance(alignment_results, pd.DataFrame)
            assert 'spin_spin_angle' in alignment_results.columns
            assert 'major_major_angle' in alignment_results.columns
            assert 'associational_only' in alignment_results.columns

    def test_save_alignment_results(self, temp_data_dir):
        """Test saving alignment results to CSV."""
        # Create mock results
        results_df = pd.DataFrame({
            'halo_id': [1, 2, 3],
            'galaxy_id': [1, 2, 3],
            'spin_spin_angle': [10.0, 20.0, 30.0],
            'major_major_angle': [15.0, 25.0, 35.0],
            'associational_only': [True, True, True]
        })
        
        output_path = Path(temp_data_dir) / "data" / "processed" / "test_alignment.csv"
        
        save_alignment_results(results_df, output_path)
        
        assert output_path.exists()
        saved_df = pd.read_csv(output_path)
        assert len(saved_df) == 3
        assert 'spin_spin_angle' in saved_df.columns
        assert 'major_major_angle' in saved_df.columns

    def test_apply_associational_flag(self, temp_data_dir):
        """Test applying the associational_only flag."""
        # Create a test CSV file
        test_df = pd.DataFrame({
            'halo_id': [1, 2, 3],
            'value': [10, 20, 30]
        })
        test_path = Path(temp_data_dir) / "data" / "processed" / "test_flag.csv"
        test_df.to_csv(test_path, index=False)
        
        # Apply the flag
        apply_associational_flag(test_path)
        
        # Verify the flag was added
        result_df = pd.read_csv(test_path)
        assert 'associational_only' in result_df.columns
        assert all(result_df['associational_only'] == True)