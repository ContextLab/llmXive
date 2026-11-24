"""T001 verification: assert existence of all top-level scaffold folders."""
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROJECT_NAME = "PROJ-1011-llmxive-follow-up-extending-researchstud"

REQUIRED_DIRS = [
    PROJECT_ROOT / "code",
    PROJECT_ROOT / "data",
    PROJECT_ROOT / "tests",
    # Nested scaffold path checked by the verification suite
    PROJECT_ROOT / "projects" / PROJECT_NAME,
    PROJECT_ROOT / "projects" / PROJECT_NAME / "code",
    PROJECT_ROOT / "projects" / PROJECT_NAME / "data",
    PROJECT_ROOT / "projects" / PROJECT_NAME / "tests",
]


def test_scaffold_directories():
    missing = [str(d) for d in REQUIRED_DIRS if not d.is_dir()]
    assert not missing, f"Missing required scaffold directories: {missing}"