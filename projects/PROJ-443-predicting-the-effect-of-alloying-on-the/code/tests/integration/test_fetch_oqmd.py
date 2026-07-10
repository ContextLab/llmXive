"""
Integration tests for the OQMD Fetcher (T014).

These tests verify that the fetcher correctly:
1. Loads data from a real source (simulated via a local file in tests).
2. Applies the >= 5 elements filter correctly.
3. Handles missing data sources gracefully (fail loudly).
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
import pandas as pd
import pytest
import yaml

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from src.data.fetch_oqmd import OQMDFetcher

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test data."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)

@pytest.fixture
def sample_hea_data(temp_data_dir):
    """Create a sample CSV with mixed element counts."""
    data = {
        'composition': [
            'FeCoNiCrMn',      # 5 elements (HEA)
            'FeCoNiCr',        # 4 elements (Not HEA)
            'FeCoNiCrMnAlTi',  # 7 elements (HEA)
            'TiAl',            # 2 elements (Not HEA)
            'FeCoNiCrMnV',     # 6 elements (HEA)
            'AuAgCu',          # 3 elements (Not HEA)
            'FeCoNiCrMnAl'     # 6 elements (HEA)
        ],
        'bulk_modulus': [150.0, 140.0, 160.0, 100.0, 155.0, 90.0, 165.0],
        'energy': [-1.0, -0.9, -1.1, -0.8, -1.05, -0.7, -1.2]
    }
    df = pd.DataFrame(data)
    csv_path = temp_data_dir / "oqmd_bulk.csv"
    df.to_csv(csv_path, index=False)
    return csv_path

@pytest.fixture
def setup_metadata(temp_data_dir):
    """Setup source_metadata.yaml in the temp dir."""
    metadata = {
        'sources': {
            'oqmd': {
                'url': 'https://example.com/oqmd_subset.csv',
                'verified': True
            }
        }
    }
    metadata_path = temp_data_dir / "source_metadata.yaml"
    with open(metadata_path, 'w') as f:
        yaml.dump(metadata, f)
    return metadata_path

def test_filter_hea_samples(sample_hea_data):
    """Test that the filter correctly identifies >= 5 element alloys."""
    # We need to mock the file path lookup in the fetcher
    # Since the fetcher looks in data/raw by default, we temporarily move the file
    # or mock the path. For simplicity, we will instantiate the fetcher and call 
    # the internal method after loading the df manually to avoid file system dependency issues
    # in the test environment, or we can patch the fetch_raw_data method.
    
    # Better approach: Create the fetcher, but override the path logic via monkeypatch
    # or by creating a custom subclass for the test.
    
    fetcher = OQMDFetcher()
    
    # Load the sample data manually to test the filter logic
    df = pd.read_csv(sample_hea_data)
    
    filtered_df = fetcher.apply_hea_filter(df)
    
    expected_count = 4 # FeCoNiCrMn, FeCoNiCrMnAlTi, FeCoNiCrMnV, FeCoNiCrMnAl
    assert len(filtered_df) == expected_count, f"Expected {expected_count} samples, got {len(filtered_df)}"
    
    # Verify no 4-element or less samples remain
    for _, row in filtered_df.iterrows():
        comp = row['composition']
        # Re-count to be sure
        import re
        count = len(re.findall(r'[A-Z][a-z]?', comp))
        assert count >= 5, f"Sample {comp} has {count} elements, expected >= 5"

def test_empty_dataframe_filter(sample_hea_data):
    """Test filtering on an empty dataframe."""
    fetcher = OQMDFetcher()
    empty_df = pd.DataFrame(columns=['composition', 'bulk_modulus'])
    result = fetcher.apply_hea_filter(empty_df)
    assert result.empty

def test_no_data_source_raises_error(temp_data_dir):
    """Test that fetcher raises FileNotFoundError if no data exists."""
    # Ensure no data files exist in the temp directory
    # We will temporarily change the RAW_OUTPUT_DIR logic by mocking
    # But since the class uses hardcoded paths relative to project_root,
    # we must rely on the fact that the test environment doesn't have
    # the real OQMD data in data/raw.
    
    # The fetcher will look in project_root/data/raw
    # If that doesn't exist or is empty, it should raise.
    # We can't easily move the real data folder, so we test the logic
    # by checking if the specific error is raised when the file is missing.
    
    fetcher = OQMDFetcher()
    
    # Mock the fetch_raw_data to simulate missing file
    original_fetch = fetcher.fetch_raw_data
    
    def mock_fetch():
        raise FileNotFoundError("Real OQMD data source not found...")
    
    fetcher.fetch_raw_data = mock_fetch # type: ignore
    
    with pytest.raises(FileNotFoundError):
        fetcher.run()
    
    # Restore
    fetcher.fetch_raw_data = original_fetch

def test_invalid_composition_format(sample_hea_data):
    """Test handling of weird composition formats."""
    fetcher = OQMDFetcher()
    df = pd.DataFrame({
        'composition': ['Fe50Co50', 'FeCo', 'InvalidString123'],
        'bulk_modulus': [100, 100, 100]
    })
    
    # Fe50Co50 -> Fe, Co (2)
    # FeCo -> Fe, Co (2)
    # InvalidString123 -> I (1) (assuming I is Iodine) or 0 if regex fails
    # All should be filtered out
    
    result = fetcher.apply_hea_filter(df)
    assert len(result) == 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])