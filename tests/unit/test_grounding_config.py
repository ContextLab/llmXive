import llmxive.config as config


def test_unpaywall_email_default():
    assert config.unpaywall_email() == "llmxive@gmail.com"


def test_unpaywall_email_env_override(monkeypatch):
    monkeypatch.setenv("UNPAYWALL_EMAIL", "x@example.org")
    assert config.unpaywall_email() == "x@example.org"


def test_unpaywall_email_blank_is_none(monkeypatch):
    monkeypatch.setenv("UNPAYWALL_EMAIL", "")
    assert config.unpaywall_email() is None  # tier-2 disabled when explicitly blank


def test_grounding_cache_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("LLMXIVE_REPO_ROOT", str(tmp_path))
    d = config.grounding_cache_dir()
    assert d == tmp_path / "state" / "grounding-cache"
