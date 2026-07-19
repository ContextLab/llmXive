import os
import json
import tempfile
import pytest
from code.data.preprocess import validate_and_preprocess, save_normalization_bounds
from code.config import get_processed_data_dir, ensure_directories

def test_full_preprocessing_pipeline():
    """Test the full preprocessing pipeline from raw CSV to processed data."""
    # Create temporary raw CSV
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("laser_power,scan_speed,layer_thickness,yield_strength,ductility,alloy_type\n")
        for i in range(60):  # Ensure N >= 50
            f.write(f"{200 + i*5},{500 + i*10},{0.03 + i*0.001},{300 + i*5},{15 + i*0.5},AlSi10Mg\n")
        raw_path = f.name
    
    try:
        # Create temporary schema
        schema = {
            "required_columns": ["laser_power", "scan_speed", "layer_thickness", "yield_strength", "ductility"],
            "optional_columns": ["fatigue_life", "alloy_type"]
        }
        schema_path = raw_path.replace('.csv', '_schema.yaml')
        with open(schema_path, 'w') as sf:
            import yaml
            yaml.dump(schema, sf)
        
        # Ensure directories exist
        ensure_directories()
        processed_dir = get_processed_data_dir()
        
        # Mock logger
        class MockLogger:
            def info(self, msg): print(msg)
            def warning(self, msg): print(f"WARNING: {msg}")
            def error(self, msg): print(f"ERROR: {msg}")
        
        logger = MockLogger()
        
        # Run preprocessing
        train_data, test_data = validate_and_preprocess(raw_path, schema_path, processed_dir, logger)
        
        # Verify outputs
        assert len(train_data) > 0
        assert len(test_data) > 0
        assert len(train_data) + len(test_data) == 60
        
        # Verify normalization bounds file exists
        bounds_path = os.path.join(processed_dir, 'normalization_bounds.json')
        assert os.path.exists(bounds_path), f"Normalization bounds file not found at {bounds_path}"
        
        # Verify bounds content
        with open(bounds_path, 'r') as f:
            bounds = json.load(f)
        
        assert 'laser_power' in bounds
        assert 'scan_speed' in bounds
        assert 'min' in bounds['laser_power']
        assert 'max' in bounds['laser_power']
        assert bounds['laser_power']['min'] >= 200.0
        assert bounds['laser_power']['max'] <= 500.0
        
        # Verify one-hot encoding worked
        assert any('alloy_type_AlSi10Mg' in row for row in train_data)
        assert 'alloy_type' not in train_data[0]
        
        # Verify scaling (values between 0 and 1)
        for row in train_data + test_data:
            for key, val in row.items():
                if isinstance(val, float) and key != 'alloy_type_AlSi10Mg':
                    assert 0.0 <= val <= 1.0, f"Value {val} for {key} not in [0, 1]"
        
        # Cleanup
        if os.path.exists(schema_path):
            os.unlink(schema_path)
            
    finally:
        os.unlink(raw_path)
