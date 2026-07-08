"""
Unit tests for prevalence analysis functions.
"""
import json
import math
from pathlib import Path
from unittest.mock import patch, MagicMock

import numpy as np
import pytest
from scipy import stats

from code.src.audit.prevalence import (
    binomial_test,
    wilson_ci,
    compute_prevalence,
    sensitivity_analysis,
    apply_dynamic_bonferroni,
    load_audit_records,
    write_prevalence_results,
    run_prevalence_analysis
)


class TestBinomialTest:
    def test_binomial_test_known_values(self):
        # 50 successes out of 100, p0=0.5 -> p-value should be 1.0 (exact match)
        p_val = binomial_test(50, 100, p0=0.5)
        assert math.isclose(p_val, 1.0, abs_tol=1e-6)

    def test_binomial_test_extreme_case(self):
        # 0 successes out of 100, p0=0.5 -> very small p-value
        p_val = binomial_test(0, 100, p0=0.5)
        assert p_val < 0.001

    def test_binomial_test_zero_total(self):
        p_val = binomial_test(0, 0, p0=0.5)
        assert p_val == 1.0

class TestWilsonCI:
    def test_wilson_ci_known_values(self):
        # 50/100, 95% CI (z=1.96)
        lower, upper = wilson_ci(50, 100, z=1.96)
        # Approximate expected values
        assert 0.40 < lower < 0.42
        assert 0.58 < upper < 0.60

    def test_wilson_ci_zero_successes(self):
        lower, upper = wilson_ci(0, 100, z=1.96)
        assert lower == 0.0
        assert upper > 0.0 and upper < 0.1

    def test_wilson_ci_all_successes(self):
        lower, upper = wilson_ci(100, 100, z=1.96)
        assert lower > 0.9 and lower < 1.0
        assert upper == 1.0

    def test_wilson_ci_zero_n(self):
        lower, upper = wilson_ci(0, 0, z=1.96)
        assert lower == 0.0
        assert upper == 0.0

class TestComputePrevalence:
    def test_compute_prevalence_basic(self):
        records = [
            {'is_inconsistent': True},
            {'is_inconsistent': False},
            {'is_inconsistent': True}
        ]
        result = compute_prevalence(records)
        assert result['total_summaries'] == 3
        assert result['inconsistent_count'] == 2
        assert math.isclose(result['inconsistent_rate'], 2/3, rel_tol=1e-4)
        assert 'wilson_ci_lower' in result
        assert 'wilson_ci_upper' in result
        assert 'binomial_p_value' in result

    def test_compute_prevalence_empty(self):
        result = compute_prevalence([])
        assert result['total_summaries'] == 0
        assert result['inconsistent_count'] == 0
        assert result['inconsistent_rate'] == 0.0

class TestSensitivityAnalysis:
    def test_sensitivity_analysis_basic(self):
        records = [
            {'is_inconsistent': True},
            {'is_inconsistent': False}
        ]
        baseline_range = [0.3, 0.5, 0.7]
        results = sensitivity_analysis(records, baseline_range)

        assert len(results) == 3
        for res in results:
            assert 'baseline_p0' in res
            assert 'binomial_p_value' in res
            assert 'inconsistent_count' in res
            assert 'total_summaries' in res

class TestDynamicBonferroni:
    def test_bonferroni_basic(self):
        p_values = [0.01, 0.04, 0.06]
        adjusted = apply_dynamic_bonferroni(p_values, num_subgroups=5)
        expected = [0.05, 0.20, 0.30]
        for a, e in zip(adjusted, expected):
            assert math.isclose(a, e, abs_tol=1e-6)

    def test_bonferroni_cap_at_one(self):
        p_values = [0.2, 0.3]
        adjusted = apply_dynamic_bonferroni(p_values, num_subgroups=5)
        # 0.2*5=1.0, 0.3*5=1.5 -> capped at 1.0
        assert adjusted[0] == 1.0
        assert adjusted[1] == 1.0

    def test_bonferroni_zero_subgroups(self):
        p_values = [0.01]
        adjusted = apply_dynamic_bonferroni(p_values, num_subgroups=0)
        # Should return original list per implementation
        assert adjusted == p_values

class TestLoadAuditRecords:
    def test_load_audit_records_valid(self, tmp_path):
        data = [
            {'id': 1, 'is_inconsistent': True},
            {'id': 2, 'is_inconsistent': False}
        ]
        file_path = tmp_path / "audit_report.json"
        with open(file_path, 'w') as f:
            json.dump(data, f)

        records = load_audit_records(file_path)
        assert len(records) == 2
        assert records[0]['id'] == 1

    def test_load_audit_records_dict_with_records_key(self, tmp_path):
        data = {
            'records': [
                {'id': 1, 'is_inconsistent': True}
            ]
        }
        file_path = tmp_path / "audit_report.json"
        with open(file_path, 'w') as f:
            json.dump(data, f)

        records = load_audit_records(file_path)
        assert len(records) == 1

    def test_load_audit_records_not_found(self, tmp_path):
        file_path = tmp_path / "nonexistent.json"
        records = load_audit_records(file_path)
        assert records == []

class TestWritePrevalenceResults:
    def test_write_prevalence_results(self, tmp_path):
        data = {
            'total_summaries': 100,
            'inconsistent_count': 10,
            'inconsistent_rate': 0.1,
            'wilson_ci_lower': 0.05,
            'wilson_ci_upper': 0.15,
            'binomial_p_value': 0.001
        }
        file_path = tmp_path / "prevalence.json"
        write_prevalence_results(file_path, data)

        assert file_path.exists()
        with open(file_path, 'r') as f:
            loaded = json.load(f)
        assert loaded['total_summaries'] == 100

class TestRunPrevalenceAnalysis:
    def test_run_prevalence_analysis_full(self, tmp_path):
        audit_data = [
            {'is_inconsistent': True} for _ in range(20)
        ] + [
            {'is_inconsistent': False} for _ in range(80)
        ]
        input_path = tmp_path / "audit_report.json"
        output_path = tmp_path / "prevalence.json"

        with open(input_path, 'w') as f:
            json.dump(audit_data, f)

        result = run_prevalence_analysis(
            input_path,
            output_path,
            sensitivity_baseline_range=[0.1, 0.5, 0.9]
        )

        assert result['total_summaries'] == 100
        assert result['inconsistent_count'] == 20
        assert 'sensitivity_analysis' in result
        assert len(result['sensitivity_analysis']) == 3
        assert output_path.exists()

if __name__ == '__main__':
    pytest.main([__file__, '-v'])