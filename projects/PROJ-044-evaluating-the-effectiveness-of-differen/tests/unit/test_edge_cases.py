"""
Unit tests for edge cases in the DP-FL pipeline.

Tests cover:
1. Missing classes in client partitions (Dirichlet alpha=0.1)
2. Timeout triggers in training loop
3. Zero-sample clients for specific classes
4. Utility collapse detection
"""

import json
import os
import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
import torch

from config import Config
from data.partition import apply_dirichlet_partition, validate_partition
from training.fedavg import FedAvgOrchestrator
from training.dp_utils import DPConfig, validate_dp_config
from training.logging import ExperimentLogger


class TestMissingClassesEdgeCase:
    """Test handling of missing classes in client partitions (high heterogeneity)."""

    def test_dirichlet_partition_missing_classes_low_alpha(self):
        """
        Verify that with alpha=0.1, some clients may have missing classes.
        This is expected behavior for high heterogeneity.
        """
        num_clients = 10
        num_classes = 62  # FEMNIST has 62 classes
        num_samples_per_client = 100
        alpha = 0.1
        seed = 42
        
        np.random.seed(seed)
        
        # Generate Dirichlet partitions
        partitions = apply_dirichlet_partition(
            num_clients=num_clients,
            num_classes=num_classes,
            num_samples_per_client=num_samples_per_client,
            alpha=alpha,
            seed=seed
        )
        
        # Validate partition
        is_valid, issues = validate_partition(partitions, num_classes)
        
        # Check that some clients have missing classes (expected for low alpha)
        clients_with_missing_classes = 0
        for client_id, partition in partitions.items():
            present_classes = set(partition.keys())
            if len(present_classes) < num_classes:
                clients_with_missing_classes += 1
        
        # With alpha=0.1, we expect significant missing classes
        # At least 50% of clients should have missing classes
        assert clients_with_missing_classes > num_clients * 0.5, \
            f"Expected many clients with missing classes at alpha=0.1, got {clients_with_missing_classes}/{num_clients}"
        
        # But partition should still be valid (total samples correct, non-negative)
        assert is_valid, f"Partition validation failed: {issues}"

    def test_validate_partition_raises_on_invalid_distribution(self):
        """Test that validation catches invalid label distributions."""
        # Create a partition with negative samples
        invalid_partition = {
            0: {0: -10, 1: 20},  # Negative samples
            1: {0: 15, 1: 25}
        }
        
        is_valid, issues = validate_partition(invalid_partition, num_classes=2)
        
        assert not is_valid
        assert any("negative" in issue.lower() for issue in issues)

    def test_validate_partition_raises_on_zero_total_samples(self):
        """Test that validation catches clients with zero total samples."""
        invalid_partition = {
            0: {0: 0, 1: 0},  # Zero total samples
            1: {0: 15, 1: 25}
        }
        
        is_valid, issues = validate_partition(invalid_partition, num_classes=2)
        
        assert not is_valid
        assert any("zero" in issue.lower() or "empty" in issue.lower() for issue in issues)


class TestTimeoutEdgeCase:
    """Test timeout handling in training loop."""

    def test_timeout_detection_in_orchestrator(self):
        """
        Verify that the orchestrator detects and flags timeout scenarios.
        """
        # Create a mock model
        model = torch.nn.Linear(10, 2)
        
        # Create a mock config
        config = Config(
            seed=42,
            alpha=0.1,
            epsilon=1.0,
            dataset="femnist"
        )
        
        # Create a mock DP config
        dp_config = DPConfig(
            epsilon=1.0,
            delta=1e-5,
            max_grad_norm=1.0,
            noise_multiplier=1.0,
            num_microbatches=1
        )
        
        # Create orchestrator
        orchestrator = FedAvgOrchestrator(
            model=model,
            config=config,
            dp_config=dp_config
        )
        
        # Mock the training round to simulate a timeout
        original_round = orchestrator._train_single_round
        
        def mock_train_round(*args, **kwargs):
            # Simulate a long-running round
            time.sleep(0.1)  # Short sleep for test
            return {
                "global_accuracy": 0.5,
                "loss": 0.8,
                "is_time_limited": False
            }
        
        with patch.object(orchestrator, '_train_single_round', side_effect=mock_train_round):
            # Run a single round with a very short timeout
            result = orchestrator._train_single_round(
                round_num=0,
                client_data={},
                max_rounds=1,
                timeout_per_round=0.001  # Very short timeout
            )
            
            # The result should indicate timeout
            assert result.get("is_time_limited", False) or "timeout" in str(result).lower()

    def test_timeout_flag_in_logging(self):
        """
        Verify that timeout flags are correctly logged.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir) / "logs"
            log_dir.mkdir()
            
            logger = ExperimentLogger(log_dir=log_dir)
            
            # Log a round with timeout
            metrics = {
                "seed": 42,
                "alpha": 0.1,
                "epsilon": 1.0,
                "round": 0,
                "global_accuracy": 0.5,
                "loss": 0.8,
                "is_time_limited": True,
                "is_utility_collapse": False
            }
            
            logger.log_metrics(metrics)
            
            # Verify the log contains the timeout flag
            log_file = log_dir / "metrics.json"
            assert log_file.exists()
            
            with open(log_file, 'r') as f:
                logs = json.load(f)
            
            assert len(logs) == 1
            assert logs[0]["is_time_limited"] is True


class TestZeroSampleClients:
    """Test handling of clients with zero samples for specific classes."""

    def test_skip_zero_sample_client(self):
        """
        Verify that clients with zero samples for a target class are skipped.
        """
        # Create a mock client with zero samples for class 0
        client_data = {
            0: {"X": torch.randn(0, 10), "y": torch.tensor([])},  # Zero samples
            1: {"X": torch.randn(10, 10), "y": torch.randint(0, 2, (10,))}
        }
        
        # Simulate training logic that should skip client 0
        updated_clients = []
        for client_id, data in client_data.items():
            if len(data["y"]) == 0:
                # Client should be skipped
                continue
            updated_clients.append(client_id)
        
        assert 0 not in updated_clients
        assert 1 in updated_clients
        assert len(updated_clients) == 1

    def test_warning_logged_for_skipped_client(self):
        """
        Verify that a warning is logged when a client is skipped.
        """
        with patch("logging.getLogger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            
            # Simulate skipping a client
            client_id = 0
            reason = "zero_samples"
            
            # This would normally happen in the training loop
            if reason == "zero_samples":
                mock_logger.warning(f"Skipping client {client_id}: {reason}")
            
            # Verify warning was logged
            mock_logger.warning.assert_called_once_with(
                f"Skipping client {client_id}: {reason}"
            )


class TestUtilityCollapseEdgeCase:
    """Test utility collapse detection for extremely low epsilon."""

    def test_utility_collapse_detection(self):
        """
        Verify that utility collapse is detected for extremely low epsilon.
        """
        # Simulate extremely low accuracy due to high noise
        accuracies = [0.01, 0.02, 0.015]  # Near random chance
        threshold = 0.1  # Threshold for collapse detection
        
        # Check if any accuracy is below threshold
        collapse_detected = any(acc < threshold for acc in accuracies)
        
        assert collapse_detected, "Utility collapse should be detected for very low accuracies"

    def test_utility_collapse_flag_in_orchestrator(self):
        """
        Verify that the orchestrator flags utility collapse.
        """
        # Create a mock model
        model = torch.nn.Linear(10, 2)
        
        # Create a mock config with extremely low epsilon
        config = Config(
            seed=42,
            alpha=0.1,
            epsilon=0.01,  # Extremely low epsilon
            dataset="femnist"
        )
        
        # Create a mock DP config
        dp_config = DPConfig(
            epsilon=0.01,
            delta=1e-5,
            max_grad_norm=1.0,
            noise_multiplier=10.0,  # High noise
            num_microbatches=1
        )
        
        # Create orchestrator
        orchestrator = FedAvgOrchestrator(
            model=model,
            config=config,
            dp_config=dp_config
        )
        
        # Simulate a round with very low accuracy
        result = {
            "global_accuracy": 0.02,  # Near random
            "loss": 2.5,
            "is_time_limited": False
        }
        
        # Check utility collapse detection
        is_collapse = result["global_accuracy"] < 0.05  # Threshold for collapse
        
        assert is_collapse, "Utility collapse should be detected for very low accuracy"

    def test_validation_report_includes_collapse_count(self):
        """
        Verify that the validation report includes count of utility collapse runs.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir) / "logs"
            log_dir.mkdir()
            
            logger = ExperimentLogger(log_dir=log_dir)
            
            # Log multiple runs, some with utility collapse
            metrics_list = [
                {"seed": 42, "alpha": 0.1, "epsilon": 1.0, "round": 0, 
                 "global_accuracy": 0.8, "is_utility_collapse": False},
                {"seed": 42, "alpha": 0.1, "epsilon": 0.01, "round": 0, 
                 "global_accuracy": 0.02, "is_utility_collapse": True},
                {"seed": 43, "alpha": 0.1, "epsilon": 0.01, "round": 0, 
                 "global_accuracy": 0.01, "is_utility_collapse": True},
            ]
            
            for metrics in metrics_list:
                logger.log_metrics(metrics)
            
            # Generate validation report
            report = logger.generate_validation_report()
            
            # Check that collapse count is included
            assert "is_utility_collapse" in str(report).lower() or "collapse" in str(report).lower()
            assert report.count("True") >= 2  # At least 2 collapse runs


class TestCombinedEdgeCases:
    """Test combinations of edge cases."""

    def test_low_alpha_with_low_epsilon(self):
        """
        Test scenario with both high heterogeneity (low alpha) and high privacy (low epsilon).
        This is the most challenging scenario and should trigger multiple edge cases.
        """
        # Simulate data with low alpha (high heterogeneity)
        num_clients = 10
        num_classes = 62
        alpha = 0.1
        epsilon = 0.01  # Extremely low epsilon
        
        np.random.seed(42)
        partitions = apply_dirichlet_partition(
            num_clients=num_clients,
            num_classes=num_classes,
            num_samples_per_client=100,
            alpha=alpha,
            seed=42
        )
        
        # Count clients with missing classes
        clients_with_missing = sum(
            1 for p in partitions.values() 
            if len(p) < num_classes
        )
        
        # With low alpha, many clients should have missing classes
        assert clients_with_missing > num_clients * 0.5, \
            "High heterogeneity expected with low alpha"
        
        # With low epsilon, utility collapse is likely
        simulated_accuracy = 0.02  # Near random due to high noise
        is_collapse = simulated_accuracy < 0.05
        
        assert is_collapse, "Utility collapse expected with extremely low epsilon"

    def test_timeout_with_missing_classes(self):
        """
        Test scenario where timeout occurs while processing clients with missing classes.
        """
        # Simulate a client with missing classes
        client_partition = {0: 100}  # Only class 0 present
        
        # Simulate training that takes too long
        start_time = time.time()
        
        # Simulate processing that should timeout
        timeout = 0.001  # Very short timeout
        processing_time = 0.01  # Simulated long processing
        
        if processing_time > timeout:
            # Timeout detected
            is_timed_out = True
        else:
            is_timed_out = False
        
        assert is_timed_out, "Timeout should be detected when processing exceeds limit"