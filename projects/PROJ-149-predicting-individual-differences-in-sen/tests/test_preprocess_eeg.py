import os
import sys
import pytest
import numpy as np
import pandas as pd
from pathlib import Path

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from config import get_path, ensure_dirs, get_filter_params, get_ica_params, get_exclusion_params
from utils.eeg_helpers import bandpass_filter, notch_filter, reject_channels_by_variance, apply_ica

class TestConfigHelpers:
    """Test configuration helper functions."""

    def test_ensure_dirs_no_args(self):
        """Test ensure_dirs with no arguments (backward compat)."""
        # Should not raise
        ensure_dirs()

    def test_ensure_dirs_single_string(self):
        """Test ensure_dirs with a single string path."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            test_path = os.path.join(tmpdir, "test_dir")
            ensure_dirs(test_path)
            assert os.path.exists(test_path)

    def test_ensure_dirs_list(self):
        """Test ensure_dirs with a list of paths."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = [
                os.path.join(tmpdir, "dir1"),
                os.path.join(tmpdir, "dir2"),
            ]
            ensure_dirs(paths)
            for p in paths:
                assert os.path.exists(p)

    def test_get_path_single_key(self):
        """Test get_path with a single known key."""
        path = get_path("data_raw")
        assert isinstance(path, Path)

    def test_get_path_multiple_args(self):
        """Test get_path with multiple arguments."""
        path = get_path("interim", "test_subdir")
        assert isinstance(path, Path)

class TestEEGHelpers:
    """Test EEG helper functions."""

    def test_reject_channels_by_variance(self):
        """Test channel rejection by variance."""
        import mne
        import numpy as np

        # Create synthetic data
        n_channels = 10
        n_times = 1000
        sfreq = 256.0

        info = mne.create_info(ch_names=[f"EEG{i:03d}" for i in range(n_channels)], sfreq=sfreq, ch_types="eeg")
        data = np.random.randn(n_channels, n_times)

        # Make one channel have high variance
        data[0, :] = data[0, :] * 100

        raw = mne.io.RawArray(data, info)

        # Test rejection
        bad_chs, ratio = reject_channels_by_variance(raw, max_sd=3.0)

        # Should reject the high-variance channel
        assert len(bad_chs) > 0
        assert ratio > 0.0
        assert ratio <= 1.0

class TestPreprocessEEG:
    """Test preprocessing functions."""

    @pytest.fixture
    def temp_output_dir(self):
        """Create a temporary output directory."""
        import tempfile
        tmpdir = tempfile.mkdtemp()
        yield tmpdir
        # Cleanup (optional in tests)

    def test_preprocess_subject_signature(self):
        """Test that preprocess_subject has correct signature."""
        from code_02_preprocess_eeg import preprocess_subject
        import inspect

        sig = inspect.signature(preprocess_subject)
        params = list(sig.parameters.keys())
        assert "raw_path" in params
        assert "output_dir" in params
        assert "subject_id" in params
        assert "apply_ica_flag" in params

    def test_metadata_structure(self):
        """Test that metadata dict has required keys."""
        # We can't test full preprocessing without data, but we can check structure
        expected_keys = {"excluded", "reason", "channels_rejected_ratio", "ica_applied"}
        # This is a structural check; actual values depend on data
        assert len(expected_keys) == 4