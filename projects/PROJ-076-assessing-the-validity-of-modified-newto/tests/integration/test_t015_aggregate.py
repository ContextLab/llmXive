import pytest
import pandas as pd
import yaml
import os
from pathlib import Path
import sys

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from aggregate import load_filtered_data, update_metadata
from utils import get_logger

logger = get_logger(__name__)

@pytest.fixture
def temp_project_structure(tmp_path):
    """
    Creates a temporary project structure with mock raw data for testing T015.
    """
    # Create directories
    raw_dir = tmp_path / "data" / "raw" / "sparc_data"
    processed_dir = tmp_path / "data" / "processed"
    raw_dir.mkdir(parents=True)
    processed_dir.mkdir(parents=True)

    # Create a mock metadata.yaml
    metadata_content = {
        'project': {'name': 'TEST', 'version': '0.1'},
        'data': {'source': 'SPARC', 'url': 'http://test'},
        'analysis': {'inclination_threshold': 10.0, 'min_points': 15},
        'paths': {'raw_data': str(raw_dir), 'processed_data': str(processed_dir / "filtered_galaxies.csv")}
    }
    metadata_file = tmp_path / "data" / "metadata.yaml"
    with open(metadata_file, 'w') as f:
        yaml.dump(metadata_content, f)

    # Create mock SPARC data files (simulating the output of T013)
    # We need to simulate the directory structure that parse_galaxy_directory expects
    # Based on T013, it expects directories containing rotation curve data
    # Let's create a mock galaxy directory with a 'rotation_curve.dat' file
    
    # Galaxy 1: Valid (inclination < 10, points >= 15)
    gal1_dir = raw_dir / "UGC_001"
    gal1_dir.mkdir()
    # Create a simple rotation curve file
    # Format: r (kpc), v_rot (km/s), v_err (km/s)
    # We need at least 15 points
    points_data = "\n".join([f"{i*0.5}\t{200 + i*0.1}\t{5.0}" for i in range(20)])
    with open(gal1_dir / "rotation_curve.dat", "w") as f:
        f.write(f"# Galaxy: UGC_001\n# Inclination: 5.0\n# Inclination Err: 1.0\n")
        f.write(points_data)

    # Galaxy 2: Invalid (inclination >= 10)
    gal2_dir = raw_dir / "UGC_002"
    gal2_dir.mkdir()
    points_data2 = "\n".join([f"{i*0.5}\t{200 + i*0.1}\t{5.0}" for i in range(20)])
    with open(gal2_dir / "rotation_curve.dat", "w") as f:
        f.write(f"# Galaxy: UGC_002\n# Inclination: 15.0\n# Inclination Err: 1.0\n")
        f.write(points_data2)

    # Galaxy 3: Invalid (points < 15)
    gal3_dir = raw_dir / "UGC_003"
    gal3_dir.mkdir()
    points_data3 = "\n".join([f"{i*0.5}\t{200 + i*0.1}\t{5.0}" for i in range(10)]) # Only 10 points
    with open(gal3_dir / "rotation_curve.dat", "w") as f:
        f.write(f"# Galaxy: UGC_003\n# Inclination: 5.0\n# Inclination Err: 1.0\n")
        f.write(points_data3)

    return tmp_path, metadata_file, raw_dir, processed_dir

def test_t015_load_and_filter(temp_project_structure):
    """
    Test that T015 correctly filters galaxies based on inclination and point count.
    """
    tmp_path, metadata_file, raw_dir, processed_dir = temp_project_structure
    output_csv = processed_dir / "filtered_galaxies.csv"

    # Run the function
    df = load_filtered_data(raw_dir, output_csv)

    # Assertions
    assert output_csv.exists(), "Output CSV file was not created."
    
    # Should contain only UGC_001 (valid galaxy)
    # UGC_002 has inclination 15.0 (>= 10) -> Filtered out
    # UGC_003 has 10 points (< 15) -> Filtered out
    assert len(df) == 1, f"Expected 1 galaxy, got {len(df)}"
    assert df.iloc[0]['galaxy_name'] == 'UGC_001', "Incorrect galaxy selected."
    assert df.iloc[0]['inclination'] == 5.0, "Incorrect inclination value."
    assert df.iloc[0]['points_count'] == 20, "Incorrect point count."

def test_t015_update_metadata(temp_project_structure):
    """
    Test that T015 updates metadata.yaml with the correct timestamp and count.
    """
    tmp_path, metadata_file, raw_dir, processed_dir = temp_project_structure
    output_csv = processed_dir / "filtered_galaxies.csv"

    # First, create the CSV
    df = load_filtered_data(raw_dir, output_csv)
    
    # Then update metadata
    update_metadata(metadata_file, output_csv, len(df))

    # Verify metadata content
    with open(metadata_file, 'r') as f:
        metadata = yaml.safe_load(f)
    
    assert 'analysis' in metadata
    assert 'last_filter_run' in metadata['analysis']
    assert 'filtered_galaxy_count' in metadata['analysis']
    assert metadata['analysis']['filtered_galaxy_count'] == 1

    # Verify timestamp is not empty
    assert metadata['analysis']['last_filter_run'] is not None
