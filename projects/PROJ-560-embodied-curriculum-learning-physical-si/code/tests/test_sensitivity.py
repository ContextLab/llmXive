import pytest
import numpy as np
import os
import sys
import json
import tempfile
from src.sensitivity import run_sensitivity_sweep, check_robustness_warning, aggregate_results_for_report
from src.models import DatasetRecord


class TestSensitivitySweepLogic:
    """Tests for sensitivity sweep logic."""
    
    def test_sweep_basic(self):
        """Test basic sweep execution."""
        records = [
            DatasetRecord(pre_test_score=50, post_test_score=60, instruction_type="A"),
            DatasetRecord(pre_test_score=50, post_test_score=55, instruction_type="B")
        ] * 20 # N=40
        
        results = run_sensitivity_sweep(records, [0.01, 0.05])
        assert len(results) == 2
        assert all(r.threshold in [0.01, 0.05] for r in results)
        
    def test_insufficient_data(self):
        """Test sweep with insufficient data."""
        records = [
            DatasetRecord(pre_test_score=50, post_test_score=60, instruction_type="A"),
            DatasetRecord(pre_test_score=50, post_test_score=55, instruction_type="B")
        ]
        
        results = run_sensitivity_sweep(records, [0.05])
        assert len(results) == 0


class TestRobustnessWarning:
    """Tests for robustness warning."""
    
    def test_warning_triggered(self):
        """Test warning when effect is negligible."""
        # Mock results with negligible effect
        from src.models import SensitivitySweep
        results = [
            SensitivitySweep(threshold=0.05, effect_size=0.1, significant=True)
        ]
        assert check_robustness_warning(results) is True
        
    def test_no_warning(self):
        """Test no warning when effect is large."""
        from src.models import SensitivitySweep
        results = [
            SensitivitySweep(threshold=0.05, effect_size=0.8, significant=True)
        ]
        assert check_robustness_warning(results) is False


class TestAggregateSweepResults:
    """Tests for aggregating sweep results."""
    
    def test_aggregate(self):
        """Test aggregation."""
        from src.models import SensitivitySweep
        results = [
            SensitivitySweep(threshold=0.01, effect_size=0.5, significant=True),
            SensitivitySweep(threshold=0.05, effect_size=0.5, significant=True)
        ]
        aggregated = aggregate_results_for_report(results)
        assert len(aggregated) == 2
        assert aggregated[0]["threshold"] == 0.01
