"""
Unit tests for T027: Metrics Comparison Logic in reporting.py
"""
import pytest
import os
import json
import tempfile
from typing import Dict, Any
from reporting import (
    calculate_p_value_shift,
    compute_ci_width_change,
    compute_effect_size_delta,
    calculate_inconsistency_rate,
    apply_bonferroni_correction,
    generate_comparison_report,
    load_json_file
)

class TestPValueShift:
    def test_calculate_p_value_shift_basic(self):
        """Test basic p-value shift calculation."""
        assert calculate_p_value_shift(0.03, 0.05) == 0.02
        assert calculate_p_value_shift(0.05, 0.03) == 0.02
        assert calculate_p_value_shift(0.001, 0.999) == 0.998

    def test_calculate_p_value_shift_none(self):
        """Test handling of None values."""
        assert calculate_p_value_shift(None, 0.05) == 0.0
        assert calculate_p_value_shift(0.05, None) == 0.0

class TestCIWidthChange:
    def test_compute_ci_width_change_basic(self):
        """Test basic CI width change."""
        # Baseline width: 10, Cleaned width: 8 -> Change: 2
        assert compute_ci_width_change((0, 10), (1, 9)) == 2.0
        # Baseline width: 5, Cleaned width: 5 -> Change: 0
        assert compute_ci_width_change((0, 5), (2, 7)) == 0.0

    def test_compute_ci_width_change_missing(self):
        """Test handling of missing CI data."""
        assert compute_ci_width_change(None, (0, 10)) == 0.0
        assert compute_ci_width_change((0, 10), None) == 0.0

class TestEffectSizeDelta:
    def test_compute_effect_size_delta_basic(self):
        """Test basic effect size delta."""
        assert compute_effect_size_delta(0.5, 0.3) == 0.2
        assert compute_effect_size_delta(0.3, 0.5) == -0.2

    def test_compute_effect_size_delta_none(self):
        """Test handling of None values."""
        assert compute_effect_size_delta(None, 0.3) == 0.0
        assert compute_effect_size_delta(0.3, None) == 0.0

class TestInconsistencyRate:
    def test_calculate_inconsistency_rate_no_change(self):
        """Test rate when significance status does not change."""
        baseline = [{'p_value': 0.03}, {'p_value': 0.08}]
        cleaned = [{'p_value': 0.04}, {'p_value': 0.09}]
        # Both significant -> Both insignificant -> No change
        assert calculate_inconsistency_rate(baseline, cleaned) == 0.0

    def test_calculate_inconsistency_rate_full_change(self):
        """Test rate when significance status changes for all."""
        baseline = [{'p_value': 0.03}, {'p_value': 0.04}]
        cleaned = [{'p_value': 0.06}, {'p_value': 0.07}]
        # Both significant -> Both insignificant -> Change
        assert calculate_inconsistency_rate(baseline, cleaned) == 1.0

    def test_calculate_inconsistency_rate_mixed(self):
        """Test rate with mixed changes."""
        baseline = [{'p_value': 0.03}, {'p_value': 0.08}]
        cleaned = [{'p_value': 0.06}, {'p_value': 0.09}]
        # 1st: Sig -> InSig (Change), 2nd: InSig -> InSig (No Change)
        assert calculate_inconsistency_rate(baseline, cleaned) == 0.5

class TestBonferroni:
    def test_apply_bonferroni_basic(self):
        """Test Bonferroni correction."""
        p_values = [0.01, 0.05, 0.10]
        adjusted = apply_bonferroni_correction(p_values, alpha=0.05)
        # n=3, alpha_adj = 0.0166
        # 0.01 * 3 = 0.03
        # 0.05 * 3 = 0.15
        # 0.10 * 3 = 0.30
        assert adjusted == [0.03, 0.15, 0.30]

    def test_apply_bonferroni_clamp(self):
        """Test that adjusted p-values are clamped to 1.0."""
        p_values = [0.9, 0.95]
        adjusted = apply_bonferroni_correction(p_values, alpha=0.05)
        # 0.9 * 2 = 1.8 -> 1.0
        # 0.95 * 2 = 1.9 -> 1.0
        assert adjusted == [1.0, 1.0]

class TestGenerateComparisonReport:
    def setup_method(self):
        """Create temporary files for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.baseline_path = os.path.join(self.temp_dir, "baseline.json")
        self.cleaned_path = os.path.join(self.temp_dir, "cleaned.json")
        self.output_path = os.path.join(self.temp_dir, "report.json")

    def teardown_method(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_generate_comparison_report_success(self):
        """Test successful generation of comparison report."""
        baseline_data = {
            "datasets": [
                {"dataset_name": "ds1", "p_value": 0.03, "ci": [0.1, 0.5], "effect_size": 0.4},
                {"dataset_name": "ds2", "p_value": 0.08, "ci": [0.2, 0.6], "effect_size": 0.2}
            ]
        }
        cleaned_data = {
            "datasets": [
                {"dataset_name": "ds1", "p_value": 0.06, "ci": [0.15, 0.45], "effect_size": 0.3},
                {"dataset_name": "ds2", "p_value": 0.09, "ci": [0.25, 0.55], "effect_size": 0.15}
            ]
        }

        with open(self.baseline_path, 'w') as f:
            json.dump(baseline_data, f)
        with open(self.cleaned_path, 'w') as f:
            json.dump(cleaned_data, f)

        report = generate_comparison_report(self.baseline_path, self.cleaned_path, self.output_path)

        assert os.path.exists(self.output_path)
        assert report['summary']['total_datasets_compared'] == 2
        assert report['summary']['inconsistency_rate'] == 0.0 # 0.03->0.06 (Sig->InSig) = 1 change?
        # Wait: 0.03 (Sig) -> 0.06 (InSig) = Change. 0.08 (InSig) -> 0.09 (InSig) = No Change.
        # So rate should be 0.5.
        # Let's re-verify logic in test.
        # My manual calculation: ds1 changes, ds2 doesn't. 1/2 = 0.5.
        assert report['summary']['inconsistency_rate'] == 0.5

        # Check per dataset
        ds1 = next(r for r in report['per_dataset_differences'] if r['dataset_name'] == 'ds1')
        assert ds1['p_value_shift'] == 0.03 # |0.06 - 0.03|

    def test_generate_comparison_report_missing_file(self):
        """Test error handling for missing input files."""
        with pytest.raises(FileNotFoundError):
            generate_comparison_report("nonexistent.json", self.cleaned_path, self.output_path)