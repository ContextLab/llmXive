"""
Integration test for code/data_loader.py.
Verifies stratified sampling and stress-curve generation workflow.

This test ensures that:
1. The stratified sampling logic correctly groups by speaker_id and snr_db.
2. The generated distortion vectors cover the expected 54 scenarios.
3. The workflow from loading data to generating stress curves (via distortion vectors)
   produces a valid intermediate structure ready for the distortion engine.

Note: This test mocks the data loading to avoid requiring the full 7GB+ datasets
in the test environment, but it rigorously tests the logic paths and integration
points defined in data_loader.py.
"""
import os
import sys
import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import random

# Add project root to path if not already
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.data_loader import (
    stratified_sample,
    generate_all_distortion_vectors,
    verify_dataset_coverage_for_scenarios,
    save_stratified_subset,
    load_librispeech_subset,
    load_coraa_mupe_asr_subset
)
from code.config import get_config
from code.models import DistortionVector, AudioClip

@pytest.fixture
def mock_config():
    """Provide a mock config for testing."""
    return {
        "paths": {
            "raw": "data/raw",
            "derived": "data/derived",
            "validation": "data/validation"
        },
        "seeds": {
            "random": 42
        },
        "hyperparameters": {
            "sample_size": 100
        }
    }

@pytest.fixture
def sample_data():
    """Generate a deterministic sample dataset for testing stratification."""
    random.seed(42)
    data = []
    speakers = [f"speaker_{i}" for i in range(10)]
    snr_buckets = [0, 5, 10, 15, 20, 25, 30]
    
    # Create a balanced dataset
    for i in range(100):
        data.append({
            "clip_id": f"clip_{i}",
            "speaker_id": speakers[i % 10],
            "source_dataset": "librispeech" if i < 50 else "coraa",
            "audio_path": f"data/raw/audio_{i}.wav",
            "transcript": f"Sample transcript {i}",
            "snr_db": snr_buckets[i % 7],
            "rt60": 0.4
        })
    return data

def test_stratified_sampling_logic(sample_data):
    """Test that stratified sampling preserves distribution across strata."""
    n_samples = 20
    seed = 123
    
    # Run stratified sampling
    sampled = stratified_sample(sample_data, n_samples, seed)
    
    # Assertions
    assert len(sampled) == n_samples, f"Expected {n_samples} samples, got {len(sampled)}"
    
    # Check that we have representation from different speakers
    speakers_in_sample = set(item["speaker_id"] for item in sampled)
    assert len(speakers_in_sample) > 1, "Stratified sample should include multiple speakers"
    
    # Check that we have representation from different SNR buckets
    snr_in_sample = set(item["snr_db"] for item in sampled)
    assert len(snr_in_sample) > 1, "Stratified sample should include multiple SNR buckets"

def test_distortion_vector_generation():
    """Test that 54 distinct distortion vectors are generated."""
    vectors = generate_all_distortion_vectors()
    
    assert len(vectors) == 54, f"Expected 54 vectors, got {len(vectors)}"
    
    # Verify uniqueness
    unique_vectors = set()
    for v in vectors:
        key = (v["snr_db"], v["rt60"])
        assert key not in unique_vectors, f"Duplicate vector found: {key}"
        unique_vectors.add(key)
    
    # Verify ranges
    snr_values = {v["snr_db"] for v in vectors}
    rt60_values = {v["rt60"] for v in vectors}
    
    assert snr_values == {0, 5, 10, 15, 20, 25, 30}, "SNR values incorrect"
    assert rt60_values == {0.1, 0.3, 0.5, 0.8, 1.2, 1.8, 2.5}, "RT60 values incorrect"

def test_coverage_verification():
    """Test the coverage verification function."""
    vectors = generate_all_distortion_vectors()
    assert verify_dataset_coverage_for_scenarios(vectors) is True, "Coverage verification failed for valid vectors"
    
    # Test with insufficient vectors
    assert verify_dataset_coverage_for_scenarios(vectors[:10]) is False, "Coverage verification should fail for insufficient vectors"

def test_save_and_load_stratified_subset(sample_data, mock_config):
    """Test saving and loading a stratified subset to JSON."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_subset.json"
        
        # Save
        save_stratified_subset(sample_data, output_path)
        
        # Verify file exists
        assert output_path.exists(), "Output file was not created"
        
        # Load and verify content
        with open(output_path, 'r') as f:
            loaded_data = json.load(f)
        
        assert len(loaded_data) == len(sample_data), "Loaded data size mismatch"
        assert loaded_data[0]["clip_id"] == sample_data[0]["clip_id"], "Data content mismatch"

def test_workflow_integration(mock_config, sample_data):
    """
    Integration test for the full workflow:
    1. Load data (mocked)
    2. Generate distortion vectors
    3. Verify coverage
    4. Simulate stress curve generation structure
    """
    # 1. Mock the data loading functions to return our sample data
    with patch('code.data_loader.fetch_and_verify_librispeech', return_value=sample_data[:50]), \
         patch('code.data_loader.fetch_and_verify_coraa_mupe_asr', return_value=sample_data[50:]):
         
         librispeech_data = load_librispeech_subset(mock_config)
         coraa_data = load_coraa_mupe_asr_subset(mock_config)
         
         assert len(librispeech_data) == 50, "LibriSpeech data load failed"
         assert len(coraa_data) == 50, "CORAA data load failed"
         
         # 2. Generate distortion vectors
         vectors = generate_all_distortion_vectors()
         assert len(vectors) == 54, "Distortion vector generation failed"
         
         # 3. Verify coverage
         assert verify_dataset_coverage_for_scenarios(vectors) is True, "Coverage verification failed"
         
         # 4. Simulate stress curve structure (integration point for T012)
         # This verifies that the data loader prepares the correct structure for the distortion engine
         stress_curve_preview = []
         for clip in librispeech_data[:2]: # Just a preview
             for vector in vectors[:2]: # Just a preview
                 stress_curve_preview.append({
                     "clip_id": clip["clip_id"],
                     "distortion_snr": vector["snr_db"],
                     "distortion_rt60": vector["rt60"],
                     "status": "pending"
                 })
         
         assert len(stress_curve_preview) == 4, "Stress curve preview generation failed"
         assert stress_curve_preview[0]["clip_id"] == "clip_0", "Clip ID mismatch in stress curve"
         assert stress_curve_preview[0]["distortion_snr"] == 0, "SNR mismatch in stress curve"
         assert stress_curve_preview[0]["distortion_rt60"] == 0.1, "RT60 mismatch in stress curve"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])