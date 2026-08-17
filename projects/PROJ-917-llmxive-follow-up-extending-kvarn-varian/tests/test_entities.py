import pytest
import numpy as np
from entities import AttentionMatrix, ScalingFactor, SimulationRun
from datetime import datetime

class TestAttentionMatrix:
    def test_valid_creation(self):
        """Test creation of a valid AttentionMatrix."""
        matrix = np.random.rand(128, 128)
        am = AttentionMatrix(
            matrix=matrix,
            mean=0.5,
            variance=0.1,
            sparsity=0.05,
            outlier_magnitude=2.0
        )
        assert am.matrix.shape == (128, 128)
        assert am.mean == 0.5
        assert am.variance == 0.1
        assert am.sparsity == 0.05
        assert am.outlier_magnitude == 2.0

    def test_invalid_shape(self):
        """Test that invalid matrix shape raises ValueError."""
        matrix = np.random.rand(64, 64)
        with pytest.raises(ValueError, match="128x128"):
            AttentionMatrix(
                matrix=matrix,
                mean=0.5,
                variance=0.1,
                sparsity=0.05,
                outlier_magnitude=2.0
            )

    def test_invalid_sparsity(self):
        """Test that sparsity outside [0, 1] raises ValueError."""
        matrix = np.random.rand(128, 128)
        with pytest.raises(ValueError, match="Sparsity"):
            AttentionMatrix(
                matrix=matrix,
                mean=0.5,
                variance=0.1,
                sparsity=1.5,
                outlier_magnitude=2.0
            )

    def test_non_finite_mean(self):
        """Test that non-finite mean raises ValueError."""
        matrix = np.random.rand(128, 128)
        with pytest.raises(ValueError, match="finite"):
            AttentionMatrix(
                matrix=matrix,
                mean=float('nan'),
                variance=0.1,
                sparsity=0.05,
                outlier_magnitude=2.0
            )

    def test_serialization_round_trip(self):
        """Test to_dict and from_dict preserve data."""
        matrix = np.random.rand(128, 128)
        original = AttentionMatrix(
            matrix=matrix,
            mean=0.5,
            variance=0.1,
            sparsity=0.05,
            outlier_magnitude=2.0
        )
        data = original.to_dict()
        restored = AttentionMatrix.from_dict(data)
        
        np.testing.assert_array_equal(restored.matrix, original.matrix)
        assert restored.mean == original.mean
        assert restored.variance == original.variance
        assert restored.sparsity == original.sparsity
        assert restored.outlier_magnitude == original.outlier_magnitude

class TestScalingFactor:
    def test_creation(self):
        sf = ScalingFactor(value=1.5, derivation_method="sinkhorn")
        assert sf.value == 1.5
        assert sf.derivation_method == "sinkhorn"

    def test_serialization(self):
        sf = ScalingFactor(value=1.5, derivation_method="sinkhorn")
        data = sf.to_dict()
        assert data['value'] == 1.5
        assert data['derivation_method'] == "sinkhorn"
        
        restored = ScalingFactor.from_dict(data)
        assert restored.value == sf.value
        assert restored.derivation_method == sf.derivation_method

class TestSimulationRun:
    def test_accumulated_kl_consistency(self):
        """Test that accumulated_kl is recalculated correctly in __post_init__."""
        sequence = [0.1, 0.2, 0.3]
        run = SimulationRun(
            run_id="test_001",
            seed=42,
            steps=3,
            kl_divergence_sequence=sequence,
            timing_metrics={"total": 1.0},
            accumulated_kl=100.0, # Intentionally wrong
            start_time="2023-01-01T00:00:00",
            end_time="2023-01-01T00:01:00",
            method="static"
        )
        assert run.accumulated_kl == pytest.approx(sum(sequence))

    def test_empty_sequence(self):
        """Test handling of empty sequence."""
        run = SimulationRun(
            run_id="test_002",
            seed=43,
            steps=0,
            kl_divergence_sequence=[],
            timing_metrics={"total": 0.0},
            accumulated_kl=0.0,
            start_time="2023-01-01T00:00:00",
            end_time="2023-01-01T00:00:00",
            method="static"
        )
        assert run.accumulated_kl == 0.0

    def test_to_json_and_from_json(self, tmp_path):
        """Test JSON serialization and deserialization."""
        run = SimulationRun(
            run_id="test_003",
            seed=44,
            steps=2,
            kl_divergence_sequence=[0.1, 0.2],
            timing_metrics={"total": 0.5},
            accumulated_kl=0.3,
            start_time="2023-01-01T00:00:00",
            end_time="2023-01-01T00:00:01",
            method="static",
            config_snapshot={"lr": 0.01}
        )
        
        file_path = tmp_path / "run.json"
        run.to_json(file_path)
        
        assert file_path.exists()
        
        loaded = SimulationRun.from_json(file_path)
        assert loaded.run_id == run.run_id
        assert loaded.seed == run.seed
        assert loaded.steps == run.steps
        assert loaded.kl_divergence_sequence == run.kl_divergence_sequence
        assert loaded.accumulated_kl == run.accumulated_kl
        assert loaded.config_snapshot == run.config_snapshot
