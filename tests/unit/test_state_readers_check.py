"""Tests for the state-artifact reader guard (issue #1139 anti-pattern 1).

Real files only: each test writes a tiny synthetic ``src/llmxive/*.py`` tree into
a temp dir, points the check's ``repo_root`` at it, and asserts the guard's exit
code — plus one test that the REAL repository is clean (locks the invariant).
"""

from __future__ import annotations

from pathlib import Path

from llmxive.checks import state_readers


def _make_repo(tmp_path: Path, modules: dict[str, str]) -> Path:
    pkg = tmp_path / "src" / "llmxive"
    pkg.mkdir(parents=True)
    for name, body in modules.items():
        (pkg / name).write_text(body, encoding="utf-8")
    return tmp_path


_WRITER = (
    "from pathlib import Path\n"
    "def go(root: Path):\n"
    "    (root / 'state' / 'xyz_widget.yaml').write_text('x', encoding='utf-8')\n"
)


def test_write_only_state_artifact_is_flagged(tmp_path, monkeypatch):
    repo = _make_repo(tmp_path, {"writer.py": _WRITER})
    monkeypatch.setattr(state_readers, "_repo_root", lambda: repo)
    monkeypatch.setattr(state_readers, "ALLOWLIST", {})
    assert state_readers.main() == 1  # dead-end: written, read by nobody


def test_writer_with_a_reader_passes(tmp_path, monkeypatch):
    reader = (
        "from pathlib import Path\n"
        "def load(root: Path):\n"
        "    return (root / 'state' / 'xyz_widget.yaml').read_text()\n"
    )
    repo = _make_repo(tmp_path, {"writer.py": _WRITER, "reader.py": reader})
    monkeypatch.setattr(state_readers, "_repo_root", lambda: repo)
    monkeypatch.setattr(state_readers, "ALLOWLIST", {})
    assert state_readers.main() == 0


def test_read_via_custom_wrapper_counts_as_reader(tmp_path, monkeypatch):
    reader = (
        "from pathlib import Path\n"
        "def _ro(p):\n"
        "    return p.read_text() if p.exists() else ''\n"
        "def use(root: Path):\n"
        "    return _ro(root / 'state' / 'xyz_widget.yaml')\n"
    )
    repo = _make_repo(tmp_path, {"writer.py": _WRITER, "reader.py": reader})
    monkeypatch.setattr(state_readers, "_repo_root", lambda: repo)
    monkeypatch.setattr(state_readers, "ALLOWLIST", {})
    assert state_readers.main() == 0


def test_write_inside_nested_block_is_still_detected(tmp_path, monkeypatch):
    # The write is nested in an `if` — the dataflow must still see it as a write
    # (regression guard for the top-level-only bug).
    nested_writer = (
        "from pathlib import Path\n"
        "def go(root: Path, flag: bool):\n"
        "    if flag:\n"
        "        p = root / 'state' / 'xyz_widget.yaml'\n"
        "        p.write_text('x', encoding='utf-8')\n"
    )
    repo = _make_repo(tmp_path, {"writer.py": nested_writer})
    monkeypatch.setattr(state_readers, "_repo_root", lambda: repo)
    monkeypatch.setattr(state_readers, "ALLOWLIST", {})
    assert state_readers.main() == 1


def test_path_helper_and_const_resolve(tmp_path, monkeypatch):
    # `_CACHE` const + `_cache_path` helper resolve so the store's own read-back
    # counts (healthy owns-and-serves store must NOT be flagged).
    store = (
        "from pathlib import Path\n"
        "_CACHE = 'xyz_widget.yaml'\n"
        "def _cache_path(root: Path):\n"
        "    return root / 'state' / _CACHE\n"
        "def save(root: Path):\n"
        "    _cache_path(root).write_text('x', encoding='utf-8')\n"
        "def load(root: Path):\n"
        "    return _cache_path(root).read_text()\n"
    )
    repo = _make_repo(tmp_path, {"store.py": store})
    monkeypatch.setattr(state_readers, "_repo_root", lambda: repo)
    monkeypatch.setattr(state_readers, "ALLOWLIST", {})
    assert state_readers.main() == 0


def test_allowlist_suppresses_a_dead_end(tmp_path, monkeypatch):
    repo = _make_repo(tmp_path, {"writer.py": _WRITER})
    monkeypatch.setattr(state_readers, "_repo_root", lambda: repo)
    monkeypatch.setattr(state_readers, "ALLOWLIST", {"xyz_widget.yaml": "external"})
    assert state_readers.main() == 0


def test_dynamic_per_project_name_is_out_of_scope(tmp_path, monkeypatch):
    # A per-project f"{id}.json" file carries no fixed basename → not a candidate,
    # so a write-only per-project store does NOT false-positive.
    store = (
        "from pathlib import Path\n"
        "def save(root: Path, pid: str):\n"
        "    (root / 'state' / f'{pid}.json').write_text('x', encoding='utf-8')\n"
    )
    repo = _make_repo(tmp_path, {"store.py": store})
    monkeypatch.setattr(state_readers, "_repo_root", lambda: repo)
    monkeypatch.setattr(state_readers, "ALLOWLIST", {})
    assert state_readers.main() == 0


def test_real_repository_has_no_dead_ends():
    """The live repo must pass — locks the invariant so any new persist-and-forget
    state writer fails CI."""
    assert state_readers.main() == 0
