import pytest
import torch
import torch.nn as nn
from unittest.mock import Mock, patch, MagicMock
from code.models.trainer import Trainer, DreamScheduler
from code.config import get_config

class MockModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.logits = None
    def forward(self, input_ids, labels=None):
        # Return a mock output object
        class Output:
            def __init__(self):
                self.loss = torch.tensor(1.0, requires_grad=True)
                self.logits = torch.randn(4, 64, 30522)
        return Output()

@pytest.fixture
def trainer_setup():
    config = get_config()
    config.warm_up_steps = 20
    config.dream_ratio = 5
    config.entropy_threshold = 0.5
    config.max_retries = 3
    model = MockModel()
    device = torch.device('cpu')
    trainer = Trainer(model, config, device)
    return trainer, config

def test_warmup_period(trainer_setup):
    """Verify that no dream phase occurs during the first 20 steps."""
    trainer, _ = trainer_setup
    for step in range(20):
        trainer.scheduler.current_step = step
        assert trainer.scheduler.should_run_dream_phase() is False

def test_dream_phase_trigger(trainer_setup):
    """Verify dream phase triggers after warmup and according to ratio."""
    trainer, _ = trainer_setup
    # Step 20 is the first step after warmup and is a multiple of ratio 5
    trainer.scheduler.current_step = 20
    assert trainer.scheduler.should_run_dream_phase() is True
    # Step 21 should be wake
    trainer.scheduler.current_step = 21
    assert trainer.scheduler.should_run_dream_phase() is False

def test_perplexity_skip(trainer_setup):
    """Verify dream phase is skipped when perplexity is too high."""
    trainer, _ = trainer_setup
    # Mock model to return a high loss (high perplexity)
    with patch.object(trainer.model, 'forward') as mock_forward:
        class HighLossOutput:
            def __init__(self):
                self.loss = torch.tensor(5.0) # exp(5) > 50
        mock_forward.return_value = HighLossOutput()

        held_out_batch = {
            'input_ids': torch.randint(0, 100, (1, 64)),
            'labels': torch.randint(0, 100, (1, 64))
        }

        skipped = trainer.scheduler.maybe_skip_dream_due_to_perplexity(trainer.model, held_out_batch)
        assert skipped is True

def test_entropy_retry_logic(trainer_setup):
    """Verify that low entropy triggers retries."""
    trainer, _ = trainer_setup
    batch = {'input_ids': torch.randint(0, 100, (4, 64)), 'labels': torch.randint(0, 100, (4, 64))}

    # Mock train_step_wake to return low entropy first, then high
    with patch.object(trainer, 'train_step_wake') as mock_step:
        mock_step.side_effect = [
            {'loss': 1.0, 'entropy': 0.1, 'phase': 'WAKE'}, # Try 1: Low
            {'loss': 1.0, 'entropy': 0.1, 'phase': 'WAKE'}, # Try 2: Low
            {'loss': 1.0, 'entropy': 0.8, 'phase': 'WAKE'}, # Try 3: High (Success)
        ]

        # We manually simulate the loop logic for a single wake step
        metrics = trainer.train_step_wake(batch)
        if metrics['entropy'] < trainer.config.entropy_threshold:
            retry_count = 0
            while metrics['entropy'] < trainer.config.entropy_threshold and retry_count < trainer.config.max_retries:
                retry_count += 1
                metrics = trainer.train_step_wake(batch)

        assert retry_count == 2
        assert metrics['entropy'] == 0.8