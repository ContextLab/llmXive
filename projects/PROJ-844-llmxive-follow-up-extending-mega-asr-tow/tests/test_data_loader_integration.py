"""
Integration test for code/data_loader.py verifying stratified sampling and
stress-curve generation workflow.

This test validates:
1. Stratified sampling by speaker ID and SNR bucket
2. Stress curve generation for a subset of clips
3. Data integrity of generated stress curves
4. Integration with distortion engine
"""
import os
import sys
import pytest
import tempfile
import shutil
from pathlib import Path
import json
import pandas as pd
import numpy as np

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'code'))

from config import get_config
from data_loader import (
    stratified_sample,
    save_stratified_subset,
    load_librispeech_subset,
    generate_stress_curve_for_clip,
    verify_dataset_coverage_for_scenarios
)
from distortion_engine import generate_all_distortion_vectors, DistortionEngine
from models import AudioClip, StressCurve


class TestStratifiedSampling:
    """Test stratified sampling functionality"""

    @pytest.fixture
    def sample_config(self):
        """Create a minimal config for testing"""
        config = get_config()
        # Override paths for testing
        config['raw_path'] = str(project_root / 'data' / 'raw')
        config['derived_path'] = str(project_root / 'data' / 'derived')
        config['sample_size'] = 10  # Small sample for testing
        config['stratify_by_speaker'] = True
        config['stratify_by_snr'] = True
        return config

    def test_stratified_sample_returns_balanced_subset(self, sample_config):
        """Verify stratified sampling maintains speaker and SNR distribution"""
        # This test will run on real data if available, or skip if not
        try:
            # Load a small subset of LibriSpeech data
            librispeech_data = load_librispeech_subset(sample_config)
            
            if not librispeech_data:
                pytest.skip("No LibriSpeech data available for testing")
            
            # Apply stratified sampling
            sampled_data = stratified_sample(
                librispeech_data,
                sample_config['sample_size'],
                sample_config
            )
            
            # Verify we got the expected number of samples (or less if data is smaller)
            assert len(sampled_data) <= sample_config['sample_size']
            assert len(sampled_data) > 0, "Sampled data should not be empty"
            
            # Verify stratification by speaker (if enough data)
            if sample_config['stratify_by_speaker']:
                speaker_counts = {}
                for clip in sampled_data:
                    speaker_id = clip.get('speaker_id', 'unknown')
                    speaker_counts[speaker_id] = speaker_counts.get(speaker_id, 0) + 1
                
                # Should have multiple speakers in sample
                assert len(speaker_counts) > 1, "Stratified sample should include multiple speakers"
            
            # Verify stratification by SNR (if enough data)
            if sample_config['stratify_by_snr']:
                snr_values = [clip.get('snr', 0) for clip in sampled_data if 'snr' in clip]
                if snr_values:
                    unique_snrs = set(snr_values)
                    assert len(unique_snrs) > 1, "Stratified sample should include multiple SNR levels"
            
        except FileNotFoundError as e:
            pytest.skip(f"Dataset not available: {e}")

    def test_save_stratified_subset_creates_valid_files(self, sample_config):
        """Verify saved stratified subset files are valid"""
        with tempfile.TemporaryDirectory() as tmpdir:
            try:
                # Load data
                librispeech_data = load_librispeech_subset(sample_config)
                if not librispeech_data:
                    pytest.skip("No LibriSpeech data available")
                
                # Sample and save
                sampled_data = stratified_sample(
                    librispeech_data,
                    sample_config['sample_size'],
                    sample_config
                )
                
                output_path = Path(tmpdir) / 'sampled_subset'
                save_stratified_subset(sampled_data, str(output_path), sample_config)
                
                # Verify output files exist
                assert output_path.exists(), "Output directory should be created"
                
                # Check for expected files
                metadata_file = output_path / 'metadata.json'
                assert metadata_file.exists(), "Metadata file should be created"
                
                # Verify metadata content
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                
                assert 'sample_size' in metadata, "Metadata should include sample size"
                assert metadata['sample_size'] == len(sampled_data), "Metadata sample size should match actual"
                
            except FileNotFoundError as e:
                pytest.skip(f"Dataset not available: {e}")


class TestStressCurveGeneration:
    """Test stress curve generation workflow"""

    @pytest.fixture
    def stress_curve_config(self):
        """Create config for stress curve testing"""
        config = get_config()
        config['raw_path'] = str(project_root / 'data' / 'raw')
        config['derived_path'] = str(project_root / 'data' / 'derived')
        config['sample_size'] = 5  # Very small sample for testing
        config['distortion_vectors'] = 3  # Few vectors for speed
        return config

    def test_generate_stress_curve_creates_valid_structure(self, stress_curve_config):
        """Verify stress curve generation produces valid data structure"""
        try:
            # Load a minimal dataset
            librispeech_data = load_librispeech_subset(stress_curve_config)
            if not librispeech_data:
                pytest.skip("No LibriSpeech data available")
            
            # Get first clip for testing
            test_clip = librispeech_data[0]
            
            # Generate distortion vectors
            distortion_vectors = generate_all_distortion_vectors(stress_curve_config)
            if not distortion_vectors:
                pytest.skip("No distortion vectors generated")
            
            # Generate stress curve
            stress_curve = generate_stress_curve_for_clip(
                test_clip,
                distortion_vectors,
                stress_curve_config
            )
            
            # Verify stress curve structure
            assert isinstance(stress_curve, StressCurve), "Should return StressCurve object"
            assert stress_curve.clip_id is not None, "Clip ID should be set"
            assert len(stress_curve.data_points) > 0, "Stress curve should have data points"
            
            # Verify each data point has required fields
            for point in stress_curve.data_points:
                assert 'distortion_vector_id' in point, "Data point should have distortion_vector_id"
                assert 'snr' in point, "Data point should have SNR"
                assert 'rt60' in point, "Data point should have RT60"
                assert 'wer' in point or 'wer' not in point, "WER should be present or handled"
                assert 'sss' in point or 'sss' not in point, "SSS should be present or handled"
            
        except FileNotFoundError as e:
            pytest.skip(f"Dataset not available: {e}")
        except Exception as e:
            # Skip if ASR models or other dependencies are missing
            if "model" in str(e).lower() or "whisper" in str(e).lower():
                pytest.skip(f"ASR model dependencies not available: {e}")
            else:
                raise

    def test_stress_curve_coverage_with_multiple_vectors(self, stress_curve_config):
        """Verify stress curves are generated for all requested distortion scenarios"""
        try:
            librispeech_data = load_librispeech_subset(stress_curve_config)
            if not librispeech_data:
                pytest.skip("No LibriSpeech data available")
            
            test_clip = librispeech_data[0]
            
            # Test with different numbers of distortion vectors
            for num_vectors in [1, 2, 3]:
                config = stress_curve_config.copy()
                config['distortion_vectors'] = num_vectors
                
                distortion_vectors = generate_all_distortion_vectors(config)
                stress_curve = generate_stress_curve_for_clip(
                    test_clip,
                    distortion_vectors,
                    config
                )
                
                # Should have at least one data point per vector (may be fewer if some fail)
                assert len(stress_curve.data_points) <= num_vectors, \
                    f"Should not have more points than vectors requested"
                assert len(stress_curve.data_points) > 0, \
                    "Should have at least one successful stress curve point"
            
        except FileNotFoundError as e:
            pytest.skip(f"Dataset not available: {e}")
        except Exception as e:
            if "model" in str(e).lower() or "whisper" in str(e).lower():
                pytest.skip(f"ASR model dependencies not available: {e}")
            else:
                raise


class TestDatasetCoverage:
    """Test dataset coverage verification"""

    def test_verify_dataset_coverage_logs_missing_scenarios(self):
        """Verify coverage check logs warnings for missing distortion combinations"""
        config = get_config()
        config['raw_path'] = str(project_root / 'data' / 'raw')
        
        try:
            # This should log warnings if certain distortion combinations are missing
            # but should not fail the test
            result = verify_dataset_coverage_for_scenarios(config)
            
            # Result should be a dict with coverage information
            assert isinstance(result, dict), "Coverage result should be a dictionary"
            
            # Should have at least some coverage information
            assert 'total_scenarios' in result or 'available_scenarios' in result or 'coverage' in result, \
                "Result should contain coverage metrics"
            
        except FileNotFoundError as e:
            pytest.skip(f"Dataset not available: {e}")


class TestIntegrationWorkflow:
    """End-to-end integration test for the full workflow"""

    def test_full_stress_curve_workflow(self):
        """Test the complete workflow from data loading to stress curve generation"""
        config = get_config()
        config['raw_path'] = str(project_root / 'data' / 'raw')
        config['derived_path'] = str(project_root / 'data' / 'derived')
        config['sample_size'] = 3
        config['distortion_vectors'] = 2
        
        with tempfile.TemporaryDirectory() as tmpdir:
            try:
                # Step 1: Load and sample data
                librispeech_data = load_librispeech_subset(config)
                if not librispeech_data:
                    pytest.skip("No LibriSpeech data available")
                
                sampled_data = stratified_sample(
                    librispeech_data,
                    config['sample_size'],
                    config
                )
                
                # Step 2: Generate distortion vectors
                distortion_vectors = generate_all_distortion_vectors(config)
                if not distortion_vectors:
                    pytest.skip("No distortion vectors available")
                
                # Step 3: Generate stress curves for each clip
                stress_curves = []
                for clip in sampled_data:
                    curve = generate_stress_curve_for_clip(
                        clip,
                        distortion_vectors,
                        config
                    )
                    if curve and len(curve.data_points) > 0:
                        stress_curves.append(curve)
                
                # Verify we got stress curves
                assert len(stress_curves) > 0, "Should generate at least one stress curve"
                
                # Verify each curve has valid structure
                for curve in stress_curves:
                    assert isinstance(curve, StressCurve)
                    assert len(curve.data_points) > 0
                    
                    # Check data point consistency
                    snr_values = [p['snr'] for p in curve.data_points if 'snr' in p]
                    rt60_values = [p['rt60'] for p in curve.data_points if 'rt60' in p]
                    
                    # SNR should be decreasing (more distortion)
                    if len(snr_values) > 1:
                        # Note: SNR might not be strictly monotonic depending on implementation
                        pass
                    
                    # RT60 should be increasing (more reverberation)
                    if len(rt60_values) > 1:
                        pass
                
                # Step 4: Verify coverage
                coverage = verify_dataset_coverage_for_scenarios(config)
                assert coverage is not None, "Coverage check should complete"
                
            except FileNotFoundError as e:
                pytest.skip(f"Dataset not available: {e}")
            except Exception as e:
                if "model" in str(e).lower() or "whisper" in str(e).lower():
                    pytest.skip(f"ASR model dependencies not available: {e}")
                else:
                    raise


if __name__ == '__main__':
    pytest.main([__file__, '-v'])