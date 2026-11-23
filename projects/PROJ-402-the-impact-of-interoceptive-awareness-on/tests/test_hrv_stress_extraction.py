import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from utils.hrv_metrics import compute_rmssd, compute_sdsn
from code_02_preprocess_hrv import extract_stress_hrv_metrics

class TestStressHRVExtraction:
    """
    Test suite for T022: Extract Stress HRV metric as the outcome variable per FR-004.
    """

    def test_extract_stress_metrics_valid_data(self):
        """
        Test that stress HRV metrics are correctly extracted from valid RR intervals.
        """
        # Create synthetic but realistic RR intervals for stress phase
        # Normal stress RR intervals: ~0.6-0.8 seconds (75-100 bpm)
        np.random.seed(42)
        n_intervals = 100
        base_rr = 0.7  # 0.7 seconds = ~86 bpm
        noise = np.random.normal(0, 0.05, n_intervals)
        stress_rr = base_rr + noise
        
        # Create processed data structure
        processed_data = {
            'rr_intervals': stress_rr,
            'peaks': np.arange(len(stress_rr)),
            'fs': 700.0,
            'signal_quality': 'good'
        }
        
        # Extract stress metrics
        subject_id = "01"
        result = extract_stress_hrv_metrics(subject_id, processed_data)
        
        # Assertions
        assert result['subject_id'] == subject_id
        assert result['phase'] == 'Stress'
        assert 'RMSSD' in result
        assert 'SDNN' in result
        assert result['n_intervals'] == n_intervals
        
        # RMSSD and SDNN should be positive
        assert result['RMSSD'] > 0
        assert result['SDNN'] > 0
        
        # Values should be in realistic range for stress (RMSSD: 10-50 ms, SDNN: 20-100 ms)
        assert 10 <= result['RMSSD'] * 1000 <= 50  # Convert to ms
        assert 20 <= result['SDNN'] * 1000 <= 100  # Convert to ms

    def test_extract_stress_metrics_insufficient_data(self):
        """
        Test that extraction fails gracefully with insufficient data.
        """
        # Very few RR intervals
        stress_rr = np.array([0.7, 0.75, 0.65, 0.72, 0.68])  # Only 5 intervals
        
        processed_data = {
            'rr_intervals': stress_rr,
            'peaks': np.arange(len(stress_rr)),
            'fs': 700.0,
            'signal_quality': 'good'
        }
        
        # Should raise ValueError for too few intervals
        with pytest.raises(ValueError, match="Not enough RR intervals"):
            extract_stress_hrv_metrics("01", processed_data)

    def test_extract_stress_metrics_empty_rr(self):
        """
        Test that extraction fails with empty RR intervals.
        """
        processed_data = {
            'rr_intervals': np.array([]),
            'peaks': np.array([]),
            'fs': 700.0,
            'signal_quality': 'good'
        }
        
        with pytest.raises(ValueError, match="No valid RR intervals"):
            extract_stress_hrv_metrics("01", processed_data)

    def test_stress_phase_segmentation(self):
        """
        Test that the stress phase is correctly segmented from the full recording.
        """
        # Create a longer recording with distinct phases
        n_total = 200
        # Baseline: first 60 intervals (30%)
        # Stress: next 80 intervals (40%)
        # Recovery: last 60 intervals (30%)
        
        # Stress phase should be intervals 60-140
        stress_rr = np.ones(80) * 0.65  # Lower RR = higher HR in stress
        full_rr = np.concatenate([
            np.ones(60) * 0.8,   # Baseline (higher RR = lower HR)
            stress_rr,            # Stress
            np.ones(60) * 0.75   # Recovery
        ])
        
        processed_data = {
            'rr_intervals': full_rr,
            'peaks': np.arange(len(full_rr)),
            'fs': 700.0,
            'signal_quality': 'good'
        }
        
        result = extract_stress_hrv_metrics("01", processed_data)
        
        # Stress RMSSD should reflect the stress phase (shorter RR intervals)
        # The stress phase has RR ~0.65, baseline ~0.8
        # RMSSD should be lower in stress than baseline
        assert result['n_intervals'] == 80
        assert result['RMSSD'] > 0
        assert result['SDNN'] > 0

    def test_output_format_compliance(self):
        """
        Test that output format matches the required CSV structure:
        subject_id, phase, RMSSD, SDNN
        """
        np.random.seed(123)
        stress_rr = np.random.normal(0.7, 0.05, 50)
        
        processed_data = {
            'rr_intervals': stress_rr,
            'peaks': np.arange(len(stress_rr)),
            'fs': 700.0,
            'signal_quality': 'good'
        }
        
        result = extract_stress_hrv_metrics("02", processed_data)
        
        # Check all required keys are present
        required_keys = ['subject_id', 'phase', 'RMSSD', 'SDNN', 'n_intervals']
        for key in required_keys:
            assert key in result, f"Missing required key: {key}"
        
        # Check data types
        assert isinstance(result['subject_id'], str)
        assert result['phase'] == 'Stress'
        assert isinstance(result['RMSSD'], (int, float, np.floating))
        assert isinstance(result['SDNN'], (int, float, np.floating))
        assert isinstance(result['n_intervals'], int)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
