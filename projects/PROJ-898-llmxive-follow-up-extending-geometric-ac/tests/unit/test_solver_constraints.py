import pytest
import numpy as np
import torch
import json
import os
import sys
import tempfile
import logging

# Add project root to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from symbolic_solver import SymbolicSolver, ConstraintMatrix, TimeoutError
from config import load_config, ExperimentConfig, SolverConfig, TopologyConfig
from gfm_wrapper import GFMWrapper
from latent_drift import LatentDriftDetector, load_reference_stats
from utils import set_deterministic_seed

logger = logging.getLogger(__name__)

@pytest.fixture
def temp_config():
    """Create a temporary config file for testing."""
    config_data = {
        "topology": {
            "counts": [5, 10],
            "seed": 42
        },
        "solver": {
            "timeout_seconds": 30,
            "max_iterations": 1000,
            "tolerance": 1e-6
        },
        "experiment": {
            "trial_count": 10,
            "sim_fps": 60,
            "target_zone": {
                "center": [0.0, 0.0, 0.5],
                "radius": 0.1
            }
        }
    }
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        import yaml
        yaml.dump(config_data, f)
        return f.name

@pytest.fixture
def mock_latent_stats():
    """Mock reference statistics for drift detection."""
    stats = {
        "mean": [0.0] * 32,
        "cov_inv": [[1.0 if i == j else 0.0 for j in range(32)] for i in range(32)]
    }
    return stats

@pytest.fixture
def sample_latent_vector():
    """Sample latent vector for testing."""
    return np.random.randn(32).astype(np.float32)

class TestSymbolicSolverConstraints:
    """Unit tests for solver constraint satisfaction and numerical stability."""

    def test_constraint_matrix_initialization(self):
        """Test that constraint matrix initializes correctly with valid dimensions."""
        dim = 64
        n_constraints = 10
        matrix = ConstraintMatrix(dim, n_constraints)
        
        assert matrix.constraint_matrix.shape == (n_constraints, dim)
        assert matrix.weights.shape == (n_constraints,)
        assert matrix.bias.shape == (n_constraints,)
        assert matrix.dim == dim
        assert matrix.n_constraints == n_constraints

    def test_constraint_violation_loss_computation(self, sample_latent_vector):
        """Test that constraint violation loss is computed correctly."""
        dim = 32
        n_constraints = 5
        matrix = ConstraintMatrix(dim, n_constraints)
        
        # Initialize weights and bias with known values
        matrix.constraint_matrix = np.random.randn(n_constraints, dim).astype(np.float32)
        matrix.weights = np.ones(n_constraints).astype(np.float32)
        matrix.bias = np.zeros(n_constraints).astype(np.float32)
        
        solver = SymbolicSolver(dim, matrix)
        
        # Test with a vector that violates constraints
        latent = torch.tensor(sample_latent_vector, dtype=torch.float32)
        loss = solver.compute_constraint_violation(latent)
        
        assert isinstance(loss, torch.Tensor)
        assert loss.dim() == 0  # Scalar tensor
        assert loss >= 0.0

    def test_constraint_satisfaction_threshold(self, sample_latent_vector):
        """Test that constraint satisfaction is detected correctly."""
        dim = 32
        n_constraints = 5
        matrix = ConstraintMatrix(dim, n_constraints)
        
        # Create a constraint matrix where all constraints are satisfied
        matrix.constraint_matrix = np.zeros((n_constraints, dim)).astype(np.float32)
        matrix.weights = np.ones(n_constraints).astype(np.float32)
        matrix.bias = np.ones(n_constraints).astype(np.float32)  # Positive bias ensures satisfaction
        
        solver = SymbolicSolver(dim, matrix)
        
        latent = torch.tensor(sample_latent_vector, dtype=torch.float32)
        is_satisfied = solver.check_constraint_satisfaction(latent, threshold=1e-3)
        
        assert is_satisfied is True

    def test_numerical_stability_with_extreme_values(self):
        """Test solver stability with extreme input values."""
        dim = 32
        n_constraints = 5
        matrix = ConstraintMatrix(dim, n_constraints)
        
        matrix.constraint_matrix = np.random.randn(n_constraints, dim).astype(np.float32)
        matrix.weights = np.ones(n_constraints).astype(np.float32)
        matrix.bias = np.zeros(n_constraints).astype(np.float32)
        
        solver = SymbolicSolver(dim, matrix)
        
        # Test with extreme values
        extreme_vector = torch.tensor([1e6] * dim, dtype=torch.float32)
        loss = solver.compute_constraint_violation(extreme_vector)
        
        assert not torch.isnan(loss)
        assert not torch.isinf(loss)

    def test_gradient_flow_through_solver(self, sample_latent_vector):
        """Test that gradients flow correctly through the solver."""
        dim = 32
        n_constraints = 5
        matrix = ConstraintMatrix(dim, n_constraints)
        
        matrix.constraint_matrix = np.random.randn(n_constraints, dim).astype(np.float32)
        matrix.weights = np.ones(n_constraints).astype(np.float32)
        matrix.bias = np.zeros(n_constraints).astype(np.float32)
        
        solver = SymbolicSolver(dim, matrix)
        
        latent = torch.tensor(sample_latent_vector, dtype=torch.float32, requires_grad=True)
        loss = solver.compute_constraint_violation(latent)
        loss.backward()
        
        assert latent.grad is not None
        assert not torch.isnan(latent.grad).any()
        assert not torch.isinf(latent.grad).any()

    def test_solver_with_config(self, temp_config):
        """Test solver initialization with loaded config."""
        config = load_config(temp_config)
        
        dim = 32
        n_constraints = config.solver.max_iterations  # Use config value
        matrix = ConstraintMatrix(dim, n_constraints)
        
        solver = SymbolicSolver(dim, matrix)
        
        assert solver.dim == dim
        assert solver.constraint_matrix.n_constraints == n_constraints

class TestLatentDriftDetection:
    """Unit tests for latent drift detection and Mahalanobis distance computation."""

    def test_mahalanobis_distance_computation(self, mock_latent_stats, sample_latent_vector):
        """Test Mahalanobis distance calculation with known statistics."""
        mean = np.array(mock_latent_stats["mean"], dtype=np.float32)
        cov_inv = np.array(mock_latent_stats["cov_inv"], dtype=np.float32)
        
        detector = LatentDriftDetector(mean, cov_inv)
        
        distance = detector.compute_mahalanobis(sample_latent_vector)
        
        assert isinstance(distance, float)
        assert distance >= 0.0

    def test_drift_detection_with_in_distribution_sample(self, mock_latent_stats):
        """Test that in-distribution samples are not flagged as drift."""
        mean = np.array(mock_latent_stats["mean"], dtype=np.float32)
        cov_inv = np.array(mock_latent_stats["cov_inv"], dtype=np.float32)
        
        detector = LatentDriftDetector(mean, cov_inv)
        
        # Create a sample very close to the mean
        in_dist_sample = mean + np.random.randn(32).astype(np.float32) * 0.01
        
        is_drift, distance = detector.detect_drift(in_dist_sample, threshold=3.0)
        
        assert is_drift is False
        assert distance < 3.0

    def test_drift_detection_with_out_of_distribution_sample(self, mock_latent_stats):
        """Test that out-of-distribution samples are flagged as drift."""
        mean = np.array(mock_latent_stats["mean"], dtype=np.float32)
        cov_inv = np.array(mock_latent_stats["cov_inv"], dtype=np.float32)
        
        detector = LatentDriftDetector(mean, cov_inv)
        
        # Create a sample far from the mean
        ood_sample = mean + np.random.randn(32).astype(np.float32) * 10.0
        
        is_drift, distance = detector.detect_drift(ood_sample, threshold=3.0)
        
        assert is_drift is True
        assert distance > 3.0

    def test_reference_stats_loading(self, mock_latent_stats):
        """Test loading reference statistics from mock data."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(mock_latent_stats, f)
            stats_file = f.name
        
        try:
            loaded_mean, loaded_cov_inv = load_reference_stats(stats_file)
            
            assert len(loaded_mean) == 32
            assert loaded_cov_inv.shape == (32, 32)
            assert np.allclose(loaded_mean, mock_latent_stats["mean"])
            assert np.allclose(loaded_cov_inv, mock_latent_stats["cov_inv"])
        finally:
            os.unlink(stats_file)

    def test_drift_detector_with_temporal_sequence(self, mock_latent_stats):
        """Test drift detection over a sequence of latent vectors."""
        mean = np.array(mock_latent_stats["mean"], dtype=np.float32)
        cov_inv = np.array(mock_latent_stats["cov_inv"], dtype=np.float32)
        
        detector = LatentDriftDetector(mean, cov_inv)
        
        # Create a sequence of samples
        sequence = []
        for i in range(10):
            if i < 5:
                # In-distribution
                sample = mean + np.random.randn(32).astype(np.float32) * 0.1
            else:
                # Out-of-distribution
                sample = mean + np.random.randn(32).astype(np.float32) * 10.0
            sequence.append(sample)
        
        drift_flags = []
        distances = []
        for sample in sequence:
            is_drift, distance = detector.detect_drift(sample, threshold=3.0)
            drift_flags.append(is_drift)
            distances.append(distance)
        
        # First 5 should not be drift
        assert all(not flag for flag in drift_flags[:5])
        # Last 5 should be drift
        assert all(flag for flag in drift_flags[5:])

    def test_covariance_inverse_validity(self):
        """Test that the inverse covariance matrix is valid for Mahalanobis computation."""
        # Create a random positive definite matrix
        A = np.random.randn(32, 32)
        cov = A @ A.T + np.eye(32) * 0.1  # Ensure positive definiteness
        cov_inv = np.linalg.inv(cov)
        
        mean = np.zeros(32, dtype=np.float32)
        
        detector = LatentDriftDetector(mean, cov_inv)
        
        # Test with various samples
        for _ in range(5):
            sample = np.random.randn(32).astype(np.float32)
            distance = detector.compute_mahalanobis(sample)
            
            assert not np.isnan(distance)
            assert not np.isinf(distance)
            assert distance >= 0.0

    def test_drift_threshold_validation(self, mock_latent_stats):
        """Test that drift thresholds are validated correctly."""
        mean = np.array(mock_latent_stats["mean"], dtype=np.float32)
        cov_inv = np.array(mock_latent_stats["cov_inv"], dtype=np.float32)
        
        detector = LatentDriftDetector(mean, cov_inv)
        
        # Test with invalid threshold (negative)
        with pytest.raises(ValueError):
            detector.detect_drift(np.zeros(32, dtype=np.float32), threshold=-1.0)
        
        # Test with invalid threshold (zero)
        with pytest.raises(ValueError):
            detector.detect_drift(np.zeros(32, dtype=np.float32), threshold=0.0)

class TestIntegrationConstraintsAndDrift:
    """Integration tests combining solver constraints and drift detection."""

    def test_solver_with_drift_awareness(self, temp_config, mock_latent_stats):
        """Test that solver respects drift detection warnings."""
        config = load_config(temp_config)
        
        dim = 32
        n_constraints = 5
        matrix = ConstraintMatrix(dim, n_constraints)
        
        matrix.constraint_matrix = np.random.randn(n_constraints, dim).astype(np.float32)
        matrix.weights = np.ones(n_constraints).astype(np.float32)
        matrix.bias = np.zeros(n_constraints).astype(np.float32)
        
        solver = SymbolicSolver(dim, matrix)
        
        mean = np.array(mock_latent_stats["mean"], dtype=np.float32)
        cov_inv = np.array(mock_latent_stats["cov_inv"], dtype=np.float32)
        detector = LatentDriftDetector(mean, cov_inv)
        
        # Create an OOD sample
        ood_sample = mean + np.random.randn(32).astype(np.float32) * 10.0
        
        # Check drift first
        is_drift, distance = detector.detect_drift(ood_sample, threshold=3.0)
        assert is_drift is True
        
        # Even if constraints are satisfied, drift should be flagged
        is_satisfied = solver.check_constraint_satisfaction(
            torch.tensor(ood_sample, dtype=torch.float32), threshold=1e-3
        )
        
        # The sample might satisfy constraints but still be OOD
        # This test verifies both components work independently
        assert isinstance(is_satisfied, bool)

    def test_constraint_optimization_with_drift_penalty(self):
        """Test that drift penalty can be incorporated into constraint optimization."""
        dim = 32
        n_constraints = 5
        matrix = ConstraintMatrix(dim, n_constraints)
        
        matrix.constraint_matrix = np.random.randn(n_constraints, dim).astype(np.float32)
        matrix.weights = np.ones(n_constraints).astype(np.float32)
        matrix.bias = np.zeros(n_constraints).astype(np.float32)
        
        solver = SymbolicSolver(dim, matrix)
        
        mean = np.zeros(dim, dtype=np.float32)
        cov_inv = np.eye(dim, dtype=np.float32)
        detector = LatentDriftDetector(mean, cov_inv)
        
        latent = torch.tensor(np.random.randn(dim).astype(np.float32), requires_grad=True)
        
        # Combined loss: constraint violation + drift penalty
        constraint_loss = solver.compute_constraint_violation(latent)
        drift_distance = detector.compute_mahalanobis(latent.detach().numpy())
        drift_penalty = drift_distance * 0.1  # Weight factor
        
        combined_loss = constraint_loss + torch.tensor(drift_penalty, dtype=torch.float32)
        
        combined_loss.backward()
        
        assert latent.grad is not None
        assert not torch.isnan(latent.grad).any()
        assert not torch.isinf(latent.grad).any()
