"""Unit tests for code/data_loader.py (T001).

Covers: missing Inclusion/Exclusion markers trigger error 101897695
(FR-010), corrupt downloads raise, and exponential backoff fires
exactly 3 times before DataUnavailableError (FR-013).
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data_loader import (  # noqa: E402
    BACKOFF_DELAYS,
    DataUnavailableError,
    ParadigmVerificationError,
    ERROR_PARADIGM_MISSING_MARKERS,
    compute_sha256,
    fetch_with_backoff,
    verify_nifti_integrity,
    verify_paradigm,
)


class TestParadigmVerification:
    def test_both_markers_present_passes(self):
        result = verify_paradigm(["Inclusion", "Exclusion", "Inclusion"])
        assert result["status"] == "verified"

    def test_missing_exclusion_triggers_101897695(self):
        with pytest.raises(ParadigmVerificationError) as exc:
            verify_paradigm(["Inclusion", "Inclusion", "Rest"])
        assert exc.value.code == 101897695
        assert str(ERROR_PARADIGM_MISSING_MARKERS) in str(exc.value) or \
            "101897695" in str(exc.value)

    def test_missing_inclusion_triggers_101897695(self):
        with pytest.raises(ParadigmVerificationError) as exc:
            verify_paradigm(["Exclusion"])
        assert exc.value.code == 101897695

    def test_no_markers_triggers_101897695(self):
        with pytest.raises(ParadigmVerificationError):
            verify_paradigm([])

    def test_case_insensitive_matching(self):
        # marker detection is case-insensitive on trial_type values
        verify_paradigm(["inclusion", "EXCLUSION"])


class TestBackoff:
    def test_backoff_fires_exactly_three_times(self):
        calls = {"n": 0}
        sleeps = []

        def failing():
            calls["n"] += 1
            raise ConnectionError("network down")

        with pytest.raises(DataUnavailableError):
            fetch_with_backoff(failing, sleep=sleeps.append)

        assert calls["n"] == 3  # exactly 3 attempts
        assert sleeps == [1.0, 2.0]  # sleeps between the 3 attempts
        assert list(BACKOFF_DELAYS) == [1.0, 2.0, 4.0]

    def test_backoff_succeeds_on_retry(self):
        state = {"n": 0}

        def flaky():
            state["n"] += 1
            if state["n"] < 3:
                raise ConnectionError("transient")
            return "ok"

        assert fetch_with_backoff(flaky, sleep=lambda s: None) == "ok"
        assert state["n"] == 3

    def test_no_sleep_after_success(self):
        sleeps = []
        assert fetch_with_backoff(lambda: 42, sleep=sleeps.append) == 42
        assert sleeps == []

    def test_final_failure_raises_data_unavailable(self):
        with pytest.raises(DataUnavailableError) as exc:
            fetch_with_backoff(lambda: (_ for _ in ()).throw(RuntimeError("x")),
                               sleep=lambda s: None)
        assert "ERR_DATA_UNAVAILABLE" in str(exc.value)


class TestIntegrity:
    def test_corrupt_download_raises(self, tmp_path):
        bad = tmp_path / "bad.nii.gz"
        bad.write_bytes(b"this is definitely not a nifti file")
        with pytest.raises(DataUnavailableError):
            verify_nifti_integrity(bad)

    def test_empty_download_raises(self, tmp_path):
        empty = tmp_path / "empty.nii.gz"
        empty.write_bytes(b"")
        with pytest.raises(DataUnavailableError):
            verify_nifti_integrity(empty)

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(DataUnavailableError):
            verify_nifti_integrity(tmp_path / "nope.nii.gz")

    def test_valid_nifti_passes(self, tmp_path):
        import nibabel as nib
        import numpy as np
        img = nib.Nifti1Image(np.zeros((4, 4, 4), dtype=np.float32), np.eye(4))
        good = tmp_path / "good.nii.gz"
        nib.save(img, good)
        verify_nifti_integrity(good)  # should not raise


class TestChecksums:
    def test_sha256_matches_known_value(self, tmp_path):
        f = tmp_path / "f.bin"
        f.write_bytes(b"hello")
        import hashlib
        assert compute_sha256(f) == hashlib.sha256(b"hello").hexdigest()

    def test_sha256_streams_large_file(self, tmp_path):
        f = tmp_path / "big.bin"
        f.write_bytes(b"x" * (5 * 1024 * 1024))
        import hashlib
        assert compute_sha256(f) == hashlib.sha256(b"x" * (5 * 1024 * 1024)).hexdigest()
