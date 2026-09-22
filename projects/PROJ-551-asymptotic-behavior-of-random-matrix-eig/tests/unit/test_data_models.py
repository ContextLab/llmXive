"""
Unit tests for the data models (T006).
"""
import pytest
from data_models import PerturbationConfig, SimulationRun

def test_perturbation_config_diagonal():
    """Test creation of a diagonal perturbation config."""
    cfg = PerturbationConfig(
        theta=2.5,
        rank=1,
        support_density=1.0,
        type="diagonal"
    )
    assert cfg.theta == 2.5
    assert cfg.rank == 1
    assert cfg.type == "diagonal"
    assert cfg.support_density == 1.0

def test_perturbation_config_block_sparse():
    """Test creation of a block-sparse perturbation config."""
    cfg = PerturbationConfig(
        theta=1.5,
        rank=2,
        support_density=0.5,
        type="block-sparse"
    )
    assert cfg.type == "block-sparse"
    assert cfg.support_density == 0.5

def test_perturbation_config_random_sparse():
    """Test creation of a random sparse perturbation config."""
    cfg = PerturbationConfig(
        theta=3.0,
        rank=1,
        support_density=0.1,
        type="random sparse"
    )
    assert cfg.type == "random sparse"
    assert cfg.support_density == 0.1

def test_perturbation_config_invalid_type():
    """Test that invalid sparsity type raises ValueError."""
    with pytest.raises(ValueError):
        PerturbationConfig(
            theta=1.0,
            rank=1,
            support_density=0.5,
            type="invalid_type"
        )

def test_perturbation_config_invalid_density():
    """Test that invalid support density raises ValueError."""
    with pytest.raises(ValueError):
        PerturbationConfig(
            theta=1.0,
            rank=1,
            support_density=1.5,
            type="diagonal"
        )

def test_simulation_run_creation():
    """Test creation of a SimulationRun."""
    pert = PerturbationConfig(
        theta=2.5,
        rank=1,
        support_density=1.0,
        type="diagonal"
    )
    run = SimulationRun(
        run_id="run-001",
        N=1000,
        seed=42,
        theta=2.5,
        eigenvalues=[2.1, 1.9, 1.8, 1.5],
        outlier_flag=True,
        perturbation_config=pert
    )
    assert run.run_id == "run-001"
    assert run.N == 1000
    assert run.outlier_flag is True
    assert len(run.eigenvalues) == 4

def test_simulation_run_serialization():
    """Test JSON serialization and deserialization of SimulationRun."""
    pert = PerturbationConfig(
        theta=2.5,
        rank=1,
        support_density=1.0,
        type="diagonal"
    )
    run = SimulationRun(
        run_id="run-002",
        N=500,
        seed=123,
        theta=2.5,
        eigenvalues=[2.05, 1.95],
        outlier_flag=True,
        perturbation_config=pert
    )
    
    json_str = run.to_json()
    assert isinstance(json_str, str)
    
    # Deserialize
    run_restored = SimulationRun.from_dict(run.to_dict())
    assert run_restored.run_id == run.run_id
    assert run_restored.eigenvalues == run.eigenvalues
    assert run_restored.outlier_flag == run.outlier_flag
    assert run_restored.perturbation_config.theta == run.perturbation_config.theta

def test_simulation_run_without_perturbation():
    """Test that SimulationRun can be created without perturbation config."""
    run = SimulationRun(
        run_id="run-003",
        N=100,
        seed=999,
        theta=0.0,
        eigenvalues=[1.0, 0.9],
        outlier_flag=False,
        perturbation_config=None
    )
    assert run.perturbation_config is None