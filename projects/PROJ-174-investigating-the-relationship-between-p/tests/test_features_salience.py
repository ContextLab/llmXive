"""
Tests for salience computation in features.py (T015b).

These tests verify:
1. Gabor kernel computation
2. Salience computation from images
3. UNFULFILLABLE status when no data available
"""
import os
import sys
import tempfile
import numpy as np
import pandas as pd
from pathlib import Path
import pytest
import cv2

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from preprocessing.features import (
    compute_gabor_kernel,
    compute_target_salience,
    compute_fixation_count,
    compute_search_time,
    extract_features,
    process_dataset_features
)


class TestGaborKernel:
    """Tests for Gabor kernel computation."""
    
    def test_kernel_shape(self):
        """Test that kernel has expected shape."""
        kernel = compute_gabor_kernel(orientation=0.0, scale=1.0)
        assert kernel.shape[0] == kernel.shape[1], "Kernel should be square"
        assert kernel.shape[0] > 0, "Kernel should have non-zero size"
    
    def test_kernel_values(self):
        """Test that kernel has valid values."""
        kernel = compute_gabor_kernel(orientation=0.0, scale=1.0)
        assert not np.all(kernel == 0), "Kernel should not be all zeros"
        assert np.any(kernel != 0), "Kernel should have non-zero values"
    
    def test_orientation_sensitivity(self):
        """Test that different orientations produce different kernels."""
        kernel1 = compute_gabor_kernel(orientation=0.0, scale=1.0)
        kernel2 = compute_gabor_kernel(orientation=np.pi/2, scale=1.0)
        
        # Kernels should be different
        assert not np.allclose(kernel1, kernel2), "Different orientations should produce different kernels"


class TestSalienceComputation:
    """Tests for target salience computation."""
    
    def test_salience_from_valid_image(self):
        """Test salience computation from a valid image."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Create a test image
            image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
            image_path = tmpdir_path / "test.png"
            cv2.imwrite(str(image_path), image)
            
            # Compute salience
            salience = compute_target_salience(image_path)
            
            assert salience is not None, "Salience should be computed"
            assert isinstance(salience, float), "Salience should be a float"
            assert salience >= 0, "Salience should be non-negative"
    
    def test_salience_from_missing_image(self):
        """Test salience computation with missing image."""
        fake_path = Path("/nonexistent/path/image.png")
        salience = compute_target_salience(fake_path)
        
        assert salience is None, "Salience should be None for missing image"
    
    def test_salience_from_corrupted_image(self):
        """Test salience computation with corrupted image."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Create a corrupted image file
            image_path = tmpdir_path / "corrupted.png"
            with open(image_path, 'wb') as f:
                f.write(b"not a valid image")
            
            salience = compute_target_salience(image_path)
            
            assert salience is None, "Salience should be None for corrupted image"


class TestFeatureExtraction:
    """Tests for feature extraction logic."""
    
    def test_extract_with_metadata(self):
        """Test extraction when metadata is available."""
        trial_metadata = {
            'search_time': 2.5,
            'fixation_count': 10,
            'target_salience': 0.75
        }
        
        features = extract_features(
            trial_data=pd.DataFrame(),
            trial_metadata=trial_metadata,
            stimulus_dir=None,
            subject_id='S001',
            trial_id='T001'
        )
        
        assert features['search_time'] == 2.5
        assert features['fixation_count'] == 10.0
        assert features['target_salience'] == 0.75
        assert features['status'] == 'OK'
    
    def test_extract_with_computed_salience(self):
        """Test extraction when salience is computed from image."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Create stimulus directory and image
            stimuli_dir = tmpdir_path / "stimuli"
            stimuli_dir.mkdir()
            
            image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
            image_path = stimuli_dir / "S001_T001.png"
            cv2.imwrite(str(image_path), image)
            
            # Metadata without target_salience
            trial_metadata = {
                'search_time': 2.5,
                'fixation_count': 10
            }
            
            features = extract_features(
                trial_data=pd.DataFrame(),
                trial_metadata=trial_metadata,
                stimulus_dir=stimuli_dir,
                subject_id='S001',
                trial_id='T001'
            )
            
            assert features['search_time'] == 2.5
            assert features['fixation_count'] == 10.0
            assert features['target_salience'] is not None, "Salience should be computed"
            assert features['status'] == 'OK'
    
    def test_extract_unfulfillable(self):
        """Test extraction when neither metadata nor image is available."""
        trial_metadata = {}  # Empty metadata
        
        features = extract_features(
            trial_data=pd.DataFrame(),
            trial_metadata=trial_metadata,
            stimulus_dir=None,  # No stimulus directory
            subject_id='S001',
            trial_id='T001'
        )
        
        assert features['search_time'] is None
        assert features['fixation_count'] is None
        assert features['target_salience'] is None
        assert features['status'] == 'UNFULFILLABLE'
    
    def test_extract_partial_metadata(self):
        """Test extraction with partial metadata (some fields missing)."""
        trial_metadata = {
            'search_time': 2.5
            # fixation_count missing
        }
        
        features = extract_features(
            trial_data=pd.DataFrame(),
            trial_metadata=trial_metadata,
            stimulus_dir=None,
            subject_id='S001',
            trial_id='T001'
        )
        
        assert features['search_time'] == 2.5
        assert features['fixation_count'] is None
        assert features['target_salience'] is None
        assert features['status'] == 'UNFULFILLABLE'  # No salience source


class TestProcessDatasetFeatures:
    """Tests for dataset-level feature processing."""
    
    def test_save_features_to_csv(self):
        """Test saving features to CSV."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "features.csv"
            
            features_list = [
                {
                    'subject_id': 'S001',
                    'trial_id': 'T001',
                    'search_time': 2.5,
                    'fixation_count': 10.0,
                    'target_salience': 0.75,
                    'status': 'OK'
                },
                {
                    'subject_id': 'S001',
                    'trial_id': 'T002',
                    'search_time': None,
                    'fixation_count': None,
                    'target_salience': None,
                    'status': 'UNFULFILLABLE'
                }
            ]
            
            process_dataset_features(features_list, output_path)
            
            assert output_path.exists(), "Output file should exist"
            
            df = pd.read_csv(output_path)
            assert len(df) == 2, "Should have 2 rows"
            assert 'subject_id' in df.columns
            assert 'trial_id' in df.columns
            assert 'search_time' in df.columns
            assert 'fixation_count' in df.columns
            assert 'target_salience' in df.columns
            assert 'status' in df.columns
    
    def test_empty_features_list(self):
        """Test processing empty feature list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "features.csv"
            
            # Should not raise an error
            process_dataset_features([], output_path)
            
            # File should not be created or be empty
            # (depending on implementation choice)


class TestMetadataExtractors:
    """Tests for individual metadata extraction functions."""
    
    def test_compute_search_time_present(self):
        """Test search_time extraction when present."""
        metadata = {'search_time': 3.14}
        result = compute_search_time(metadata)
        assert result == 3.14
    
    def test_compute_search_time_missing(self):
        """Test search_time extraction when missing."""
        metadata = {}
        result = compute_search_time(metadata)
        assert result is None
    
    def test_compute_fixation_count_present(self):
        """Test fixation_count extraction when present."""
        metadata = {'fixation_count': 15}
        result = compute_fixation_count(metadata)
        assert result == 15.0
    
    def test_compute_fixation_count_missing(self):
        """Test fixation_count extraction when missing."""
        metadata = {}
        result = compute_fixation_count(metadata)
        assert result is None