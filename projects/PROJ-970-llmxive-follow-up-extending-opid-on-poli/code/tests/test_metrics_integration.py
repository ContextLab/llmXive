"""
Integration tests for the metrics module.
These tests verify the interaction between different metric functions.
"""
import os
import tempfile
import pytest
import csv

try:
    from code.utils.metrics import (
        calculate_success_rate,
        calculate_action_entropy,
        calculate_checksum,
        aggregate_success_rates_by_tier_threshold,
        write_success_rate_summary,
        log_data_hygiene
    )
except ImportError:
    from utils.metrics import (
        calculate_success_rate,
        calculate_action_entropy,
        calculate_checksum,
        aggregate_success_rates_by_tier_threshold,
        write_success_rate_summary,
        log_data_hygiene
    )


class TestMetricsPipeline:
    """Test the complete pipeline from episode results to summary."""

    def test_full_pipeline(self):
        """Test the complete pipeline: generate data -> aggregate -> write -> verify."""
        # Simulate episode results
        episode_results = []
        for tier in [1, 2, 3]:
            for threshold in [0.0, 0.5, 1.0]:
                for i in range(10):
                    episode_results.append({
                        'tier': tier,
                        'threshold': threshold,
                        'success': 1 if i < 7 else 0  # 70% success rate
                    })

        # Aggregate
        aggregated = aggregate_success_rates_by_tier_threshold(episode_results)

        # Write to CSV
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            temp_path = f.name

        try:
            write_success_rate_summary(aggregated, temp_path)

            # Verify file exists and has correct structure
            assert os.path.exists(temp_path)

            with open(temp_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            # Should have 9 rows (3 tiers * 3 thresholds)
            assert len(rows) == 9

            # Verify checksum can be calculated
            checksum = calculate_checksum(temp_path)
            assert len(checksum) == 64

            # Verify hygiene log
            hygiene_log = log_data_hygiene(temp_path, "Integration test summary")
            assert hygiene_log['checksum'] == checksum
        finally:
            os.unlink(temp_path)

    def test_success_rate_consistency(self):
        """Verify success rate calculation is consistent across aggregation."""
        # Create deterministic test data
        results = [
            {'tier': 1, 'threshold': 0.5, 'success': 1},
            {'tier': 1, 'threshold': 0.5, 'success': 1},
            {'tier': 1, 'threshold': 0.5, 'success': 0},
        ]

        aggregated = aggregate_success_rates_by_tier_threshold(results)
        result = aggregated[(1, 0.5)]

        # Manually calculate expected
        assert result.successes == 2
        assert result.total == 3
        assert abs(result.rate - 2/3) < 1e-6

    def test_entropy_in_pipeline(self):
        """Test that entropy calculation works in a simulated pipeline context."""
        # Simulate action sequences from multiple episodes
        all_entropies = []

        for episode_id in range(5):
            # Each episode has a sequence of actions
            actions = [i % 3 for i in range(20)]  # Cyclic actions
            entropy = calculate_action_entropy(actions)
            all_entropies.append(entropy)

        # All should be the same for deterministic cyclic pattern
        assert all(abs(e - all_entropies[0]) < 1e-6 for e in all_entropies)

        # Verify entropy value is reasonable
        # 3 actions in uniform cycle -> entropy should be log2(3)
        import math
        expected = math.log2(3)
        assert abs(all_entropies[0] - expected) < 0.01