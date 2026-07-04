"""
Unit tests for the reporting module (T028).
Verifies that findings are correctly framed as 'predictive accuracy' 
and 'associational uncertainty'.
"""
import pytest
import os
import sys
from pathlib import Path
import tempfile
import shutil

# Add code to path if running directly
if 'code' not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from src.evaluation.reporting import (
    format_predictive_accuracy_statement,
    format_associational_uncertainty_statement,
    generate_final_report
)

class TestPredictiveAccuracyFraming:
    def test_basic_accuracy_statement(self):
        metrics = {'rmse': 2.5, 'mae': 1.8}
        statement = format_predictive_accuracy_statement(metrics)
        
        assert "predictive accuracy" in statement.lower()
        assert "RMSE" in statement
        assert "MAE" in statement
        assert "2.5" in statement
        assert "1.8" in statement

    def test_dm_test_statement(self):
        metrics = {'rmse': 2.0, 'mae': 1.5, 'dm_p_value': 0.03}
        statement = format_predictive_accuracy_statement(metrics)
        
        assert "Diebold-Mariano" in statement
        assert "significantly different" in statement.lower() or "no statistically significant difference" in statement.lower()
        
        metrics_high_p = {'rmse': 2.0, 'mae': 1.5, 'dm_p_value': 0.20}
        statement_high_p = format_predictive_accuracy_statement(metrics_high_p)
        assert "no statistically significant difference" in statement_high_p.lower()

class TestAssociationalUncertaintyFraming:
    def test_basic_uncertainty_statement(self):
        statement = format_associational_uncertainty_statement(coverage=0.92, ci_width=3.5, model_type="Bayesian Model")
        
        assert "associational uncertainty" in statement.lower()
        assert "credible intervals" in statement.lower()
        assert "92.0" in statement
        assert "3.5" in statement
        assert "variance" in statement.lower()

    def test_under_coverage_warning(self):
        statement = format_associational_uncertainty_statement(coverage=0.85, ci_width=3.5, model_type="Bayesian Model")
        assert "underestimating associational uncertainty" in statement.lower()

class TestFinalReportGeneration:
    def test_report_structure(self):
        freq_metrics = {'rmse': 2.0, 'mae': 1.5}
        bayes_metrics = {'rmse': 1.8, 'mae': 1.4, 'coverage': 0.94, 'ci_width': 4.0}
        
        report = generate_final_report(
            frequentist_metrics=freq_metrics,
            bayesian_metrics=bayes_metrics,
            dm_results=None
        )
        
        assert "PREDICTIVE ACCURACY ANALYSIS" in report
        assert "ASSOCIATIONAL UNCERTAINTY ANALYSIS" in report
        assert "predictive accuracy" in report.lower()
        assert "associational uncertainty" in report.lower()
        assert "2.0" in report
        assert "1.8" in report

    def test_report_file_creation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_report.txt"
            freq_metrics = {'rmse': 2.0, 'mae': 1.5}
            bayes_metrics = {'rmse': 1.8, 'mae': 1.4, 'coverage': 0.94, 'ci_width': 4.0}
            
            generate_final_report(
                frequentist_metrics=freq_metrics,
                bayesian_metrics=bayes_metrics,
                dm_results=[],
                output_path=output_path
            )
            
            assert output_path.exists()
            with open(output_path, 'r') as f:
                content = f.read()
                assert "PREDICTIVE ACCURACY ANALYSIS" in content
                assert "ASSOCIATIONAL UNCERTAINTY ANALYSIS" in content

    def test_dm_results_in_report(self):
        dm_results = [
            {'model_a': 'Model A', 'model_b': 'Model B', 'statistic': 2.5, 'p_value': 0.01}
        ]
        freq_metrics = {'rmse': 2.0, 'mae': 1.5}
        bayes_metrics = {'rmse': 1.8, 'mae': 1.4, 'coverage': 0.94, 'ci_width': 4.0}
        
        report = generate_final_report(
            frequentist_metrics=freq_metrics,
            bayesian_metrics=bayes_metrics,
            dm_results=dm_results
        )
        
        assert "Diebold-Mariano" in report
        assert "Model A" in report
        assert "Model B" in report
        assert "0.01" in report