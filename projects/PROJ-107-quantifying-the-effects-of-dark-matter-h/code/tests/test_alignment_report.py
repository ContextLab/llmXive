"""
Tests for T038: Alignment report generation with associational_only flag.
"""
import pytest
import os
import sys
import tempfile
import shutil
from pathlib import Path
import csv
import numpy as np

# Add code directory to path
code_dir = Path(__file__).parent.parent
sys.path.insert(0, str(code_dir))

from analysis.generate_alignment_report import (
    load_halo_shapes,
    load_galaxy_properties,
    compute_alignment_angles,
    save_alignment_results,
    apply_associational_flag,
    run_alignment_analysis
)
from utils.config import get_project_root, get_data_processed_path

class TestAlignmentReportGeneration:
    """Test suite for alignment report generation (T038)."""

    @pytest.fixture
    def setup_test_data(self, tmp_path):
        """Create temporary test data files."""
        # Create processed directory
        processed_dir = tmp_path / "data" / "processed"
        processed_dir.mkdir(parents=True, exist_ok=True)
        
        # Create sample halo_shapes.csv
        halo_file = processed_dir / "halo_shapes.csv"
        with open(halo_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'halo_id', 'mass', 'b_a_ratio', 'c_a_ratio', 'triaxiality', 'particle_count'
            ])
            writer.writeheader()
            writer.writerow({
                'halo_id': 1, 'mass': 1e12, 'b_a_ratio': 0.6, 'c_a_ratio': 0.4, 
                'triaxiality': 0.5, 'particle_count': 15000
            })
            writer.writerow({
                'halo_id': 2, 'mass': 1.2e12, 'b_a_ratio': 0.8, 'c_a_ratio': 0.7, 
                'triaxiality': 0.2, 'particle_count': 20000
            })
            writer.writerow({
                'halo_id': 3, 'mass': 0.9e12, 'b_a_ratio': 0.5, 'c_a_ratio': 0.3, 
                'triaxiality': 0.6, 'particle_count': 12000
            })
        
        # Create sample galaxy_properties.csv
        galaxy_file = processed_dir / "galaxy_properties.csv"
        with open(galaxy_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'halo_id', 'sfr', 'radius', 'stellar_mass'
            ])
            writer.writeheader()
            writer.writerow({'halo_id': 1, 'sfr': 2.5, 'radius': 5.0, 'stellar_mass': 1e10})
            writer.writerow({'halo_id': 2, 'sfr': 3.1, 'radius': 6.2, 'stellar_mass': 1.2e10})
            writer.writerow({'halo_id': 3, 'sfr': 1.8, 'radius': 4.5, 'stellar_mass': 0.9e10})
        
        return processed_dir

    def test_compute_alignment_angles(self, setup_test_data):
        """Test that alignment angles are computed correctly."""
        processed_dir = setup_test_data
        
        # Load test data
        halos = []
        with open(processed_dir / "halo_shapes.csv", 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                halos.append({
                    'halo_id': int(row['halo_id']),
                    'mass': float(row['mass']),
                    'b_a_ratio': float(row['b_a_ratio']),
                    'c_a_ratio': float(row['c_a_ratio']),
                    'triaxiality': float(row['triaxiality']),
                    'particle_count': int(row['particle_count'])
                })
        
        galaxies = []
        with open(processed_dir / "galaxy_properties.csv", 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                galaxies.append({
                    'halo_id': int(row['halo_id']),
                    'sfr': float(row['sfr']),
                    'radius': float(row['radius']),
                    'stellar_mass': float(row['stellar_mass'])
                })
        
        # Compute alignment angles
        results = compute_alignment_angles(halos, galaxies)
        
        # Verify results
        assert len(results) > 0, "No alignment results computed"
        
        for result in results:
            assert 'halo_id' in result
            assert 'misalignment_angle_deg' in result
            assert 0 <= result['misalignment_angle_deg'] <= 90, \
                f"Angle out of range: {result['misalignment_angle_deg']}"
            assert 'b_a_ratio' in result
            assert 'triaxiality' in result

    def test_save_alignment_results(self, setup_test_data):
        """Test that alignment results are saved correctly."""
        processed_dir = setup_test_data
        
        # Create test results
        test_results = [
            {
                'halo_id': 1, 'mass': 1e12, 'b_a_ratio': 0.6, 'c_a_ratio': 0.4,
                'triaxiality': 0.5, 'sfr': 2.5, 'radius': 5.0,
                'misalignment_angle_deg': 45.2
            }
        ]
        
        # Save results
        output_file = processed_dir / "test_alignment.csv"
        save_alignment_results(test_results, output_file)
        
        # Verify file exists and has correct content
        assert output_file.exists(), "Output file not created"
        
        with open(output_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 1
            assert rows[0]['halo_id'] == '1'
            assert rows[0]['misalignment_angle_deg'] == '45.2'

    def test_apply_associational_flag(self, setup_test_data):
        """Test that associational_only flag is applied correctly."""
        processed_dir = setup_test_data
        
        # Create test file
        test_file = processed_dir / "test_flag.csv"
        with open(test_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['col1', 'col2'])
            writer.writeheader()
            writer.writerow({'col1': 'a', 'col2': 'b'})
        
        # Apply flag
        apply_associational_flag(test_file)
        
        # Verify flag is present
        with open(test_file, 'r') as f:
            reader = csv.DictReader(f)
            assert 'associational_only' in reader.fieldnames
            rows = list(reader)
            assert len(rows) == 1
            assert rows[0]['associational_only'] == 'true'

    def test_full_pipeline(self, setup_test_data, tmp_path):
        """Test the full alignment report generation pipeline."""
        processed_dir = setup_test_data
        
        # Mock the get_data_processed_path to use our temp directory
        import analysis.generate_alignment_report as module
        original_func = module.get_data_processed_path
        module.get_data_processed_path = lambda: processed_dir
        
        try:
            # Run the pipeline
            output_path = run_alignment_analysis()
            
            # Verify output file exists
            assert output_path.exists(), "Output file not created"
            assert output_path.name == "alignment_angles.csv"
            
            # Verify content
            with open(output_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) > 0
                assert 'associational_only' in reader.fieldnames
                assert all(row['associational_only'] == 'true' for row in rows)
                assert all('misalignment_angle_deg' in row for row in rows)
        
        finally:
            # Restore original function
            module.get_data_processed_path = original_func

    def test_empty_input_handling(self, tmp_path):
        """Test handling of empty input data."""
        processed_dir = tmp_path / "data" / "processed"
        processed_dir.mkdir(parents=True, exist_ok=True)
        
        # Create empty halo file
        halo_file = processed_dir / "halo_shapes.csv"
        with open(halo_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'halo_id', 'mass', 'b_a_ratio', 'c_a_ratio', 'triaxiality', 'particle_count'
            ])
            writer.writeheader()
        
        # Create empty galaxy file
        galaxy_file = processed_dir / "galaxy_properties.csv"
        with open(galaxy_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'halo_id', 'sfr', 'radius', 'stellar_mass'
            ])
            writer.writeheader()
        
        # Load data
        halos = []
        with open(halo_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                halos.append(row)
        
        galaxies = []
        with open(galaxy_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                galaxies.append(row)
        
        # Compute alignment (should return empty list)
        results = compute_alignment_angles(halos, galaxies)
        assert results == [], "Expected empty results for empty input"
        
        # Save empty results
        output_file = processed_dir / "empty_alignment.csv"
        save_alignment_results(results, output_file)
        assert output_file.exists()

    def test_invalid_shape_metrics_excluded(self, setup_test_data):
        """Test that haloes with invalid shape metrics are excluded."""
        processed_dir = setup_test_data
        
        # Add a halo with invalid metrics
        with open(processed_dir / "halo_shapes.csv", 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'halo_id', 'mass', 'b_a_ratio', 'c_a_ratio', 'triaxiality', 'particle_count'
            ])
            writer.writerow({
                'halo_id': 999, 'mass': 1e12, 'b_a_ratio': -0.1, 'c_a_ratio': 0.4,
                'triaxiality': 0.5, 'particle_count': 15000
            })
        
        # Load data
        halos = []
        with open(processed_dir / "halo_shapes.csv", 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                halos.append({
                    'halo_id': int(row['halo_id']),
                    'mass': float(row['mass']),
                    'b_a_ratio': float(row['b_a_ratio']),
                    'c_a_ratio': float(row['c_a_ratio']),
                    'triaxiality': float(row['triaxiality']),
                    'particle_count': int(row['particle_count'])
                })
        
        galaxies = []
        with open(processed_dir / "galaxy_properties.csv", 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                galaxies.append({
                    'halo_id': int(row['halo_id']),
                    'sfr': float(row['sfr']),
                    'radius': float(row['radius']),
                    'stellar_mass': float(row['stellar_mass'])
                })
        
        # Compute alignment
        results = compute_alignment_angles(halos, galaxies)
        
        # Verify invalid halo is excluded
        halo_ids = [r['halo_id'] for r in results]
        assert 999 not in halo_ids, "Invalid halo should be excluded"
        assert 1 in halo_ids, "Valid halo should be included"
        assert 2 in halo_ids, "Valid halo should be included"
        assert 3 in halo_ids, "Valid halo should be included"