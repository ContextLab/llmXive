import os
import sys
import pytest
import pandas as pd
from pathlib import Path
import tempfile
import shutil

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from data.ingest import load_try_data, load_synthetic_genomics, merge_datasets
from utils.logging import DataPipelineLog
from config import get_config

@pytest.fixture
def temp_dirs():
    """Create temporary directories for raw and processed data."""
    base = tempfile.mkdtemp()
    raw_dir = os.path.join(base, "data", "raw")
    processed_dir = os.path.join(base, "data", "processed")
    logs_dir = os.path.join(base, "data", "logs")
    
    os.makedirs(raw_dir)
    os.makedirs(processed_dir)
    os.makedirs(logs_dir)
    
    yield {
        "base": base,
        "raw": raw_dir,
        "processed": processed_dir,
        "logs": logs_dir
    }
    
    shutil.rmtree(base)

@pytest.fixture
def mock_try_csv(temp_dirs):
    """Create a mock TRY CSV file."""
    path = Path(temp_dirs["raw"]) / "try_data.csv"
    data = {
        "species_id": ["A", "B", "C", "D"],
        "trait_1": [10.5, 20.0, 30.5, 40.0],
        "trait_2": [100, 200, 300, 400]
    }
    df = pd.DataFrame(data)
    df.to_csv(path, index=False)
    return path

@pytest.fixture
def mock_genomics_csv(temp_dirs):
    """Create a mock synthetic genomics CSV file."""
    path = Path(temp_dirs["processed"]) / "synthetic_genomics.csv"
    # Species A and B exist, C and D do not (to test exclusion)
    data = {
        "species_id": ["A", "B"],
        "gene_1": [1, 0],
        "gene_2": [1, 1]
    }
    df = pd.DataFrame(data)
    df.to_csv(path, index=False)
    return path

def test_ingest_merge_logic(temp_dirs, mock_try_csv, mock_genomics_csv):
    """Test that merge correctly identifies missing species and produces output."""
    
    # Setup Logger
    logger = DataPipelineLog(log_dir=temp_dirs["logs"], filename="test_ingest.log")
    
    # Load Data
    try_df = load_try_data(temp_dirs["raw"])
    genomics_df = load_synthetic_genomics(temp_dirs["processed"])
    
    # Merge
    merged_df, missing_count, missing_species = merge_datasets(try_df, genomics_df, logger)
    
    # Assertions
    assert len(merged_df) == 2, "Merged dataset should only contain species A and B"
    assert "species_id" in merged_df.columns
    assert set(merged_df["species_id"]) == {"A", "B"}
    
    assert missing_count == 2, "Species C and D should be excluded"
    assert "C" in missing_species
    assert "D" in missing_species
    
    logger.close()

def test_ingest_save_output(temp_dirs, mock_try_csv, mock_genomics_csv):
    """Test that the main logic saves the file correctly."""
    # This test simulates the core logic of main() without calling the full CLI
    logger = DataPipelineLog(log_dir=temp_dirs["logs"], filename="test_ingest_save.log")
    
    try_df = load_try_data(temp_dirs["raw"])
    genomics_df = load_synthetic_genomics(temp_dirs["processed"])
    
    merged_df, _, _ = merge_datasets(try_df, genomics_df, logger)
    
    output_path = Path(temp_dirs["processed"]) / "merged_dataset.csv"
    merged_df.to_csv(output_path, index=False)
    
    assert output_path.exists(), "Output CSV should be created"
    
    loaded_output = pd.read_csv(output_path)
    assert len(loaded_output) == 2
    
    logger.close()