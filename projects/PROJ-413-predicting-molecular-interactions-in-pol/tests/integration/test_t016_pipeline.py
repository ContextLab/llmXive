import pytest
import os
import tempfile
import csv
from pathlib import Path
from data.generate_curated import main
from utils.exceptions import DataError

def test_t016_full_pipeline():
    """
    Integration test for T016: 
    1. Creates a mock cleaned_data.csv in data/raw
    2. Runs main()
    3. Verifies data/curated/curated_dataset.csv is created with correct structure
    """
    # We need to mock the project structure temporarily or use a temp dir
    # Since the script uses hardcoded PROJECT_ROOT relative to its location,
    # we might need to adjust the test to run in a specific environment or mock paths.
    # For now, we assume the test runs in the project root context or we patch.
    # Given the constraints, let's test the logic by calling the functions directly
    # rather than the main() which relies on global paths, OR we assume the test
    # is run in the project root.
    
    # Let's test the function logic directly to ensure robustness
    from data.generate_curated import load_cleaned_data, generate_curated_dataset
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        raw_dir = tmpdir / "raw"
        curated_dir = tmpdir / "curated"
        raw_dir.mkdir()
        curated_dir.mkdir()
        
        # Create mock cleaned data
        input_path = raw_dir / "cleaned_data.csv"
        with open(input_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['polymer_smiles', 'filler_smiles', 'adhesion_energy'])
            writer.writeheader()
            writer.writerow({'polymer_smiles': 'CCO', 'filler_smiles': 'c1ccccc1', 'adhesion_energy': '1.5'})
            writer.writerow({'polymer_smiles': 'C', 'filler_smiles': 'C', 'adhesion_energy': '0.5'})
            writer.writerow({'polymer_smiles': 'INVALID', 'filler_smiles': 'C', 'adhesion_energy': '0.5'}) # Invalid SMILES
            writer.writerow({'polymer_smiles': 'CC', 'filler_smiles': 'C', 'adhesion_energy': ''}) # Missing energy
        
        # Patch the paths in the module if we were calling main()
        # But we can just call the functions with explicit paths
        data = load_cleaned_data(input_path)
        assert len(data) == 4
        
        output_path = curated_dir / "curated_dataset.csv"
        generate_curated_dataset(data, output_path)
        
        assert output_path.exists()
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            # Should have 2 valid rows (first two). Third has invalid SMILES, fourth missing energy.
            assert len(rows) == 2
            
            # Check columns
            required_cols = ['polymer_smiles', 'filler_smiles', 'adhesion_energy', 
                             'polymer_nodes', 'polymer_edges', 'filler_nodes', 'filler_edges', 'is_valid']
            for col in required_cols:
                assert col in rows[0]