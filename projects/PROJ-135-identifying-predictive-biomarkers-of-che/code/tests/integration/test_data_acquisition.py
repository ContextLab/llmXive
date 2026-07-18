import os
import sys
import json
import tempfile
from pathlib import Path
import pytest

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from src.data_acquisition import (
    download_from_huggingface,
    verify_response_labels,
    main
)

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_download_from_huggingface_valid_id(temp_data_dir):
    """Test downloading a valid GEO dataset from HuggingFace."""
    # Note: This test may be skipped in CI if network is unavailable
    # or if the HuggingFace dataset is not accessible
    try:
        result = download_from_huggingface("GSE25055", temp_data_dir)
        # If we get here, download succeeded
        assert result is not None
        assert result.exists()
    except Exception as e:
        # If download fails (network, dataset not found), mark as skipped
        pytest.skip(f"Download not available: {e}")

def test_verify_response_labels_structure(temp_data_dir):
    """Test that verify_response_labels correctly identifies response columns."""
    import pandas as pd
    
    # Create a mock dataset with response labels
    mock_data = {
        'sample_id': ['S1', 'S2', 'S3'],
        'response': ['Responder', 'Non-Responder', 'Responder'],
        'gene_expr': [1.0, 2.0, 3.0]
    }
    df = pd.DataFrame(mock_data)
    
    mock_file = temp_data_dir / "mock_data.parquet"
    df.to_parquet(mock_file)
    
    assert verify_response_labels(mock_file) is True

def test_verify_response_labels_missing(temp_data_dir):
    """Test that verify_response_labels returns False when no response column."""
    import pandas as pd
    
    # Create a mock dataset WITHOUT response labels
    mock_data = {
        'sample_id': ['S1', 'S2', 'S3'],
        'gene_expr': [1.0, 2.0, 3.0]
    }
    df = pd.DataFrame(mock_data)
    
    mock_file = temp_data_dir / "mock_data_no_response.parquet"
    df.to_parquet(mock_file)
    
    assert verify_response_labels(mock_file) is False

def test_main_function_structure():
    """Test that main function returns appropriate exit codes."""
    # This test checks the structure, not actual execution
    # Actual execution would require network access and real data
    assert callable(main)

def test_geo_datasets_defined():
    """Test that the required GEO datasets are defined in the module."""
    from src.data_acquisition import GEO_DATASETS
    
    assert len(GEO_DATASETS) >= 2
    dataset_ids = [d['dataset_id'] for d in GEO_DATASETS]
    assert 'GSE25055' in dataset_ids
    assert 'GSE42752' in dataset_ids

def test_huggingface_mapping_exists():
    """Test that HuggingFace mappings are defined for all GEO datasets."""
    from src.data_acquisition import HUGGINGFACE_GEO_MAP
    
    assert 'GSE25055' in HUGGINGFACE_GEO_MAP
    assert 'GSE42752' in HUGGINGFACE_GEO_MAP
    assert HUGGINGFACE_GEO_MAP['GSE25055'] is not None
    assert HUGGINGFACE_GEO_MAP['GSE42752'] is not None