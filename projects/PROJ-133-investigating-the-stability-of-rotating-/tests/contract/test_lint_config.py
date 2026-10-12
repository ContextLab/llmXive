"""Contract test that checks linting configuration files exist."""
import pathlib

def test_lint_config():
    root = pathlib.Path(__file__).parents[2]
    required = {".ruff.toml", "pyproject.toml", ".pre-commit-config.yaml"}
    present = {p.name for p in root.iterdir() if p.is_file()}
    assert required.issubset(present), f"Missing lint config files: {required - present}"
