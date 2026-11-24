"""T002c: verify data/artifacts/ exists at the project root."""
from pathlib import Path

from llmxive_toolkit import paths

def test_data_artifacts_dir_exists():
    artifacts_dir = paths.data("artifacts")
    assert artifacts_dir.is_dir(), f"{artifacts_dir} does not exist"
    assert (artifacts_dir / ".gitkeep").exists()