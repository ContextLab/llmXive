import json
import os
import tempfile
from pathlib import Path
import pandas as pd
import pytest

# Import the functions we are testing
from dft_calculator import (
    load_raw_dataset,
    get_valid_geometry_indices,
    stratified_subset_selection,
    write_subset_indices
)

@pytest.fixture
def temp_project_structure():
    """Create a temporary directory structure mimicking the project."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        data_raw = root / "data" / "raw"
        data_geo = root / "data" / "optimized_geometries"
        state = root / "state"
        
        data_raw.mkdir(parents=True)
        data_geo.mkdir(parents=True)
        state.mkdir(parents=True)
        
        # Create a mock raw dataset
        csv_content = """molecule_id,SMILES,experimental_barrier
        mol1,C,10.5
        mol2,CC,20.2
        mol3,CCC,15.0
        mol4,CCCC,30.0
        mol5,CCCCC,25.5
        mol6,CCCCCC,12.0
        mol7,CCCCCCC,18.0
        mol8,CCCCCCCC,22.0
        mol9,CCCCCCCCC,28.0
        mol10,CCCCCCCCCC,14.0
        """
        (data_raw / "barrier_dataset.csv").write_text(csv_content)
        
        # Create some mock geometry files
        for i in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]:
            (data_geo / f"mol{i}.xyz").write_text(f"1\ncomment\nC 0 0 0\n")
        
        yield root
        
def test_load_raw_dataset(temp_project_structure):
    """Test loading the raw dataset."""
    path = temp_project_structure / "data" / "raw" / "barrier_dataset.csv"
    df = load_raw_dataset(path)
    assert len(df) == 10
    assert 'molecule_id' in df.columns
    assert 'experimental_barrier' in df.columns

def test_get_valid_geometry_indices(temp_project_structure):
    """Test scanning for valid geometry files."""
    path = temp_project_structure / "data" / "optimized_geometries"
    ids = get_valid_geometry_indices(path)
    assert len(ids) == 10
    assert "mol1" in ids
    assert "mol10" in ids

def test_stratified_subset_selection_all(temp_project_structure):
    """Test selection when N < 50 (should return all)."""
    # Create a small dataset
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        data_geo = root / "data" / "optimized_geometries"
        data_raw = root / "data" / "raw"
        data_geo.mkdir(parents=True)
        data_raw.mkdir(parents=True)
        
        # Create 5 samples
        csv_content = "molecule_id,SMILES,experimental_barrier\n"
        for i in range(1, 6):
            csv_content += f"mol{i},C,{i*10}\n"
            (data_geo / f"mol{i}.xyz").write_text("1\n\nC 0 0 0\n")
        
        (data_raw / "barrier_dataset.csv").write_text(csv_content)
        
        df = load_raw_dataset(data_raw / "barrier_dataset.csv")
        ids = get_valid_geometry_indices(data_geo)
        df_filtered = df[df['molecule_id'].isin(ids)]
        
        selected = stratified_subset_selection(df_filtered, sample_size=50)
        assert len(selected) == 5

def test_stratified_subset_selection_subset(temp_project_structure):
    """Test selection when N >= 50 (should return 50)."""
    # We will simulate a larger dataset by creating many rows in the fixture
    # But for this test, we'll just mock the dataframe directly to save setup time
    # since the fixture only has 10 rows.
    
    # Create a synthetic dataframe with 100 rows
    data = []
    for i in range(100):
        data.append({
            'molecule_id': f"mol{i}",
            'SMILES': 'C' * (i % 10 + 1),
            'experimental_barrier': float(i % 100)
        })
    df_large = pd.DataFrame(data)
    
    selected = stratified_subset_selection(df_large, sample_size=50)
    assert len(selected) == 50
    # Check that it's a subset of original
    assert all(mid in df_large['molecule_id'].values for mid in selected)

def test_write_subset_indices(temp_project_structure):
    """Test writing the subset to JSON."""
    ids = ["mol1", "mol2", "mol3"]
    output_path = temp_project_structure / "state" / "test_subset.json"
    write_subset_indices(ids, output_path)
    
    assert output_path.exists()
    with open(output_path, 'r') as f:
        data = json.load(f)
    
    assert "molecule_ids" in data
    assert data["molecule_ids"] == ids