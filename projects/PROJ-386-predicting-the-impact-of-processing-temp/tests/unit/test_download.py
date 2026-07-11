import os
import sys
import json
import tempfile
import pytest
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.config import ensure_dirs, set_global_seed
from code.data.download import filter_non_rolling_processes

@pytest.fixture
def mock_dataset_path():
    """Create a temporary CSV file with mock rolling and non-rolling data."""
    ensure_dirs()
    set_global_seed(42)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        # Header
        f.write("source_id,process_type,rolling_temperature,grain_size,composition\n")
        # Rolling entries (should be kept)
        f.write("1,Rolling,450.5,25.0,{\"Mg\": 1.2, \"Si\": 0.5}\n")
        f.write("2,Rolling,500.0,30.0,{\"Mg\": 0.8, \"Cu\": 0.4}\n")
        # Non-rolling entries (should be filtered out)
        f.write("3,Casting,650.0,150.0,{\"Mg\": 1.0}\n")
        f.write("4,SPD,400.0,5.0,{\"Mg\": 2.0, \"Zn\": 0.5}\n")
        f.write("5,Extrusion,380.0,40.0,{\"Mg\": 1.5}\n")
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)

def test_filters_non_rolling_processes(mock_dataset_path):
    """
    Verifies exclusion of non-rolling processes (Casting, SPD, Extrusion).
    
    Expected behavior:
    - Input contains: Rolling, Rolling, Casting, SPD, Extrusion
    - Output should contain ONLY the 2 Rolling entries.
    """
    output_path = str(Path(mock_dataset_path).parent / "filtered_rolling.csv")
    
    # Run the filter function
    filter_non_rolling_processes(mock_dataset_path, output_path)
    
    # Verify output file exists
    assert os.path.exists(output_path), "Output file was not created."
    
    # Read and count lines in output
    with open(output_path, 'r') as f:
        lines = f.readlines()
    
    # Check header
    assert lines[0].strip() == "source_id,process_type,rolling_temperature,grain_size,composition"
    
    # Check data rows
    # We expect exactly 2 data rows (the Rolling entries)
    data_rows = lines[1:]
    assert len(data_rows) == 2, f"Expected 2 rows, got {len(data_rows)}. Non-rolling processes were not filtered correctly."
    
    # Verify the content of the rows
    for row in data_rows:
        parts = row.strip().split(',')
        assert parts[1] == "Rolling", f"Found non-Rolling process type '{parts[1]}' in output."
    
    # Cleanup output file
    if os.path.exists(output_path):
        os.unlink(output_path)