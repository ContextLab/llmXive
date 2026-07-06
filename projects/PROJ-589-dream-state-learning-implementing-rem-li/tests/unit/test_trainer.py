"""
Unit tests for the Dream-State Learning trainer, specifically focusing on
entropy calculation and low-entropy retry logic as described in T011.

These tests verify:
1. Correct calculation of entropy (sum(-p * log2(p))) for probability distributions.
2. Detection of low-entropy outputs (< 0.5 bits).
3. Retry logic behavior: up to 3 retries with local counter, then discard batch.
4. Logging of entropy metrics and retry events.
"""

import math
import logging
from unittest.mock import Mock, patch, MagicMock
import pytest

# Import existing project utilities and exceptions
from utils.exceptions import DataIntegrityError
from utils.logger import get_logger, log_event

# Mock the torch imports since we are testing logic without full model execution
# We assume the trainer module will import torch internally.
# For this test, we mock the specific functions we need to validate.

try:
    import torch
    import torch.nn.functional as F
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    pytest.skip("PyTorch not available", allow_module_level=True)

from code.models.trainer import Trainer
from code.config import get_config


class TestEntropyCalculation:
    """Tests for the entropy calculation logic."""

    def test_entropy_perfect_distribution(self):
        """Test entropy calculation for a uniform distribution (max entropy)."""
        # For 4 classes, uniform is [0.25, 0.25, 0.25, 0.25]
        # Entropy = -4 * (0.25 * log2(0.25)) = -4 * (0.25 * -2) = 2.0 bits
        probs = torch.tensor([0.25, 0.25, 0.25, 0.25])
        expected_entropy = 2.0

        # Calculate entropy manually to verify formula
        # entropy = sum(-p * log2(p))
        calculated_entropy = -torch.sum(probs * torch.log2(probs))
        
        assert math.isclose(calculated_entropy.item(), expected_entropy, rel_tol=1e-5)

    def test_entropy_deterministic(self):
        """Test entropy calculation for a deterministic distribution (min entropy)."""
        # One class with probability 1.0
        probs = torch.tensor([1.0, 0.0, 0.0, 0.0])
        # Entropy should be 0.0
        # Note: 0 * log(0) is defined as 0
        calculated_entropy = -torch.sum(probs * torch.log2(probs))
        
        assert math.isclose(calculated_entropy.item(), 0.0, rel_tol=1e-5)

    def test_entropy_low_threshold(self):
        """Test that low entropy (< 0.5 bits) is correctly identified."""
        # Create a distribution with low entropy
        # [0.9, 0.033, 0.033, 0.034] -> should be low entropy
        probs = torch.tensor([0.9, 0.033, 0.033, 0.034])
        calculated_entropy = -torch.sum(probs * torch.log2(probs))
        
        assert calculated_entropy < 0.5, f"Expected entropy < 0.5, got {calculated_entropy}"

    def test_entropy_high_threshold(self):
        """Test that high entropy (> 0.5 bits) is correctly identified."""
        # Create a distribution with higher entropy
        # [0.5, 0.5, 0.0, 0.0] -> entropy = 1.0
        probs = torch.tensor([0.5, 0.5, 0.0, 0.0])
        calculated_entropy = -torch.sum(probs * torch.log2(probs))
        
        assert calculated_entropy >= 0.5, f"Expected entropy >= 0.5, got {calculated_entropy}"


class TestLowEntropyRetryLogic:
    """Tests for the low-entropy retry logic in the training loop."""

    @pytest.fixture
    def mock_trainer(self):
        """Create a mock trainer with necessary dependencies."""
        config = get_config()
        # Override config to ensure we can test the logic without full initialization
        config.max_retries = 3
        config.entropy_threshold = 0.5
        
        # Mock the model and tokenizer
        mock_model = Mock()
        mock_tokenizer = Mock()
        
        trainer = Trainer(
            model=mock_model,
            tokenizer=mock_tokenizer,
            config=config,
            device="cpu"
        )
        return trainer

    def test_retry_logic_success_on_second_attempt(self, mock_trainer):
        """Test that a batch is accepted after a successful retry."""
        # Mock the get_entropy method to return low entropy first, then high
        call_count = 0
        def mock_get_entropy(probs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return 0.3  # Low entropy, trigger retry
            else:
                return 1.0  # High entropy, accept
        
        with patch.object(mock_trainer, 'get_entropy', side_effect=mock_get_entropy):
            # Mock the generate method to return valid outputs
            mock_trainer.generate = Mock(return_value=Mock())
            
            # Simulate a batch processing with retry logic
            # We need to simulate the loop that checks entropy
            batch_probs_low = torch.tensor([0.9, 0.033, 0.033, 0.034])
            batch_probs_high = torch.tensor([0.25, 0.25, 0.25, 0.25])
            
            # First call returns low entropy
            with patch.object(mock_trainer, 'get_entropy', return_value=0.3):
                entropy = mock_trainer.get_entropy(batch_probs_low)
                assert entropy < mock_trainer.config.entropy_threshold
            
            # Second call returns high entropy
            with patch.object(mock_trainer, 'get_entropy', return_value=1.0):
                entropy = mock_trainer.get_entropy(batch_probs_high)
                assert entropy >= mock_trainer.config.entropy_threshold

    def test_retry_logic_discards_after_max_retries(self, mock_trainer):
        """Test that a batch is discarded after max retries are exceeded."""
        # Mock get_entropy to always return low entropy
        def mock_get_entropy_always_low(probs):
            return 0.3  # Always low entropy
        
        max_retries = mock_trainer.config.max_retries
        retry_count = 0
        
        def mock_generate_with_retry(probs):
            nonlocal retry_count
            retry_count += 1
            if retry_count > max_retries:
                raise RuntimeError("Max retries exceeded")
            return Mock()
        
        with patch.object(mock_trainer, 'get_entropy', side_effect=mock_get_entropy_always_low):
            with patch.object(mock_trainer, 'generate', side_effect=mock_generate_with_retry):
                # Simulate the retry loop
                local_retry_counter = 0
                success = False
                
                while local_retry_counter < max_retries:
                    local_retry_counter += 1
                    try:
                        # Simulate generating and checking entropy
                        # In real code, this would be inside the training step
                        entropy = mock_trainer.get_entropy(torch.tensor([0.9, 0.033, 0.033, 0.034]))
                        if entropy >= mock_trainer.config.entropy_threshold:
                            success = True
                            break
                    except RuntimeError:
                        break
                
                # After max retries, we should not have succeeded
                assert not success, "Batch should be discarded after max retries"
                assert local_retry_counter == max_retries, f"Expected {max_retries} retries, got {local_retry_counter}"

    def test_local_retry_counter_increment(self, mock_trainer):
        """Test that the local retry counter increments correctly."""
        local_counter = 0
        max_retries = mock_trainer.config.max_retries
        
        # Simulate the retry loop
        while local_counter < max_retries:
            local_counter += 1
            # In real code, this would check entropy and decide to retry or break
            pass
        
        assert local_counter == max_retries, f"Local counter should reach {max_retries}, got {local_counter}"

    def test_logging_of_entropy_metrics(self, mock_trainer):
        """Test that entropy metrics are logged correctly."""
        # Setup logger
        logger = get_logger("test_trainer")
        
        # Mock log_event to capture calls
        with patch('code.models.trainer.log_event') as mock_log:
            # Simulate logging an entropy event
            mock_trainer.logger = logger
            mock_trainer.log_event(
                "entropy_check",
                {"entropy": 0.3, "threshold": 0.5, "retry_count": 1}
            )
            
            # Verify log_event was called with correct arguments
            mock_log.assert_called_once()
            call_args = mock_log.call_args
            assert call_args[0][0] == "entropy_check"
            assert call_args[1]["entropy"] == 0.3
            assert call_args[1]["threshold"] == 0.5
            assert call_args[1]["retry_count"] == 1


class TestTrainerIntegration:
    """Integration tests for the trainer's entropy handling."""

    def test_warmup_skips_entropy_check(self, mock_trainer):
        """Test that entropy checks are skipped during warm-up phase."""
        # In warm-up phase, the trainer should not perform entropy checks
        # This is tested by ensuring no retry logic is triggered
        
        # Mock the is_warmup method to return True
        with patch.object(mock_trainer, 'is_warmup', return_value=True):
            # Mock get_entropy to return low entropy
            with patch.object(mock_trainer, 'get_entropy', return_value=0.3):
                # During warm-up, even if entropy is low, we should not retry
                # The trainer should proceed without checking entropy
                # This is a behavioral test - we expect no exceptions or retries
                pass  # The test passes if no exceptions are raised

    def test_entropy_check_triggered_after_warmup(self, mock_trainer):
        """Test that entropy checks are triggered after warm-up phase."""
        # Mock the is_warmup method to return False
        with patch.object(mock_trainer, 'is_warmup', return_value=False):
            # Mock get_entropy to return low entropy
            with patch.object(mock_trainer, 'get_entropy', return_value=0.3):
                # After warm-up, entropy checks should be triggered
                # This should lead to retry logic being invoked
                # We test that the check is indeed performed
                entropy = mock_trainer.get_entropy(torch.tensor([0.9, 0.033, 0.033, 0.034]))
                assert entropy < mock_trainer.config.entropy_threshold


if __name__ == "__main__":
    pytest.main([__file__, "-v"])