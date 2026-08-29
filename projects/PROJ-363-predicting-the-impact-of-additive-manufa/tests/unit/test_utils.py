import os
import tempfile
import json
import logging
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Import the module under test
from code.utils import (
    setup_logging,
    load_env_config,
    set_seed,
    compute_file_hash,
    compute_string_hash,
    load_state,
    update_state,
    get_state_hash,
    validate_hash,
    PipelineError,
    ConfigurationError,
    StateError,
    HashError,
)


class TestSetupLogging:
    def test_setup_logging_returns_logger(self):
        logger = setup_logging()
        assert isinstance(logger, logging.Logger)
        assert logger.name == "llmXive_pipeline"

    def test_setup_logging_idempotent(self):
        logger1 = setup_logging()
        logger2 = setup_logging()
        assert logger1 is logger2
        # Should only have one handler added if called twice
        assert len(logger1.handlers) == 1

    def test_setup_logging_custom_level(self):
        logger = setup_logging(log_level="DEBUG")
        assert logger.level == logging.DEBUG

    def test_setup_logging_invalid_level_raises(self):
        with pytest.raises(ConfigurationError):
            setup_logging(log_level="INVALID_LEVEL")

    def test_setup_logging_file_handler(self):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".log") as tmp:
            tmp_path = tmp.name
        try:
            logger = setup_logging(log_file=tmp_path)
            assert any(isinstance(h, logging.FileHandler) for h in logger.handlers)
        finally:
            os.unlink(tmp_path)


class TestLoadEnvConfig:
    def test_load_env_config_no_env_file(self, tmp_path, monkeypatch):
        # Ensure no .env exists in cwd
        monkeypatch.chdir(tmp_path)
        config = load_env_config()
        assert isinstance(config, dict)

    def test_load_env_config_with_env_file(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        env_file = tmp_path / ".env"
        env_file.write_text("TEST_VAR=value123\nANOTHER_VAR=456")
        
        with patch("code.utils.load_dotenv") as mock_load_dotenv:
            mock_load_dotenv.return_value = True
            config = load_env_config()
            mock_load_dotenv.assert_called_once_with(env_file)


class TestSetSeed:
    def test_set_seed_default(self):
        seed = set_seed()
        assert isinstance(seed, int)

    def test_set_seed_explicit(self):
        seed = set_seed(12345)
        assert seed == 12345

    def test_set_seed_invalid_env_fallback(self, monkeypatch):
        monkeypatch.setenv("RANDOM_SEED", "not_a_number")
        seed = set_seed()
        assert seed == 42  # Should fallback to default


class TestComputeFileHash:
    def test_compute_file_hash_valid(self, tmp_path):
        test_file = tmp_path / "test.txt"
        test_file.write_text("hello world")
        
        hash1 = compute_file_hash(test_file)
        hash2 = compute_file_hash(test_file)
        
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hex length

    def test_compute_file_hash_not_found(self, tmp_path):
        missing_file = tmp_path / "nonexistent.txt"
        with pytest.raises(FileNotFoundError):
            compute_file_hash(missing_file)

    def test_compute_file_hash_invalid_algorithm(self, tmp_path):
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")
        with pytest.raises(HashError):
            compute_file_hash(test_file, algorithm="invalid_algo")


class TestComputeStringHash:
    def test_compute_string_hash(self):
        h1 = compute_string_hash("test")
        h2 = compute_string_hash("test")
        h3 = compute_string_hash("different")
        
        assert h1 == h2
        assert h1 != h3
        assert len(h1) == 64

    def test_compute_string_hash_invalid_algorithm(self):
        with pytest.raises(HashError):
            compute_string_hash("test", algorithm="bad")


class TestLoadState:
    def test_load_state_missing_file(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        state = load_state()
        assert state["version"] == 1
        assert state["artifacts"] == {}

    def test_load_state_valid_yaml(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        state_file = tmp_path / "state.yaml"
        state_file.write_text("version: 2\nartifacts:\n  key: val")
        
        state = load_state(state_file)
        assert state["version"] == 2
        assert state["artifacts"]["key"] == "val"

    def test_load_state_invalid_yaml_raises(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        state_file = tmp_path / "state.yaml"
        state_file.write_text("invalid: yaml: content: [")
        
        with pytest.raises(StateError):
            load_state(state_file)


class TestUpdateState:
    def test_update_state(self, tmp_path):
        state = {"artifacts": {}}
        test_file = tmp_path / "data.csv"
        test_file.write_text("col1,col2\n1,2")
        
        new_state = update_state(state, "test_artifact", test_file)
        
        assert "test_artifact" in new_state["artifacts"]
        assert new_state["artifacts"]["test_artifact"]["path"] == str(test_file)
        assert "hash" in new_state["artifacts"]["test_artifact"]
        assert new_state["artifacts"]["test_artifact"]["updated"] is True

    def test_update_state_missing_file_raises(self):
        state = {"artifacts": {}}
        with pytest.raises(FileNotFoundError):
            update_state(state, "missing", "/nonexistent/path.csv")


class TestGetStateHash:
    def test_get_state_hash_consistency(self):
        state = {"artifacts": {"a": "b"}, "version": 1}
        h1 = get_state_hash(state)
        h2 = get_state_hash(state)
        assert h1 == h2

    def test_get_state_hash_different_state(self):
        state1 = {"artifacts": {"a": "b"}}
        state2 = {"artifacts": {"a": "c"}}
        assert get_state_hash(state1) != get_state_hash(state2)


class TestValidateHash:
    def test_validate_hash_success(self, tmp_path):
        test_file = tmp_path / "file.txt"
        test_file.write_text("content")
        current_hash = compute_file_hash(test_file)
        
        state = {
            "artifacts": {
                "my_art": {"path": str(test_file), "hash": current_hash}
            }
        }
        
        assert validate_hash(state, "my_art") is True

    def test_validate_hash_mismatch(self, tmp_path):
        test_file = tmp_path / "file.txt"
        test_file.write_text("content")
        
        state = {
            "artifacts": {
                "my_art": {"path": str(test_file), "hash": "wrong_hash"}
            }
        }
        
        assert validate_hash(state, "my_art") is False

    def test_validate_hash_missing_artifact(self):
        assert validate_hash({"artifacts": {}}, "missing") is False

    def test_validate_hash_missing_file(self, tmp_path):
        state = {
            "artifacts": {
                "my_art": {"path": "/nonexistent/file", "hash": "abc"}
            }
        }
        assert validate_hash(state, "my_art") is False