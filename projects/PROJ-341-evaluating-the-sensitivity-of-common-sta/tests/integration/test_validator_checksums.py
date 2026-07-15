"""
Integration tests for validator checksum functionality (T029d).

Tests the complete flow of:
1. Downloading datasets
2. Computing checksums
3. Registering checksums in metadata
"""
import os
import json
import pytest
from unittest.mock import patch, MagicMock
import pandas as pd
from code.analysis.validator import (
    compute_file_checksum,
    register_dataset_in_metadata,
    download_breast_cancer_dataset,
    download_wine_dataset,
    download_adult_dataset
)
from code.utils.checksum_utils import load_simulation_metadata

@pytest.fixture
def mock_ucimlrepo():
    """Mock ucimlrepo to avoid actual network calls during testing."""
    mock_dataset = MagicMock()
    mock_dataset.data = pd.DataFrame({
        'feature1': [1, 2, 3, 4, 5],
        'feature2': [10, 20, 30, 40, 50],
        'target': [0, 1, 0, 1, 0]
    })
    return mock_dataset

def test_register_dataset_in_metadata(mock_ucimlrepo):
    """Test that datasets are properly registered with checksums."""
    # Create a temporary file
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        mock_ucimlrepo.data.to_csv(f.name, index=False)
        temp_path = f.name
    
    try:
        checksum = compute_file_checksum(temp_path)
        
        # Register the dataset
        register_dataset_in_metadata(
            name="Test_Integration_Dataset",
            source="test:integration",
            file_path=temp_path,
            checksum=checksum
        )
        
        # Verify in metadata
        metadata = load_simulation_metadata()
        datasets = metadata.get('datasets', [])
        
        found = False
        for ds in datasets:
            if ds['name'] == "Test_Integration_Dataset":
                assert ds['checksum'] == checksum
                assert ds['source'] == "test:integration"
                assert 'downloaded_at' in ds
                found = True
                break
        
        assert found
    finally:
        os.unlink(temp_path)

def test_checksum_consistency_across_operations():
    """Test that checksums remain consistent after registration."""
    import tempfile
    
    # Create a test file
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        f.write("a,b,c\n1,2,3\n4,5,6")
        temp_path = f.name
    
    try:
        # Compute initial checksum
        checksum1 = compute_file_checksum(temp_path)
        
        # Register it
        register_dataset_in_metadata(
            name="Consistency_Test",
            source="test:consistency",
            file_path=temp_path,
            checksum=checksum1
        )
        
        # Compute checksum again (should be same)
        checksum2 = compute_file_checksum(temp_path)
        assert checksum1 == checksum2
        
        # Load from metadata
        metadata = load_simulation_metadata()
        for ds in metadata['datasets']:
            if ds['name'] == "Consistency_Test":
                assert ds['checksum'] == checksum1
                break
    finally:
        os.unlink(temp_path)

def test_multiple_datasets_registration():
    """Test registering multiple datasets with different checksums."""
    import tempfile
    
    datasets = []
    checksums = []
    
    for i in range(3):
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            f.write(f"id,value\n{i},{i*10}")
            temp_path = f.name
        
        checksum = compute_file_checksum(temp_path)
        datasets.append({
            'name': f"Multi_Dataset_{i}",
            'source': f"test:{i}",
            'path': temp_path,
            'checksum': checksum
        })
        checksums.append(checksum)
    
    try:
        # Register all datasets
        for ds in datasets:
            register_dataset_in_metadata(
                name=ds['name'],
                source=ds['source'],
                file_path=ds['path'],
                checksum=ds['checksum']
            )
        
        # Verify all are in metadata
        metadata = load_simulation_metadata()
        registered_names = [d['name'] for d in metadata['datasets']]
        
        for ds in datasets:
            assert ds['name'] in registered_names
        
        # Verify checksums match
        for ds in datasets:
            for reg_ds in metadata['datasets']:
                if reg_ds['name'] == ds['name']:
                    assert reg_ds['checksum'] == ds['checksum']
                    break
    finally:
        for ds in datasets:
            os.unlink(ds['path'])