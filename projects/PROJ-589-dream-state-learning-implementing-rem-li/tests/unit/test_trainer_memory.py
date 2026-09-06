import pytest
import torch
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile
import os

from models.trainer import Trainer, DreamScheduler
from utils.memory_monitor import MemoryLimitExceeded
from config import Config

@pytest.fixture
def temp_config():
    """Create a temporary config for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config = Config(
            model_name="distilbert-base-uncased",
            device="cpu",
            max_memory_mb=100,  # 100MB limit for testing
            checkpoint_dir=os.path.join(tmpdir, "checkpoints"),
            warmup_steps=5,
            dream_ratio=0.25,
            dae_mask_rate=0.15,
            min_entropy_threshold=0.5,
            learning_rate=5e-5,
            weight_decay=0.01,
            max_grad_norm=1.0,
            num_epochs=1,
            log_interval=1,
            checkpoint_interval=10,
            seed=42
        )
        # Ensure checkpoint dir exists
        Path(config.checkpoint_dir).mkdir(parents=True, exist_ok=True)
        yield config

@pytest.fixture
def dummy_model():
    """Create a simple dummy model for testing."""
    model = torch.nn.TransformerEncoder(
        torch.nn.TransformerEncoderLayer(d_model=16, nhead=2),
        num_layers=2
    )
    return model

@pytest.fixture
def dummy_batch():
    """Create a dummy batch for testing."""
    batch_size = 4
    seq_len = 16
    vocab_size = 1000
    
    return {
        'input_ids': torch.randint(0, vocab_size, (batch_size, seq_len)),
        'attention_mask': torch.ones(batch_size, seq_len, dtype=torch.long),
        'labels': torch.randint(0, vocab_size, (batch_size, seq_len))
    }

class TestDreamScheduler:
    def test_warmup_prevents_dream(self, temp_config):
        """Test that dream phase is skipped during warmup."""
        scheduler = DreamScheduler(temp_config)
        
        # During warmup, should_dream should always be False
        for step in range(temp_config.warmup_steps):
            scheduler.step_counter = step
            assert not scheduler.should_dream(), f"Dream should not trigger at step {step}"
        
        # After warmup, should trigger periodically
        scheduler.step_counter = temp_config.warmup_steps
        assert not scheduler.should_dream()  # First step after warmup might not be dream
        
        # Check periodic behavior
        cycle_len = int(1.0 / temp_config.dream_ratio)
        for step in range(temp_config.warmup_steps + 1, temp_config.warmup_steps + cycle_len * 3):
            scheduler.step_counter = step
            expected_dream = (step - temp_config.warmup_steps) % cycle_len == 0
            assert scheduler.should_dream() == expected_dream

    def test_increment(self, temp_config):
        """Test that increment updates step counter."""
        scheduler = DreamScheduler(temp_config)
        initial_step = scheduler.step_counter
        scheduler.increment()
        assert scheduler.step_counter == initial_step + 1

class TestTrainerMemoryIntegration:
    def test_memory_monitor_initialization(self, temp_config, dummy_model):
        """Test that trainer initializes memory monitor correctly."""
        trainer = Trainer(dummy_model, temp_config)
        assert trainer.memory_monitor.limit_kb == temp_config.max_memory_mb * 1024
        assert trainer.memory_monitor.checkpoint_dir == temp_config.checkpoint_dir

    def test_checkpoint_saved_on_memory_warning(self, temp_config, dummy_model, dummy_batch):
        """Test that checkpoint is saved when memory usage is high."""
        trainer = Trainer(dummy_model, temp_config)
        
        # Mock memory monitor to simulate high memory usage
        with patch.object(trainer.memory_monitor, 'get_current_rss_kb', return_value=temp_config.max_memory_mb * 1024 * 0.95):
            with patch.object(trainer, '_save_checkpoint') as mock_save:
                # Run a training step
                trainer.train_step(dummy_batch)
                
                # Checkpoint should be saved
                mock_save.assert_called_with(reason="memory_warning")

    def test_memory_limit_exceeded_abort(self, temp_config, dummy_model, dummy_batch):
        """Test that training aborts and saves checkpoint on memory limit exceeded."""
        trainer = Trainer(dummy_model, temp_config)
        
        # Mock enforce_memory_limit to raise MemoryLimitExceeded
        with patch('models.trainer.enforce_memory_limit', side_effect=MemoryLimitExceeded("Test OOM")):
            with patch.object(trainer, '_save_checkpoint') as mock_save:
                with pytest.raises(MemoryLimitExceeded):
                    trainer.train_step(dummy_batch)
                
                # Checkpoint should be saved before raising
                mock_save.assert_called_with(reason="oom_abort")

    def test_checkpoint_created_in_directory(self, temp_config, dummy_model, dummy_batch):
        """Test that checkpoint files are actually created on disk."""
        trainer = Trainer(dummy_model, temp_config)
        
        # Run a training step
        trainer.train_step(dummy_batch)
        
        # Check if checkpoint file exists
        checkpoint_files = list(Path(temp_config.checkpoint_dir).glob("*.pt"))
        assert len(checkpoint_files) > 0, "No checkpoint files created"
        
        # Verify checkpoint contains expected keys
        checkpoint = torch.load(checkpoint_files[0])
        assert 'model_state_dict' in checkpoint
        assert 'optimizer_state_dict' in checkpoint
        assert 'step' in checkpoint

    def test_wake_dream_phase_logging(self, temp_config, dummy_model, dummy_batch):
        """Test that phase transitions are tracked correctly."""
        trainer = Trainer(dummy_model, temp_config)
        
        # Run multiple steps to trigger both phases
        metrics_wake = None
        metrics_dream = None
        
        for i in range(20):
            trainer.scheduler.step_counter = i
            metrics = trainer.train_step(dummy_batch)
            
            if metrics['is_dream']:
                metrics_dream = metrics
            else:
                metrics_wake = metrics
        
        # Should have seen both phases
        assert metrics_wake is not None, "No wake phase detected"
        assert metrics_dream is not None, "No dream phase detected"
        assert metrics_wake['phase'] == 'wake'
        assert metrics_dream['phase'] == 'dream'

    def test_entropy_check_triggers_warning(self, temp_config, dummy_model, dummy_batch):
        """Test that low entropy triggers warning (mocked)."""
        trainer = Trainer(dummy_model, temp_config)
        
        # Mock the entropy calculation to return low value
        original_calc = trainer._calculate_entropy
        def mock_calc(logits):
            return 0.1  # Very low entropy
        
        with patch.object(trainer, '_calculate_entropy', side_effect=mock_calc):
            with patch.object(trainer.logger, 'warning') as mock_warning:
                trainer.train_step(dummy_batch)
                
                # Should log warning about low entropy
                mock_warning.assert_called()

class TestTrainerTrainingLoop:
    def test_training_loop_creates_checkpoints(self, temp_config, dummy_model):
        """Test that the full training loop creates checkpoints."""
        # Create a tiny dataset
        dataset = torch.utils.data.TensorDataset(
            torch.randint(0, 100, (10, 16)),
            torch.ones(10, 16, dtype=torch.long),
            torch.randint(0, 100, (10, 16))
        )
        dataloader = torch.utils.data.DataLoader(dataset, batch_size=2)
        
        trainer = Trainer(dummy_model, temp_config)
        trainer.train(dataloader, epochs=1)
        
        # Check if checkpoints were created
        checkpoint_files = list(Path(temp_config.checkpoint_dir).glob("*.pt"))
        assert len(checkpoint_files) >= 1, "No checkpoints created during training"

    def test_training_loop_handles_memory_error(self, temp_config, dummy_model):
        """Test that training loop properly handles memory errors."""
        dataset = torch.utils.data.TensorDataset(
            torch.randint(0, 100, (10, 16)),
            torch.ones(10, 16, dtype=torch.long),
            torch.randint(0, 100, (10, 16))
        )
        dataloader = torch.utils.data.DataLoader(dataset, batch_size=2)
        
        trainer = Trainer(dummy_model, temp_config)
        
        # Mock memory limit to trigger early
        with patch('models.trainer.enforce_memory_limit', side_effect=MemoryLimitExceeded("Test")):
            with pytest.raises(MemoryLimitExceeded):
                trainer.train(dataloader, epochs=1)
                
            # Checkpoint should have been saved
            checkpoint_files = list(Path(temp_config.checkpoint_dir).glob("*oom_abort*.pt"))
            assert len(checkpoint_files) > 0, "No OOM checkpoint saved"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
