"""
Unit tests for shared entities: AttentionTrajectory, ScalingFactor, SimulationRun.
"""

import pytest
import numpy as np
import json
from pathlib import Path
import tempfile
import os

# Import entities
from shared.entities import AttentionTrajectory, ScalingFactor, SimulationRun


class TestAttentionTrajectory:
    """Tests for AttentionTrajectory entity."""
    
    def test_creation_basic(self):
        """Test basic trajectory creation."""
        mean = np.array([0.1, 0.2, 0.3])
        var = np.array([0.01, 0.02, 0.03])
        skew = np.array([0.1, 0.1, 0.1])
        kurt = np.array([3.0, 3.0, 3.0])
        
        trajectory = AttentionTrajectory(
            trajectory_id="test_001",
            mean=mean,
            var=var,
            skew=skew,
            kurt=kurt,
            scaling_factor=1.5,
            drift_type="linear",
            drift_params={"slope": 0.1},
            seed=42
        )
        
        assert trajectory.trajectory_id == "test_001"
        assert trajectory.num_steps == 3
        assert trajectory.scaling_factor == 1.5
        assert trajectory.drift_type == "linear"
        assert trajectory.seed == 42
    
    def test_creation_array_conversion(self):
        """Test that lists are converted to numpy arrays."""
        trajectory = AttentionTrajectory(
            trajectory_id="test_002",
            mean=[0.1, 0.2, 0.3],
            var=[0.01, 0.02, 0.03],
            skew=[0.1, 0.1, 0.1],
            kurt=[3.0, 3.0, 3.0],
            scaling_factor=1.0
        )
        
        assert isinstance(trajectory.mean, np.ndarray)
        assert isinstance(trajectory.var, np.ndarray)
        assert isinstance(trajectory.skew, np.ndarray)
        assert isinstance(trajectory.kurt, np.ndarray)
    
    def test_numerical_stability_epsilon_floor(self):
        """Test that near-zero variance gets epsilon floor applied."""
        trajectory = AttentionTrajectory(
            trajectory_id="test_003",
            mean=[0.1, 0.2, 0.3],
            var=[1e-10, 0.02, 0.03],  # First value is very small
            skew=[0.1, 0.1, 0.1],
            kurt=[3.0, 3.0, 3.0],
            scaling_factor=1.0
        )
        
        # First variance should be floored to 1e-8
        assert trajectory.var[0] >= 1e-8
    
    def test_invalid_scaling_factor(self):
        """Test that negative scaling factor raises error."""
        with pytest.raises(ValueError, match="Scaling factor must be positive"):
            AttentionTrajectory(
                trajectory_id="test_004",
                mean=[0.1, 0.2],
                var=[0.01, 0.02],
                skew=[0.1, 0.1],
                kurt=[3.0, 3.0],
                scaling_factor=-1.0
            )
    
    def test_array_length_mismatch(self):
        """Test that mismatched array lengths raise error."""
        with pytest.raises(ValueError, match="All moment arrays must have the same length"):
            AttentionTrajectory(
                trajectory_id="test_005",
                mean=[0.1, 0.2, 0.3],
                var=[0.01, 0.02],  # Different length
                skew=[0.1, 0.1, 0.1],
                kurt=[3.0, 3.0, 3.0],
                scaling_factor=1.0
            )
    
    def test_to_dict_and_from_dict(self):
        """Test serialization and deserialization."""
        original = AttentionTrajectory(
            trajectory_id="test_006",
            mean=np.array([0.1, 0.2, 0.3]),
            var=np.array([0.01, 0.02, 0.03]),
            skew=np.array([0.1, 0.1, 0.1]),
            kurt=np.array([3.0, 3.0, 3.0]),
            scaling_factor=1.5,
            drift_type="exponential",
            drift_params={"rate": 0.05},
            seed=123
        )
        
        data = original.to_dict()
        restored = AttentionTrajectory.from_dict(data)
        
        assert restored.trajectory_id == original.trajectory_id
        assert np.allclose(restored.mean, original.mean)
        assert np.allclose(restored.var, original.var)
        assert np.allclose(restored.skew, original.skew)
        assert np.allclose(restored.kurt, original.kurt)
        assert restored.scaling_factor == original.scaling_factor
        assert restored.drift_type == original.drift_type
        assert restored.drift_params == original.drift_params
        assert restored.seed == original.seed
    
    def test_save_and_load(self):
        """Test saving and loading to/from file."""
        trajectory = AttentionTrajectory(
            trajectory_id="test_007",
            mean=np.array([0.1, 0.2, 0.3]),
            var=np.array([0.01, 0.02, 0.03]),
            skew=np.array([0.1, 0.1, 0.1]),
            kurt=np.array([3.0, 3.0, 3.0]),
            scaling_factor=1.2,
            drift_type="sinusoidal",
            drift_params={"amplitude": 0.1, "frequency": 0.5}
        )
        
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "trajectory.json"
            
            # Save
            trajectory.save(filepath)
            assert filepath.exists()
            
            # Load
            loaded = AttentionTrajectory.load(filepath)
            assert loaded.trajectory_id == trajectory.trajectory_id
            assert np.allclose(loaded.mean, trajectory.mean)
    
    def test_save_creates_directories(self):
        """Test that save creates parent directories if needed."""
        trajectory = AttentionTrajectory(
            trajectory_id="test_008",
            mean=np.array([0.1]),
            var=np.array([0.01]),
            skew=np.array([0.1]),
            kurt=np.array([3.0]),
            scaling_factor=1.0
        )
        
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "subdir" / "deep" / "trajectory.json"
            trajectory.save(filepath)
            assert filepath.exists()

class TestScalingFactor:
    """Tests for ScalingFactor entity."""
    
    def test_creation_basic(self):
        """Test basic scaling factor creation."""
        factor = ScalingFactor(
            factor_id="sf_001",
            trajectory_id="traj_001",
            value=1.5,
            method="sinkhorn",
            step_index=5,
            confidence=0.95
        )
        
        assert factor.factor_id == "sf_001"
        assert factor.trajectory_id == "traj_001"
        assert factor.value == 1.5
        assert factor.method == "sinkhorn"
        assert factor.step_index == 5
        assert factor.confidence == 0.95
    
    def test_creation_without_step_index(self):
        """Test creation without step index (trajectory-level)."""
        factor = ScalingFactor(
            factor_id="sf_002",
            trajectory_id="traj_002",
            value=2.0,
            method="closed_form"
        )
        
        assert factor.step_index is None
    
    def test_invalid_value(self):
        """Test that negative value raises error."""
        with pytest.raises(ValueError, match="Scaling factor value must be positive"):
            ScalingFactor(
                factor_id="sf_003",
                trajectory_id="traj_003",
                value=-1.0
            )
    
    def test_invalid_confidence(self):
        """Test that confidence outside [0, 1] raises error."""
        with pytest.raises(ValueError, match="Confidence must be between 0 and 1"):
            ScalingFactor(
                factor_id="sf_004",
                trajectory_id="traj_004",
                value=1.0,
                confidence=1.5
            )
    
    def test_to_dict_and_from_dict(self):
        """Test serialization and deserialization."""
        original = ScalingFactor(
            factor_id="sf_005",
            trajectory_id="traj_005",
            value=1.75,
            method="mlp",
            step_index=10,
            confidence=0.88
        )
        
        data = original.to_dict()
        restored = ScalingFactor.from_dict(data)
        
        assert restored.factor_id == original.factor_id
        assert restored.trajectory_id == original.trajectory_id
        assert restored.value == original.value
        assert restored.method == original.method
        assert restored.step_index == original.step_index
        assert restored.confidence == original.confidence
    
    def test_default_confidence(self):
        """Test that confidence defaults to None."""
        factor = ScalingFactor(
            factor_id="sf_006",
            trajectory_id="traj_006",
            value=1.0
        )
        
        assert factor.confidence is None

class TestSimulationRun:
    """Tests for SimulationRun entity."""
    
    def test_creation_basic(self):
        """Test basic simulation run creation."""
        config = {"num_steps": 100, "method": "static_prior"}
        run = SimulationRun(
            run_id="sim_001",
            config=config,
            method="static_prior"
        )
        
        assert run.run_id == "sim_001"
        assert run.config == config
        assert run.method == "static_prior"
        assert run.status == "pending"
        assert run.num_steps == 0
    
    def test_invalid_status(self):
        """Test that invalid status raises error."""
        with pytest.raises(ValueError, match="Invalid status"):
            SimulationRun(
                run_id="sim_002",
                config={},
                status="invalid_status"
            )
    
    def test_update_status(self):
        """Test status update."""
        run = SimulationRun(run_id="sim_003", config={})
        
        run.update_status("success")
        assert run.status == "success"
        assert run.end_time is not None
        
        run.update_status("failed", "Test error")
        assert run.status == "failed"
        assert run.error_message == "Test error"
    
    def test_add_step_metric(self):
        """Test adding step metrics."""
        run = SimulationRun(run_id="sim_004", config={})
        
        run.add_step_metric({"step": 0, "kl": 0.1})
        run.add_step_metric({"step": 1, "kl": 0.2})
        
        assert run.num_steps == 2
        assert len(run.step_metrics) == 2
        assert run.step_metrics[0]["step"] == 0
    
    def test_finalize(self):
        """Test finalizing a run."""
        run = SimulationRun(run_id="sim_005", config={})
        
        run.finalize(
            accumulated_kl_divergence=0.5,
            accumulated_error=0.3,
            avg_latency_per_token=1.2,
            optimization_overhead=0.1
        )
        
        assert run.status == "success"
        assert run.accumulated_kl_divergence == 0.5
        assert run.accumulated_error == 0.3
        assert run.avg_latency_per_token == 1.2
        assert run.optimization_overhead == 0.1
        assert run.end_time is not None
    
    def test_to_dict_and_from_dict(self):
        """Test serialization and deserialization."""
        original = SimulationRun(
            run_id="sim_006",
            config={"num_steps": 100},
            accumulated_kl_divergence=0.4,
            accumulated_error=0.2,
            num_steps=10,
            avg_latency_per_token=1.5,
            optimization_overhead=0.05,
            method="sinkhorn",
            status="success"
        )
        original.step_metrics = [{"step": i, "kl": 0.1} for i in range(10)]
        
        data = original.to_dict()
        restored = SimulationRun.from_dict(data)
        
        assert restored.run_id == original.run_id
        assert restored.config == original.config
        assert restored.accumulated_kl_divergence == original.accumulated_kl_divergence
        assert restored.accumulated_error == original.accumulated_error
        assert restored.num_steps == original.num_steps
        assert restored.avg_latency_per_token == original.avg_latency_per_token
        assert restored.optimization_overhead == original.optimization_overhead
        assert restored.method == original.method
        assert restored.status == original.status
        assert len(restored.step_metrics) == len(original.step_metrics)
    
    def test_save_and_load(self):
        """Test saving and loading to/from file."""
        run = SimulationRun(
            run_id="sim_007",
            config={"method": "test"},
            accumulated_kl_divergence=0.3,
            accumulated_error=0.1,
            num_steps=5,
            avg_latency_per_token=1.0,
            optimization_overhead=0.02,
            method="test_method",
            status="success"
        )
        run.step_metrics = [{"step": i, "kl": 0.06} for i in range(5)]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "run.json"
            
            # Save
            run.save(filepath)
            assert filepath.exists()
            
            # Load
            loaded = SimulationRun.load(filepath)
            assert loaded.run_id == run.run_id
            assert loaded.accumulated_kl_divergence == run.accumulated_kl_divergence
            assert len(loaded.step_metrics) == len(run.step_metrics)
    
    def test_file_not_found(self):
        """Test loading from non-existent file raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "nonexistent.json"
            
            with pytest.raises(FileNotFoundError):
                SimulationRun.load(filepath)