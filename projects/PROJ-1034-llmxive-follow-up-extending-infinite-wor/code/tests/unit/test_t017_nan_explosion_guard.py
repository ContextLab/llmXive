"""
Unit tests for T017: NaN and State Explosion Guard.
"""
import pytest
import pandas as pd
import numpy as np
import json
import tempfile
import os
from src.analysis.NaN_and_explosion_guard import (
    validate_metrics_no_nan,
    handle_state_explosion_warning,
    check_metrics_for_explosion,
    run_validation_on_log,
    StateExplosionWarning
)

class TestT017NaNAndExplosionGuard:
    
    def test_validate_no_nan_clean_data(self):
        """Test that clean data passes validation."""
        df = pd.DataFrame({
            'coherence_score': [0.9, 0.95, 0.88],
            'diversity_score': [0.5, 0.6, 0.55],
            'step_latency': [0.01, 0.02, 0.015]
        })
        is_valid, errors = validate_metrics_no_nan(df)
        assert is_valid is True
        assert len(errors) == 0

    def test_validate_catches_nan(self):
        """Test that NaN values are detected."""
        df = pd.DataFrame({
            'coherence_score': [0.9, np.nan, 0.88],
            'diversity_score': [0.5, 0.6, 0.55]
        })
        is_valid, errors = validate_metrics_no_nan(df)
        assert is_valid is False
        assert any("NaN" in e for e in errors)
        assert any("coherence_score" in e for e in errors)

    def test_validate_catches_inf(self):
        """Test that Inf values are detected."""
        df = pd.DataFrame({
            'coherence_score': [0.9, np.inf, 0.88],
            'diversity_score': [0.5, 0.6, 0.55]
        })
        is_valid, errors = validate_metrics_no_nan(df)
        assert is_valid is False
        assert any("Inf" in e for e in errors)

    def test_handle_state_explosion_threshold(self):
        """Test that values exceeding threshold raise warning."""
        # Normal value
        result = handle_state_explosion_warning(0.5, "test_metric", {})
        assert result is False

        # Explosion value
        with pytest.raises(StateExplosionWarning):
            handle_state_explosion_warning(1e7, "test_metric", {"step": 100})

    def test_handle_state_explosion_inf(self):
        """Test that Inf values raise warning."""
        with pytest.raises(StateExplosionWarning):
            handle_state_explosion_warning(np.inf, "test_metric", {"step": 100})

    def test_check_metrics_for_explosion(self):
        """Test detection of explosion events in DataFrame."""
        df = pd.DataFrame({
            'normal': [1.0, 2.0, 3.0],
            'explosion_inf': [1.0, np.inf, 3.0],
            'explosion_high': [1.0, 1e7, 3.0]
        })
        explosions = check_metrics_for_explosion(df)
        
        assert len(explosions) == 2
        types = [e['type'] for e in explosions]
        assert 'inf_value' in types
        assert 'threshold_exceeded' in types

    def test_run_validation_on_log_jsonl(self):
        """Test full validation pipeline on a JSONL log file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            # Write valid data
            f.write(json.dumps({"coherence": 0.9, "diversity": 0.5}) + "\n")
            f.write(json.dumps({"coherence": 0.95, "diversity": 0.6}) + "\n")
            temp_path = f.name

        try:
            report = run_validation_on_log(temp_path)
            assert report["nan_check_passed"] is True
            assert report["explosion_check_passed"] is True
            assert len(report["errors"]) == 0
        finally:
            os.unlink(temp_path)

    def test_run_validation_on_log_with_nan(self):
        """Test validation fails on NaN in JSONL log."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            f.write(json.dumps({"coherence": 0.9, "diversity": 0.5}) + "\n")
            f.write(json.dumps({"coherence": None, "diversity": 0.6}) + "\n") # None becomes NaN in pandas
            temp_path = f.name

        try:
            report = run_validation_on_log(temp_path)
            assert report["nan_check_passed"] is False
            assert len(report["errors"]) > 0
        finally:
            os.unlink(temp_path)

    def test_run_validation_on_log_with_explosion(self):
        """Test validation flags explosion in JSONL log."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            f.write(json.dumps({"coherence": 0.9, "diversity": 0.5}) + "\n")
            f.write(json.dumps({"coherence": 0.95, "diversity": 1e9}) + "\n") # Explosion
            temp_path = f.name

        try:
            report = run_validation_on_log(temp_path)
            assert report["explosion_check_passed"] is False
            assert len(report["warnings"]) > 0
        finally:
            os.unlink(temp_path)
