"""Plumbing tests for the code_adapter step (spec 024).

These exercise the DETERMINISTIC split/write logic with ``chat_with_fallback``
monkeypatched to a fixed multi-file response — no network. The real end-to-end
(actual free-model) run is driven separately; per the constitution this stub is
only for the deterministic plumbing, not as a primary mock test of the LLM.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from llmxive.backends.base import ChatResponse
from llmxive.execution.analysis_runner import extract_run_commands
from llmxive.paper_reprocess import code_adapter

# The real repo root (so registry_loader.get("code_adapter") + its prompt
# resolve); pdir/submodule live in tmp so nothing real is mutated.
_REPO_ROOT = Path(__file__).resolve().parents[2]

# A well-formed multi-file response: a runnable code/run.py that writes a real
# artifact under data/, a quickstart.md whose single bash fence runs it, and a
# code/README.md documenting the simplification.
_GOOD_RESPONSE = """\
<!-- FILE: code/run.py -->
```python
import csv, os
os.makedirs("data", exist_ok=True)
with open("data/result.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["metric", "value"])
    w.writerow(["accuracy", 0.5])
print("wrote data/result.csv")
```

<!-- FILE: quickstart.md -->
# Quickstart (CPU adaptation)

```bash
python code/run.py
```

<!-- FILE: code/README.md -->
Simplified to a 2-row synthetic proxy of the paper's accuracy metric.
"""

# A response whose only "files" escape the project dir (path traversal) — must
# be ignored, leaving no usable code/*.py + quickstart, hence [].
_ESCAPE_RESPONSE = """\
<!-- FILE: ../evil.py -->
```python
print("should never be written")
```

<!-- FILE: quickstart.md -->
```bash
python ../evil.py
```
"""


def _patch_chat(monkeypatch: pytest.MonkeyPatch, response_text: str) -> None:
    """Monkeypatch the router used inside code_adapter to a fixed reply.

    Patches the underlying ``chat_with_fallback`` symbol that ``_call_adapter``
    imports, so the FULL deterministic path (registry lookup → prompt assembly →
    split → write) is exercised against a fixed model reply — only the network
    call is stubbed.
    """
    def _fake_chat(messages, **kwargs):  # noqa: ANN001
        return ChatResponse(text=response_text, model="stub", backend="stub")

    import llmxive.backends.router as router
    monkeypatch.setattr(router, "chat_with_fallback", _fake_chat)


def _make_submodule(tmp_path: Path) -> Path:
    """A minimal vendored repo with one entry script (so source collection has
    something to read)."""
    sub = tmp_path / "external" / "demo-repo"
    sub.mkdir(parents=True)
    (sub / "train.py").write_text("import torch\nprint('gpu heavy')\n", encoding="utf-8")
    return sub


def test_adapt_code_writes_files_and_quickstart_is_runnable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pdir = tmp_path / "PROJ-999-demo"
    pdir.mkdir()
    sub = _make_submodule(tmp_path)
    _patch_chat(monkeypatch, _GOOD_RESPONSE)

    written = code_adapter.adapt_code(
        pdir,
        repo_root=_REPO_ROOT,
        paper_summary="**Title:** Demo\n\n**Abstract:** A demo paper.",
        submodule_abs=sub,
        file_tree="train.py",
        entry_scripts=["train.py"],
    )

    assert set(written) == {"code/run.py", "code/README.md", "quickstart.md"}
    # The files actually landed on disk under pdir.
    assert (pdir / "code" / "run.py").is_file()
    assert (pdir / "code" / "README.md").is_file()
    quickstart = pdir / "quickstart.md"
    assert quickstart.is_file()
    # The quickstart's python command is extractable by the execution gate.
    cmds = extract_run_commands(quickstart.read_text(encoding="utf-8"))
    assert cmds == ["python code/run.py"]


def test_adapt_code_ignores_path_escape(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pdir = tmp_path / "PROJ-998-demo"
    pdir.mkdir()
    sub = _make_submodule(tmp_path)
    _patch_chat(monkeypatch, _ESCAPE_RESPONSE)

    written = code_adapter.adapt_code(
        pdir,
        repo_root=_REPO_ROOT,
        paper_summary="x",
        submodule_abs=sub,
        file_tree="train.py",
        entry_scripts=["train.py"],
    )

    # The ../evil.py path is ignored; with no in-tree code/*.py the result is [].
    assert written == []
    assert not (tmp_path / "evil.py").exists()
    assert not (pdir.parent / "evil.py").exists()
    # Nothing was written under pdir either.
    assert not (pdir / "code").exists()


def test_adapt_code_llm_error_returns_empty(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pdir = tmp_path / "PROJ-997-demo"
    pdir.mkdir()
    sub = _make_submodule(tmp_path)

    def _boom(**kwargs):  # noqa: ANN003
        raise RuntimeError("model exploded")

    monkeypatch.setattr(code_adapter, "_call_adapter", _boom)

    written = code_adapter.adapt_code(
        pdir,
        repo_root=_REPO_ROOT,
        paper_summary="x",
        submodule_abs=sub,
        file_tree="train.py",
        entry_scripts=["train.py"],
    )

    assert written == []
    # No partial output written on the error path.
    assert not (pdir / "code").exists()
    assert not (pdir / "quickstart.md").exists()
