import pytest
import pandas as pd
import numpy as np
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.preprocessing.generate_exclusion_log import (
    load_covariate_data,
    generate_exclusion_log,
    get_project_root
)

@pytest.fixture
def temp_covariate_file():
    """Create a temporary TSV file with sample covariate data."""
    data = {
        'sample_id': ['S1', 'S2', 'S3', 'S4', 'S5'],
        'age': [25, 30, np.nan, 45, 50],
        'bmi': [22.5, np.nan, 24.0, 26.5, np.nan],
        'antibiotics': [0, 1, 0, np.nan, 0],
        'fiber': [15.0, 20.0, 18.0, 10.0, 25.0]
    }
    df = pd.DataFrame(data)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.tsv', delete=False) as f:
        df.to_csv(f, sep='\t', index=False)
        path = Path(f.name)
    
    yield path
    
    # Cleanup
    if path.exists():
        os.unlink(path)

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for output files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_generate_exclusion_log_basic(temp_covariate_file, temp_output_dir):
    """Test basic generation of exclusion log."""
    df = load_covariate_data(temp_covariate_file)
    output_path = temp_output_dir / "test_exclusion_log.txt"
    
    # S2: 1/3 missing (33%) -> Exclude (>20%)
    # S3: 1/3 missing (33%) -> Exclude (>20%)
    # S5: 1/3 missing (33%) -> Exclude (>20%)
    # S1, S4: 0% missing -> Retain
    excluded_count = generate_exclusion_log(
        df, 
        output_path, 
        missing_threshold=0.20,
        id_column='sample_id'
    )
    
    assert excluded_count == 3
    assert output_path.exists()
    
    content = output_path.read_text()
    assert "Covariate Exclusion Log" in content
    assert "Samples excluded: 3" in content
    assert "S2" in content
    assert "S3" in content
    assert "S5" in content

def test_generate_exclusion_log_no_exclusions(temp_output_dir):
    """Test log generation when no samples are excluded."""
    data = {
        'sample_id': ['S1', 'S2'],
        'age': [25, 30],
        'bmi': [22.5, 24.0]
    }
    df = pd.DataFrame(data)
    
    output_path = temp_output_dir / "test_no_exclusion.txt"
    excluded_count = generate_exclusion_log(df, output_path, missing_threshold=0.20)
    
    assert excluded_count == 0
    content = output_path.read_text()
    assert "Samples excluded: 0" in content
    assert "(None)" in content

def test_generate_exclusion_log_empty_file(temp_output_dir):
    """Test handling of an empty DataFrame."""
    df = pd.DataFrame()
    output_path = temp_output_dir / "test_empty.txt"
    
    with pytest.raises(ValueError, match="Input DataFrame is empty"):
        generate_exclusion_log(df, output_path)

def test_file_not_found():
    """Test handling of missing input file."""
    non_existent = Path("/tmp/non_existent_file_xyz.tsv")
    
    with pytest.raises(FileNotFoundError):
        load_covariate_data(non_existent)

def test_generate_exclusion_log_index_based_id(temp_output_dir):
    """Test log generation using index as ID when no id_column is provided."""
    data = {
        'age': [25, np.nan, 30],
        'bmi': [22.5, 24.0, np.nan]
    }
    df = pd.DataFrame(data)
    
    output_path = temp_output_dir / "test_index_id.txt"
    # Row 1 has 1/2 missing (50%) -> Exclude
    excluded_count = generate_exclusion_log(df, output_path, missing_threshold=0.20)
    
    assert excluded_count == 1
    content = output_path.read_text()
    # Should contain the index value '1'
    assert "1" in content
