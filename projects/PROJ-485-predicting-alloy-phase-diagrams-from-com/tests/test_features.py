"""
Tests for feature generation module.
"""
import os
import sys
import csv
import tempfile
import pytest
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from features.generate_descriptors import (
    load_elemental_properties,
    calculate_mean_atomic_radius,
    calculate_electronegativity_variance,
    calculate_valence_electron_count,
    calculate_hume_rothery_concentration,
    generate_descriptors,
    process_alloy_dataset
)
from utils.error_codes import ErrorCode

@pytest.fixture
def sample_properties():
    """Sample elemental properties for testing."""
    return {
        'CU': {
            'atomic_radius_angstrom': 1.28,
            'electronegativity_pauling': 1.90,
            'valence_electrons': 1.0
        },
        'ZN': {
            'atomic_radius_angstrom': 1.33,
            'electronegativity_pauling': 1.65,
            'valence_electrons': 2.0
        },
        'AL': {
            'atomic_radius_angstrom': 1.43,
            'electronegativity_pauling': 1.61,
            'valence_electrons': 3.0
        },
        'FE': {
            'atomic_radius_angstrom': 1.24,
            'electronegativity_pauling': 1.83,
            'valence_electrons': 2.0
        }
    }

@pytest.fixture
def temp_properties_file(sample_properties):
    """Create a temporary properties CSV file."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        writer = csv.DictWriter(f, fieldnames=['element', 'atomic_radius_angstrom', 'electronegativity_pauling', 'valence_electrons'])
        writer.writeheader()
        for element, props in sample_properties.items():
            writer.writerow({
                'element': element,
                'atomic_radius_angstrom': props['atomic_radius_angstrom'],
                'electronegativity_pauling': props['electronegativity_pauling'],
                'valence_electrons': props['valence_electrons']
            })
        temp_path = f.name
    
    yield temp_path
    
    os.unlink(temp_path)

def test_load_elemental_properties(temp_properties_file):
    """Test loading elemental properties from CSV."""
    properties = load_elemental_properties(temp_properties_file)
    
    assert len(properties) == 4
    assert 'CU' in properties
    assert abs(properties['CU']['atomic_radius_angstrom'] - 1.28) < 0.001
    assert abs(properties['ZN']['electronegativity_pauling'] - 1.65) < 0.001

def test_load_elemental_properties_file_not_found():
    """Test error handling for missing properties file."""
    with pytest.raises(FileNotFoundError):
        load_elemental_properties('/nonexistent/path.csv')

def test_calculate_mean_atomic_radius(sample_properties):
    """Test mean atomic radius calculation."""
    # Equal mix of Cu and Zn
    composition = {'CU': 0.5, 'ZN': 0.5}
    mean_radius = calculate_mean_atomic_radius(composition, sample_properties)
    
    expected = (1.28 * 0.5) + (1.33 * 0.5)
    assert abs(mean_radius - expected) < 0.001

def test_calculate_electronegativity_variance(sample_properties):
    """Test electronegativity variance calculation."""
    # Equal mix of Cu and Zn
    composition = {'CU': 0.5, 'ZN': 0.5}
    variance = calculate_electronegativity_variance(composition, sample_properties)
    
    mean_en = (1.90 * 0.5) + (1.65 * 0.5)
    expected_variance = ((1.90 - mean_en) ** 2 * 0.5) + ((1.65 - mean_en) ** 2 * 0.5)
    
    assert abs(variance - expected_variance) < 0.001

def test_calculate_valence_electron_count(sample_properties):
    """Test valence electron count calculation."""
    # Equal mix of Cu and Zn
    composition = {'CU': 0.5, 'ZN': 0.5}
    ve_count = calculate_valence_electron_count(composition, sample_properties)
    
    expected = (1.0 * 0.5) + (2.0 * 0.5)
    assert abs(ve_count - expected) < 0.001

def test_calculate_hume_rothery_concentration(sample_properties):
    """Test Hume-Rothery concentration calculation."""
    # Cu-Zn system
    composition = {'CU': 0.5, 'ZN': 0.5}
    hr_params = calculate_hume_rothery_concentration(composition, sample_properties)
    
    # Calculate expected values
    r_cu = sample_properties['CU']['atomic_radius_angstrom']
    r_zn = sample_properties['ZN']['atomic_radius_angstrom']
    r_avg = (r_cu + r_zn) / 2.0
    expected_radius_diff = abs(r_cu - r_zn) / r_avg
    
    en_cu = sample_properties['CU']['electronegativity_pauling']
    en_zn = sample_properties['ZN']['electronegativity_pauling']
    expected_en_diff = abs(en_cu - en_zn)
    
    assert abs(hr_params['radius_diff_max'] - expected_radius_diff) < 0.001
    assert abs(hr_params['en_diff_max'] - expected_en_diff) < 0.001

def test_generate_descriptors(sample_properties):
    """Test full descriptor generation."""
    composition = {'CU': 0.6, 'ZN': 0.4}
    descriptors = generate_descriptors(composition, sample_properties)
    
    assert 'mean_atomic_radius' in descriptors
    assert 'electronegativity_variance' in descriptors
    assert 'valence_electron_count' in descriptors
    assert 'radius_diff_max' in descriptors
    assert 'en_diff_max' in descriptors
    assert 'is_solid_soluble' in descriptors
    assert 'num_elements' in descriptors
    assert 'max_fraction' in descriptors
    
    assert descriptors['num_elements'] == 2
    assert descriptors['max_fraction'] == 0.6

def test_descriptor_deviation(temp_properties_file):
    """
    Test that derived values deviate ≤1% from elemental properties.
    This is a mandatory test per SC-005 and SC-007.
    """
    properties = load_elemental_properties(temp_properties_file)
    
    # Test single element (should be exactly the property value)
    for element, props in properties.items():
        composition = {element: 1.0}
        descriptors = generate_descriptors(composition, properties)
        
        # Mean radius should match the element's radius
        assert abs(descriptors['mean_atomic_radius'] - props['atomic_radius_angstrom']) < 0.001
        
        # Variance should be 0 for single element
        assert abs(descriptors['electronegativity_variance']) < 0.001
        
        # VE count should match
        assert abs(descriptors['valence_electron_count'] - props['valence_electrons']) < 0.001

def test_process_alloy_dataset(temp_properties_file):
    """Test processing an alloy dataset."""
    # Create temporary input file
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as infile:
        writer = csv.DictWriter(infile, fieldnames=['system_id', 'element_cu', 'element_zn'])
        writer.writeheader()
        writer.writerow({'system_id': 'CuZn_1', 'element_cu': '0.7', 'element_zn': '0.3'})
        writer.writerow({'system_id': 'CuZn_2', 'element_cu': '0.5', 'element_zn': '0.5'})
        input_path = infile.name
    
    # Create temporary output file
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as outfile:
        output_path = outfile.name
    
    try:
        count = process_alloy_dataset(input_path, output_path, temp_properties_file)
        
        assert count == 2
        
        # Verify output file
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
        assert len(rows) == 2
        assert rows[0]['system_id'] == 'CuZn_1'
        assert rows[1]['system_id'] == 'CuZn_2'
        
        # Check that numeric fields are populated
        assert float(rows[0]['mean_atomic_radius']) > 0
        assert float(rows[0]['electronegativity_variance']) >= 0
        
    finally:
        os.unlink(input_path)
        os.unlink(output_path)

def test_process_alloy_dataset_empty_composition(temp_properties_file):
    """Test handling of empty composition."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as infile:
        writer = csv.DictWriter(infile, fieldnames=['system_id', 'element_cu', 'element_zn'])
        writer.writeheader()
        writer.writerow({'system_id': 'Empty', 'element_cu': '', 'element_zn': ''})
        input_path = infile.name
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as outfile:
        output_path = outfile.name
    
    try:
        count = process_alloy_dataset(input_path, output_path, temp_properties_file)
        assert count == 0  # Empty composition should be skipped
    finally:
        os.unlink(input_path)
        os.unlink(output_path)

def test_generate_descriptors_unknown_element(sample_properties):
    """Test handling of unknown elements in composition."""
    composition = {'CU': 0.5, 'UNKNOWN': 0.5}
    descriptors = generate_descriptors(composition, sample_properties)
    
    # Should still calculate based on known elements
    assert 'mean_atomic_radius' in descriptors
    assert descriptors['num_elements'] == 1  # Only counts known elements

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
