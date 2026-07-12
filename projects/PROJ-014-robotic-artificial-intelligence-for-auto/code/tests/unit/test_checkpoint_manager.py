import os
import sys
import pytest
import tempfile
import pickle
from pathlib import Path
import time

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.environment.checkpoint_manager import CheckpointManager, create_checkpoint_manager

@pytest.fixture
def temp_checkpoint_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def checkpoint_manager(temp_checkpoint_dir):
    return create_checkpoint_manager(checkpoint_dir=temp_checkpoint_dir)

class TestCheckpointManager:
    def test_save_and_load_checkpoint(self, checkpoint_manager):
        seed = 42
        episode_id = 1
        step = 10
        success = True
        metrics = {"distance": 5.0, "steps": 10}
        
        # Save
        path = checkpoint_manager.save_checkpoint(
            seed=seed,
            episode_id=episode_id,
            step=step,
            success=success,
            metrics=metrics,
            env_state={"pos": (0, 0)}
        )
        
        assert path.exists()
        
        # Load
        data = checkpoint_manager.load_checkpoint(seed)
        assert data is not None
        assert data['state']['seed'] == seed
        assert data['state']['episode_id'] == episode_id
        assert data['state']['step'] == step
        assert data['state']['success'] == success
        assert data['state']['metrics'] == metrics
        assert data['env_state'] == {"pos": (0, 0)}

    def test_clear_checkpoint(self, checkpoint_manager):
        seed = 42
        episode_id = 1
        
        checkpoint_manager.save_checkpoint(
            seed=seed,
            episode_id=episode_id,
            step=5,
            success=True,
            metrics={},
            env_state=None
        )
        
        assert checkpoint_manager._get_checkpoint_path(seed, episode_id).exists()
        
        result = checkpoint_manager.clear_checkpoint(seed, episode_id)
        assert result is True
        assert not checkpoint_manager._get_checkpoint_path(seed, episode_id).exists()

    def test_load_nonexistent_checkpoint(self, checkpoint_manager):
        data = checkpoint_manager.load_checkpoint(seed=999)
        assert data is None

    def test_latest_checkpoint_selection(self, checkpoint_manager):
        seed = 42
        
        # Save two checkpoints for same seed, different episodes
        checkpoint_manager.save_checkpoint(seed, 1, 10, True, {}, None)
        time.sleep(0.1) # Ensure different mtime
        checkpoint_manager.save_checkpoint(seed, 2, 20, False, {}, None)
        
        # Should load the latest one (episode 2)
        data = checkpoint_manager.load_checkpoint(seed)
        assert data is not None
        assert data['state']['episode_id'] == 2
        assert data['state']['step'] == 20

    def test_cleanup_old_checkpoints(self, checkpoint_manager, temp_checkpoint_dir):
        seed = 42
        
        # Create an old file manually
        old_path = checkpoint_manager._get_checkpoint_path(seed, 999)
        with open(old_path, 'wb') as f:
            pickle.dump({'state': {}, 'env_state': None}, f)
        
        # Set old modification time
        old_time = time.time() - 7200 # 2 hours ago
        os.utime(old_path, (old_time, old_time))
        
        # Run cleanup
        count = checkpoint_manager.cleanup_old_checkpoints(max_age_seconds=3600)
        assert count == 1
        assert not old_path.exists()
        
        # New file should remain
        checkpoint_manager.save_checkpoint(seed, 1, 1, True, {}, None)
        count = checkpoint_manager.cleanup_old_checkpoints(max_age_seconds=3600)
        assert count == 0
        assert checkpoint_manager._get_checkpoint_path(seed, 1).exists()