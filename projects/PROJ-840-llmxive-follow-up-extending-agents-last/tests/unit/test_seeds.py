import os
import json
import random
import hashlib
import pytest
from pathlib import Path

# Import the actual implementation from the existing API surface
from utils.seeds import (
    set_seed,
    get_seed_state,
    restore_seed_state,
    verify_seed,
    generate_task_seed,
    save_seed_state,
    load_seed_state,
    verify_pairing
)

@pytest.fixture
def temp_seed_dir(tmp_path):
    """Create a temporary directory for seed state files."""
    seed_dir = tmp_path / "seeds"
    seed_dir.mkdir()
    return str(seed_dir)

class TestSetSeed:
    def test_set_seed_deterministic(self):
        """Verify that setting a seed produces deterministic results."""
        set_seed(42)
        val1 = random.random()
        
        set_seed(42)
        val2 = random.random()
        
        assert val1 == val2

    def test_set_seed_different_values(self):
        """Verify different seeds produce different results."""
        set_seed(42)
        val1 = random.random()
        
        set_seed(123)
        val2 = random.random()
        
        assert val1 != val2

class TestGetSeedState:
    def test_get_seed_state_returns_dict(self):
        """Verify get_seed_state returns a dictionary."""
        set_seed(42)
        state = get_seed_state()
        assert isinstance(state, dict)
        assert "random_state" in state

class TestRestoreSeedState:
    def test_restore_seed_state(self, temp_seed_dir):
        """Verify restoring a saved seed state reproduces results."""
        set_seed(42)
        original_val = random.random()
        
        state = get_seed_state()
        save_seed_state(state, temp_seed_dir, "test_state")
        
        set_seed(123)  # Change seed
        new_val = random.random()
        assert new_val != original_val
        
        restored_state = load_seed_state(temp_seed_dir, "test_state")
        restore_seed_state(restored_state)
        restored_val = random.random()
        
        assert restored_val == original_val

class TestVerifySeed:
    def test_verify_seed_success(self):
        """Verify correct seed verification."""
        set_seed(42)
        is_valid = verify_seed(42)
        assert is_valid is True

    def test_verify_seed_failure(self):
        """Verify incorrect seed detection."""
        set_seed(42)
        is_valid = verify_seed(123)
        assert is_valid is False

class TestGenerateTaskSeed:
    def test_generate_task_seed_deterministic(self):
        """Verify task seed generation is deterministic for same inputs."""
        seed1 = generate_task_seed("task_1", "description_1")
        seed2 = generate_task_seed("task_1", "description_1")
        assert seed1 == seed2

    def test_generate_task_seed_unique(self):
        """Verify different tasks get different seeds."""
        seed1 = generate_task_seed("task_1", "description_1")
        seed2 = generate_task_seed("task_2", "description_1")
        assert seed1 != seed2

class TestSaveLoadSeedState:
    def test_save_load_seed_state(self, temp_seed_dir):
        """Verify saving and loading seed state works."""
        set_seed(42)
        state = get_seed_state()
        
        save_path = save_seed_state(state, temp_seed_dir, "test")
        assert os.path.exists(save_path)
        
        loaded_state = load_seed_state(temp_seed_dir, "test")
        assert loaded_state == state

class TestVerifyPairing:
    def test_verify_pairing_success(self):
        """Verify correct pairing verification."""
        task_id = "task_001"
        seed = 42
        
        checksum = verify_pairing(task_id, seed)
        assert isinstance(checksum, str)
        assert len(checksum) == 64  # SHA-256 hex length

    def test_verify_pairing_deterministic(self):
        """Verify pairing checksum is deterministic."""
        task_id = "task_001"
        seed = 42
        
        checksum1 = verify_pairing(task_id, seed)
        checksum2 = verify_pairing(task_id, seed)
        
        assert checksum1 == checksum2

    def test_verify_pairing_different_inputs(self):
        """Verify different inputs produce different checksums."""
        checksum1 = verify_pairing("task_001", 42)
        checksum2 = verify_pairing("task_002", 42)
        checksum3 = verify_pairing("task_001", 123)
        
        assert checksum1 != checksum2
        assert checksum1 != checksum3
        assert checksum2 != checksum3

    def test_verify_pairing_file_creation(self, temp_seed_dir):
        """Verify verify_pairing creates pairing record file."""
        task_id = "task_001"
        seed = 42
        
        checksum = verify_pairing(task_id, seed, temp_seed_dir)
        
        pairing_file = Path(temp_seed_dir) / f"{task_id}_pairing.json"
        assert pairing_file.exists()
        
        with open(pairing_file, 'r') as f:
            data = json.load(f)
        
        assert data["task_id"] == task_id
        assert data["seed"] == seed
        assert data["checksum"] == checksum
