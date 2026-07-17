import os
import sys
import json
import tempfile
import pytest
from pathlib import Path
import pandas as pd
import numpy as np

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from data.loader import run_stress_test, MicrostructureDataset, OOMSafeDataLoader
from utils.config import set_seed, get_seed

@pytest.fixture
def sample_manifest(tmp_path):
    """Create a temporary manifest file with sample data."""
    set_seed(42)
    
    # Create sample images and manifest
    images_dir = tmp_path / 'images'
    images_dir.mkdir()
    
    data = []
    for i in range(10):
        # Create a small dummy image
        img_path = images_dir / f'image_{i:04d}.png'
        img = np.random.randint(0, 255, (64, 64, 3), dtype=np.uint8)
        import cv2
        cv2.imwrite(str(img_path), img)
        
        data.append({
            'image_id': f'id_{i:04d}',
            'image_path': str(img_path),
            'yield_strength': np.random.uniform(200, 500)
        })
    
    manifest_path = tmp_path / 'test_manifest.csv'
    df = pd.DataFrame(data)
    df.to_csv(manifest_path, index=False)
    
    return manifest_path

@pytest.mark.integration
def test_stress_test_memory_limit(sample_manifest):
    """Test that stress test correctly measures memory and respects limits."""
    # Run with a very low limit to ensure it fails
    results = run_stress_test(sample_manifest, max_memory_gb=0.001)  # 1MB limit
    
    assert results['status'] == 'failed'
    assert 'exceeded limit' in results['error'].lower()
    assert results['peak_memory_gb'] > 0.001

@pytest.mark.integration
def test_stress_test_passes_normal_limit(sample_manifest):
    """Test that stress test passes with reasonable memory limit."""
    results = run_stress_test(sample_manifest, max_memory_gb=7.0)
    
    assert results['status'] == 'success'
    assert results['peak_memory_gb'] <= 7.0
    assert results['total_samples'] == 10
    assert results['total_batches'] > 0
    assert results['batch_size_used'] > 0
    assert results['error'] is None

@pytest.mark.integration
def test_stress_test_output_format(sample_manifest):
    """Test that stress test output has correct JSON structure."""
    results = run_stress_test(sample_manifest, max_memory_gb=7.0)
    
    required_fields = [
        'status', 'peak_memory_gb', 'batch_size_used', 
        'total_samples', 'total_batches', 'error', 'timestamp'
    ]
    
    for field in required_fields:
        assert field in results, f"Missing required field: {field}"
    
    assert isinstance(results['status'], str)
    assert isinstance(results['peak_memory_gb'], float)
    assert isinstance(results['batch_size_used'], int)
    assert isinstance(results['total_samples'], int)
    assert isinstance(results['total_batches'], int)
    assert results['error'] is None or isinstance(results['error'], str)
    assert isinstance(results['timestamp'], str)