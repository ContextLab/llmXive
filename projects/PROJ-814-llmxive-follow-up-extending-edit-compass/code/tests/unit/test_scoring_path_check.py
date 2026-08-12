import pytest
import os
import tempfile
import json
from pathlib import Path
from src.services.scoring import process_fidelity_batch, load_filtered_instances
from unittest.mock import patch, MagicMock

@pytest.fixture
def temp_instances():
    """Create temporary instance data with valid and invalid paths."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create valid images
        valid_source = os.path.join(tmpdir, "valid_source.png")
        valid_edited = os.path.join(tmpdir, "valid_edited.png")
        
        # Create dummy images using PIL
        from PIL import Image
        img = Image.new('RGB', (100, 100), color='red')
        img.save(valid_source)
        img.save(valid_edited)

        instances = [
            {
                'id': 'valid_1',
                'source_image_path': valid_source,
                'edited_image_path': valid_edited,
                'instruction': 'Change color to blue',
                'category': 'World Knowledge Reasoning'
            },
            {
                'id': 'missing_source',
                'source_image_path': '/nonexistent/path.png',
                'edited_image_path': valid_edited,
                'instruction': 'Change color',
                'category': 'World Knowledge Reasoning'
            },
            {
                'id': 'missing_edited',
                'source_image_path': valid_source,
                'edited_image_path': '/nonexistent/path2.png',
                'instruction': 'Change color',
                'category': 'World Knowledge Reasoning'
            },
            {
                'id': 'missing_both',
                'source_image_path': '',
                'edited_image_path': '',
                'instruction': 'Change color',
                'category': 'World Knowledge Reasoning'
            }
        ]
        yield instances

def test_skips_missing_source_image(temp_instances, caplog):
    """Test that instances with missing source images are skipped and logged."""
    with caplog.at_level("WARNING"):
        results = process_fidelity_batch(temp_instances, batch_size=10)
    
    # Should only have the valid instance
    assert len(results) == 1
    assert results[0]['instance_id'] == 'valid_1'
    
    # Check warning logs
    assert any("missing_source" in record.message for record in caplog.records)
    assert any("missing_both" in record.message for record in caplog.records)

def test_skips_missing_edited_image(temp_instances, caplog):
    """Test that instances with missing edited images are skipped and logged."""
    with caplog.at_level("WARNING"):
        results = process_fidelity_batch(temp_instances, batch_size=10)
    
    # Should only have the valid instance
    assert len(results) == 1
    assert results[0]['instance_id'] == 'valid_1'
    
    assert any("missing_edited" in record.message for record in caplog.records)

def test_processes_valid_image_pair(temp_instances):
    """Test that valid image pairs are processed correctly."""
    results = process_fidelity_batch(temp_instances, batch_size=10)
    
    assert len(results) == 1
    assert results[0]['instance_id'] == 'valid_1'
    assert 'ssim' in results[0]
    assert 'lpips' in results[0]
    assert 'fidelity_score' in results[0]
    assert 0 <= results[0]['ssim'] <= 1
    assert 0 <= results[0]['lpips'] <= 2  # LPIPS can be > 1 but usually < 1 for similar images
    assert 0 <= results[0]['fidelity_score'] <= 1