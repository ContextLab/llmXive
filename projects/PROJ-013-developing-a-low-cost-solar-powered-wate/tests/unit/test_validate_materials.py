import pytest
import csv
import os
import tempfile
from pathlib import Path

from code.validate_materials import validate_materials_csv

def create_temp_csv(rows, header=None):
    """Helper to create a temporary CSV file for testing."""
    if header is None:
        header = [
            'material_id', 'thermal_conductivity', 'emissivity', 
            'specific_heat', 'density', 'unit_price', 'cost', 'status'
        ]
    
    fd, path = tempfile.mkstemp(suffix='.csv')
    with os.fdopen(fd, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        for row in rows:
            writer.writerow(row)
    return Path(path)

def test_valid_materials_pass():
    """Test that valid materials with correct data pass validation."""
    rows = [
        ['Aluminum', '237', '0.09', '900', '2700', '2.50', '150.0', 'valid'],
        ['Copper', '401', '0.03', '385', '8960', '6.00', '350.0', 'valid']
    ]
    path = create_temp_csv(rows)
    try:
        is_valid, errors = validate_materials_csv(path)
        assert is_valid is True
        assert len(errors) == 0
    finally:
        os.unlink(path)

def test_missing_value_fails():
    """Test that a missing value in a valid material fails validation."""
    rows = [
        ['Aluminum', '', '0.09', '900', '2700', '2.50', '150.0', 'valid'],
    ]
    path = create_temp_csv(rows)
    try:
        is_valid, errors = validate_materials_csv(path)
        assert is_valid is False
        assert any('Missing value' in err for err in errors)
    finally:
        os.unlink(path)

def test_non_positive_cost_fails():
    """Test that a non-positive cost in a valid material fails validation."""
    rows = [
        ['Aluminum', '237', '0.09', '900', '2700', '2.50', '-10.0', 'valid'],
    ]
    path = create_temp_csv(rows)
    try:
        is_valid, errors = validate_materials_csv(path)
        assert is_valid is False
        assert any('Cost must be positive' in err for err in errors)
    finally:
        os.unlink(path)

def test_zero_cost_fails():
    """Test that a zero cost in a valid material fails validation."""
    rows = [
        ['Aluminum', '237', '0.09', '900', '2700', '2.50', '0.0', 'valid'],
    ]
    path = create_temp_csv(rows)
    try:
        is_valid, errors = validate_materials_csv(path)
        assert is_valid is False
        assert any('Cost must be positive' in err for err in errors)
    finally:
        os.unlink(path)

def test_invalid_status_ignored():
    """Test that materials with invalid status are not strictly validated for cost."""
    rows = [
        ['Plastic', '0.2', '0.9', '1500', '1200', '1.00', '-5.0', 'invalid_price'],
    ]
    path = create_temp_csv(rows)
    try:
        is_valid, errors = validate_materials_csv(path)
        # Should pass because we only validate 'valid' status strictly
        # However, if there are NO valid materials, it should fail
        # Let's add a valid one to ensure the invalid one is ignored
        rows.append(['Steel', '50', '0.8', '450', '7850', '1.50', '20.0', 'valid'])
        with open(path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'material_id', 'thermal_conductivity', 'emissivity', 
                'specific_heat', 'density', 'unit_price', 'cost', 'status'
            ])
            for r in rows:
                writer.writerow(r)
        
        is_valid, errors = validate_materials_csv(path)
        assert is_valid is True
        assert len(errors) == 0
    finally:
        os.unlink(path)

def test_no_valid_materials_fails():
    """Test that having no valid materials fails validation."""
    rows = [
        ['Plastic', '0.2', '0.9', '1500', '1200', '1.00', '10.0', 'invalid_price'],
    ]
    path = create_temp_csv(rows)
    try:
        is_valid, errors = validate_materials_csv(path)
        assert is_valid is False
        assert any('No materials with' in err for err in errors)
    finally:
        os.unlink(path)
