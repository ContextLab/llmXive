"""
Unit tests for statistical_analysis.py
"""
import os
import sys
import csv
import tempfile
import logging
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from collections import defaultdict

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.evaluation.statistical_analysis import (
    load_quality_metrics,
    load_correctness_results,
    chi_square_test,
    anova_test,
    bonferroni_correction,
    run_statistical_analysis,
    save_analysis_results
)

logger = logging.getLogger(__name__)


class TestLoadQualityMetrics:
    def test_load_quality_metrics_valid(self):
        """Test loading a valid quality metrics CSV."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            writer = csv.DictWriter(f, fieldnames=['input_id', 'prompt_condition', 'complexity', 'loc'])
            writer.writeheader()
            writer.writerow({'input_id': '1', 'prompt_condition': 'zero_shot', 'complexity': '5.0', 'loc': '20'})
            writer.writerow({'input_id': '2', 'prompt_condition': 'few_shot', 'complexity': '3.0', 'loc': '15'})
            f.flush()
            
            result = load_quality_metrics(Path(f.name))
            
            assert 'zero_shot' in result
            assert 'few_shot' in result
            assert len(result['zero_shot']) == 1
            assert result['zero_shot'][0]['complexity'] == 5.0
            assert result['few_shot'][0]['loc'] == 15
        
        os.unlink(f.name)

    def test_load_quality_metrics_missing_file(self):
        """Test loading from a non-existent file."""
        result = load_quality_metrics(Path('/nonexistent/file.csv'))
        assert result == {}


class TestLoadCorrectnessResults:
    def test_load_correctness_results_valid(self):
        """Test loading a valid correctness results CSV."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            writer = csv.DictWriter(f, fieldnames=['input_id', 'prompt_condition', 'passed'])
            writer.writeheader()
            writer.writerow({'input_id': '1', 'prompt_condition': 'zero_shot', 'passed': '1'})
            writer.writerow({'input_id': '2', 'prompt_condition': 'zero_shot', 'passed': '0'})
            writer.writerow({'input_id': '3', 'prompt_condition': 'few_shot', 'passed': '1'})
            f.flush()
            
            result = load_correctness_results(Path(f.name))
            
            assert 'zero_shot' in result
            assert 'few_shot' in result
            assert len(result['zero_shot']) == 2
            assert result['zero_shot'][0]['passed'] == 1
            assert result['zero_shot'][1]['passed'] == 0
            assert result['few_shot'][0]['passed'] == 1
        
        os.unlink(f.name)

    def test_load_correctness_results_missing_file(self):
        """Test loading from a non-existent file."""
        result = load_correctness_results(Path('/nonexistent/file.csv'))
        assert result == {}


class TestChiSquareTest:
    @pytest.mark.skipif(not hasattr(__import__('scipy', fromlist=['stats']), 'stats'), reason="scipy not installed")
    def test_chi_square_test_basic(self):
        """Test Chi-square test with basic data."""
        data = {
            'condition_a': [{'passed': 1}, {'passed': 1}, {'passed': 0}],
            'condition_b': [{'passed': 1}, {'passed': 0}, {'passed': 0}]
        }
        
        result = chi_square_test(data)
        
        assert 'statistic' in result
        assert 'p_value' in result
        assert 'contingency_table' in result
        assert len(result['contingency_table']) == 2
        assert len(result['contingency_table'][0]) == 2 # [failed, passed]

    def test_chi_square_test_insufficient_conditions(self):
        """Test Chi-square test with only one condition."""
        data = {
            'condition_a': [{'passed': 1}]
        }
        
        result = chi_square_test(data)
        assert 'error' in result
        assert 'Insufficient conditions' in result['error']


class TestAnovaTest:
    @pytest.mark.skipif(not hasattr(__import__('scipy', fromlist=['stats']), 'stats'), reason="scipy not installed")
    def test_anova_test_basic(self):
        """Test ANOVA test with basic data."""
        data = {
            'condition_a': [{'complexity': 5.0}, {'complexity': 6.0}, {'complexity': 5.5}],
            'condition_b': [{'complexity': 3.0}, {'complexity': 3.5}, {'complexity': 4.0}]
        }
        
        result = anova_test(data, 'complexity')
        
        assert 'f_statistic' in result
        assert 'p_value' in result
        assert 'group_means' in result
        assert 'condition_a' in result['group_means']
        assert 'condition_b' in result['group_means']

    def test_anova_test_insufficient_conditions(self):
        """Test ANOVA test with only one condition."""
        data = {
            'condition_a': [{'complexity': 5.0}]
        }
        
        result = anova_test(data, 'complexity')
        assert 'error' in result
        assert 'Insufficient conditions' in result['error']


class TestBonferroniCorrection:
    def test_bonferroni_correction_basic(self):
        """Test Bonferroni correction with basic p-values."""
        p_values = [0.01, 0.05, 0.10]
        
        result = bonferroni_correction(p_values)
        
        assert 'corrected_p_values' in result
        assert 'adjusted_alpha' in result
        assert 'significant' in result
        assert result['num_tests'] == 3
        # Adjusted alpha should be 0.05 / 3
        assert abs(result['adjusted_alpha'] - 0.05/3) < 1e-6
        
        # First p-value (0.01 * 3 = 0.03) should be significant if < 0.0166
        # Actually: 0.03 < 0.0166 is False. So none might be significant.
        # Let's check logic: 0.01 * 3 = 0.03. 0.05/3 = 0.0166. 0.03 > 0.0166 -> not significant.
        # 0.05 * 3 = 0.15. 0.10 * 3 = 0.30.
        assert all(not s for s in result['significant'])

    def test_bonferroni_correction_empty(self):
        """Test Bonferroni correction with empty list."""
        result = bonferroni_correction([])
        assert 'error' in result

class TestSaveAnalysisResults:
    def test_save_analysis_results_creates_file(self):
        """Test that save_analysis_results creates a valid CSV."""
        results = {
            "chi_square": {"p_value": 0.03, "statistic": 4.5, "degrees_of_freedom": 1},
            "anova_complexity": {"p_value": 0.04, "f_statistic": 3.2},
            "anova_loc": {"p_value": 0.06, "f_statistic": 2.8},
            "bonferroni": {"adjusted_alpha": 0.016, "num_tests": 3},
            "summary": {}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            output_path = Path(f.name)
        
        save_analysis_results(results, output_path)
        
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 3 # chi_square, anova_complexity, anova_loc
            assert rows[0]['test_type'] == 'chi_square'
            assert rows[1]['test_type'] == 'anova'
            assert rows[1]['metric'] == 'complexity'
        
        os.unlink(output_path)