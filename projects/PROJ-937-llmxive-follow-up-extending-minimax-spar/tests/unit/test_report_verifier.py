"""
Unit tests for code/eval/report_verifier.py (T036).
"""
import json
import pytest
import tempfile
from pathlib import Path
from eval.report_verifier import (
    verify_report_structure,
    verify_sensitivity_table_structure,
    verify_numeric_values,
    verify_report_file_exists,
    verify_report,
    REQUIRED_KEYS
)

class TestVerifyReportStructure:
    def test_all_keys_present(self):
        report = {
            'f1_score': 0.95,
            'p_value': 0.03,
            'false_positive_rate': 0.05,
            'sensitivity_table': [],
            'ttest_stat': 2.1,
            'wilcoxon_stat': 1.5
        }
        assert verify_report_structure(report, REQUIRED_KEYS) is True

    def test_missing_key(self):
        report = {
            'f1_score': 0.95,
            'p_value': 0.03,
            # missing others
        }
        assert verify_report_structure(report, REQUIRED_KEYS) is False

    def test_extra_keys_allowed(self):
        report = {
            'f1_score': 0.95,
            'p_value': 0.03,
            'false_positive_rate': 0.05,
            'sensitivity_table': [],
            'ttest_stat': 2.1,
            'wilcoxon_stat': 1.5,
            'extra_field': 'allowed'
        }
        assert verify_report_structure(report, REQUIRED_KEYS) is True

class TestVerifySensitivityTableStructure:
    def test_valid_list_of_dicts(self):
        table = [
            {'threshold': 0.01, 'metric_value': 0.9},
            {'threshold': 0.05, 'metric_value': 0.85}
        ]
        assert verify_sensitivity_table_structure(table) is True

    def test_empty_list(self):
        assert verify_sensitivity_table_structure([]) is True

    def test_not_list(self):
        assert verify_sensitivity_table_structure("not a list") is False

    def test_dict_without_expected_keys(self):
        table = [{'wrong_key': 1}]
        # Should warn but not fail strictly
        assert verify_sensitivity_table_structure(table) is True

class TestVerifyNumericValues:
    def test_all_valid_numbers(self):
        report = {
            'f1_score': 0.95,
            'p_value': 0.03,
            'ttest_stat': 2.1,
            'wilcoxon_stat': 1.5,
            'false_positive_rate': 0.05
        }
        assert verify_numeric_values(report) is True

    def test_none_values(self):
        report = {
            'f1_score': None,
            'p_value': 0.03,
            'ttest_stat': 2.1,
            'wilcoxon_stat': 1.5,
            'false_positive_rate': 0.05
        }
        assert verify_numeric_values(report) is False

    def test_string_values(self):
        report = {
            'f1_score': "0.95",
            'p_value': 0.03,
            'ttest_stat': 2.1,
            'wilcoxon_stat': 1.5,
            'false_positive_rate': 0.05
        }
        assert verify_numeric_values(report) is False

    def test_fpr_as_list(self):
        report = {
            'f1_score': 0.95,
            'p_value': 0.03,
            'ttest_stat': 2.1,
            'wilcoxon_stat': 1.5,
            'false_positive_rate': [0.01, 0.05, 0.1]
        }
        assert verify_numeric_values(report) is True

class TestVerifyReportFileExists:
    def test_file_exists(self, tmp_path):
        test_file = tmp_path / "test.json"
        test_file.write_text("{}")
        assert verify_report_file_exists(test_file) is True

    def test_file_not_exists(self, tmp_path):
        test_file = tmp_path / "nonexistent.json"
        assert verify_report_file_exists(test_file) is False

class TestVerifyReport:
    def test_full_valid_report(self, tmp_path):
        report = {
            'f1_score': 0.95,
            'p_value': 0.03,
            'false_positive_rate': 0.05,
            'sensitivity_table': [
                {'threshold': 0.01, 'metric_value': 0.9}
            ],
            'ttest_stat': 2.1,
            'wilcoxon_stat': 1.5
        }
        report_file = tmp_path / "benchmark_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f)
        
        assert verify_report(report_file) is True

    def test_missing_file(self, tmp_path):
        non_existent = tmp_path / "missing.json"
        assert verify_report(non_existent) is False

    def test_invalid_json(self, tmp_path):
        report_file = tmp_path / "bad.json"
        report_file.write_text("not valid json")
        assert verify_report(report_file) is False

    def test_missing_required_keys(self, tmp_path):
        report = {'f1_score': 0.95}
        report_file = tmp_path / "incomplete.json"
        with open(report_file, 'w') as f:
            json.dump(report, f)
        
        assert verify_report(report_file) is False
