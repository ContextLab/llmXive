import pytest
import pandas as pd
import numpy as np
import os
import tempfile
from pathlib import Path
from PIL import Image
import cv2

from stimuli.process import categorize_complexity, process_stimuli_batch

@pytest.fixture
def sample_image_dir(tmp_path):
    """Create a temporary directory with sample images."""
    # Create a solid color image (low complexity)
    solid_img = np.zeros((100, 100, 3), dtype=np.uint8)
    solid_img[:] = [128, 128, 128]
    solid_path = tmp_path / "solid_gray.png"
    cv2.imwrite(str(solid_path), solid_img)

    # Create a high-frequency noise image (high complexity)
    noise_img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
    noise_path = tmp_path / "noise.png"
    cv2.imwrite(str(noise_path), noise_img)

    # Create a simple gradient image (medium complexity)
    gradient_img = np.zeros((100, 100, 3), dtype=np.uint8)
    for i in range(100):
        gradient_img[i, :] = int(i * 2.55)
    gradient_path = tmp_path / "gradient.png"
    cv2.imwrite(str(gradient_path), gradient_img)

    return tmp_path

def test_categorize_complexity_basic():
    """Test basic categorization functionality."""
    df = pd.DataFrame({
        'filename': ['img1.png', 'img2.png', 'img3.png'],
        'edge_density': [0.1, 0.5, 0.9],
        'entropy': [0.2, 0.6, 0.95],
        'fractal_dim': [1.1, 1.5, 1.9]
    })

    result = categorize_complexity(df)

    assert 'complexity_category' in result.columns
    assert result['complexity_category'].nunique() == 3
    assert set(result['complexity_category'].unique()) == {'Low', 'Medium', 'High'}

def test_categorize_complexity_empty():
    """Test categorization on empty DataFrame."""
    df = pd.DataFrame(columns=['filename', 'edge_density', 'entropy', 'fractal_dim'])
    result = categorize_complexity(df)
    assert result.empty
    assert 'complexity_category' not in result.columns

def test_categorize_complexity_missing_columns():
    """Test categorization fails with missing columns."""
    df = pd.DataFrame({
        'filename': ['img1.png'],
        'edge_density': [0.5]
    })
    with pytest.raises(ValueError):
        categorize_complexity(df)

def test_categorize_complexity_identical_values():
    """Test categorization when all values are identical."""
    df = pd.DataFrame({
        'filename': ['img1.png', 'img2.png', 'img3.png'],
        'edge_density': [0.5, 0.5, 0.5],
        'entropy': [0.5, 0.5, 0.5],
        'fractal_dim': [0.5, 0.5, 0.5]
    })
    result = categorize_complexity(df)
    # Should handle gracefully, likely all in one category or fallback
    assert 'complexity_category' in result.columns

def test_process_stimuli_batch_integration(sample_image_dir, tmp_path):
    """Test full batch processing pipeline."""
    output_path = tmp_path / "test_complexity_scores.csv"
    
    df = process_stimuli_batch(str(sample_image_dir), str(output_path))
    
    # Verify output file exists
    assert output_path.exists()
    
    # Verify DataFrame schema
    expected_columns = ['filename', 'edge_density', 'entropy', 'fractal_dim', 'complexity_category']
    assert list(df.columns) == expected_columns
    
    # Verify we processed all images
    assert len(df) == 3
    
    # Verify categories are assigned
    assert df['complexity_category'].nunique() >= 1  # At least one category
    
    # Verify noise image has higher scores than solid image
    noise_row = df[df['filename'] == 'noise.png'].iloc[0]
    solid_row = df[df['filename'] == 'solid_gray.png'].iloc[0]
    
    assert noise_row['edge_density'] > solid_row['edge_density']
    assert noise_row['entropy'] > solid_row['entropy']

def test_process_stimuli_batch_empty_dir(tmp_path):
    """Test processing when directory is empty."""
    output_path = tmp_path / "empty_scores.csv"
    df = process_stimuli_batch(str(tmp_path), str(output_path))
    
    assert df.empty
    assert output_path.exists()
    # Verify file has correct headers even if empty
    with open(output_path, 'r') as f:
        header = f.readline().strip()
        assert 'filename' in header
        assert 'edge_density' in header
        assert 'entropy' in header
        assert 'fractal_dim' in header
        assert 'complexity_category' in header

def test_process_stimuli_batch_nonexistent_dir():
    """Test processing when directory does not exist."""
    with pytest.raises(FileNotFoundError):
        process_stimuli_batch("/nonexistent/path", "/tmp/output.csv")
