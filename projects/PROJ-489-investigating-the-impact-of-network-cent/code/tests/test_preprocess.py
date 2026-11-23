import json
import os
import tempfile
import numpy as np
import mne
import pytest

from preprocess import (
    apply_bandpass_filter,
    remove_ica_artifacts,
    epoch_by_sleep_stage,
    validate_no_nans,
)

@pytest.fixture(scope="module")
def synthetic_raw():
    """Create a synthetic Raw object containing three sinusoids."""
    sfreq = 200.0  # Hz
    times = np.arange(0, 10, 1 / sfreq)  # 10 s
    # 0.1 Hz (very low), 10 Hz (in band), 100 Hz (above band)
    sig_low = np.sin(2 * np.pi * 0.1 * times)
    sig_mid = np.sin(2 * np.pi * 10 * times)
    sig_high = np.sin(2 * np.pi * 100 * times)
    data = sig_low + sig_mid + sig_high
    data = data[np.newaxis, :]  # single channel
    info = mne.create_info(ch_names=["EEG 001"], sfreq=sfreq, ch_types=["eeg"])
    raw = mne.io.RawArray(data, info)
    return raw

def test_apply_bandpass_filter_passes_mid_frequency(synthetic_raw):
    """The 10 Hz component should remain while 0.1 Hz and 100 Hz are attenuated."""
    raw_filt = apply_bandpass_filter(synthetic_raw, low=0.5, high=45.0)

    # Compute power spectral density of the filtered signal
    psd, freqs = mne.time_frequency.psd_welch(
        raw_filt, fmin=0, fmax=120, n_fft=1024, verbose=False
    )
    psd = psd[0]  # single channel

    # Identify peaks near the target frequencies
    idx_mid = np.argmin(np.abs(freqs - 10))
    idx_low = np.argmin(np.abs(freqs - 0.1))
    idx_high = np.argmin(np.abs(freqs - 100))

    # Expect mid frequency power > low and high frequency power
    assert psd[idx_mid] > psd[idx_low] * 5  # at least 5‑times larger
    assert psd[idx_mid] > psd[idx_high] * 5

def test_remove_ica_artifacts_flags_high_kurtosis():
    """A synthetic component with extreme outliers should be dropped."""
    sfreq = 200.0
    # Create two channels: one clean sinusoid, one with a spike (high kurtosis)
    times = np.arange(0, 5, 1 / sfreq)
    clean = np.sin(2 * np.pi * 10 * times)
    spike = np.copy(clean)
    spike[::sfreq] += 20  # add a large spike once per second
    data = np.vstack([clean, spike])
    info = mne.create_info(ch_names=["EEG 001", "EEG 002"], sfreq=sfreq, ch_types=["eeg", "eeg"])
    raw = mne.io.RawArray(data, info)

    # Use a very low kurtosis threshold to guarantee detection
    cleaned = remove_ica_artifacts(raw, kurtosis_thr=0.1, power_ratio_thr=0.1)

    # The function returns a Raw object; we check that ICA components were excluded
    # by confirming that the number of channels is unchanged but the data variance
    # is reduced (spike removed).
    orig_var = np.var(raw.get_data())
    new_var = np.var(cleaned.get_data())
    assert new_var < orig_var * 0.9  # variance should drop noticeably

def test_epoch_by_sleep_stage_creates_files(tmp_path, monkeypatch):
    """Epoching should write .npz and .json files to the expected locations."""
    sfreq = 200.0
    times = np.arange(0, 60, 1 / sfreq)  # 1 min of data
    data = np.sin(2 * np.pi * 10 * times)[np.newaxis, :]
    info = mne.create_info(ch_names=["EEG 001"], sfreq=sfreq, ch_types=["eeg"])
    raw = mne.io.RawArray(data, info)

    # Create simple annotations: 30 s of “N2”, then 30 s of “REM”
    onsets = [0, 30]
    durations = [30, 30]
    descriptions = ["N2", "REM"]
    annot = mne.Annotations(onsets, durations, descriptions, orig_time=raw.first_samp / sfreq)
    raw.set_annotations(annot)

    # Monkey‑patch paths.data to write into the temporary directory
    def fake_data(*parts):
        return tmp_path.joinpath(*parts)

    monkeypatch.setattr("llmxive_toolkit.paths.data", fake_data)

    epochs, labels = epoch_by_sleep_stage(raw, annot, epoch_sec=30)

    # Verify returned shapes
    assert epochs.shape[0] == 2  # two epochs
    assert labels == ["N2", "REM"]

    # Verify that files were written
    epochs_file = tmp_path / "processed" / "epochs_unknown.npz"
    meta_file = tmp_path / "processed" / "metadata_unknown.json"
    assert epochs_file.is_file()
    assert meta_file.is_file()

    # Load the saved .npz to confirm contents
    loaded = np.load(epochs_file)
    np.testing.assert_array_equal(loaded["data"], epochs)

    # Load and check metadata JSON
    with open(meta_file, "r", encoding="utf-8") as f:
        meta = json.load(f)
    assert "waking_night_id" in meta
    assert "sleep_night_id" in meta

def test_validate_no_nans_raises():
    """validate_no_nans should raise when NaNs are present and log the issue."""
    arr = np.array([[1.0, np.nan], [2.0, 3.0]])

    # Ensure the validation log starts empty
    log_path = paths.data("processed", "validation_log.txt")
    if log_path.exists():
        os.remove(log_path)

    with pytest.raises(ValueError):
        validate_no_nans(arr)

    # After the exception, the log file should contain the warning line
    assert log_path.is_file()
    with open(log_path, "r", encoding="utf-8") as f:
        contents = f.read()
    assert "NaN detected" in contents