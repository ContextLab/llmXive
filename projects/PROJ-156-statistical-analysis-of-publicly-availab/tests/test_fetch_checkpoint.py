import json
from pathlib import Path

def test_fetch_checkpoint_exists():
    checkpoint_path = Path("data") / "checkpoints" / "fetch_checkpoint.json"
    assert checkpoint_path.is_file(), "Fetch checkpoint file should exist"
    with open(checkpoint_path, "r") as f:
        data = json.load(f)
    assert "completed_games" in data
    assert isinstance(data["completed_games"], list)
    assert len(data["completed_games"]) > 0