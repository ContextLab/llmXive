import pytest
import os
import json
import csv
from pathlib import Path
import numpy as np
from scipy import stats

# Import functions from analyzer
# Assuming analyzer.py is in code/ and we are running from root
import sys
sys.path.insert(0, 'code')
from analyzer import apply_bonferroni_correction, apply_holm_bonferroni_correction, generate_corrected_pvalues_csv, pair_llm_human_results

class TestHolmBonferroni:
    def test_holm_bonferroni_basic(self):
        """Test Holm-Bonferroni with simple p-values."""
        p_values = [0.04, 0.01, 0.03]
        results = apply_holm_bonferroni_correction(p_values, alpha=0.05)
        
        # Sorted: 0.01, 0.03, 0.04
        # n=3
        # i=0 (0.01): adj = 3 * 0.01 = 0.03. Sig? 0.03 < 0.05 -> True
        # i=1 (0.03): adj = max(2 * 0.03, 0.03) = 0.06. Sig? 0.06 < 0.05 -> False
        # i=2 (0.04): adj = max(1 * 0.04, 0.06) = 0.06. Sig? 0.06 < 0.05 -> False
        
        # Map back to original order: [0.04, 0.01, 0.03]
        # 0.04 -> index 2 in sorted -> adj 0.06
        # 0.01 -> index 0 in sorted -> adj 0.03
        # 0.03 -> index 1 in sorted -> adj 0.06
        
        expected_order = [0.06, 0.03, 0.06]
        expected_sig = [False, True, False]
        
        for i, (res, exp_adj, exp_sig) in enumerate(zip(results, expected_order, expected_sig)):
            assert abs(res[1] - exp_adj) < 1e-6, f"Index {i}: expected adj {exp_adj}, got {res[1]}"
            assert res[2] == exp_sig, f"Index {i}: expected sig {exp_sig}, got {res[2]}"

    def test_holm_bonferroni_empty(self):
        """Test with empty list."""
        results = apply_holm_bonferroni_correction([])
        assert results == []

    def test_holm_bonferroni_all_significant(self):
        """Test with very small p-values."""
        p_values = [0.001, 0.002, 0.003]
        results = apply_holm_bonferroni_correction(p_values, alpha=0.05)
        for _, _, is_sig in results:
            assert is_sig == True

class TestBonferroni:
    def test_bonferroni_basic(self):
        """Test Bonferroni correction."""
        p_values = [0.04, 0.03, 0.02]
        results = apply_bonferroni_correction(p_values, alpha=0.05)
        
        # n=3
        # 0.04 * 3 = 0.12
        # 0.03 * 3 = 0.09
        # 0.02 * 3 = 0.06
        # All > 0.05 -> False
        
        for _, corr_p, is_sig in results:
            assert is_sig == False
            assert 0.05 < corr_p <= 1.0

class TestGenerateCorrectedPvalues:
    def test_csv_generation(self, tmp_path):
        """Test that the CSV is generated with correct columns."""
        # Mock paired data
        paired_data = [
            {'task_id': '1', 'diff_line': 0.1, 'diff_branch': 0.2},
            {'task_id': '2', 'diff_line': -0.1, 'diff_branch': -0.2},
            {'task_id': '3', 'diff_line': 0.05, 'diff_branch': 0.05},
        ]
        
        output_file = tmp_path / "corrected_pvalues.csv"
        generate_corrected_pvalues_csv(paired_data, str(output_file), alpha=0.05)
        
        assert output_file.exists()
        
        with open(output_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        assert len(rows) > 0
        assert 'subgroup' in rows[0]
        assert 'original_p_value' in rows[0]
        assert 'corrected_p_value' in rows[0]
        assert 'is_significant' in rows[0]

    def test_exclusion_logic(self, tmp_path):
        """Test that sensitivity analysis is not included (by design of this function)."""
        # This test verifies that the function doesn't accidentally include sensitivity thresholds.
        # Since generate_corrected_pvalues_csv only processes line/branch diffs,
        # we just verify the output doesn't have sensitivity rows.
        paired_data = [
            {'task_id': '1', 'diff_line': 0.1, 'diff_branch': None},
        ]
        
        output_file = tmp_path / "corrected_pvalues.csv"
        generate_corrected_pvalues_csv(paired_data, str(output_file))
        
        with open(output_file, 'r') as f:
            content = f.read()
        
        assert 'sensitivity' not in content.lower()