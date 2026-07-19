import os
import json
import tempfile
import pytest
import numpy as np
from code.data.preprocess import (
    load_raw_csv,
    detect_missing_values,
    compute_medians,
    impute_missing_values,
    encode_categorical,
    check_sample_count,
    check_zero_variance,
    split_and_scale,
    save_normalization_bounds
)
from code.config import get_processed_data_dir, ensure_directories

def test_load_raw_csv():
    """Test loading a raw CSV file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("laser_power,scan_speed,yield_strength\n")
        f.write("200,500,300\n")
        f.write("250,600,350\n")
        temp_path = f.name
    
    try:
        data = load_raw_csv(temp_path)
        assert len(data) == 2
        assert data[0]['laser_power'] == '200'
        assert data[1]['yield_strength'] == '350'
    finally:
        os.unlink(temp_path)

def test_detect_missing_values():
    """Test detection of missing values."""
    data = [
        {'laser_power': '200', 'scan_speed': '', 'yield_strength': '300'},
        {'laser_power': '', 'scan_speed': '500', 'yield_strength': '350'},
        {'laser_power': '250', 'scan_speed': '600', 'yield_strength': '300'}
    ]
    missing = detect_missing_values(data, ['laser_power', 'scan_speed'])
    assert missing['laser_power'] == 1
    assert missing['scan_speed'] == 1

def test_compute_medians():
    """Test median computation."""
    data = [
        {'laser_power': '200', 'scan_speed': '500', 'yield_strength': '300'},
        {'laser_power': '250', 'scan_speed': '600', 'yield_strength': '350'},
        {'laser_power': '225', 'scan_speed': '550', 'yield_strength': '325'}
    ]
    medians = compute_medians(data, ['laser_power', 'scan_speed', 'yield_strength'])
    assert medians['laser_power'] == 225.0
    assert medians['scan_speed'] == 550.0
    assert medians['yield_strength'] == 325.0

def test_impute_missing_values():
    """Test median imputation."""
    data = [
        {'laser_power': '200', 'scan_speed': '', 'yield_strength': '300'},
        {'laser_power': '', 'scan_speed': '500', 'yield_strength': '350'}
    ]
    medians = {'laser_power': 200.0, 'scan_speed': 500.0, 'yield_strength': 325.0}
    imputed = impute_missing_values(data, medians, ['laser_power', 'scan_speed', 'yield_strength'])
    assert imputed[0]['scan_speed'] == 500.0
    assert imputed[1]['laser_power'] == 200.0

def test_encode_categorical():
    """Test one-hot encoding of categorical column."""
    data = [
        {'laser_power': '200', 'alloy_type': 'AlSi10Mg'},
        {'laser_power': '250', 'alloy_type': 'Ti64'},
        {'laser_power': '225', 'alloy_type': 'AlSi10Mg'}
    ]
    encoded, columns = encode_categorical(data, 'alloy_type')
    assert 'alloy_type' not in encoded[0]
    assert 'alloy_type_AlSi10Mg' in encoded[0]
    assert 'alloy_type_Ti64' in encoded[0]
    assert encoded[0]['alloy_type_AlSi10Mg'] == 1.0
    assert encoded[0]['alloy_type_Ti64'] == 0.0
    assert encoded[1]['alloy_type_AlSi10Mg'] == 0.0
    assert encoded[1]['alloy_type_Ti64'] == 1.0

def test_check_sample_count():
    """Test sample count validation."""
    data = [{'laser_power': '200'}] * 49
    with pytest.raises(ValueError, match="Sample count"):
        check_sample_count(data, min_samples=50)
    
    data = [{'laser_power': '200'}] * 50
    check_sample_count(data, min_samples=50)  # Should not raise

def test_check_zero_variance():
    """Test zero variance detection."""
    data = [
        {'laser_power': 200.0, 'scan_speed': 500.0},
        {'laser_power': 200.0, 'scan_speed': 500.0},
        {'laser_power': 200.0, 'scan_speed': 500.0}
    ]
    # Mock logger
    class MockLogger:
        def warning(self, msg): pass
    
    dropped = check_zero_variance(data, ['laser_power', 'scan_speed'], MockLogger())
    assert 'laser_power' in dropped
    assert 'scan_speed' in dropped

def test_split_and_scale():
    """Test train-test split and MinMax scaling."""
    data = [
        {'laser_power': 200.0, 'scan_speed': 500.0},
        {'laser_power': 250.0, 'scan_speed': 600.0},
        {'laser_power': 300.0, 'scan_speed': 700.0},
        {'laser_power': 350.0, 'scan_speed': 800.0},
        {'laser_power': 400.0, 'scan_speed': 900.0}
    ]
    train, test, bounds = split_and_scale(data, train_ratio=0.6, random_seed=42)
    
    # Check bounds
    assert bounds['laser_power']['min'] == 200.0
    assert bounds['laser_power']['max'] == 400.0
    
    # Check scaling (values should be between 0 and 1)
    for row in train + test:
        assert 0.0 <= row['laser_power'] <= 1.0
        assert 0.0 <= row['scan_speed'] <= 1.0

def test_save_normalization_bounds():
    """Test saving normalization bounds to JSON."""
    bounds = {
        'laser_power': {'min': 200.0, 'max': 400.0},
        'scan_speed': {'min': 500.0, 'max': 900.0}
    }
    
    ensure_directories()
    processed_dir = get_processed_data_dir()
    output_path = os.path.join(processed_dir, 'test_bounds.json')
    
    save_normalization_bounds(bounds, output_path)
    
    assert os.path.exists(output_path)
    with open(output_path, 'r') as f:
        loaded = json.load(f)
    assert loaded == bounds
    
    os.unlink(output_path)
