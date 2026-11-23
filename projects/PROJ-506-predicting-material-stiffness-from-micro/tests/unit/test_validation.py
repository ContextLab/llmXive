import pytest
import numpy as np
import json
import yaml
import tempfile
import os
from pathlib import Path
from code.data_generation.validate_tensors import (
    load_schema,
    validate_schema_conformity,
    compute_vrh_bounds,
    validate_vrh_bounds,
    validate_dataset
)

class TestSchemaValidation:
    """Tests for schema conformity validation."""
    
    def test_load_schema(self):
        """Test loading a valid schema file."""
        schema_content = """
        required:
          - image_path: string
          - stiffness_tensor: float[]
          - inclusion_density: float
          - topology_type: string
          - shape_factor: float
          - connectivity: float
          - seed: integer
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(schema_content)
            temp_path = f.name
            
        try:
            schema = load_schema(temp_path)
            assert 'required' in schema
            assert len(schema['required']) == 7
        finally:
            os.unlink(temp_path)
            
    def test_validate_schema_conformity_valid(self):
        """Test validation of a conforming metadata entry."""
        schema = {
            'required': [
                'image_path: string',
                'stiffness_tensor: float[]',
                'inclusion_density: float',
                'seed: integer'
            ]
        }
        
        metadata = {
            'image_path': 'data/raw/micro_123.png',
            'stiffness_tensor': [100.0, 100.0, 50.0, 50.0, 50.0, 50.0],
            'inclusion_density': 0.3,
            'seed': 123
        }
        
        is_valid, errors = validate_schema_conformity(metadata, schema)
        assert is_valid
        assert len(errors) == 0
        
    def test_validate_schema_conformity_missing_field(self):
        """Test validation when a required field is missing."""
        schema = {
            'required': [
                'image_path: string',
                'stiffness_tensor: float[]',
                'seed: integer'
            ]
        }
        
        metadata = {
            'image_path': 'data/raw/micro_123.png',
            'stiffness_tensor': [100.0, 100.0, 50.0, 50.0, 50.0, 50.0]
        }
        
        is_valid, errors = validate_schema_conformity(metadata, schema)
        assert not is_valid
        assert len(errors) == 1
        assert 'seed' in errors[0]
        
    def test_validate_schema_conformity_wrong_type(self):
        """Test validation when a field has wrong type."""
        schema = {
            'required': [
                'stiffness_tensor: float[]',
                'seed: integer'
            ]
        }
        
        metadata = {
            'stiffness_tensor': [100.0, 100.0, 50.0, 50.0, 50.0, 50.0],
            'seed': 'not_an_integer'
        }
        
        is_valid, errors = validate_schema_conformity(metadata, schema)
        assert not is_valid
        assert len(errors) == 1
        assert 'integer' in errors[0]

class TestVRHBounds:
    """Tests for Voigt-Reuss-Hill bounds calculation."""
    
    def test_compute_vrh_bounds_void_inclusions(self):
        """Test VRH bounds with void inclusions (stiffness = 0)."""
        density = 0.3
        matrix_stiffness = 100.0
        inclusion_stiffness = 0.0
        
        lower, upper = compute_vrh_bounds(density, matrix_stiffness, inclusion_stiffness)
        
        # Reuss bound should be 0 for void inclusions
        assert lower == 0.0
        # Voigt bound should be (1 - 0.3) * 100 = 70
        assert np.isclose(upper, 70.0)
        
    def test_compute_vrh_bounds_solid_inclusions(self):
        """Test VRH bounds with solid inclusions."""
        density = 0.3
        matrix_stiffness = 100.0
        inclusion_stiffness = 200.0
        
        lower, upper = compute_vrh_bounds(density, matrix_stiffness, inclusion_stiffness)
        
        # Voigt bound: 0.7 * 100 + 0.3 * 200 = 130
        assert np.isclose(upper, 130.0)
        # Reuss bound: 1 / (0.7/100 + 0.3/200) = 1 / (0.007 + 0.0015) = 1 / 0.0085 ≈ 117.65
        assert np.isclose(lower, 117.647, rtol=1e-3)
        
    def test_compute_vrh_bounds_invalid_density(self):
        """Test that invalid density raises an error."""
        with pytest.raises(ValueError):
            compute_vrh_bounds(-0.1)
        with pytest.raises(ValueError):
            compute_vrh_bounds(1.5)
            
    def test_validate_vrh_bounds_valid(self):
        """Test validation of a stiffness value within bounds."""
        stiffness_tensor = [70.0, 70.0, 35.0, 35.0, 35.0, 35.0]
        density = 0.3
        
        is_valid, error = validate_vrh_bounds(stiffness_tensor, density, 0)
        assert is_valid
        assert error == ""
        
    def test_validate_vrh_bounds_below_lower(self):
        """Test validation of a stiffness value below lower bound."""
        stiffness_tensor = [-10.0, 70.0, 35.0, 35.0, 35.0, 35.0]
        density = 0.3
        
        is_valid, error = validate_vrh_bounds(stiffness_tensor, density, 0)
        assert not is_valid
        assert "below lower bound" in error
        
    def test_validate_vrh_bounds_above_upper(self):
        """Test validation of a stiffness value above upper bound."""
        stiffness_tensor = [100.0, 70.0, 35.0, 35.0, 35.0, 35.0]
        density = 0.3
        
        is_valid, error = validate_vrh_bounds(stiffness_tensor, density, 0)
        assert not is_valid
        assert "above upper bound" in error
        
    def test_validate_vrh_bounds_out_of_range_index(self):
        """Test validation with an out-of-range component index."""
        stiffness_tensor = [70.0, 70.0, 35.0, 35.0, 35.0, 35.0]
        density = 0.3
        
        is_valid, error = validate_vrh_bounds(stiffness_tensor, density, 10)
        assert not is_valid
        assert "out of range" in error

class TestDatasetValidation:
    """Tests for the full dataset validation pipeline."""
    
    def test_validate_dataset_all_valid(self):
        """Test validation of a dataset with all valid entries."""
        schema_content = """
        required:
          - image_path: string
          - stiffness_tensor: float[]
          - inclusion_density: float
          - seed: integer
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(schema_content)
            schema_path = f.name
            
        metadata_list = [
            {
                'image_path': 'data/raw/micro_1.png',
                'stiffness_tensor': [70.0, 70.0, 35.0, 35.0, 35.0, 35.0],
                'inclusion_density': 0.3,
                'seed': 1
            },
            {
                'image_path': 'data/raw/micro_2.png',
                'stiffness_tensor': [50.0, 50.0, 25.0, 25.0, 25.0, 25.0],
                'inclusion_density': 0.5,
                'seed': 2
            }
        ]
        
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as f:
            log_path = f.name
            
        try:
            valid_count, invalid_count = validate_dataset(
                metadata_list, schema_path, log_path
            )
            
            assert valid_count == 2
            assert invalid_count == 0
            
            # Check log file exists and has content
            assert Path(log_path).exists()
            with open(log_path, 'r') as f:
                lines = f.readlines()
                assert len(lines) == 3  # Header + 2 entries
        finally:
            os.unlink(schema_path)
            os.unlink(log_path)
            
    def test_validate_dataset_with_invalid_entries(self):
        """Test validation of a dataset with some invalid entries."""
        schema_content = """
        required:
          - image_path: string
          - stiffness_tensor: float[]
          - inclusion_density: float
          - seed: integer
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(schema_content)
            schema_path = f.name
            
        metadata_list = [
            {
                'image_path': 'data/raw/micro_1.png',
                'stiffness_tensor': [70.0, 70.0, 35.0, 35.0, 35.0, 35.0],
                'inclusion_density': 0.3,
                'seed': 1
            },
            {
                'image_path': 'data/raw/micro_2.png',
                'stiffness_tensor': [200.0, 70.0, 35.0, 35.0, 35.0, 35.0],  # Above upper bound
                'inclusion_density': 0.3,
                'seed': 2
            },
            {
                'image_path': 'data/raw/micro_3.png',
                'stiffness_tensor': [50.0, 50.0, 25.0, 25.0, 25.0, 25.0],
                'inclusion_density': 0.5,
                'seed': 3
            }
        ]
        
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as f:
            log_path = f.name
            
        try:
            valid_count, invalid_count = validate_dataset(
                metadata_list, schema_path, log_path
            )
            
            assert valid_count == 2
            assert invalid_count == 1
            
            # Check log file contains the invalid entry
            with open(log_path, 'r') as f:
                content = f.read()
                assert 'INVALID' in content
                assert 'above upper bound' in content
        finally:
            os.unlink(schema_path)
            os.unlink(log_path)