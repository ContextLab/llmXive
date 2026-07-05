"""
Unit tests for the bias-adjustment module (T046).

These tests verify that the bias adjustment logic correctly:
1. Computes domain weights.
2. Calculates domain-weighted prevalence.
3. Detects domain violations (any domain > 30%).
4. Ensures no domain exceeds the 30% proportion threshold in the balanced subsample.
"""

import pytest
import json
import tempfile
import os
from pathlib import Path
from typing import List, Dict, Any

# Import the functions from the bias_adjustment module
from code.src.audit.bias_adjustment import (
    compute_domain_weights,
    compute_domain_weighted_prevalence,
    check_domain_violation,
    run_bias_adjustment
)
from code.src.audit.domain_subsample import (
    load_audit_records_from_json,
    create_balanced_subsample,
    calculate_domain_proportions
)

# Helper to create mock audit records
def create_mock_records(domains: List[str], inconsistent_flags: List[bool]) -> List[Dict[str, Any]]:
    """
    Creates a list of mock audit records for testing.
    Each record has a 'domain' and an 'is_inconsistent' flag.
    """
    records = []
    for i, (domain, is_inconsistent) in enumerate(zip(domains, inconsistent_flags)):
        records.append({
            "id": f"record_{i}",
            "domain": domain,
            "is_inconsistent": is_inconsistent,
            "url": f"https://{domain}/test{i}",
            "p_value_reported": 0.05,
            "p_value_reconstructed": 0.06,
            "effect_size_reported": 0.1,
            "effect_size_reconstructed": 0.11,
            "sample_size_control": 100,
            "sample_size_treatment": 100,
            "baseline_rate": 0.2,
            "variant_rate": 0.22
        })
    return records

class TestComputeDomainWeights:
    def test_compute_weights_basic(self):
        """Test that domain weights are computed correctly based on counts."""
        domains = ["domain_a", "domain_a", "domain_b", "domain_c", "domain_c", "domain_c"]
        weights = compute_domain_weights(domains)

        # Total records = 6
        # domain_a: 2/6 = 0.333...
        # domain_b: 1/6 = 0.166...
        # domain_c: 3/6 = 0.5

        assert abs(weights["domain_a"] - (2/6)) < 1e-6
        assert abs(weights["domain_b"] - (1/6)) < 1e-6
        assert abs(weights["domain_c"] - (3/6)) < 1e-6

    def test_compute_weights_empty(self):
        """Test that an empty list returns an empty dict."""
        weights = compute_domain_weights([])
        assert weights == {}

class TestComputeDomainWeightedPrevalence:
    def test_weighted_prevalence_calculation(self):
        """Test that weighted prevalence is calculated correctly."""
        records = create_mock_records(
            domains=["domain_a", "domain_a", "domain_b"],
            inconsistent_flags=[True, False, True]
        )
        # domain_a: 1 inconsistent out of 2 -> 0.5
        # domain_b: 1 inconsistent out of 1 -> 1.0
        # Weights: domain_a (2/3), domain_b (1/3)
        # Expected: (0.5 * 2/3) + (1.0 * 1/3) = 1/3 + 1/3 = 2/3 approx 0.666...

        weights = {"domain_a": 2/3, "domain_b": 1/3}
        prevalence = compute_domain_weighted_prevalence(records, weights)

        assert abs(prevalence - (2/3)) < 1e-6

    def test_weighted_prevalence_no_inconsistencies(self):
        """Test that weighted prevalence is 0 if no inconsistencies."""
        records = create_mock_records(
            domains=["domain_a", "domain_b"],
            inconsistent_flags=[False, False]
        )
        weights = {"domain_a": 0.5, "domain_b": 0.5}
        prevalence = compute_domain_weighted_prevalence(records, weights)
        assert prevalence == 0.0

class TestCheckDomainViolation:
    def test_violation_detected(self):
        """Test that a violation is detected when a domain exceeds 30%."""
        proportions = {"domain_a": 0.4, "domain_b": 0.3, "domain_c": 0.3}
        has_violation, violating_domains = check_domain_violation(proportions, threshold=0.3)

        assert has_violation is True
        assert "domain_a" in violating_domains

    def test_no_violation(self):
        """Test that no violation is detected when all domains are <= 30%."""
        proportions = {"domain_a": 0.25, "domain_b": 0.25, "domain_c": 0.25, "domain_d": 0.25}
        has_violation, violating_domains = check_domain_violation(proportions, threshold=0.3)

        assert has_violation is False
        assert violating_domains == []

    def test_boundary_case(self):
        """Test boundary case where domain is exactly 30%."""
        proportions = {"domain_a": 0.3, "domain_b": 0.7}
        # Threshold is 0.3, so 0.3 is NOT a violation (must be > 0.3)
        has_violation, violating_domains = check_domain_violation(proportions, threshold=0.3)
        
        # Note: The requirement says "no domain exceeds 30%", implying > 0.3 is bad.
        # If the implementation uses >=, this might differ, but logically > 0.3 is the violation.
        # Assuming strict inequality for "exceeds".
        assert has_violation is False

class TestBalancedSubsampleProportions:
    def test_balanced_subsample_respects_threshold(self):
        """
        Test that creating a balanced subsample ensures no domain exceeds 30% proportion.
        This is the core requirement for T046.
        """
        # Create a dataset where domain_a is dominant (60%)
        # Total 100 records: 60 domain_a, 20 domain_b, 20 domain_c
        domains = ["domain_a"] * 60 + ["domain_b"] * 20 + ["domain_c"] * 20
        inconsistent_flags = [True] * 100 # All inconsistent for simplicity
        records = create_mock_records(domains, inconsistent_flags)

        # Create a balanced subsample
        # The subsample should limit the dominant domain so no single domain > 30%
        # If we target a max of 30%, and we have 3 domains, we might cap each at 33% or similar
        # The function create_balanced_subsample should handle the logic to ensure <= 30%
        
        # Let's assume the subsample logic caps the max proportion to 0.3
        # We need to verify the result of create_balanced_subsample
        
        subsample = create_balanced_subsample(records, max_domain_proportion=0.3)
        
        # Calculate proportions in the subsample
        subsample_domains = [r["domain"] for r in subsample]
        proportions = calculate_domain_proportions(subsample_domains)
        
        # Verify no domain exceeds 0.3
        for domain, prop in proportions.items():
            assert prop <= 0.3, f"Domain {domain} has proportion {prop} which exceeds 0.3"
        
        # Verify the subsample is not empty
        assert len(subsample) > 0

    def test_balanced_subsample_with_equal_domains(self):
        """Test that balanced subsample works correctly when domains are already balanced."""
        domains = ["domain_a"] * 20 + ["domain_b"] * 20 + ["domain_c"] * 20
        inconsistent_flags = [True] * 60
        records = create_mock_records(domains, inconsistent_flags)

        subsample = create_balanced_subsample(records, max_domain_proportion=0.3)
        
        # In this case, the subsample might be the full set or a subset, 
        # but proportions should remain <= 0.3 (which they are, 1/3 = 0.333... > 0.3)
        # Wait, 1/3 is 0.333, which IS > 0.3. So if we have 3 equal domains, 
        # we cannot have a valid subsample with max 0.3 unless we drop some domains entirely?
        # Or the logic is: if we have 3 domains, max proportion is 1/3. If 1/3 > 0.3, 
        # then we must reduce the count of the largest domains until the condition is met?
        # Actually, if we have 3 domains, the minimum possible max proportion is 1/3.
        # If the requirement is strictly <= 0.3, and we have 3 domains, it's impossible 
        # to have all 3 represented with equal weight without exceeding 0.3.
        # The function should likely drop domains or reduce counts such that the max is <= 0.3.
        # Let's check the logic: if we have 3 domains, and we want max <= 0.3, 
        # we can't have all 3. We might have to drop one or reduce counts significantly.
        # However, for the test, we just need to verify the condition holds.
        
        subsample_domains = [r["domain"] for r in subsample]
        proportions = calculate_domain_proportions(subsample_domains)
        
        for domain, prop in proportions.items():
            assert prop <= 0.3, f"Domain {domain} has proportion {prop} which exceeds 0.3"

class TestRunBiasAdjustment:
    def test_run_bias_adjustment_integration(self):
        """Integration test for the run_bias_adjustment function."""
        # Create a temporary file for the input
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            records = create_mock_records(
                domains=["domain_a"] * 60 + ["domain_b"] * 20 + ["domain_c"] * 20,
                inconsistent_flags=[True] * 100
            )
            json.dump(records, f)
            input_path = f.name

        try:
            # Run the bias adjustment
            output_dir = tempfile.mkdtemp()
            result = run_bias_adjustment(input_path, output_dir)
            
            # Verify the result contains the expected keys
            assert "bias_adjusted_prevalence" in result
            assert "domain_weights" in result
            assert "subsample_path" in result
            
            # Verify the subsample file exists and has correct proportions
            subsample_path = result["subsample_path"]
            assert os.path.exists(subsample_path)
            
            with open(subsample_path, 'r') as f:
                subsample_records = json.load(f)
            
            subsample_domains = [r["domain"] for r in subsample_records]
            proportions = calculate_domain_proportions(subsample_domains)
            
            for domain, prop in proportions.items():
                assert prop <= 0.3, f"Domain {domain} has proportion {prop} which exceeds 0.3"
        finally:
            os.unlink(input_path)
            # Cleanup temp output files if needed (run_bias_adjustment might create them)
            # For now, we just clean the input file.