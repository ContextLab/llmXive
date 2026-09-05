import pytest
import numpy as np
import json
import yaml
import csv
import tempfile
from pathlib import Path
from code.data_generation.validate_tensors import (
    load_schema,
    validate_schema_conformity,
    compute_vrh_bounds,
    validate_vrh_bounds,
    validate_dataset
)

class TestLoadSchema:
    def test_load_valid_schema(self):
        """Test loading a valid schema file."""
        schema_content = """
        type: object
        required:
          - field1
        properties:
          field1:
            type: string
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(schema_content)
            schema_path = Path(f.name)
        
        try:
            schema = load_schema(schema_path)
            assert schema['type'] == 'object'
            assert 'field1' in schema['required']
        finally:
            schema_path.unlink()

    def test_load_missing_schema(self):
        """Test loading a non-existent schema file."""
        with pytest.raises(FileNotFoundError):
            load_schema(Path('/nonexistent/path/schema.yaml'))

class TestValidateSchemaConformity:
    def test_valid_entry(self):
        """Test validation of a conformant entry."""
        schema = {
            'type': 'object',
            'required': ['name', 'value'],
            'properties': {
                'name': {'type': 'string'},
                'value': {'type': 'number'}
            }
        }
        
        entry = {
            'name': 'test',
            'value': 42.5
        }
        
        errors = validate_schema_conformity(entry, schema)
        assert len(errors) == 0

    def test_missing_required_field(self):
        """Test validation with missing required field."""
        schema = {
            'type': 'object',
            'required': ['name', 'value'],
            'properties': {
                'name': {'type': 'string'},
                'value': {'type': 'number'}
            }
        }
        
        entry = {
            'name': 'test'
        }
        
        errors = validate_schema_conformity(entry, schema)
        assert len(errors) == 1
        assert 'Missing required field: value' in errors[0]

    def test_wrong_type(self):
        """Test validation with wrong field type."""
        schema = {
            'type': 'object',
            'required': ['name'],
            'properties': {
                'name': {'type': 'string'}
            }
        }
        
        entry = {
            'name': 123
        }
        
        errors = validate_schema_conformity(entry, schema)
        assert len(errors) == 1
        assert "should be string" in errors[0]

    def test_enum_violation(self):
        """Test validation with enum constraint violation."""
        schema = {
            'type': 'object',
            'required': ['type'],
            'properties': {
                'type': {'type': 'string', 'enum': ['a', 'b', 'c']}
            }
        }
        
        entry = {
            'type': 'd'
        }
        
        errors = validate_schema_conformity(entry, schema)
        assert len(errors) == 1
        assert "not in allowed values" in errors[0]

class TestComputeVRHBounds:
    def test_valid_moduli(self):
        """Test computation of VRH bounds with valid input."""
        matrix_moduli = (200.0, 0.3)  # E=200 GPa, nu=0.3
        inclusion_moduli = (100.0, 0.25)  # E=100 GPa, nu=0.25
        volume_fraction = 0.5
        
        bounds = compute_vrh_bounds(matrix_moduli, inclusion_moduli, volume_fraction)
        
        assert 'K_Voigt' in bounds
        assert 'K_Reuss' in bounds
        assert 'K_Hill' in bounds
        assert 'G_Voigt' in bounds
        assert 'G_Reuss' in bounds
        assert 'G_Hill' in bounds
        
        # Voigt should be >= Hill >= Reuss
        assert bounds['K_Voigt'] >= bounds['K_Hill'] >= bounds['K_Reuss']
        assert bounds['G_Voigt'] >= bounds['G_Hill'] >= bounds['G_Reuss']
        
        # All bounds should be positive
        assert all(v > 0 for v in bounds.values())

    def test_zero_volume_fraction(self):
        """Test with zero volume fraction (pure matrix)."""
        matrix_moduli = (200.0, 0.3)
        inclusion_moduli = (100.0, 0.25)
        volume_fraction = 0.0
        
        bounds = compute_vrh_bounds(matrix_moduli, inclusion_moduli, volume_fraction)
        
        # At v=0, bounds should equal matrix moduli
        K_m = 200.0 / (3 * (1 - 2 * 0.3))
        G_m = 200.0 / (2 * (1 + 0.3))
        
        assert abs(bounds['K_Hill'] - K_m) < 1e-6
        assert abs(bounds['G_Hill'] - G_m) < 1e-6

class TestValidateVRHBounds:
    def test_valid_tensor(self):
        """Test validation of a valid stiffness tensor."""
        stiffness = np.array([[200.0, 80.0], [80.0, 200.0]])
        bounds = {'K_Hill': 150.0, 'G_Hill': 80.0}
        
        errors = validate_vrh_bounds(stiffness, bounds)
        assert len(errors) == 0

    def test_negative_values(self):
        """Test validation with negative stiffness values."""
        stiffness = np.array([[-200.0, 80.0], [80.0, 200.0]])
        bounds = {'K_Hill': 150.0, 'G_Hill': 80.0}
        
        errors = validate_vrh_bounds(stiffness, bounds)
        assert len(errors) == 1
        assert "negative values" in errors[0]

    def test_nan_values(self):
        """Test validation with NaN values."""
        stiffness = np.array([[np.nan, 80.0], [80.0, 200.0]])
        bounds = {'K_Hill': 150.0, 'G_Hill': 80.0}
        
        errors = validate_vrh_bounds(stiffness, bounds)
        assert len(errors) == 1
        assert "NaN" in errors[0]

    def test_inf_values(self):
        """Test validation with Inf values."""
        stiffness = np.array([[np.inf, 80.0], [80.0, 200.0]])
        bounds = {'K_Hill': 150.0, 'G_Hill': 80.0}
        
        errors = validate_vrh_bounds(stiffness, bounds)
        assert len(errors) == 1
        assert "Inf" in errors[0]

    def test_empty_tensor(self):
        """Test validation with empty tensor."""
        stiffness = np.array([])
        bounds = {'K_Hill': 150.0, 'G_Hill': 80.0}
        
        errors = validate_vrh_bounds(stiffness, bounds)
        assert len(errors) == 1
        assert "Empty" in errors[0]

class TestValidateDataset:
    def test_validate_valid_dataset(self):
        """Test validation of a valid dataset."""
        schema_content = """
        type: object
        required:
          - seed
          - stiffness_tensor
        properties:
          seed:
            type: integer
          stiffness_tensor:
            type: array
            items:
              type: number
        """
        
        metadata = {
            'entries': [
                {
                    'seed': 1,
                    'stiffness_tensor': [200.0, 80.0, 80.0, 200.0],
                    'inclusion_density': 0.3,
                    'topology_type': 'random'
                },
                {
                    'seed': 2,
                    'stiffness_tensor': [180.0, 70.0, 70.0, 180.0],
                    'inclusion_density': 0.5,
                    'topology_type': 'aligned'
                }
            ]
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            schema_path = tmpdir / 'schema.yaml'
            metadata_path = tmpdir / 'metadata.json'
            log_path = tmpdir / 'validation_log.csv'
            
            with open(schema_path, 'w') as f:
                f.write(schema_content)
            
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f)
            
            failures = validate_dataset(
                metadata_path=metadata_path,
                schema_path=schema_path,
                validation_log_path=log_path
            )
            
            assert failures == 0
            assert log_path.exists()

    def test_validate_invalid_dataset(self):
        """Test validation of a dataset with invalid entries."""
        schema_content = """
        type: object
        required:
          - seed
          - stiffness_tensor
        properties:
          seed:
            type: integer
          stiffness_tensor:
            type: array
            items:
              type: number
        """
        
        metadata = {
            'entries': [
                {
                    'seed': 1,
                    'stiffness_tensor': [200.0, 80.0, 80.0, 200.0],
                    'inclusion_density': 0.3,
                    'topology_type': 'random'
                },
                {
                    'seed': 2,
                    'stiffness_tensor': [-100.0, 70.0, 70.0, 180.0],  # Negative value
                    'inclusion_density': 0.5,
                    'topology_type': 'aligned'
                },
                {
                    'seed': 3,
                    'stiffness_tensor': [np.nan, 70.0, 70.0, 180.0],  # NaN value
                    'inclusion_density': 0.7,
                    'topology_type': 'percolating'
                }
            ]
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            schema_path = tmpdir / 'schema.yaml'
            metadata_path = tmpdir / 'metadata.json'
            log_path = tmpdir / 'validation_log.csv'
            
            with open(schema_path, 'w') as f:
                f.write(schema_content)
            
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f)
            
            failures = validate_dataset(
                metadata_path=metadata_path,
                schema_path=schema_path,
                validation_log_path=log_path
            )
            
            assert failures == 2  # Two invalid entries
            
            # Check log file contents
            with open(log_path, 'r') as f:
                reader = csv.reader(f)
                rows = list(reader)
            
            assert len(rows) == 3  # Header + 2 failures
            assert rows[0] == ['entry_id', 'reason', 'density', 'topology']
            
            # Check that failures are logged
            reasons = [row[1] for row in rows[1:]]
            assert any("negative" in r.lower() for r in reasons)
            assert any("nan" in r.lower() for r in reasons)

    def test_validate_with_solver_convergence_failure(self):
        """Test validation with solver convergence failure."""
        schema_content = """
        type: object
        required:
          - seed
          - stiffness_tensor
        properties:
          seed:
            type: integer
          stiffness_tensor:
            type: array
            items:
              type: number
        """
        
        metadata = {
            'entries': [
                {
                    'seed': 1,
                    'stiffness_tensor': [200.0, 80.0, 80.0, 200.0],
                    'solver_residual': 0.0001,  # Below threshold
                    'inclusion_density': 0.3,
                    'topology_type': 'random'
                },
                {
                    'seed': 2,
                    'stiffness_tensor': [180.0, 70.0, 70.0, 180.0],
                    'solver_residual': 0.001,  # Above threshold
                    'inclusion_density': 0.5,
                    'topology_type': 'aligned'
                }
            ]
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            schema_path = tmpdir / 'schema.yaml'
            metadata_path = tmpdir / 'metadata.json'
            log_path = tmpdir / 'validation_log.csv'
            
            with open(schema_path, 'w') as f:
                f.write(schema_content)
            
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f)
            
            failures = validate_dataset(
                metadata_path=metadata_path,
                schema_path=schema_path,
                validation_log_path=log_path
            )
            
            assert failures == 1
            
            # Check log file
            with open(log_path, 'r') as f:
                reader = csv.reader(f)
                rows = list(reader)
            
            assert len(rows) == 2  # Header + 1 failure
            assert "Solver Convergence Failure" in rows[1][1]