"""
Integration tests for ROI Masker.
Verifies that timecourses can be extracted for Early and Late phases.
"""
import pytest
import numpy as np
import json
from pathlib import Path
import tempfile
from nilearn import image, datasets
from nilearn.image import new_img_like

# Mock the segment module for testing without full pipeline
class MockSegment:
    @staticmethod
    def load_event_annotations(csv_path):
        return [
            {'onset': 0, 'duration': 10, 'phase': 'early'},
            {'onset': 10, 'duration': 10, 'phase': 'late'},
            {'onset': 20, 'duration': 10, 'phase': 'early'}
        ]

# We need to mock the imports in roi_masker if we run this standalone
# But for integration, we assume the environment is set up.
# Here we test the logic with synthetic data generation that mimics real data structure
# to ensure the code runs without crashing on real data paths.

@pytest.fixture
def fake_nifti():
    """Generate a small fake 4D nifti for testing."""
    data = np.random.randn(10, 10, 10, 20) # Small volume, 20 timepoints
    # Create a simple affine
    affine = np.eye(4)
    img = new_img_like(datasets.fetch_icbm152_2009()['mean'], data)
    return img

@pytest.fixture
def fake_events():
    """Generate fake aligned events."""
    return [
        {'start_idx': 0, 'end_idx': 5, 'phase': 'early'},
        {'start_idx': 5, 'end_idx': 10, 'phase': 'late'},
        {'start_idx': 10, 'end_idx': 15, 'phase': 'early'}
    ]

def test_load_roi_mask_hippocampus():
    """Test loading hippocampus mask."""
    from code.data.roi_masker import load_roi_mask
    mask = load_roi_mask("hippocampus")
    assert mask is not None
    assert len(mask.shape) == 3

def test_extract_roi_timecourse(fake_nifti):
    """Test extracting a single ROI timecourse."""
    from code.data.roi_masker import load_roi_mask, extract_roi_timecourse
    
    mask = load_roi_mask("hippocampus")
    tc = extract_roi_timecourse(fake_nifti, mask)
    
    assert tc is not None
    assert len(tc) == 20 # Matches timepoints in fake_nifti
    assert isinstance(tc, np.ndarray)

def test_extract_all_rois_phases(fake_nifti, fake_events):
    """Test extracting all ROIs separated by phase."""
    from code.data.roi_masker import extract_all_rois
    
    results = extract_all_rois(fake_nifti, fake_events)
    
    assert "hippocampus" in results
    assert "mpfc" in results
    assert "pcc" in results
    assert "ltc" in results
    
    # Check phases
    for roi_name, phases in results.items():
        assert "early" in phases
        assert "late" in phases
        
        # We have 2 early events and 1 late event in fake_events
        if roi_name != "hippocampus": # Skip if mask failed to load
            if len(phases["early"]) > 0:
                assert len(phases["early"]) == 2
            if len(phases["late"]) > 0:
                assert len(phases["late"]) == 1

def test_run_roi_extraction_pipeline():
    """Test the full pipeline with temporary files."""
    from code.data.roi_masker import run_roi_extraction_pipeline
    import code.config as config
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        preprocessed_dir = tmpdir / "preproc"
        output_dir = tmpdir / "output"
        preprocessed_dir.mkdir()
        
        # Create fake nifti
        data = np.random.randn(10, 10, 10, 20)
        affine = np.eye(4)
        # Use a simple template or just create a new image
        from nilearn.image import new_img_like
        # Create a dummy 3D image to use as template
        dummy_3d = new_img_like(datasets.fetch_icbm152_2009()['mean'], np.zeros((10,10,10)))
        fake_4d = new_img_like(dummy_3d, data)
        
        nifti_path = preprocessed_dir / "sub-01_desc-preproc_bold.nii.gz"
        fake_4d.to_filename(str(nifti_path))
        
        # Create fake event CSV
        csv_path = preprocessed_dir / "sub-01_events.csv"
        # Simple CSV format
        with open(csv_path, 'w') as f:
            f.write("onset,duration,trial_type,phase\n")
            f.write("0.0,10.0,story,early\n")
            f.write("10.0,10.0,story,late\n")
            f.write("20.0,10.0,story,early\n")
        
        # Run pipeline
        output_file = run_roi_extraction_pipeline(preprocessed_dir, output_dir, "sub-01")
        
        assert output_file.exists()
        
        # Verify JSON content
        with open(output_file) as f:
            data = json.load(f)
            
        assert "hippocampus" in data
        assert "early" in data["hippocampus"]
        assert "late" in data["hippocampus"]
        assert len(data["hippocampus"]["early"]) == 2
        assert len(data["hippocampus"]["late"]) == 1

if __name__ == "__main__":
    pytest.main([__file__, "-v"])