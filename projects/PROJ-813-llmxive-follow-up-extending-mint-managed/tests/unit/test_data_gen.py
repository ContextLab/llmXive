"""
Unit tests for data generation module.
"""

import numpy as np
import pandas as pd
import pytest
from pathlib import Path
import tempfile
import sys

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.data.generate_adapters import (
    generate_clustered_base_weights,
    generate_adapter_weights,
    generate_adapters
)
from utils.seeds import set_global_seed
from data.schema import validate_adapter_dataframe
from utils.exceptions import SimulationError


class TestClusteredBaseWeights:
    """Tests for cluster base weight generation."""

    def test_clustered_weights_shape(self):
        """Test that generated weights have correct shape."""
        rng = set_global_seed(42)
        num_clusters = 5
        weight_dim = 128

        weights = generate_clustered_base_weights(num_clusters, weight_dim, rng)

        assert weights.shape == (num_clusters, weight_dim)

    def test_clustered_weights_normalized(self):
        """Test that cluster centers are normalized."""
        rng = set_global_seed(42)
        num_clusters = 3
        weight_dim = 64

        weights = generate_clustered_base_weights(num_clusters, weight_dim, rng)

        norms = np.linalg.norm(weights, axis=1)
        assert np.allclose(norms, 1.0, atol=1e-6)

    def test_clustered_weights_deterministic(self):
        """Test that same seed produces same results."""
        num_clusters = 4
        weight_dim = 32

        rng1 = set_global_seed(123)
        weights1 = generate_clustered_base_weights(num_clusters, weight_dim, rng1)

        rng2 = set_global_seed(123)
        weights2 = generate_clustered_base_weights(num_clusters, weight_dim, rng2)

        assert np.array_equal(weights1, weights2)


class TestAdapterWeights:
    """Tests for individual adapter weight generation."""

    def test_adapter_weights_shapes(self):
        """Test that A and B matrices have correct shapes."""
        rng = set_global_seed(42)
        base_weights = generate_clustered_base_weights(2, 128, rng)

        adapter_id = 0
        rank = 16
        cluster_assignment = 0

        a_matrix, b_matrix = generate_adapter_weights(
            adapter_id, rank, cluster_assignment, base_weights, rng
        )

        assert a_matrix.shape == (rank, 128)
        assert b_matrix.shape == (128, rank)

    def test_adapter_weights_cluster_correlation(self):
        """Test that adapters in same cluster have correlated weights."""
        rng = set_global_seed(42)
        base_weights = generate_clustered_base_weights(2, 64, rng)

        # Generate two adapters in same cluster
        a1, b1 = generate_adapter_weights(0, 8, 0, base_weights, rng)
        rng2 = set_global_seed(42)
        base_weights2 = generate_clustered_base_weights(2, 64, rng2)
        a2, b2 = generate_adapter_weights(1, 8, 0, base_weights2, rng2)

        # Same cluster should have similar A matrix structure
        correlation = np.corrcoef(a1.flatten(), a2.flatten())[0, 1]
        assert correlation > 0.5  # Should be positively correlated

    def test_adapter_weights_different_clusters(self):
        """Test that adapters in different clusters have less correlation."""
        rng = set_global_seed(42)
        base_weights = generate_clustered_base_weights(3, 64, rng)

        # Generate adapters in different clusters
        a1, b1 = generate_adapter_weights(0, 8, 0, base_weights, rng)
        rng2 = set_global_seed(42)
        base_weights2 = generate_clustered_base_weights(3, 64, rng2)
        a2, b2 = generate_adapter_weights(1, 8, 2, base_weights2, rng2)

        correlation = np.corrcoef(a1.flatten(), a2.flatten())[0, 1]
        # Different clusters should have lower correlation than same cluster
        assert correlation < 0.9


class TestGenerateAdapters:
    """Tests for the main adapter generation function."""

    def test_generate_adapters_creates_clustered_weights(self):
        """Test that generated adapters have clustered weight structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_adapters.parquet"

            df = generate_adapters(
                num_adapters=100,
                rank_min=1,
                rank_max=32,
                num_clusters=5,
                weight_dim=64,
                seed=42,
                output_path=str(output_path)
            )

            # Check DataFrame structure
            assert len(df) == 100
            assert 'adapter_id' in df.columns
            assert 'rank' in df.columns
            assert 'cluster_id' in df.columns
            assert 'a_matrix' in df.columns
            assert 'b_matrix' in df.columns

            # Check rank distribution
            assert df['rank'].min() >= 1
            assert df['rank'].max() <= 32

            # Check cluster distribution (should be roughly uniform)
            cluster_counts = df['cluster_id'].value_counts()
            assert len(cluster_counts) == 5

    def test_generate_adapters_schema_validation(self):
        """Test that generated data passes schema validation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_adapters.parquet"

            df = generate_adapters(
                num_adapters=50,
                rank_min=1,
                rank_max=16,
                num_clusters=3,
                weight_dim=32,
                seed=42,
                output_path=str(output_path)
            )

            # Should not raise exception
            validate_adapter_dataframe(df)

    def test_generate_adapters_invalid_rank(self):
        """Test that invalid rank range raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_adapters.parquet"

            with pytest.raises(SimulationError):
                generate_adapters(
                    num_adapters=10,
                    rank_min=0,  # Invalid: must be >= 1
                    rank_max=16,
                    num_clusters=3,
                    weight_dim=32,
                    seed=42,
                    output_path=str(output_path)
                )

    def test_generate_adapters_deterministic(self):
        """Test that same seed produces same results."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path1 = Path(tmpdir) / "test_adapters1.parquet"
            output_path2 = Path(tmpdir) / "test_adapters2.parquet"

            df1 = generate_adapters(
                num_adapters=20,
                rank_min=1,
                rank_max=16,
                num_clusters=3,
                weight_dim=32,
                seed=42,
                output_path=str(output_path1)
            )

            df2 = generate_adapters(
                num_adapters=20,
                rank_min=1,
                rank_max=16,
                num_clusters=3,
                weight_dim=32,
                seed=42,
                output_path=str(output_path2)
            )

            # Compare ranks and cluster assignments
            assert list(df1['rank']) == list(df2['rank'])
            assert list(df1['cluster_id']) == list(df2['cluster_id'])

    def test_generate_adapters_sparsity_computation(self):
        """Test that sparsity is computed correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_adapters.parquet"

            df = generate_adapters(
                num_adapters=10,
                rank_min=1,
                rank_max=8,
                num_clusters=2,
                weight_dim=16,
                seed=42,
                output_path=str(output_path)
            )

            assert 'sparsity' in df.columns
            assert all(0 <= s <= 1 for s in df['sparsity'])

    def test_generate_adapters_file_created(self):
        """Test that output file is actually created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_adapters.parquet"

            generate_adapters(
                num_adapters=10,
                rank_min=1,
                rank_max=8,
                num_clusters=2,
                weight_dim=16,
                seed=42,
                output_path=str(output_path)
            )

            assert output_path.exists()
            assert output_path.stat().st_size > 0

            # Verify we can read it back
            df_read = pd.read_parquet(output_path)
            assert len(df_read) == 10