"""
Unit tests for connectivity matrix construction (T011).
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

# Import the module under test
from code.centrality.connectivity import (
    compute_correlation_matrix,
    extract_roi_time_series,
    load_atlas_mask,
    process_participant_connectivity,
    run_connectivity_pipeline
)


class TestComputeCorrelationMatrix:
    """Tests for compute_correlation_matrix function."""

    def test_correlation_identity(self):
        """Test that correlation of a signal with itself is 1."""
        ts = np.random.rand(100, 1)
        corr = compute_correlation_matrix(ts)
        assert np.isclose(corr[0, 0], 1.0)

    def test_correlation_perfect_negative(self):
        """Test perfect negative correlation."""
        ts = np.random.rand(100, 2)
        ts[:, 1] = -ts[:, 0]  # Perfect negative correlation
        corr = compute_correlation_matrix(ts)
        assert np.isclose(corr[0, 1], -1.0)

    def test_correlation_shape(self):
        """Test output shape matches input number of ROIs."""
        n_timepoints = 100
        n_rois = 5
        ts = np.random.rand(n_timepoints, n_rois)
        corr = compute_correlation_matrix(ts)
        assert corr.shape == (n_rois, n_rois)

    def test_correlation_nan_handling(self):
        """Test that NaNs in input are handled gracefully."""
        ts = np.random.rand(100, 2)
        ts[0, 0] = np.nan
        corr = compute_correlation_matrix(ts)
        # The function should handle NaNs (either by filling or returning NaNs)
        # Our implementation fills with 0, so no NaNs should remain in the result
        assert not np.any(np.isnan(corr))

    def test_insufficient_timepoints(self):
        """Test that < 2 timepoints raises an error."""
        ts = np.random.rand(1, 2)
        with pytest.raises(ValueError):
            compute_correlation_matrix(ts)


class TestExtractROITimeSeries:
    """Tests for extract_roi_time_series function."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create mock images
        self.atlas_data = np.zeros((10, 10, 10), dtype=np.int32)
        self.atlas_data[0:3, 0:3, 0:3] = 1
        self.atlas_data[3:6, 3:6, 3:6] = 2
        self.atlas_data[6:9, 6:9, 6:9] = 3

        self.func_data = np.random.rand(10, 10, 10, 20)  # 20 timepoints

    def test_extract_all_rois(self):
        """Test extraction of all non-zero ROIs."""
        atlas_img = MagicMock()
        atlas_img.get_fdata.return_value = self.atlas_data
        
        func_img = MagicMock()
        func_img.get_fdata.return_value = self.func_data

        # Mock NiftiLabelsMasker to return expected shape
        with patch('code.centrality.connectivity.NiftiLabelsMasker') as MockMasker:
            mock_instance = MockMasker.return_value
            mock_instance.fit_transform.return_value = np.random.rand(20, 3) # 20 timepoints, 3 ROIs
            
            ts = extract_roi_time_series(func_img, atlas_img)
            assert ts.shape == (20, 3)

    def test_extract_specific_rois(self):
        """Test extraction of specific ROIs."""
        atlas_img = MagicMock()
        atlas_img.get_fdata.return_value = self.atlas_data

        func_img = MagicMock()
        func_img.get_fdata.return_value = self.func_data

        with patch('code.centrality.connectivity.NiftiLabelsMasker') as MockMasker:
            mock_instance = MockMasker.return_value
            # Simulate returning all 3 ROIs first, then we filter
            mock_instance.fit_transform.return_value = np.random.rand(20, 3)
            
            ts = extract_roi_time_series(func_img, atlas_img, rois=[1, 3])
            # Should return only 2 ROIs
            assert ts.shape == (20, 2)


class TestLoadAtlasMask:
    """Tests for load_atlas_mask function."""

    def test_file_not_found(self):
        """Test that FileNotFoundError is raised for missing file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_path = Path(tmpdir) / "nonexistent.nii"
            with pytest.raises(FileNotFoundError):
                load_atlas_mask(fake_path)

    def test_load_existing(self, tmp_path):
        """Test loading an existing file."""
        # Create a fake NIfTI file
        from nibabel import Nifti1Image
        data = np.zeros((5, 5, 5), dtype=np.int32)
        img = Nifti1Image(data, np.eye(4))
        fake_path = tmp_path / "atlas.nii"
        img.to_filename(str(fake_path))

        loaded = load_atlas_mask(fake_path)
        assert loaded is not None


class TestProcessParticipantConnectivity:
    """Tests for process_participant_connectivity function."""

    def setup_method(self):
        """Set up test fixtures."""
        self.tmpdir = tempfile.TemporaryDirectory()
        self.output_dir = Path(self.tmpdir.name)
        
        # Create fake images
        from nibabel import Nifti1Image
        
        # Atlas
        atlas_data = np.zeros((10, 10, 10), dtype=np.int32)
        atlas_data[0:3, 0:3, 0:3] = 1
        atlas_data[3:6, 3:6, 3:6] = 2
        self.atlas_img = Nifti1Image(atlas_data, np.eye(4))
        self.atlas_path = self.output_dir / "atlas.nii"
        self.atlas_img.to_filename(str(self.atlas_path))

        # Func
        func_data = np.random.rand(10, 10, 10, 20)
        self.func_img = Nifti1Image(func_data, np.eye(4))
        self.func_path = self.output_dir / "preprocessed_test001.nii.gz"
        self.func_img.to_filename(str(self.func_path))

    def teardown_method(self):
        """Clean up temporary files."""
        self.tmpdir.cleanup()

    def test_success(self):
        """Test successful processing."""
        # Mock the extraction and correlation to avoid heavy computation
        with patch('code.centrality.connectivity.extract_roi_time_series') as mock_extract:
            with patch('code.centrality.connectivity.compute_correlation_matrix') as mock_corr:
                mock_extract.return_value = np.random.rand(20, 2)
                mock_corr.return_value = np.eye(2)
                
                matrix_path, metadata = process_participant_connectivity(
                    "test001", self.func_path, self.atlas_path, self.output_dir
                )
                
                assert metadata["status"] == "success"
                assert metadata["n_rois"] == 2
                assert matrix_path.exists()

    def test_missing_preprocessed(self):
        """Test error when preprocessed file is missing."""
        with pytest.raises(FileNotFoundError):
            process_participant_connectivity(
                "missing", 
                self.output_dir / "nonexistent.nii", 
                self.atlas_path, 
                self.output_dir
            )


class TestRunConnectivityPipeline:
    """Tests for run_connectivity_pipeline function."""

    def setup_method(self):
        """Set up test fixtures."""
        self.tmpdir = tempfile.TemporaryDirectory()
        self.data_dir = Path(self.tmpdir.name) / "data"
        self.data_dir.mkdir()
        self.output_dir = Path(self.tmpdir.name) / "output"
        self.output_dir.mkdir()

        # Create fake atlas
        from nibabel import Nifti1Image
        atlas_data = np.zeros((10, 10, 10), dtype=np.int32)
        atlas_data[0:3, 0:3, 0:3] = 1
        self.atlas_img = Nifti1Image(atlas_data, np.eye(4))
        self.atlas_path = self.data_dir / "aal_atlas.nii.gz"
        self.atlas_img.to_filename(str(self.atlas_path))

    def teardown_method(self):
        """Clean up."""
        self.tmpdir.cleanup()

    def test_run_pipeline(self):
        """Test running the pipeline for multiple participants."""
        # Create fake preprocessed files
        for i in range(3):
            pid = f"sub_{i:03d}"
            func_data = np.random.rand(10, 10, 10, 20)
            from nibabel import Nifti1Image
            func_img = Nifti1Image(func_data, np.eye(4))
            func_path = self.data_dir / f"preprocessed_{pid}.nii.gz"
            func_img.to_filename(str(func_path))

        # Mock the heavy lifting
        with patch('code.centrality.connectivity.process_participant_connectivity') as mock_proc:
            mock_proc.return_value = (
                self.output_dir / "conn_matrix_sub_000.npy",
                {"participant_id": "sub_000", "status": "success", "n_rois": 1}
            )
            
            results = run_connectivity_pipeline(
                participant_ids=["sub_000", "sub_001", "sub_002"],
                data_dir=self.data_dir,
                output_dir=self.output_dir,
                atlas_path=self.atlas_path
            )
            
            assert len(results) == 3
            assert all(r["status"] == "success" for r in results)

    def test_missing_preprocessed_in_pipeline(self):
        """Test pipeline handles missing files gracefully."""
        # Only create one file
        pid = "sub_000"
        func_data = np.random.rand(10, 10, 10, 20)
        from nibabel import Nifti1Image
        func_img = Nifti1Image(func_data, np.eye(4))
        func_path = self.data_dir / f"preprocessed_{pid}.nii.gz"
        func_img.to_filename(str(func_path))

        results = run_connectivity_pipeline(
            participant_ids=["sub_000", "sub_001"],
            data_dir=self.data_dir,
            output_dir=self.output_dir,
            atlas_path=self.atlas_path
        )

        assert len(results) == 2
        assert results[0]["status"] == "success"
        assert results[1]["status"] == "failed"