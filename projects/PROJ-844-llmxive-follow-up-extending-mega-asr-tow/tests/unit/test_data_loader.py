"""Unit tests for code/data_loader.py"""
import pytest
from pathlib import Path
from data_loader import (
    compute_file_hash,
    verify_checksum,
    stratified_sample,
    generate_all_distortion_vectors,
    verify_dataset_coverage_for_scenarios
)

def test_compute_file_hash_returns_string():
    """Verify hash computation returns a hex string"""
    import tempfile
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"test data")
        f.flush()
        hash_val = compute_file_hash(f.name)
        assert isinstance(hash_val, str)
        assert len(hash_val) == 64  # SHA256 hex length

def test_verify_checksum_with_valid_hash():
    """Verify checksum validation with known good hash"""
    import tempfile
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"test data")
        f.flush()
        # Compute actual hash
        actual_hash = compute_file_hash(f.name)
        assert verify_checksum(f.name, actual_hash) is True

def test_verify_checksum_with_invalid_hash():
    """Verify checksum validation fails with bad hash"""
    import tempfile
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"test data")
        f.flush()
        assert verify_checksum(f.name, "0" * 64) is False

def test_generate_all_distortion_vectors_count():
    """Verify generation of 54 distortion vectors"""
    vectors = generate_all_distortion_vectors()
    assert len(vectors) == 54

def test_distortion_vectors_have_required_fields():
    """Verify each vector has SNR and RT60"""
    vectors = generate_all_distortion_vectors()
    for v in vectors:
        assert "snr_db" in v
        assert "rt60_sec" in v

def test_stratified_sample_returns_list():
    """Verify stratified sampling returns a list"""
    # Mock data: list of dicts with speaker_id and snr_bucket
    mock_data = [
        {"speaker_id": "1", "snr_bucket": "low", "audio_path": "a.wav"},
        {"speaker_id": "1", "snr_bucket": "high", "audio_path": "b.wav"},
        {"speaker_id": "2", "snr_bucket": "low", "audio_path": "c.wav"},
        {"speaker_id": "2", "snr_bucket": "high", "audio_path": "d.wav"},
    ]
    sample = stratified_sample(mock_data, sample_size=2)
    assert isinstance(sample, list)
    assert len(sample) <= len(mock_data)

def test_verify_dataset_coverage_returns_bool():
    """Verify coverage check returns boolean"""
    # Mock vectors
    mock_vectors = generate_all_distortion_vectors()
    result = verify_dataset_coverage_for_scenarios(mock_vectors)
    assert isinstance(result, bool)
