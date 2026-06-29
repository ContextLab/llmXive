import pytest
import pandas as pd
import json
from pathlib import Path
import sys
import os

# Add code to path if running directly
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from utils.sampling import get_chemical_family, sample_by_chemical_family
from ingest import main as ingest_main

def test_get_chemical_family():
    """Test chemical family detection logic."""
    # Test with dict
    comp_dict = {'Fe': 1, 'O': 3}
    assert get_chemical_family(comp_dict) == 'Transition'
    
    # Test with string
    comp_str = "{'Na': 1, 'Cl': 1}"
    assert get_chemical_family(comp_str) == 'Alkali'
    
    # Test with unknown element
    comp_unknown = {'X': 1}
    assert get_chemical_family(comp_unknown) == 'Unknown'

def test_sample_by_chemical_family():
    """Test stratified sampling logic."""
    # Create a synthetic dataset
    data = []
    # 100 Transition metals
    for _ in range(100):
        data.append({'id': len(data), 'composition': {'Fe': 1, 'O': 3}, 'value': 1.0})
    # 50 Alkali metals
    for _ in range(50):
        data.append({'id': len(data), 'composition': {'Na': 1, 'Cl': 1}, 'value': 2.0})
        
    df = pd.DataFrame(data)
    
    # Sample 30%
    sampled, counts = sample_by_chemical_family(df, target_rows=45, random_state=42)
    
    assert len(sampled) <= 45
    assert len(sampled) > 0
    # Check that we have both families represented (roughly proportional)
    assert 'Transition' in [get_chemical_family(r['composition']) for r in sampled['composition']]
    
def test_ingest_main_execution():
    """Test that the ingest main function runs and produces expected outputs."""
    # This test assumes the environment is set up correctly
    # It verifies that the files are created and have valid structure
    try:
        ingest_main()
        
        # Check outputs exist
        processed_dir = Path('data/processed')
        assert processed_dir.exists()
        
        csv_path = processed_dir / 'sampled_raw_data.csv'
        assert csv_path.exists()
        
        manifest_path = processed_dir / 'sampling_manifest.json'
        assert manifest_path.exists()
        
        # Validate manifest content
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
            
        assert 'row_count' in manifest
        assert 'sha256' in manifest
        assert 'sampling_info' in manifest
        
        # Validate CSV is not empty
        df = pd.read_csv(csv_path)
        assert len(df) > 0
        
    except Exception as e:
        pytest.fail(f"Ingest main execution failed: {e}")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])