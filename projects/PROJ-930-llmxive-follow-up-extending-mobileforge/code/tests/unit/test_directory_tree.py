"""Unit test for T001: the full project directory tree exists."""

from pathlib import Path

# Project root is three levels up from this test file:
# <root>/code/tests/unit/test_directory_tree.py
PROJECT_ROOT = Path(__file__).resolve().parents[3]
CODE_DIR = PROJECT_ROOT / "code"

REQUIRED_DIRS = [
    CODE_DIR / "data" / "raw",
    CODE_DIR / "data" / "processed",
    CODE_DIR / "data" / "evaluation",
    CODE_DIR / "models",
    CODE_DIR / "utils",
    CODE_DIR / "tests" / "unit",
    CODE_DIR / "tests" / "integration",
]


class TestDirectoryTree:
    def test_all_required_directories_exist(self):
        missing = [d for d in REQUIRED_DIRS if not d.is_dir()]
        assert not missing, f"Missing directories: {missing}"

    def test_directories_are_readable(self):
        for d in REQUIRED_DIRS:
            assert d.is_dir()
            # iterdir must not raise (readability check)
            _ = list(d.iterdir())

    def test_utils_directory_has_existing_modules(self):
        utils_dir = CODE_DIR / "utils"
        assert (utils_dir / "emulator.py").is_file()
        assert (utils_dir / "metrics.py").is_file()