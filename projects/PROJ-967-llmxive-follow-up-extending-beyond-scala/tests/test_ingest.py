import os
import tempfile
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from ingest import load_and_align_data, setup_logging, setup_directories

@pytest.fixture
def sample_dataframe():
    """Create a valid sample dataframe matching the expected schema."""
    n = 10
    return pd.DataFrame({
        "image_path": [f"img_{i}.jpg" for i in range(n)],
        "species_id": [1, 2, 3, 1, 2, 3, 1, 2, 3, 1],
        "prompt_text": [f"Describe image {i}" for i in range(n)],
        "teacher_scores": [
            [0.1, 0.2, 0.3, 0.4] for _ in range(n)
        ],
        "student_scalar": [0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4],
        "human_annotations": [
            [0.2, 0.3, 0.4, 0.5] for _ in range(n)
        ],
        "primary_dimension": [0, 1, 2, 3, 0, 1, 2, 3, 0, 1]
    })

@pytest.fixture
def temp_output_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_load_and_align_valid_data(sample_dataframe, temp_output_dir):
    """Test that valid data loads and writes correctly."""
    input_path = temp_output_dir / "input.parquet"
    output_path = temp_output_dir / "output.parquet"
    
    sample_dataframe.to_parquet(input_path)
    
    logger = setup_logging()
    df_out, flags = load_and_align_data(logger, str(input_path), str(output_path))
    
    assert df_out.shape == sample_dataframe.shape
    assert os.path.exists(output_path)
    assert len(flags) == 0

def test_load_and_align_missing_columns(sample_dataframe, temp_output_dir):
    """Test that missing columns raise an error."""
    input_path = temp_output_dir / "input_missing.parquet"
    output_path = temp_output_dir / "output.parquet"
    
    # Remove a required column
    df_missing = sample_dataframe.drop(columns=["student_scalar"])
    df_missing.to_parquet(input_path)
    
    logger = setup_logging()
    
    with pytest.raises(ValueError, match="Missing required columns"):
        load_and_align_data(logger, str(input_path), str(output_path))

def test_load_and_align_invalid_primary_dimension(sample_dataframe, temp_output_dir):
    """Test that invalid primary_dimension values are flagged."""
    input_path = temp_output_dir / "input_invalid.parquet"
    output_path = temp_output_dir / "output.parquet"
    
    # Inject an invalid primary_dimension
    df_invalid = sample_dataframe.copy()
    df_invalid.loc[0, "primary_dimension"] = 99
    df_invalid.to_parquet(input_path)
    
    logger = setup_logging()
    df_out, flags = load_and_align_data(logger, str(input_path), str(output_path))
    
    assert len(flags) > 0
    assert any(f["column"] == "primary_dimension" for f in flags)

def test_load_and_align_null_values(sample_dataframe, temp_output_dir):
    """Test that null values in critical columns are flagged."""
    input_path = temp_output_dir / "input_null.parquet"
    output_path = temp_output_dir / "output.parquet"
    
    df_null = sample_dataframe.copy()
    df_null.loc[0, "student_scalar"] = np.nan
    df_null.to_parquet(input_path)
    
    logger = setup_logging()
    df_out, flags = load_and_align_data(logger, str(input_path), str(output_path))
    
    assert len(flags) > 0
    assert any(f["column"] == "student_scalar" for f in flags)

def test_file_not_found(temp_output_dir):
    """Test that missing input file raises FileNotFoundError."""
    logger = setup_logging()
    input_path = temp_output_dir / "nonexistent.parquet"
    output_path = temp_output_dir / "output.parquet"
    
    with pytest.raises(FileNotFoundError):
        load_and_align_data(logger, str(input_path), str(output_path))
