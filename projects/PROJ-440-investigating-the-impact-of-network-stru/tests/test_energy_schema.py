"""
Tests for the energy decay schema and validation logic.
"""
import pytest
import os
import tempfile
import csv
import yaml
from pathlib import Path

# Add the project root to the path if needed
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.utils.energy_schema_loader import load_energy_schema, validate_csv_against_schema


class TestSchemaLoading:
    def test_load_schema_exists(self):
        """Test that the schema file can be loaded."""
        schema = load_energy_schema()
        assert schema is not None
        assert 'properties' in schema
        assert 'required' in schema
        
    def test_schema_has_required_fields(self):
        """Test that the schema defines all required fields."""
        schema = load_energy_schema()
        required = schema.get('required', [])
        
        expected_fields = [
            'graph_id', 'decay_rate', 'r_squared', 'status', 
            'convergence_std', 'class', 'clustering_coeff', 
            'avg_path_length', 'avg_degree', 'fit_parameters'
        ]
        
        for field in expected_fields:
            assert field in required, f"Missing required field: {field}"
            
    def test_schema_properties_defined(self):
        """Test that all properties have type definitions."""
        schema = load_energy_schema()
        properties = schema.get('properties', {})
        
        assert 'graph_id' in properties
        assert 'decay_rate' in properties
        assert 'r_squared' in properties
        assert 'status' in properties
        assert 'convergence_std' in properties
        
        # Check types
        assert properties['graph_id']['type'] == 'string'
        assert properties['decay_rate']['type'] == 'number'
        assert properties['r_squared']['type'] == 'number'
        assert properties['status']['type'] == 'string'
        
        
class TestCSVValidation:
    def test_valid_csv(self):
        """Test validation against a correctly formatted CSV."""
        # Create a temporary valid CSV
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            writer = csv.writer(f)
            writer.writerow(['graph_id', 'class', 'N', 'decay_rate', 'r_squared', 'status', 
                           'convergence_std', 'clustering_coeff', 'avg_path_length', 'avg_degree',
                           'fit_parameters'])
            writer.writerow(['test_001', 'random', '100', '0.05', '0.98', 'dissipative', 
                           '0.002', '0.01', '5.5', '4.0', '{}'])
            temp_path = f.name
        
        try:
            is_valid, message = validate_csv_against_schema(temp_path)
            assert is_valid, f"Validation failed unexpectedly: {message}"
        finally:
            os.unlink(temp_path)
            
    def test_missing_required_column(self):
        """Test validation fails when a required column is missing."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            writer = csv.writer(f)
            # Missing 'decay_rate' column
            writer.writerow(['graph_id', 'class', 'N', 'r_squared', 'status'])
            writer.writerow(['test_001', 'random', '100', '0.98', 'dissipative'])
            temp_path = f.name
        
        try:
            is_valid, message = validate_csv_against_schema(temp_path)
            assert not is_valid
            assert 'decay_rate' in message
        finally:
            os.unlink(temp_path)
            
    def test_invalid_enum_value(self):
        """Test validation fails when an enum value is invalid."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            writer = csv.writer(f)
            writer.writerow(['graph_id', 'class', 'N', 'decay_rate', 'r_squared', 'status', 
                           'convergence_std', 'clustering_coeff', 'avg_path_length', 'avg_degree',
                           'fit_parameters'])
            # Invalid status value
            writer.writerow(['test_001', 'random', '100', '0.05', '0.98', 'invalid_status', 
                           '0.002', '0.01', '5.5', '4.0', '{}'])
            temp_path = f.name
        
        try:
            is_valid, message = validate_csv_against_schema(temp_path)
            assert not is_valid
            assert 'invalid_status' in message
        finally:
            os.unlink(temp_path)
            
    def test_invalid_numeric_value(self):
        """Test validation fails when a numeric value is not a number."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            writer = csv.writer(f)
            writer.writerow(['graph_id', 'class', 'N', 'decay_rate', 'r_squared', 'status', 
                           'convergence_std', 'clustering_coeff', 'avg_path_length', 'avg_degree',
                           'fit_parameters'])
            # Invalid numeric value for decay_rate
            writer.writerow(['test_001', 'random', '100', 'not_a_number', '0.98', 'dissipative', 
                           '0.002', '0.01', '5.5', '4.0', '{}'])
            temp_path = f.name
        
        try:
            is_valid, message = validate_csv_against_schema(temp_path)
            assert not is_valid
            assert 'not_a_number' in message
        finally:
            os.unlink(temp_path)
            
    def test_file_not_found(self):
        """Test validation fails when file does not exist."""
        is_valid, message = validate_csv_against_schema('nonexistent_file.csv')
        assert not is_valid
        assert 'not found' in message.lower()