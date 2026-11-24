import pytest
import torch
from config import get_config
from models.trainer import Trainer, DummyOptimizer, DreamScheduler

@pytest.fixture
def dummy_model():
    # Simple linear model for testing purposes
    return torch.nn.Linear(10, 10)

@pytest.fixture
def dummy_config():
    # Use the lightweight config helper that includes all required attributes
    return get_config()

@pytest.fixture
def dummy_tokenizer():
    class DummyTokenizer:
        def __init__(self):
            self.pad_token_id = 0
    return DummyTokenizer()

def test_warmup_length(dummy_model, dummy_config, dummy_tokenizer):
    trainer = Trainer(dummy_model, dummy_config, dummy_config.device, dummy_tokenizer)
    scheduler = trainer.scheduler
    # Warm‑up steps should be exactly the configured number
    assert scheduler.warm_up_steps == dummy_config.warm_up_steps

def test_low_entropy_retry(dummy_model, dummy_config, dummy_tokenizer):
    # Force low entropy by mocking calculate_entropy
    original_calc = trainer = Trainer(dummy_model, dummy_config, dummy_config.device, dummy_tokenizer).calculate_entropy
    def low_entropy(*args, **kwargs):
        return 0.0  # below threshold
    Trainer.calculate_entropy = staticmethod(low_entropy)

    trainer = Trainer(dummy_model, dummy_config, dummy_config.device, dummy_tokenizer)
    # Simulate a dream step and ensure retries happen (max_retries = 3)
    batch = {"input_ids": torch.randint(0, 100, (4, 8)), "labels": torch.randint(0, 100, (4, 8))}
    metrics = trainer.train_step_dream(batch)
    # After retries, entropy should still be low and phase remains DREAM
    assert metrics["entropy"] < dummy_config.entropy_threshold
    # Restore original method
    Trainer.calculate_entropy = original_calc

def test_high_perplexity_skip_and_dummy_wake(dummy_model, dummy_config, dummy_tokenizer):
    # Mock held‑out batch to produce high perplexity
    trainer = Trainer(dummy_model, dummy_config, dummy_config.device, dummy_tokenizer)
    held_out_batch = {
        "input_ids": torch.randint(0, 100, (1, 8)),
        "labels": torch.randint(0, 100, (1, 8))
    }
    # Force a high loss to exceed threshold
    trainer.scheduler.perplexity_skip_threshold = 0.0  # any loss triggers skip
    batch = {"input_ids": torch.randint(0, 100, (4, 8)), "labels": torch.randint(0, 100, (4, 8))}
    metrics = trainer.train_step_dream(batch, held_out_batch=held_out_batch)
    assert metrics["phase"] == "DUMMY_WAKE"

def test_real_token_count_matches_baseline(dummy_model, dummy_config, dummy_tokenizer):
    # Simulate two runs: experimental (with possible dummy wakes) and baseline (continuous)
    trainer = Trainer(dummy_model, dummy_config, dummy_config.device, dummy_tokenizer)
    scheduler = trainer.scheduler
    # Assume 30 steps total, warm‑up 20, ratio 5 (4 wake + 1 dream)
    scheduler.warm_up_steps = 20
    scheduler.wake_to_dream_ratio = 5
    scheduler.current_step = 0
    real_tokens = 0
    for _ in range(30):
        if scheduler.should_run_dream_phase():
            # Dream step would be skipped, triggering dummy wake
            real_tokens += 4  # dummy wake counts as 4 wake steps
        else:
            real_tokens += 1
        scheduler.advance_step()
    # Baseline would simply have 30 wake steps
    assert real_tokens == 30