import json
import tempfile
from pathlib import Path
import pytest
from code.state_manager import initialize_state_file, load_state, update_state_flag


def test_initialize_state_file_creates_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        state_path = Path(tmpdir) / "state.json"
        result = initialize_state_file(state_path)
        
        assert state_path.exists()
        assert "p_n_available" in result
        assert result["p_n_available"] is None
        assert "last_updated" in result


def test_load_state_raises_if_missing():
    with tempfile.TemporaryDirectory() as tmpdir:
        state_path = Path(tmpdir) / "missing.json"
        with pytest.raises(FileNotFoundError):
            load_state(state_path)


def test_update_state_flag():
    with tempfile.TemporaryDirectory() as tmpdir:
        state_path = Path(tmpdir) / "state.json"
        initialize_state_file(state_path)
        
        new_state = update_state_flag(state_path, "p_n_available", True)
        
        assert new_state["p_n_available"] is True
        
        # Verify file on disk
        loaded = load_state(state_path)
        assert loaded["p_n_available"] is True
