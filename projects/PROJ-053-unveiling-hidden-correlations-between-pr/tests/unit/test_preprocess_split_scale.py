import pytest
import numpy as np
from pathlib import Path
import sys
import os

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / 'code'))

from data.preprocess import load_raw_csv, detect_missing_values, compute_medians, impute_missing_values
from data.preprocess import encode_categorical, check_sample_count, check_zero_variance
from data.preprocess import split_and_scale
from config import get_random_seed

def test_split_and_scale_fit_only_on_train():
    """Test that MinMaxScaler is fit only on training data."""
    # Create mock data
    mock_data = [
        {'laser_power': 100.0, 'scan_speed': 200.0, 'layer_thickness': 0.1, 'yield_strength': 200.0, 'ductility': 10.0},
        {'laser_power': 200.0, 'scan_speed': 400.0, 'layer_thickness': 0.2, 'yield_strength': 400.0, 'ductility': 20.0},
        {'laser_power': 300.0, 'scan_speed': 600.0, 'layer_thickness': 0.3, 'yield_strength': 600.0, 'ductility': 30.0},
        {'laser_power': 400.0, 'scan_speed': 800.0, 'layer_thickness': 0.4, 'yield_strength': 800.0, 'ductility': 40.0},
        {'laser_power': 500.0, 'scan_speed': 1000.0, 'layer_thickness': 0.5, 'yield_strength': 1000.0, 'ductility': 50.0},
        {'laser_power': 600.0, 'scan_speed': 1200.0, 'layer_thickness': 0.6, 'yield_strength': 1200.0, 'ductility': 60.0},
        {'laser_power': 700.0, 'scan_speed': 1400.0, 'layer_thickness': 0.7, 'yield_strength': 1400.0, 'ductility': 70.0},
        {'laser_power': 800.0, 'scan_speed': 1600.0, 'layer_thickness': 0.8, 'yield_strength': 1600.0, 'ductility': 80.0},
        {'laser_power': 900.0, 'scan_speed': 1800.0, 'layer_thickness': 0.9, 'yield_strength': 1800.0, 'ductility': 90.0},
        {'laser_power': 1000.0, 'scan_speed': 2000.0, 'layer_thickness': 1.0, 'yield_strength': 2000.0, 'ductility': 100.0},
    ]
    
    train_result, test_result, scaler, feature_names = split_and_scale(mock_data, test_size=0.2, random_state=42)
    
    # Check that test set values are scaled using train statistics
    # In MinMaxScaler, values are scaled as (x - min) / (max - min)
    # If we fit on train, the test values should be scaled based on train min/max
    # If train min=100, max=900 (for laser_power), then:
    # train 100 -> 0.0, train 900 -> 1.0
    # test 1000 -> (1000-100)/(900-100) = 900/800 = 1.125 (outside [0,1])
    
    # Extract scaled values
    train_laser = [row['laser_power'] for row in train_result['data']]
    test_laser = [row['laser_power'] for row in test_result['data']]
    
    # Check train range is [0, 1]
    assert min(train_laser) >= 0.0 and max(train_laser) <= 1.0, "Train set should be scaled to [0, 1]"
    
    # Check that test set might exceed [0, 1] if it has values outside train range
    # This confirms scaler was fit only on train
    # In our mock, test has 1000 which is > 900 (max train), so scaled value > 1.0
    assert max(test_laser) > 1.0, "Test set should have values > 1.0 if scaler fit only on train"
    
    # Also verify the split is majority-minority (80/20)
    assert len(train_result['data']) > len(test_result['data']), "Train set should be majority"

def test_split_and_scale_random_state():
    """Test that random_state ensures reproducibility."""
    mock_data = [
        {'laser_power': float(i*100), 'scan_speed': float(i*200), 'layer_thickness': float(i*0.1), 
         'yield_strength': float(i*200), 'ductility': float(i*10)}
        for i in range(1, 21)
    ]
    
    result1, _, _, _ = split_and_scale(mock_data, test_size=0.2, random_state=42)
    result2, _, _, _ = split_and_scale(mock_data, test_size=0.2, random_state=42)
    
    # Check that results are identical
    assert len(result1['data']) == len(result2['data'])
    for r1, r2 in zip(result1['data'], result2['data']):
        assert r1['laser_power'] == r2['laser_power']
        assert r1['yield_strength'] == r2['yield_strength']

def test_split_and_scale_target_preservation():
    """Test that target columns are preserved and scaled correctly."""
    mock_data = [
        {'laser_power': 100.0, 'scan_speed': 200.0, 'layer_thickness': 0.1, 'yield_strength': 200.0, 'ductility': 10.0},
        {'laser_power': 200.0, 'scan_speed': 400.0, 'layer_thickness': 0.2, 'yield_strength': 400.0, 'ductility': 20.0},
        {'laser_power': 300.0, 'scan_speed': 600.0, 'layer_thickness': 0.3, 'yield_strength': 600.0, 'ductility': 30.0},
        {'laser_power': 400.0, 'scan_speed': 800.0, 'layer_thickness': 0.4, 'yield_strength': 800.0, 'ductility': 40.0},
        {'laser_power': 500.0, 'scan_speed': 1000.0, 'layer_thickness': 0.5, 'yield_strength': 1000.0, 'ductility': 50.0},
        {'laser_power': 600.0, 'scan_speed': 1200.0, 'layer_thickness': 0.6, 'yield_strength': 1200.0, 'ductility': 60.0},
        {'laser_power': 700.0, 'scan_speed': 1400.0, 'layer_thickness': 0.7, 'yield_strength': 1400.0, 'ductility': 70.0},
        {'laser_power': 800.0, 'scan_speed': 1600.0, 'layer_thickness': 0.8, 'yield_strength': 1600.0, 'ductility': 80.0},
    ]
    
    train_result, test_result, scaler, feature_names = split_and_scale(mock_data, test_size=0.2, random_state=42)
    
    # Check that targets are present
    assert 'yield_strength' in train_result['data'][0]
    assert 'ductility' in train_result['data'][0]
    assert 'yield_strength' in test_result['data'][0]
    assert 'ductility' in test_result['data'][0]
    
    # Check that targets are also scaled (since they are numeric and included in X for scaling)
    # Note: In our implementation, targets are scaled along with features
    train_ys = [row['yield_strength'] for row in train_result['data']]
    assert min(train_ys) >= 0.0 and max(train_ys) <= 1.0, "Target yield_strength should be scaled to [0, 1]"