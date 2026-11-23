"""
Unit tests for the generate_materials_csv script logic.

Verifies that the CSV generation logic correctly:
1. Loads materials from the hardcoded source.
2. Integrates pricing data.
3. Calculates costs correctly.
4. Handles missing prices by setting status to 'invalid_price'.
"""
import os
import csv
import tempfile
from pathlib import Path
import pytest

from data_ingestion import load_nist_materials, fetch_market_prices, calculate_mass, calculate_cost, GeometryConfig
from generate_materials_csv import generate_materials_csv

# Mock geometry for testing
TEST_GEOMETRY = GeometryConfig(
    geometry_id="test_geom",
    inclination_angle=45.0,
    surface_area=1.0,
    thickness=0.003
)

def test_load_nist_materials_exists():
    """Verify that NIST materials can be loaded."""
    materials = load_nist_materials()
    assert isinstance(materials, dict)
    assert len(materials) > 0
    # Check for expected keys in at least one material
    first_material = next(iter(materials.values()))
    assert "thermal_conductivity" in first_material
    assert "emissivity" in first_material

def test_fetch_market_prices_structure():
    """Verify that fetch_market_prices returns a dict of prices."""
    prices = fetch_market_prices()
    assert isinstance(prices, dict)
    # Prices should be positive floats
    for mat, price in prices.items():
        assert isinstance(price, float)
        assert price > 0

def test_generate_csv_creates_file():
    """Verify that generate_materials_csv creates the output file."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_path = Path(tmp_dir) / "materials.csv"
        generate_materials_csv(output_path)
        
        assert output_path.exists()
        assert output_path.stat().st_size > 0

def test_csv_columns_present():
    """Verify that the CSV has the correct column headers."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_path = Path(tmp_dir) / "materials.csv"
        generate_materials_csv(output_path)
        
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            
            expected_headers = [
                "material_id", "thermal_conductivity", "emissivity", 
                "specific_heat", "density", "unit_price", "cost", "status"
            ]
            
            for header in expected_headers:
                assert header in headers, f"Missing header: {header}"

def test_csv_status_values():
    """Verify that the status column contains valid values."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_path = Path(tmp_dir) / "materials.csv"
        generate_materials_csv(output_path)
        
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            statuses = set(row['status'] for row in reader)
            
            # Status should be either 'valid' or 'invalid_price'
            allowed_statuses = {"valid", "invalid_price"}
            assert statuses.issubset(allowed_statuses), f"Unexpected statuses found: {statuses - allowed_statuses}"

def test_cost_calculation_positive_for_valid():
    """Verify that valid materials have positive costs."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_path = Path(tmp_dir) / "materials.csv"
        generate_materials_csv(output_path)
        
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['status'] == 'valid':
                    cost = float(row['cost'])
                    assert cost > 0, f"Valid material {row['material_id']} has non-positive cost: {cost}"
                elif row['status'] == 'invalid_price':
                    cost = float(row['cost'])
                    assert cost == 0.0, f"Invalid material {row['material_id']} should have 0 cost, got {cost}"

def test_csv_no_missing_values_for_valid_materials():
    """Verify that valid materials do not have missing values in key columns."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_path = Path(tmp_dir) / "materials.csv"
        generate_materials_csv(output_path)
        
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['status'] == 'valid':
                    # Check that numeric fields are not empty strings
                    assert row['thermal_conductivity'] != "", f"Missing thermal_conductivity for {row['material_id']}"
                    assert row['emissivity'] != "", f"Missing emissivity for {row['material_id']}"
                    assert row['specific_heat'] != "", f"Missing specific_heat for {row['material_id']}"
                    assert row['density'] != "", f"Missing density for {row['material_id']}"
                    assert row['unit_price'] != "", f"Missing unit_price for {row['material_id']}"
                    assert row['cost'] != "", f"Missing cost for {row['material_id']}"