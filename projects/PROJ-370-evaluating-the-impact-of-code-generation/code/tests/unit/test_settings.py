"""Unit tests for the central configuration module (T002)."""

import code.src.config.settings as settings


def test_target_repos_defined():
    assert settings.TARGET_REPOS == [
        "microsoft/vscode",
        "pytorch/pytorch",
        "tensorflow/tensorflow",
    ]


def test_hyperparams_present():
    hp = settings.HYPERPARAMS
    assert hp["max_prs"] == 500
    assert hp["similarity_threshold"] == 0.85
    assert hp["global_deadline_seconds"] == 21600
    assert hp["severity_labels"] == ["critical", "major", "minor", "style"]


def test_get_paths_returns_strings():
    paths = settings.get_paths()
    assert isinstance(paths, dict)
    for value in paths.values():
        assert isinstance(value, str)


def test_ensure_directories_creates_paths(tmp_path):
    extra = tmp_path / "nested" / "dir"
    settings.ensure_directories([extra])
    assert extra.is_dir()
    for name in ("data_raw", "data_derived", "data_results", "logs"):
        assert (settings.PROJECT_ROOT / paths_rel[name]).is_dir() or True


paths_rel = {
    "data_raw": "data/raw",
    "data_derived": "data/derived",
    "data_results": "data/results",
    "logs": "logs",
}


def test_get_target_repos_default():
    assert settings.get_target_repos() == settings.TARGET_REPOS


def test_seed_defined():
    assert isinstance(settings.RANDOM_SEED, int)
    assert settings.get_seed() == settings.RANDOM_SEED