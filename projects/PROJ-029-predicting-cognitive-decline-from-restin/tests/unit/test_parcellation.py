"""
Unit tests for parcellation and atlas utilities.

TDD Rule: This file must exist and FAIL before T018 is implemented.
"""
import pytest
import numpy as np
import nibabel as nib
from pathlib import Path
import tempfile
import os

# Import from project
from utils.atlas import load_aal_atlas_mask, validate_atlas_shape, create_minimal_atlas
from nilearn.datasets import fetch_atlas_aal
from nilearn.image import new_img_like
from nilearn.maskers import NiftiLabelsMasker


class TestAtlasUtils:
    """Tests for atlas utility functions."""

    def test_validate_atlas_shape_valid(self):
        """Test validation with a valid dummy atlas."""
        with tempfile.TemporaryDirectory() as tmpdir:
            atlas_path = Path(tmpdir) / "test_atlas.nii.gz"
            # Create a valid dummy atlas
            create_minimal_atlas(atlas_path, shape=(10, 10, 10), n_regions=5)
            
            assert validate_atlas_shape(atlas_path) is True

    def test_validate_atlas_shape_missing(self):
        """Test validation with a missing file."""
        assert validate_atlas_shape(Path("/nonexistent/file.nii.gz")) is False

    def test_validate_atlas_shape_empty(self):
        """Test validation with an empty (all zeros) atlas."""
        with tempfile.TemporaryDirectory() as tmpdir:
            atlas_path = Path(tmpdir) / "empty_atlas.nii.gz"
            data = np.zeros((10, 10, 10), dtype=np.int16)
            img = nib.Nifti1Image(data, np.eye(4))
            nib.save(img, str(atlas_path))
            
            assert validate_atlas_shape(atlas_path) is False

    def test_load_aal_atlas_mask(self):
        """Test loading an atlas mask."""
        with tempfile.TemporaryDirectory() as tmpdir:
            atlas_path = Path(tmpdir) / "test_atlas.nii.gz"
            create_minimal_atlas(atlas_path, shape=(10, 10, 10), n_regions=5)
            
            data = load_aal_atlas_mask(atlas_path)
            
            assert isinstance(data, np.ndarray)
            assert data.shape == (10, 10, 10)
            assert np.max(data) == 5
            assert np.min(data) == 0

    def test_create_minimal_atlas(self):
        """Test creating a minimal atlas."""
        with tempfile.TemporaryDirectory() as tmpdir:
            atlas_path = Path(tmpdir) / "created_atlas.nii.gz"
            result_path = create_minimal_atlas(atlas_path, shape=(10, 10, 10), n_regions=5)
            
            assert result_path.exists()
            assert result_path == atlas_path
            
            # Verify content
            data = load_aal_atlas_mask(atlas_path)
            assert np.max(data) == 5


class TestParcellationAAL:
    """
    Unit test for AAL atlas parcellation.
    
    Implementation: Create test function `test_parcellation_applies_aal` that 
    loads a dummy BIDS subject, applies the AAL atlas via `nilearn`, and 
    asserts the output shape is (90, 90).
    
    TDD Rule: This file must exist and FAIL before T018 is implemented.
    """

    def test_parcellation_applies_aal(self):
        """
        Test that AAL atlas parcellation produces a 90x90 connectivity matrix.
        
        Steps:
        1. Fetch the real AAL atlas using nilearn (real source).
        2. Create a dummy 4D fMRI image (simulated time series) that matches 
           the atlas space (or resample to it).
        3. Apply the NiftiLabelsMasker to extract time series and compute 
           the correlation matrix.
        4. Assert the output shape is (90, 90).
        """
        # 1. Fetch real AAL atlas
        # This downloads the real atlas from the nilearn data repository.
        # It will fail loudly if the network is down, satisfying the "real data" constraint.
        try:
            atlas_data = fetch_atlas_aal()
        except Exception as e:
            pytest.fail(f"Failed to fetch real AAL atlas from nilearn: {e}")

        atlas_img = atlas_data.maps
        labels = atlas_data.labels

        # The AAL atlas typically has 90 ROIs (excluding background).
        # We expect the correlation matrix to be (90, 90).
        expected_shape = (90, 90)
        
        # 2. Create a dummy fMRI image to simulate a subject scan.
        # We create a dummy image in the same space as the atlas for simplicity.
        # In a real pipeline, we would load a real subject's preprocessed fMRI.
        # Here we generate a synthetic time series of random values to test 
        # the *parcellation logic* (masking and correlation calculation).
        # This is a DUMMY INPUT for the test, not the final research data.
        
        # Get the affine and shape of the atlas
        affine = atlas_img.affine
        shape = atlas_img.shape
        
        # Create a dummy 4D image: (x, y, z, time)
        # We use a small number of timepoints (e.g., 10) just to compute correlation.
        n_timepoints = 10
        dummy_data = np.random.randn(shape[0], shape[1], shape[2], n_timepoints)
        dummy_img = nib.Nifti1Image(dummy_data.astype(np.float32), affine)
        
        # 3. Apply the masker
        # NiftiLabelsMasker extracts the mean time series for each label and 
        # computes the correlation matrix.
        masker = NiftiLabelsMasker(
            labels_img=atlas_img,
            standardize=True,
            detrend=False,
            low_pass=None,
            high_pass=None,
            t_r=2.0, # dummy TR
            memory="cached",
            verbose=0
        )
        
        # Fit and transform
        try:
            # This will compute the correlation matrix
            correlation_matrix = masker.fit_transform(dummy_img)
            
            # The output of fit_transform with correlation_matrix=True (default for some setups, 
            # but NiftiLabelsMasker returns time series by default. We need to compute correlation manually 
            # or use the 'connectivity_matrix' attribute if available, or just compute it from time series.
            # Actually, NiftiLabelsMasker returns (n_regions, n_timepoints) by default.
            # We need to compute the correlation matrix from this.
            
            if correlation_matrix.ndim == 2:
                # correlation_matrix shape: (n_regions, n_timepoints)
                # Compute correlation between regions
                # np.corrcoef expects variables in rows
                corr_matrix = np.corrcoef(correlation_matrix)
            else:
                # If it's already a matrix (unlikely for this masker without specific args)
                corr_matrix = correlation_matrix
                
        except Exception as e:
            pytest.fail(f"Failed to apply AAL parcellation: {e}")

        # 4. Assert shape
        # The AAL atlas has 90 regions (excluding background which is label 0).
        # The correlation matrix should be 90x90.
        assert corr_matrix.shape == expected_shape, (
            f"Expected shape {expected_shape} but got {corr_matrix.shape}. "
            f"Atlas labels count: {len(labels)}"
        )
        
        # Additional sanity checks
        assert not np.any(np.isnan(corr_matrix)), "Correlation matrix contains NaN values."
        assert np.allclose(np.diag(corr_matrix), 1.0), "Diagonal of correlation matrix is not 1.0."

    def test_parcellation_with_real_aal_count(self):
        """
        Verify that the fetched AAL atlas indeed has 90 regions (excluding background).
        This ensures our test expectation is grounded in the real data source.
        """
        try:
            atlas_data = fetch_atlas_aal()
        except Exception as e:
            pytest.fail(f"Failed to fetch real AAL atlas: {e}")

        labels = atlas_data.labels
        # AAL v1 typically has 90 regions. The first label is often 'Background' or empty string.
        # We filter out empty or 'Background' labels.
        valid_labels = [l for l in labels if l and l != 'Background']
        
        # The mask typically contains 0 for background and 1..90 for regions.
        # We verify the count matches the expected 90.
        # Note: Some versions of AAL might have 116 or other counts. 
        # The task description specifically asks for (90, 90), so we assume AAL-90.
        # If the fetched atlas is different, we adapt or fail.
        
        # Let's check the unique values in the atlas map (excluding 0)
        atlas_img = atlas_data.maps
        data = atlas_img.get_fdata()
        unique_values = np.unique(data)
        non_zero_values = unique_values[unique_values > 0]
        
        # The number of regions is the number of unique non-zero labels.
        n_regions = len(non_zero_values)
        
        # The task requires (90, 90). If the real atlas is different, we note it.
        # However, for the test to pass as per the task description, we assert 90.
        # If the real dataset is different, this test will fail, indicating a mismatch 
        # between the task spec and the real data.
        # Given the task explicitly says "asserts the output shape is (90, 90)",
        # we proceed with that assertion. If the real AAL is different, the test fails,
        # which is the correct TDD behavior (test fails before implementation).
        
        # To be robust, we check if it's 90. If not, we might need to adjust the task
        # or the atlas version. But for now, we assert 90 as per the task requirement.
        assert n_regions == 90, (
            f"Expected 90 regions in AAL atlas but found {n_regions}. "
            f"Unique values: {non_zero_values}. This test requires AAL-90."
        )