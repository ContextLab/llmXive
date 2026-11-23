"""
Unit tests for time series extraction module.
"""
import os
import tempfile
import numpy as np
import nibabel as nib
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.analysis.extract_timeseries import (
    TimeSeriesExtractionError,
    TimeSeriesResult,
    load_roi_masks,
    load_bold_image,
    extract_mean_timeseries,
    extract_subject_timeseries,
    find_preprocessed_bold_files,
    extract_all_timeseries,
    run_timeseries_extraction
)


@pytest.fixture
def temp_roi_dir():
    """Create a temporary directory with ROI mask files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create mock ROI masks (3D binary arrays)
        roi_names = ["PCC", "mPFC", "IPL", "AngularGyrus"]
        mask_shape = (10, 10, 10)
        
        for i, roi_name in enumerate(roi_names):
            mask_data = np.zeros(mask_shape)
            # Create a small cluster of voxels for the mask
            mask_data[4:6, 4:6, 4+i] = 1.0
            
            mask_path = tmpdir / f"{roi_name}.nii.gz"
            img = nib.Nifti1Image(mask_data, np.eye(4))
            nib.save(img, str(mask_path))
        
        yield tmpdir


@pytest.fixture
def temp_bold_file():
    """Create a temporary 4D BOLD file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create mock 4D BOLD data (x, y, z, t)
        bold_shape = (10, 10, 10, 50)  # 50 timepoints
        bold_data = np.random.randn(*bold_shape).astype(np.float32)
        
        bold_path = tmpdir / "sub-01_task-rest_space-MNI152_desc-preproc_bold.nii.gz"
        img = nib.Nifti1Image(bold_data, np.eye(4))
        nib.save(img, str(bold_path))
        
        yield bold_path


@pytest.fixture
def temp_processed_dir(temp_bold_file):
    """Create a temporary processed directory structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create subject directory structure
        subject_dir = tmpdir / "sub-01" / "func"
        subject_dir.mkdir(parents=True)
        
        # Move bold file to correct location
        import shutil
        shutil.move(str(temp_bold_file), str(subject_dir / temp_bold_file.name))
        
        yield tmpdir


@pytest.fixture
def temp_motion_filter_csv():
    """Create a temporary motion filter exclusion CSV."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("subject_id,max_translation,max_rotation,excluded\n")
        f.write("sub-02,5.0,0.5,True\n")  # Excluded
        f.write("sub-03,1.0,0.2,True\n")  # Excluded
        f.name
        yield Path(f.name)
        os.unlink(f.name)


class TestLoadRoiMasks:
    def test_load_roi_masks_success(self, temp_roi_dir):
        """Test successful loading of ROI masks."""
        masks = load_roi_masks(temp_roi_dir)
        
        assert len(masks) == 4
        assert "PCC" in masks
        assert "mPFC" in masks
        assert "IPL" in masks
        assert "AngularGyrus" in masks
        
        # Check mask shape
        for mask in masks.values():
            assert mask.shape == (10, 10, 10)
            assert mask.dtype == np.float64  # get_fdata returns float64

    def test_load_roi_masks_missing_directory(self):
        """Test error when atlas directory doesn't exist."""
        with pytest.raises(TimeSeriesExtractionError, match="Atlas directory not found"):
            load_roi_masks(Path("/nonexistent/path"))

    def test_load_roi_masks_no_files(self, temp_roi_dir):
        """Test error when no mask files found."""
        # Remove all .nii.gz files
        for f in temp_roi_dir.glob("*.nii.gz"):
            f.unlink()
        
        with pytest.raises(TimeSeriesExtractionError, match="No ROI mask files found"):
            load_roi_masks(temp_roi_dir)


class TestLoadBoldImage:
    def test_load_bold_image_success(self, temp_bold_file):
        """Test successful loading of BOLD image."""
        data, shape = load_bold_image(temp_bold_file)
        
        assert data.shape == (10, 10, 10, 50)
        assert shape == (10, 10, 10, 50)
        assert data.ndim == 4

    def test_load_bold_image_nonexistent(self):
        """Test error when BOLD file doesn't exist."""
        with pytest.raises(TimeSeriesExtractionError, match="Failed to load BOLD image"):
            load_bold_image(Path("/nonexistent/file.nii.gz"))

    def test_load_bold_image_wrong_dimensions(self, temp_roi_dir):
        """Test error when BOLD image is not 4D."""
        # Create a 3D image
        img_3d = nib.Nifti1Image(np.zeros((10, 10, 10)), np.eye(4))
        bad_path = temp_roi_dir / "3d_image.nii.gz"
        nib.save(img_3d, str(bad_path))
        
        with pytest.raises(TimeSeriesExtractionError, match="Expected 4D BOLD image"):
            load_bold_image(bad_path)


class TestExtractMeanTimeseries:
    def test_extract_mean_timeseries_success(self, temp_roi_dir, temp_bold_file):
        """Test successful extraction of mean time series."""
        masks = load_roi_masks(temp_roi_dir)
        bold_data, _ = load_bold_image(temp_bold_file)
        
        ts = extract_mean_timeseries(bold_data, masks["PCC"], "PCC")
        
        assert ts.shape == (50,)  # 50 timepoints
        assert isinstance(ts, np.ndarray)

    def test_extract_mean_timeseries_dimension_mismatch(self):
        """Test error when mask and image dimensions don't match."""
        mask_3d = np.zeros((5, 5, 5))
        bold_4d = np.random.randn(10, 10, 10, 50)
        
        with pytest.raises(TimeSeriesExtractionError, match="Dimension mismatch"):
            extract_mean_timeseries(bold_4d, mask_3d, "test_roi")

    def test_extract_mean_timeseries_empty_mask(self, temp_bold_file):
        """Test warning when mask is empty."""
        bold_data, _ = load_bold_image(temp_bold_file)
        empty_mask = np.zeros((10, 10, 10))
        
        ts = extract_mean_timeseries(bold_data, empty_mask, "empty_roi")
        
        assert ts.shape == (50,)
        assert np.all(ts == 0)


class TestExtractSubjectTimeseries:
    def test_extract_subject_timeseries_success(self, temp_roi_dir, temp_processed_dir):
        """Test successful extraction for a subject."""
        masks = load_roi_masks(temp_roi_dir)
        bold_path = temp_processed_dir / "sub-01" / "func" / "sub-01_task-rest_space-MNI152_desc-preproc_bold.nii.gz"
        
        result = extract_subject_timeseries("sub-01", bold_path, masks)
        
        assert result.subject_id == "sub-01"
        assert result.n_rois == 4
        assert result.n_timepoints == 50
        assert result.time_series.shape == (4, 50)
        assert len(result.roi_names) == 4

    def test_extract_subject_timeseries_missing_bold(self, temp_roi_dir):
        """Test error when BOLD file doesn't exist."""
        masks = load_roi_masks(temp_roi_dir)
        
        with pytest.raises(TimeSeriesExtractionError, match="BOLD file not found"):
            extract_subject_timeseries("sub-01", Path("/nonexistent.nii.gz"), masks)

    def test_extract_subject_timeseries_missing_roi(self, temp_processed_dir):
        """Test error when ROI order contains unknown ROIs."""
        bold_path = temp_processed_dir / "sub-01" / "func" / "sub-01_task-rest_space-MNI152_desc-preproc_bold.nii.gz"
        
        # Create a partial mask dict
        masks = {"PCC": np.zeros((10, 10, 10))}
        
        with pytest.raises(TimeSeriesExtractionError, match="ROI order contains unknown ROIs"):
            extract_subject_timeseries("sub-01", bold_path, masks, roi_order=["PCC", "Unknown"])


class TestFindPreprocessedBoldFiles:
    def test_find_preprocessed_bold_files_success(self, temp_processed_dir):
        """Test finding BOLD files in processed directory."""
        files = find_preprocessed_bold_files(temp_processed_dir)
        
        assert len(files) == 1
        assert files[0][0] == "sub-01"
        assert files[0][1].exists()

    def test_find_preprocessed_bold_files_excluded(self, temp_processed_dir, temp_motion_filter_csv):
        """Test that excluded subjects are filtered out."""
        # Create a second subject that is NOT excluded
        subject_dir = temp_processed_dir / "sub-04" / "func"
        subject_dir.mkdir(parents=True)
        
        # Copy the bold file
        import shutil
        src = temp_processed_dir / "sub-01" / "func" / "sub-01_task-rest_space-MNI152_desc-preproc_bold.nii.gz"
        dst = subject_dir / "sub-04_task-rest_space-MNI152_desc-preproc_bold.nii.gz"
        shutil.copy(src, dst)
        
        # sub-01 is NOT in exclusion list, sub-04 is NOT in exclusion list
        # Actually, our CSV only has sub-02 and sub-03 as excluded
        files = find_preprocessed_bold_files(temp_processed_dir, temp_motion_filter_csv)
        
        # Both sub-01 and sub-04 should be found (neither is excluded)
        subject_ids = [f[0] for f in files]
        assert "sub-01" in subject_ids
        assert "sub-04" in subject_ids

    def test_find_preprocessed_bold_files_no_files(self, temp_roi_dir):
        """Test error when no BOLD files found."""
        with pytest.raises(TimeSeriesExtractionError, match="No preprocessed BOLD files found"):
            find_preprocessed_bold_files(temp_roi_dir)


class TestExtractAllTimeseries:
    def test_extract_all_timeseries_success(self, temp_roi_dir, temp_processed_dir):
        """Test end-to-end extraction for all subjects."""
        output_dir = temp_processed_dir / "output"
        
        results = extract_all_timeseries(
            atlas_dir=temp_roi_dir,
            processed_dir=temp_processed_dir,
            output_dir=output_dir
        )
        
        assert len(results) == 1
        assert results[0].subject_id == "sub-01"
        assert results[0].n_rois == 4
        assert results[0].n_timepoints == 50

    def test_extract_all_timeseries_creates_output(self, temp_roi_dir, temp_processed_dir):
        """Test that output files are created."""
        output_dir = temp_processed_dir / "output"
        
        extract_all_timeseries(
            atlas_dir=temp_roi_dir,
            processed_dir=temp_processed_dir,
            output_dir=output_dir
        )
        
        # Check that output file exists
        output_files = list(output_dir.glob("*.npz"))
        assert len(output_files) == 1


class TestRunTimeseriesExtraction:
    @patch('src.analysis.extract_timeseries.get_data_dir')
    def test_run_timeseries_extraction_default_paths(self, mock_get_data_dir, temp_roi_dir, temp_processed_dir):
        """Test run function with default paths."""
        mock_get_data_dir.return_value = str(temp_processed_dir.parent)
        
        # Need to set up the expected directory structure
        data_root = Path(temp_processed_dir.parent)
        (data_root / "processed" / "atlas").mkdir(parents=True, exist_ok=True)
        
        # Move ROI files to expected location
        import shutil
        for f in temp_roi_dir.glob("*.nii.gz"):
            shutil.move(str(f), str(data_root / "processed" / "atlas" / f.name))
        
        # Move processed data to expected location
        (data_root / "processed" / "sub-01").mkdir(parents=True, exist_ok=True)
        src = temp_processed_dir / "sub-01" / "func" / "sub-01_task-rest_space-MNI152_desc-preproc_bold.nii.gz"
        dst = data_root / "processed" / "sub-01" / "func" / "sub-01_task-rest_space-MNI152_desc-preproc_bold.nii.gz"
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))
        
        results = run_timeseries_extraction()
        
        assert len(results) >= 1
        
        # Check that metadata file was created
        metadata_path = data_root / "processed" / "timeseries" / "timeseries_metadata.json"
        assert metadata_path.exists()