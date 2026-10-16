import json

from llmxive_toolkit import paths

from init_repro_state import ensure_checksums_manifest


def test_creates_empty_checksum_manifest():
    path = paths.data("checksums.json")
    if path.exists():
        path.unlink()
    ensure_checksums_manifest()
    assert path.exists()
    with open(path, "r", encoding="utf-8") as f:
        assert json.load(f) == {}


def test_preserves_existing_manifest():
    path = paths.data("checksums.json")
    existing = {"some_file": "abc123"}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(existing, f)
    ensure_checksums_manifest()
    with open(path, "r", encoding="utf-8") as f:
        assert json.load(f) == existing