import os
import json
import csv
import tempfile
from pathlib import Path
import numpy as np
from PIL import Image

import pytest

from code.data.persistor import (
    compute_image_hash,
    persist_masked_images,
    persist_scores,
    run_persistence_pipeline
)
from code.utils.seed import set_seed

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def sample_images():
    """Create sample image and mask arrays."""
    set_seed(42)
    images = []
    for i in range(5):
        img = np.random.randint(0, 256, (64, 64, 3), dtype=np.uint8)
        mask = np.random.randint(0, 2, (64, 64), dtype=np.uint8)
        images.append((img, mask, f"test_img_{i}"))
    return images

def test_compute_image_hash(temp_dir):
    """Test image hash computation."""
    # Create a test image
    img_path = temp_dir / "test.png"
    img = Image.fromarray(np.random.randint(0, 256, (32, 32, 3), dtype=np.uint8))
    img.save(img_path)
    
    # Compute hash
    hash1 = compute_image_hash(img_path)
    hash2 = compute_image_hash(img_path)
    
    # Hashes should be identical for same file
    assert hash1 == hash2
    assert len(hash1) == 64  # SHA-256 hex length

def test_persist_masked_images(temp_dir, sample_images):
    """Test persisting masked images."""
    hash_registry = {}
    
    records = persist_masked_images(
        sample_images,
        temp_dir / "masked_images",
        hash_registry
    )
    
    # Check records
    assert len(records) == len(sample_images)
    assert len(hash_registry) == len(sample_images)
    
    # Check files exist
    for record in records:
        filepath = Path(record['path'])
        assert filepath.exists()
        assert filepath.suffix == '.png'
        
        # Check hash is recorded
        image_id = record['image_id']
        assert image_id in hash_registry
        assert hash_registry[image_id] == record['hash']

def test_persist_scores(temp_dir):
    """Test persisting scores to CSV."""
    scores = [
        {"image_id": "img_1", "score": 3.5, "mode": "CI_MODE"},
        {"image_id": "img_2", "score": 4.2, "mode": "CI_MODE"},
        {"image_id": "img_3", "score": 2.1, "mode": "CI_MODE"}
    ]
    
    output_file = temp_dir / "scores.csv"
    persist_scores(scores, output_file)
    
    # Check file exists
    assert output_file.exists()
    
    # Read and verify
    with open(output_file, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    assert len(rows) == 3
    assert rows[0]['image_id'] == 'img_1'
    assert float(rows[0]['score']) == 3.5
    assert rows[0]['mode'] == 'CI_MODE'

def test_persist_scores_empty(temp_dir):
    """Test persisting empty scores list."""
    output_file = temp_dir / "empty_scores.csv"
    persist_scores([], output_file)
    
    # File should be created but empty (or just header)
    assert output_file.exists()

def test_run_persistence_pipeline_integration(temp_dir, monkeypatch):
    """Test full persistence pipeline (mocked dataset fetch)."""
    # Mock the dataset fetch to return small sample
    from code.data import loader
    original_fetch = loader.fetch_places365_subset
    
    def mock_fetch(sample_size=10):
        set_seed(42)
        dataset = []
        for i in range(sample_size):
            img = np.random.randint(0, 256, (64, 64, 3), dtype=np.uint8)
            dataset.append({
                'image_id': f"mock_img_{i}",
                'image': img
            })
        return dataset
    
    monkeypatch.setattr(loader, 'fetch_places365_subset', mock_fetch)
    
    # Mock config
    from code import config
    original_mode = config._mode
    config._mode = 'CI'
    
    # Mock paths
    original_get_path = config.get_path
    def mock_get_path(key):
        path_map = {
            'processed_images': temp_dir / 'processed' / 'masked_images',
            'annotations': temp_dir / 'annotations'
        }
        return path_map.get(key, temp_dir / key)
    
    monkeypatch.setattr(config, 'get_path', mock_get_path)
    monkeypatch.setattr(config, 'ensure_paths_exist', lambda: None)
    
    try:
        # Run pipeline
        summary = run_persistence_pipeline(
            {'seed': 42},
            sample_size=10
        )
        
        # Verify summary
        assert summary['total_images'] == 10
        assert summary['masks_generated'] == 10
        assert summary['images_persisted'] == 10
        assert summary['scores_persisted'] == 10
        assert summary['mode'] == 'CI_MODE'
        
        # Verify files exist
        assert Path(summary['output_dir']).exists()
        assert Path(summary['scores_file']).exists()
        assert Path(summary['hash_registry_file']).exists()
        
        # Verify CSV content
        with open(summary['scores_file'], 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert len(rows) == 10
        assert all('mode' in row and row['mode'] == 'CI_MODE' for row in rows)
        
    finally:
        # Restore mocks
        config._mode = original_mode
        config.get_path = original_get_path
        loader.fetch_places365_subset = original_fetch