"""
Unit tests for generate_power_analysis module.

Tests verify that T029b produces valid power analysis JSON with
required fields and non-null numeric values.
"""

import os
import sys
import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from data.generate_power_analysis import (
    calculate_min_sample_size,
    run_power_analysis,
    DEFAULT_VARIANCE,
    DEFAULT_EFFECT_SIZE,
    DEFAULT_POWER,
    DEFAULT_ALPHA
)

class TestCalculateMinSampleSize:
    """Tests for calculate_min_sample_size function."""
    
    def test_basic_calculation(self):
        """Test basic sample size calculation with default parameters."""
        n = calculate_min_sample_size(
            effect_size=DEFAULT_EFFECT_SIZE,
            variance=DEFAULT_VARIANCE,
            power=DEFAULT_POWER,
            alpha=DEFAULT_ALPHA
        )
        
        assert n > 0, "Sample size must be positive"
        assert isinstance(n, int), "Sample size must be an integer"
    
    def test_effect_size_influence(self):
        """Test that larger effect sizes result in smaller sample sizes."""
        n_small_effect = calculate_min_sample_size(
            effect_size=0.2,
            variance=1.0
        )
        n_large_effect = calculate_min_sample_size(
            effect_size=0.8,
            variance=1.0
        )
        
        assert n_large_effect < n_small_effect, \
            "Larger effect size should require smaller sample size"
    
    def test_variance_influence(self):
        """Test that higher variance results in larger sample sizes."""
        n_low_var = calculate_min_sample_size(
            effect_size=0.2,
            variance=0.5
        )
        n_high_var = calculate_min_sample_size(
            effect_size=0.2,
            variance=2.0
        )
        
        assert n_high_var > n_low_var, \
            "Higher variance should require larger sample size"
    
    def test_zero_effect_size_raises_error(self):
        """Test that zero effect size raises ValueError."""
        with pytest.raises(ValueError, match="Effect size cannot be zero"):
            calculate_min_sample_size(
                effect_size=0.0,
                variance=1.0
            )

class TestRunPowerAnalysis:
    """Tests for run_power_analysis function."""
    
    def test_output_file_created(self):
        """Test that output JSON file is created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / 'test_power_analysis.json'
            
            results = run_power_analysis(output_path)
            
            assert output_path.exists(), "Output file should be created"
            assert output_path.suffix == '.json', "Output should be JSON file"
    
    def test_required_fields_present(self):
        """Test that all required fields are present in output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / 'test_power_analysis.json'
            
            run_power_analysis(output_path)
            
            with open(output_path, 'r') as f:
                data = json.load(f)
            
            required_fields = [
                'min_sample_size',
                'expected_variance',
                'effect_size'
            ]
            
            for field in required_fields:
                assert field in data, f"Required field '{field}' missing"
    
    def test_values_are_non_null_numeric(self):
        """Test that all numeric values are non-null."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / 'test_power_analysis.json'
            
            run_power_analysis(output_path)
            
            with open(output_path, 'r') as f:
                data = json.load(f)
            
            # Check min_sample_size
            assert data['min_sample_size'] is not None
            assert isinstance(data['min_sample_size'], int)
            assert data['min_sample_size'] > 0
            
            # Check expected_variance
            assert data['expected_variance'] is not None
            assert isinstance(data['expected_variance'], (int, float))
            assert data['expected_variance'] > 0
            
            # Check effect_size
            assert data['effect_size'] is not None
            assert isinstance(data['effect_size'], (int, float))
            assert data['effect_size'] > 0
    
    def test_default_values_used(self):
        """Test that default heuristic values are used when not specified."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / 'test_power_analysis.json'
            
            run_power_analysis(output_path)
            
            with open(output_path, 'r') as f:
                data = json.load(f)
            
            assert data['expected_variance'] == DEFAULT_VARIANCE
            assert data['effect_size'] == DEFAULT_EFFECT_SIZE
            assert data['power'] == DEFAULT_POWER
            assert data['alpha'] == DEFAULT_ALPHA
    
    def test_custom_values_used(self):
        """Test that custom values override defaults."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / 'test_power_analysis.json'
            
            custom_variance = 2.5
            custom_effect_size = 0.5
            
            run_power_analysis(
                output_path,
                variance=custom_variance,
                effect_size=custom_effect_size
            )
            
            with open(output_path, 'r') as f:
                data = json.load(f)
            
            assert data['expected_variance'] == custom_variance
            assert data['effect_size'] == custom_effect_size
    
    def test_creates_parent_directories(self):
        """Test that parent directories are created if they don't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create nested path that doesn't exist
            nested_path = Path(tmpdir) / 'nested' / 'deep' / 'output.json'
            
            run_power_analysis(nested_path)
            
            assert nested_path.exists(), "File should be created with parent dirs"
    
    def test_notes_field_present(self):
        """Test that notes field explains placeholder nature."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / 'test_power_analysis.json'
            
            run_power_analysis(output_path)
            
            with open(output_path, 'r') as f:
                data = json.load(f)
            
            assert 'notes' in data
            assert 'placeholder' in data['notes'].lower() or \
                   'structural validation' in data['notes'].lower()

class TestIntegration:
    """Integration tests for the complete workflow."""
    
    def test_full_workflow(self):
        """Test complete workflow from calculation to file output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / 'power_analysis.json'
            
            # Run the analysis
            results = run_power_analysis(output_path)
            
            # Verify in-memory results
            assert 'min_sample_size' in results
            assert 'expected_variance' in results
            assert 'effect_size' in results
            
            # Verify file contents match
            with open(output_path, 'r') as f:
                file_data = json.load(f)
            
            assert file_data['min_sample_size'] == results['min_sample_size']
            assert file_data['expected_variance'] == results['expected_variance']
            assert file_data['effect_size'] == results['effect_size']
    
    def test_t029b_verification_criteria(self):
        """
        Test that T029b verification criteria are met:
        - data/metrics/power_analysis.json exists
        - Contains non-null numeric values
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / 'power_analysis.json'
            
            # Generate the file
            run_power_analysis(output_path)
            
            # Verify existence
            assert output_path.exists(), "power_analysis.json must exist"
            
            # Verify content
            with open(output_path, 'r') as f:
                data = json.load(f)
            
            # Verify non-null numeric values
            assert data['min_sample_size'] is not None
            assert isinstance(data['min_sample_size'], (int, float))
            assert data['min_sample_size'] > 0
            
            assert data['expected_variance'] is not None
            assert isinstance(data['expected_variance'], (int, float))
            assert data['expected_variance'] > 0
            
            assert data['effect_size'] is not None
            assert isinstance(data['effect_size'], (int, float))
            assert data['effect_size'] > 0