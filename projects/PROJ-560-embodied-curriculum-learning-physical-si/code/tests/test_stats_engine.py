import pytest
import numpy as np
from typing import List, Tuple
from src.stats_engine import (
    run_t_test,
    calculate_effect_size,
    calculate_confidence_interval,
    apply_bonferroni_correction,
    check_collinearity,
    calculate_power,
    frame_inference,
    aggregate_stats_results,
    write_partial_results,
    finalize_results
)
import pandas as pd
import os
import json
import tempfile
from pathlib import Path

class TestPowerAnalysis:
    def test_calculate_power(self):
        effect_size = 0.5
        n1 = 50
        n2 = 50
        result = calculate_power(effect_size, n1, n2)
        assert "achieved_power" in result
        assert "is_underpowered" in result
        assert result["sample_sizes"]["n1"] == n1
        assert result["sample_sizes"]["n2"] == n2

    def test_t_test_underpowered(self):
        # Test with small sample size
        effect_size = 0.5
        n1 = 10
        n2 = 10
        result = calculate_power(effect_size, n1, n2)
        assert result["is_underpowered"] is True

class TestTTest:
    def test_welch_t_test(self):
        group1 = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        group2 = np.array([2.0, 3.0, 4.0, 5.0, 6.0])
        t_stat, p_val = run_t_test(group1, group2, equal_var=False)
        assert isinstance(t_stat, float)
        assert isinstance(p_val, float)
        assert 0 <= p_val <= 1

    def test_student_t_test(self):
        group1 = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        group2 = np.array([2.0, 3.0, 4.0, 5.0, 6.0])
        t_stat, p_val = run_t_test(group1, group2, equal_var=True)
        assert isinstance(t_stat, float)
        assert isinstance(p_val, float)

class TestEffectSize:
    def test_cohen_d(self):
        group1 = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        group2 = np.array([2.0, 3.0, 4.0, 5.0, 6.0])
        d = calculate_effect_size(group1, group2)
        assert isinstance(d, float)

    def test_cohen_d_zero_std(self):
        group1 = np.array([1.0, 1.0, 1.0])
        group2 = np.array([1.0, 1.0, 1.0])
        d = calculate_effect_size(group1, group2)
        assert d == 0.0

class TestBonferroni:
    def test_bonferroni_correction(self):
        p_val = 0.01
        n_concepts = 5
        corrected = apply_bonferroni_correction(p_val, n_concepts)
        assert corrected == min(0.01 * 5, 1.0)

    def test_bonferroni_cap(self):
        p_val = 0.1
        n_concepts = 20
        corrected = apply_bonferroni_correction(p_val, n_concepts)
        assert corrected == 1.0

class TestCollinearity:
    def test_collinearity_detection(self):
        df = pd.DataFrame({
            "x1": [1, 2, 3, 4, 5],
            "x2": [2, 4, 6, 8, 10],  # Perfect correlation
            "x3": [1, 3, 2, 4, 3]
        })
        result = check_collinearity(df, ["x1", "x2", "x3"])
        assert result["detected"] is True
        assert "x1_x2" in result["high_correlations"]
        assert abs(result["high_correlations"]["x1_x2"]) > 0.8

    def test_no_collinearity(self):
        df = pd.DataFrame({
            "x1": [1, 2, 3, 4, 5],
            "x2": [5, 1, 4, 2, 3],
            "x3": [3, 5, 1, 4, 2]
        })
        result = check_collinearity(df, ["x1", "x2", "x3"])
        assert result["detected"] is False

class TestFraming:
    def test_framing_statement(self):
        statement = frame_inference()
        assert "associational" in statement
        assert "causal inference" not in statement.lower() or "no causal inference" in statement.lower()

class TestAggregateResults:
    def test_aggregate_stats_results(self):
        ancova = {"f_stat": 5.0, "p_val": 0.01}
        t_stat = 2.5
        p_val = 0.02
        corr_p = 0.05
        eff_size = 0.5
        ci = (0.1, 0.9)
        power = {"achieved_power": 0.9, "is_underpowered": False}
        collin = {"detected": False, "high_correlations": {}}
        
        result = aggregate_stats_results(
            ancova_results=ancova,
            t_statistic=t_stat,
            p_value=p_val,
            corrected_p_value=corr_p,
            effect_size_cohen_d=eff_size,
            confidence_interval=ci,
            power_analysis=power,
            collinearity_diagnostics=collin
        )
        
        assert result["ancova_results"] == ancova
        assert result["t_statistic"] == t_stat
        assert result["p_value"] == p_val
        assert result["corrected_p_value"] == corr_p
        assert result["effect_size_cohen_d"] == eff_size
        assert result["confidence_interval"] == list(ci)
        assert result["power_analysis"] == power
        assert result["collinearity_diagnostics"] == collin
        assert "inference_framing" in result

class TestWritePartialResults:
    def test_write_partial_results(self):
        ancova = {"f_stat": 5.0, "p_val": 0.01}
        t_stat = 2.5
        p_val = 0.02
        corr_p = 0.05
        eff_size = 0.5
        ci = (0.1, 0.9)
        power = {"achieved_power": 0.9, "is_underpowered": False}
        collin = {"detected": False, "high_correlations": {}}
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_results.json")
            result_path = write_partial_results(
                ancova_results=ancova,
                t_statistic=t_stat,
                p_value=p_val,
                corrected_p_value=corr_p,
                effect_size_cohen_d=eff_size,
                confidence_interval=ci,
                power_analysis=power,
                collinearity_diagnostics=collin,
                output_path=output_path
            )
            
            assert os.path.exists(result_path)
            with open(result_path, 'r') as f:
                data = json.load(f)
            
            assert "ancova_results" in data
            assert "t_statistic" in data
            assert "p_value" in data
            assert "corrected_p_value" in data
            assert "effect_size_cohen_d" in data
            assert "confidence_interval" in data
            assert "inference_framing" in data
            assert "power_analysis" in data
            assert "collinearity_diagnostics" in data

class TestFinalizeResults:
    def test_finalize_results(self):
        ancova = {"f_stat": 5.0, "p_val": 0.01}
        t_stat = 2.5
        p_val = 0.02
        corr_p = 0.05
        eff_size = 0.5
        ci = (0.1, 0.9)
        power = {"achieved_power": 0.9, "is_underpowered": False}
        collin = {"detected": False, "high_correlations": {}}
        
        with tempfile.TemporaryDirectory() as tmpdir:
            partial_path = os.path.join(tmpdir, "partial.json")
            final_path = os.path.join(tmpdir, "final.json")
            
            # Write partial first
            write_partial_results(
                ancova_results=ancova,
                t_statistic=t_stat,
                p_value=p_val,
                corrected_p_value=corr_p,
                effect_size_cohen_d=eff_size,
                confidence_interval=ci,
                power_analysis=power,
                collinearity_diagnostics=collin,
                output_path=partial_path
            )
            
            sensitivity = [{"threshold_value": 0.05, "n_participants_retained": 100, "effect_size_cohen_d": 0.5, "robustness_flag": True}]
            robustness_warning = False
            
            result_path = finalize_results(
                partial_results_path=partial_path,
                sensitivity_analysis=sensitivity,
                robustness_warning=robustness_warning,
                output_path=final_path
            )
            
            assert os.path.exists(result_path)
            with open(result_path, 'r') as f:
                data = json.load(f)
            
            assert "sensitivity_analysis" in data
            assert data["sensitivity_analysis"] == sensitivity
            assert data["robustness_warning"] == robustness_warning
            # Check that original keys are preserved
            assert "ancova_results" in data
            assert "t_statistic" in data
            assert "p_value" in data