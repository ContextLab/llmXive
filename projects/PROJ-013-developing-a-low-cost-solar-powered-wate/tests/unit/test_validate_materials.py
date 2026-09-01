"""
Unit tests for T016 validation logic.
"""
import os
import csv
import tempfile
from pathlib import Path
import pytest

from code.validate_materials import validate_materials_csv

@pytest.fixture
def temp_csv_dir():
    """Create a temporary directory for test CSV files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def create_test_csv(temp_csv_dir: Path, rows: list, fieldnames: list = None) -> Path:
    """Helper to create a test CSV file."""
    if fieldnames is None:
        fieldnames = [
            'material_id', 'thermal_conductivity', 'emissivity', 
            'specific_heat', 'density', 'unit_price', 'calculated_cost', 'status'
        ]
    
    csv_path = temp_csv_dir / 'test_materials.csv'
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return csv_path

def test_valid_materials_pass(temp_csv_dir):
    """Test that a CSV with valid materials passes validation."""
    rows = [
        {
            'material_id': 'aluminum',
            'thermal_conductivity': '237',
            'emissivity': '0.09',
            'specific_heat': '900',
            'density': '2700',
            'unit_price': '2.50',
            'calculated_cost': '125.00',
            'status': 'valid'
        }
    ]
    csv_path = create_test_csv(temp_csv_dir, rows)
    
    is_valid, errors = validate_materials_csv(csv_path)
    
    assert is_valid is True
    assert len(errors) == 0

def test_missing_value_fails(temp_csv_dir):
    """Test that missing values in valid materials cause failure."""
    rows = [
        {
            'material_id': 'copper',
            'thermal_conductivity': '',  # Missing
            'emissivity': '0.03',
            'specific_heat': '385',
            'density': '8960',
            'unit_price': '9.50',
            'calculated_cost': '450.00',
            'status': 'valid'
        }
    ]
    csv_path = create_test_csv(temp_csv_dir, rows)
    
    is_valid, errors = validate_materials_csv(csv_path)
    
    assert is_valid is False
    assert any("Missing value" in err for err in errors)

def test_negative_cost_fails(temp_csv_dir):
    """Test that negative costs cause validation failure."""
    rows = [
        {
            'material_id': 'steel',
            'thermal_conductivity': '50',
            'emissivity': '0.90',
            'specific_heat': '500',
            'density': '7850',
            'unit_price': '1.20',
            'calculated_cost': '-50.00',  # Negative cost
            'status': 'valid'
        }
    ]
    csv_path = create_test_csv(temp_csv_dir, rows)
    
    is_valid, errors = validate_materials_csv(csv_path)
    
    assert is_valid is False
    assert any("Cost must be positive" in err for err in errors)

def test_zero_cost_fails(temp_csv_dir):
    """Test that zero costs cause validation failure."""
    rows = [
        {
            'material_id': 'plastic',
            'thermal_conductivity': '0.2',
            'emissivity': '0.95',
            'specific_heat': '1800',
            'density': '1200',
            'unit_price': '0.80',
            'calculated_cost': '0.00',  # Zero cost
            'status': 'valid'
        }
    ]
    csv_path = create_test_csv(temp_csv_dir, rows)
    
    is_valid, errors = validate_materials_csv(csv_path)
    
    assert is_valid is False
    assert any("Cost must be positive" in err for err in errors)

def test_invalid_price_status_allowed(temp_csv_dir):
    """Test that entries with invalid_price status are allowed (missing values ok)."""
    rows = [
        {
            'material_id': 'unknown_material',
            'thermal_conductivity': '',
            'emissivity': '',
            'specific_heat': '',
            'density': '',
            'unit_price': '',
            'calculated_cost': '',
            'status': 'invalid_price'
        },
        {
            'material_id': 'aluminum',
            'thermal_conductivity': '237',
            'emissivity': '0.09',
            'specific_heat': '900',
            'density': '2700',
            'unit_price': '2.50',
            'calculated_cost': '125.00',
            'status': 'valid'
        }
    ]
    csv_path = create_test_csv(temp_csv_dir, rows)
    
    is_valid, errors = validate_materials_csv(csv_path)
    
    assert is_valid is True
    assert len(errors) == 0

def test_file_not_found(temp_csv_dir):
    """Test that missing file returns failure."""
    csv_path = temp_csv_dir / 'nonexistent.csv'
    
    is_valid, errors = validate_materials_csv(csv_path)
    
    assert is_valid is False
    assert any("File not found" in err for err in errors)

def test_empty_csv_fails(temp_csv_dir):
    """Test that an empty CSV (no rows) fails."""
    rows = []
    csv_path = create_test_csv(temp_csv_dir, rows)
    
    is_valid, errors = validate_materials_csv(csv_path)
    
    assert is_valid is False
    assert any("empty" in err.lower() for err in errors)

def test_mixed_valid_invalid(temp_csv_dir):
    """Test a CSV with both valid and invalid_price entries."""
    rows = [
        {
            'material_id': 'aluminum',
            'thermal_conductivity': '237',
            'emissivity': '0.09',
            'specific_heat': '900',
            'density': '2700',
            'unit_price': '2.50',
            'calculated_cost': '125.00',
            'status': 'valid'
        },
        {
            'material_id': 'missing_price_material',
            'thermal_conductivity': '',
            'emissivity': '',
            'specific_heat': '',
            'density': '',
            'unit_price': '',
            'calculated_cost': '',
            'status': 'invalid_price'
        },
        {
            'material_id': 'copper',
            'thermal_conductivity': '401',
            'emissivity': '0.03',
            'specific_heat': '385',
            'density': '8960',
            'unit_price': '9.50',
            'calculated_cost': '450.00',
            'status': 'valid'
        }
    ]
    csv_path = create_test_csv(temp_csv_dir, rows)
    
    is_valid, errors = validate_materials_csv(csv_path)
    
    assert is_valid is True
    assert len(errors) == 0

def test_non_numeric_cost_fails(temp_csv_dir):
    """Test that non-numeric cost values fail validation."""
    rows = [
        {
            'material_id': 'aluminum',
            'thermal_conductivity': '237',
            'emissivity': '0.09',
            'specific_heat': '900',
            'density': '2700',
            'unit_price': '2.50',
            'calculated_cost': 'not_a_number',
            'status': 'valid'
        }
    ]
    csv_path = create_test_csv(temp_csv_dir, rows)
    
    is_valid, errors = validate_materials_csv(csv_path)
    
    assert is_valid is False
    assert any("Non-numeric value" in err for err in errors)