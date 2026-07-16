import os
import sys
import csv
import tempfile
import shutil
from pathlib import Path

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from generators.synthetic_data_generator import generate_synthetic_data, save_to_csv
from infrastructure.path_utils import get_project_root, resolve_path

def test_synthetic_fallback_generation():
    """
    Test that T012 fallback logic generates the required file and data.
    """
    # Create a temporary directory for testing to avoid polluting the real data dir
    # However, the task requires writing to data/raw. We will test the generation logic
    # and then verify the file creation in the real path if possible, or mock the path.
    
    # For this test, we simulate the generation and verify the content structure.
    data = generate_synthetic_data(n_samples=100, defect_density_range=(0.001, 0.1), seed=42)
    
    assert len(data) >= 100, "Should generate at least 100 entries"
    
    required_keys = ["defect_type", "defect_density", "conductivity", "elastic_tensor", "fracture_energy", "data_source"]
    for entry in data:
        for key in required_keys:
            assert key in entry, f"Missing key {key} in entry"
        
        density = float(entry["defect_density"])
        assert 0.001 <= density <= 0.1, f"Defect density {density} out of bounds"
        
        assert entry["data_source"] == "synthetic", "data_source flag not set to synthetic"
        
        # Check physical bounds (approximate)
        assert float(entry["conductivity"]) > 0
        assert float(entry["fracture_energy"]) > 0
    
    print("T012 Fallback generation logic test passed.")

def test_fallback_file_creation():
    """
    Test that the fallback script actually writes the file to disk.
    """
    # We rely on the main script logic or direct call to save_to_csv
    # Since the task requires the file to be written, we verify the function does it.
    # We'll write to a temp file to be safe, then assert existence.
    
    temp_dir = tempfile.mkdtemp()
    try:
        # Mock the path resolution for this test
        # In real run, it goes to data/raw
        test_file = os.path.join(temp_dir, "test_fallback.csv")
        
        data = generate_synthetic_data(n_samples=10)
        save_to_csv(data, test_file)
        
        assert os.path.exists(test_file), "File was not created"
        
        with open(test_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 10, "Row count mismatch"
            
        print("T012 File creation test passed.")
    finally:
        shutil.rmtree(temp_dir)

if __name__ == "__main__":
    test_synthetic_fallback_generation()
    test_fallback_file_creation()
    print("All T012 tests passed.")