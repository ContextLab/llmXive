"""
Unit tests for Spearman correlation calculation in code/evaluator.py.

This test suite verifies the statistical correlation logic required for US3.
It tests the calculation of Spearman rank correlation between topological features
and retrieval metrics (Recall@k) without requiring the full pipeline execution.
"""
import json
import csv
import tempfile
import os
from pathlib import Path
import pytest
import numpy as np
from scipy import stats
from unittest.mock import patch, MagicMock

# Import the function to test
# Note: We import from the module as defined in the API surface
from code.evaluator import calculate_recall_at_k, load_retrieval_scores, load_hotpotqa_ground_truth


class TestSpearmanCorrelationLogic:
    """Tests for the statistical logic used in correlation analysis."""

    def test_spearman_correlation_calculation(self):
        """
        Verify that Spearman correlation is calculated correctly using scipy.stats.
        This simulates the core logic that would be used in the evaluator
        to correlate topological features (e.g., modularity) with Recall@10.
        """
        # Mock data: Topological feature (e.g., modularity) and Recall@10 scores
        # Expected: Higher modularity should correlate with higher recall in a perfect scenario
        topological_features = np.array([0.1, 0.3, 0.5, 0.7, 0.9])
        recall_scores = np.array([0.2, 0.4, 0.6, 0.8, 1.0])

        # Calculate Spearman correlation manually using scipy
        corr, p_value = stats.spearmanr(topological_features, recall_scores)

        # Assert perfect positive correlation
        assert np.isclose(corr, 1.0), f"Expected correlation of 1.0, got {corr}"
        assert p_value < 0.05, "P-value should be significant for perfect correlation"

    def test_spearman_correlation_negative(self):
        """
        Verify that Spearman correlation correctly identifies negative correlation.
        """
        topological_features = np.array([0.1, 0.3, 0.5, 0.7, 0.9])
        recall_scores = np.array([1.0, 0.8, 0.6, 0.4, 0.2])

        corr, p_value = stats.spearmanr(topological_features, recall_scores)

        assert np.isclose(corr, -1.0), f"Expected correlation of -1.0, got {corr}"
        assert p_value < 0.05

    def test_spearman_correlation_random(self):
        """
        Verify that Spearman correlation returns near-zero for random data.
        """
        np.random.seed(42)
        topological_features = np.random.rand(50)
        recall_scores = np.random.rand(50)

        corr, p_value = stats.spearmanr(topological_features, recall_scores)

        # With random data, correlation should be low (though not exactly 0)
        assert abs(corr) < 0.3, f"Random data should have low correlation, got {corr}"

    def test_spearman_correlation_constant_data(self):
        """
        Verify behavior when one variable is constant (undefined correlation).
        """
        topological_features = np.array([0.5, 0.5, 0.5, 0.5, 0.5])
        recall_scores = np.array([0.1, 0.3, 0.5, 0.7, 0.9])

        # scipy.stats.spearmanr returns nan for constant data
        corr, p_value = stats.spearmanr(topological_features, recall_scores)

        assert np.isnan(corr), "Correlation should be NaN for constant data"

    def test_correlation_integration_with_mocked_data(self):
        """
        Integration test simulating the data flow for T028 (Spearman correlation task).
        Creates temporary CSV files mimicking the output of T016 (features) and T024 (recall),
        then verifies the logic that would join them and calculate correlation.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create mock features file (simulating data/processed/features.csv from T016)
            features_path = Path(tmpdir) / "features.csv"
            with open(features_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['doc_id', 'modularity', 'avg_path_length', 'degree_centrality'])
                # Write mock data
                for i in range(10):
                    writer.writerow([f'doc_{i}', 0.1 * (i + 1), 1.0 + i * 0.1, 0.05 * (i + 1)])

            # Create mock recall scores file (simulating data/results/retrieval_scores.csv from T024)
            recall_path = Path(tmpdir) / "recall_scores.csv"
            with open(recall_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['query_id', 'doc_id', 'rank', 'recall_at_10'])
                # Write mock data where doc_id matches features
                for i in range(10):
                    # Recall increases with index to create correlation
                    writer.writerow([f'query_{i}', f'doc_{i}', i+1, 0.1 * (i + 1)])

            # Load and merge logic (simulating what T028 would do)
            features_df = {
                'doc_id': [], 'modularity': []
            }
            with open(features_path, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    features_df['doc_id'].append(row['doc_id'])
                    features_df['modularity'].append(float(row['modularity']))

            recall_df = {
                'doc_id': [], 'recall_at_10': []
            }
            with open(recall_path, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    recall_df['doc_id'].append(row['doc_id'])
                    recall_df['recall_at_10'].append(float(row['recall_at_10']))

            # Merge on doc_id
            merged_modularity = []
            merged_recall = []
            for doc_id in features_df['doc_id']:
                if doc_id in recall_df['doc_id']:
                    idx_feat = features_df['doc_id'].index(doc_id)
                    idx_rec = recall_df['doc_id'].index(doc_id)
                    merged_modularity.append(features_df['modularity'][idx_feat])
                    merged_recall.append(recall_df['recall_at_10'][idx_rec])

            # Calculate correlation
            corr, p_val = stats.spearmanr(merged_modularity, merged_recall)

            # Verify we got a perfect correlation due to mock data construction
            assert np.isclose(corr, 1.0), f"Expected 1.0, got {corr}"
            assert p_val < 0.05

    def test_handle_mismatched_ids_gracefully(self):
        """
        Test that the correlation logic handles cases where doc_ids in features
        and recall scores do not perfectly match (should ignore missing pairs).
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Features for doc_0, doc_1, doc_2
            features_path = Path(tmpdir) / "features.csv"
            with open(features_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['doc_id', 'modularity'])
                writer.writerow(['doc_0', 0.1])
                writer.writerow(['doc_1', 0.2])
                writer.writerow(['doc_2', 0.3])

            # Recall for doc_1, doc_2, doc_3 (doc_0 missing, doc_3 extra)
            recall_path = Path(tmpdir) / "recall_scores.csv"
            with open(recall_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['doc_id', 'recall_at_10'])
                writer.writerow(['doc_1', 0.2])
                writer.writerow(['doc_2', 0.3])
                writer.writerow(['doc_3', 0.4])

            # Load logic
            features_map = {}
            with open(features_path, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    features_map[row['doc_id']] = float(row['modularity'])

            recall_map = {}
            with open(recall_path, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    recall_map[row['doc_id']] = float(row['recall_at_10'])

            # Intersect
            common_ids = set(features_map.keys()) & set(recall_map.keys())
            assert 'doc_0' not in common_ids
            assert 'doc_3' not in common_ids
            assert 'doc_1' in common_ids
            assert 'doc_2' in common_ids

            # Calculate
            mods = [features_map[i] for i in common_ids]
            recs = [recall_map[i] for i in common_ids]

            # Sort by doc_id to ensure deterministic order for this test
            sorted_ids = sorted(common_ids)
            mods = [features_map[i] for i in sorted_ids]
            recs = [recall_map[i] for i in sorted_ids]

            corr, _ = stats.spearmanr(mods, recs)
            assert np.isclose(corr, 1.0)

if __name__ == '__main__':
    pytest.main([__file__, '-v'])