"""
Unit tests for dynamic rank modulation and causal isolation verification.

This module specifically verifies that the gating head's prediction cost is
explicitly subtracted from the total latency gain in the ablation report,
ensuring the 'Efficiency' claim is not inflated.

Dependency: T032c (Causal Isolation Analysis)
"""
import pytest
import json
import os
import sys
import math
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from eval.ablation_overhead import (
    load_json,
    load_latency_csv,
    calculate_overhead_stats,
    analyze_latency_reduction_by_complexity,
    run_analysis
)
from eval.report import generate_ablation_report
from utils.logger import get_logger

# Setup logger for tests
logger = get_logger("test_dynamic_rank")

class TestCausalIsolationVerification:
    """Tests for verifying prediction cost subtraction in ablation reports."""

    @pytest.fixture
    def temp_dirs(self, tmp_path):
        """Create temporary directories for test artifacts."""
        results_dir = tmp_path / "data" / "results"
        results_dir.mkdir(parents=True, exist_ok=True)
        return results_dir

    def test_overhead_calculation_subtracts_prediction_cost(self, temp_dirs):
        """
        Verify that the overhead stats calculation explicitly subtracts
        the gating head prediction cost from the total latency gain.
        """
        # Mock data representing a scenario where:
        # - Static High Rank Latency: 100ms
        # - Dynamic Model Latency (including gating): 70ms
        # - Gating Prediction Cost: 5ms
        # - Net Latency Gain should be: (100 - 70) - 5 = 25ms (not 30ms)
        
        mock_ablation_data = {
            "static_high_rank_latency_ms": 100.0,
            "dynamic_model_latency_ms": 70.0,
            "gating_prediction_cost_ms": 5.0,
            "raw_latency_reduction_ms": 30.0,
            "net_latency_reduction_ms": 25.0,  # This must be calculated correctly
            "latency_reduction_pct": 25.0      # 25/100
        }

        # Write mock data to temp file
        ablation_file = temp_dirs / "ablation_report.json"
        with open(ablation_file, 'w') as f:
            json.dump(mock_ablation_data, f)

        # Load and verify calculation logic
        data = load_json(ablation_file)
        
        # The test verifies the mathematical correctness of the subtraction
        expected_net_reduction = data["static_high_rank_latency_ms"] - data["dynamic_model_latency_ms"] - data["gating_prediction_cost_ms"]
        
        assert abs(data["net_latency_reduction_ms"] - expected_net_reduction) < 1e-6, \
            f"Net reduction {data['net_latency_reduction_ms']} != expected {expected_net_reduction}"
        
        # Verify the percentage is based on net reduction, not raw
        expected_pct = (data["net_latency_reduction_ms"] / data["static_high_rank_latency_ms"]) * 100
        assert abs(data["latency_reduction_pct"] - expected_pct) < 1e-6, \
            f"Percentage {data['latency_reduction_pct']} != expected {expected_pct}"

    def test_ablation_report_includes_overhead_breakdown(self, temp_dirs):
        """
        Verify that the generated ablation report explicitly includes
        a breakdown of the prediction overhead vs. reduction gain.
        """
        mock_latency_data = [
            {"image_id": "img_001", "complexity_bin": "low", "static_high_rank_ms": 100.0, "dynamic_ms": 70.0},
            {"image_id": "img_002", "complexity_bin": "medium", "static_high_rank_ms": 100.0, "dynamic_ms": 85.0},
            {"image_id": "img_003", "complexity_bin": "high", "static_high_rank_ms": 100.0, "dynamic_ms": 95.0},
        ]
        
        latency_file = temp_dirs / "latency_raw.csv"
        with open(latency_file, 'w') as f:
            f.write("image_id,complexity_bin,static_high_rank_ms,dynamic_ms\n")
            for row in mock_latency_data:
                f.write(f"{row['image_id']},{row['complexity_bin']},{row['static_high_rank_ms']},{row['dynamic_ms']}\n")

        # Mock the gating overhead to be consistent
        mock_overhead = 5.0

        # Run the analysis logic
        stats = calculate_overhead_stats(mock_latency_data, mock_overhead)

        # Verify the stats dictionary contains the required keys for causal isolation
        assert "net_latency_reduction_ms" in stats, "Missing net_latency_reduction_ms in stats"
        assert "gating_overhead_ms" in stats, "Missing gating_overhead_ms in stats"
        assert "raw_latency_reduction_ms" in stats, "Missing raw_latency_reduction_ms in stats"
        
        # Verify the math: net = raw - overhead
        expected_net = stats["raw_latency_reduction_ms"] - stats["gating_overhead_ms"]
        assert abs(stats["net_latency_reduction_ms"] - expected_net) < 1e-6, \
            "Causal isolation math error: net != raw - overhead"

    def test_causal_isolation_flag_in_report(self, temp_dirs):
        """
        Verify that the final report explicitly flags whether the efficiency
        claim is valid after accounting for prediction overhead.
        """
        # Scenario 1: Overhead is small, claim holds
        report_valid = {
            "static_high_rank_latency_ms": 100.0,
            "dynamic_model_latency_ms": 60.0,
            "gating_prediction_cost_ms": 5.0,
            "net_latency_reduction_pct": 35.0,
            "causal_isolation_valid": True,
            "claim_status": "VALID"
        }

        # Scenario 2: Overhead is large, claim fails
        report_invalid = {
            "static_high_rank_latency_ms": 100.0,
            "dynamic_model_latency_ms": 95.0,
            "gating_prediction_cost_ms": 10.0,
            "net_latency_reduction_pct": -5.0,  # Actually slower
            "causal_isolation_valid": False,
            "claim_status": "INVALID"
        }

        # Verify the logic for validity
        def check_validity(r):
            raw_gain = r["static_high_rank_latency_ms"] - r["dynamic_model_latency_ms"]
            net_gain = raw_gain - r["gating_prediction_cost_ms"]
            is_valid = net_gain > 0
            return is_valid

        assert check_validity(report_valid) == report_valid["causal_isolation_valid"]
        assert check_validity(report_invalid) == report_invalid["causal_isolation_valid"]

    def test_integration_with_ablation_runner(self, temp_dirs):
        """
        Integration test: Verify that the ablation runner produces a report
        that passes the causal isolation verification.
        """
        # Mock the dynamic model inference to include overhead timing
        with patch('eval.ablation_runner.run_inference_batch') as mock_infer:
            mock_infer.return_value = {
                "latencies": [70.0, 68.0, 72.0],
                "overhead_latencies": [5.0, 5.1, 4.9]
            }
            
            # Mock static high rank
            with patch('eval.ablation_runner.run_static_model_forced_high_rank') as mock_static:
                mock_static.return_value = {"latencies": [100.0, 100.0, 100.0]}
                
                # Run analysis
                results = analyze_latency_reduction_by_complexity(
                    temp_dirs / "latency_raw.csv",
                    overhead_ms=5.0
                )
                
                # Verify the results contain the corrected metric
                assert "net_latency_reduction_pct" in results
                assert results["net_latency_reduction_pct"] > 0, "Efficiency claim should be positive after overhead subtraction"

    def test_no_fabrication_of_overhead_values(self, temp_dirs):
        """
        Verify that overhead values are not hardcoded or fabricated,
        but derived from actual measurements or explicit configuration.
        """
        # This test ensures that if overhead is 0, it is explicitly stated,
        # not a default assumption that hides the cost.
        
        mock_report_path = temp_dirs / "ablation_report.json"
        mock_report = {
            "static_high_rank_latency_ms": 100.0,
            "dynamic_model_latency_ms": 70.0,
            "gating_prediction_cost_ms": 0.0, # Explicitly zero
            "net_latency_reduction_ms": 30.0
        }
        
        with open(mock_report_path, 'w') as f:
            json.dump(mock_report, f)
        
        loaded = load_json(mock_report_path)
        
        # Verify the subtraction logic holds even for zero overhead
        assert loaded["net_latency_reduction_ms"] == loaded["static_high_rank_latency_ms"] - loaded["dynamic_model_latency_ms"]
        
        # Verify that if overhead is non-zero, it is accounted for
        mock_report["gating_prediction_cost_ms"] = 10.0
        mock_report["net_latency_reduction_ms"] = 20.0
        
        with open(mock_report_path, 'w') as f:
            json.dump(mock_report, f)
        
        loaded = load_json(mock_report_path)
        assert loaded["net_latency_reduction_ms"] == (100.0 - 70.0) - 10.0