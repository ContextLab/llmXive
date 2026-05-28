"""Integration tests for ImplementerReviser + filesystem re-verification
(spec 015 T058, FR-027 + discrepancy #1 + #49).

Fake-backend tests cover the multi-file code-revise contract and the
filesystem-assertion re-verification helper (which closes #49 — today the
implementer marks tasks [X] without proving the deliverable landed).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pytest

from llmxive.convergence.revisers.implementer_reviser import (
    ImplementerReviser,
    _is_code_artifact,
    verify_task_assertions,
)
from llmxive.convergence.types import Concern, Severity

_REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass
class _FakeResponse:
    text: str
    model: str = "fake-model"
    backend: str = "fake"


@dataclass
class _FakeBackend:
    response_text: str
    last_messages: list = None  # type: ignore[assignment]

    def chat(self, messages, model=None):  # type: ignore[no-untyped-def]
        self.last_messages = list(messages)
        return _FakeResponse(text=self.response_text)


# --- predicate tests ------------------------------------------------------


def test_is_code_artifact_matches_expected_paths():
    assert _is_code_artifact("code/helpers/util.py")
    assert _is_code_artifact("tests/unit/test_foo.py")
    assert _is_code_artifact("src/llmxive/foo.py")
    assert _is_code_artifact("data/raw/dataset.csv")
    assert _is_code_artifact("scripts/run.sh")
    # excluded:
    assert not _is_code_artifact("specs/000-x/spec.md")
    assert not _is_code_artifact("paper/source/main.tex")
    assert not _is_code_artifact(".llmxive/state.json")
    assert not _is_code_artifact("docs/api.md")


# --- filesystem re-verification helper ----------------------------------


def test_verify_task_assertions_passes_when_paths_exist(tmp_path: Path):
    # Create files the tasks claim to have produced.
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "x.py").write_text("# code")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_x.py").write_text("# tests")
    tasks = (
        "## Tasks\n"
        "- [X] T001 Write `src/x.py`\n"
        "- [X] T002 Add `tests/test_x.py`\n"
    )
    unverified = verify_task_assertions(tasks, repo_root=tmp_path)
    assert unverified == []


def test_verify_task_assertions_flags_missing_paths(tmp_path: Path):
    tasks = (
        "## Tasks\n"
        "- [X] T001 Write `src/missing.py`\n"
        "- [X] T002 Add `tests/also_missing.py`\n"
        "- [ ] T003 Future work `src/later.py`\n"  # not checked off, should be ignored
    )
    unverified = verify_task_assertions(tasks, repo_root=tmp_path)
    missing = {p for _, p in unverified}
    assert "src/missing.py" in missing
    assert "tests/also_missing.py" in missing
    assert "src/later.py" not in missing  # only completed tasks are verified


def test_verify_task_assertions_handles_letter_suffixed_ids(tmp_path: Path):
    """Atomized tasks have suffixed ids like T001a, T001b."""
    tasks = "- [X] T001a Write `src/a.py`\n"
    unverified = verify_task_assertions(tasks, repo_root=tmp_path)
    assert unverified == [("T001a", "src/a.py")]


# --- ImplementerReviser end-to-end --------------------------------------


def test_implementer_reviser_edits_code_files(tmp_path: Path):
    code_key = "src/proj/util.py"
    test_key = "tests/unit/test_util.py"
    artifacts = {
        code_key: "def add(a, b):\n    return a + b\n",
        test_key: "from proj.util import add\n\ndef test_add():\n    assert add(1,2)==3\n",
        "__spec_md__": "# spec\n## FR\n- FR-001: addition.\n- FR-002: subtraction (NEW).\n",
        "__plan_md__": "# plan\nphase 1: arithmetic.\n",
        "__tasks_md__": "- [X] T001 add `src/proj/util.py`\n",
        "__constitution__": "Principle V: real-call testing.",
        "__analyze_report__": "code_quality: util.py lacks docstring.",
    }
    concerns = [
        Concern(
            id="C1", reviewer="implementation_completeness", severity=Severity.CODE,
            artifact=code_key, location="add",
            text="FR-002 (subtraction) is unimplemented.",
        ),
    ]
    new_code = (
        "def add(a, b):\n    \"\"\"Add two numbers.\"\"\"\n    return a + b\n\n"
        "def sub(a, b):\n    \"\"\"Subtract two numbers.\"\"\"\n    return a - b\n"
    )
    fake_reply = {
        "updated_artifacts": {code_key: new_code},
        "responses": [
            {"concern_id": "C1", "response": "Added sub() function",
             "what_changed": "util.py now has sub()",
             "artifacts_changed": [code_key]},
        ],
    }
    backend = _FakeBackend(response_text=json.dumps(fake_reply))
    reviser = ImplementerReviser(
        backend=backend, repo_root=_REPO_ROOT, project_id="PROJ-000-x",
        project_root=tmp_path,
        summarize_cache_dir=tmp_path / "summarize_cache",
    )
    updated, responses = reviser.revise(artifacts, concerns)

    assert "def sub" in updated[code_key]
    # Test file should NOT have been touched (LLM didn't emit it).
    assert updated[test_key] == artifacts[test_key]
    assert any(r.concern_id == "C1" for r in responses)


def test_implementer_reviser_appends_unverified_filesystem_responses(tmp_path: Path):
    """The reviser MUST surface tasks marked [X] whose deliverable paths
    do not exist post-revise — closes discrepancy #49 (today the
    implementer can claim completion without producing the artifact)."""
    code_key = "src/proj/x.py"
    (tmp_path / "src" / "proj").mkdir(parents=True)
    (tmp_path / "src" / "proj" / "x.py").write_text("# real file")
    # tasks claims TWO files; only the first actually exists.
    tasks_md = (
        "- [X] T001 wrote `src/proj/x.py`\n"
        "- [X] T002 wrote `src/proj/missing.py`\n"
    )
    artifacts = {
        code_key: "# real file",
        "__tasks_md__": tasks_md,
    }
    fake_reply = {"updated_artifacts": {}, "responses": []}
    backend = _FakeBackend(response_text=json.dumps(fake_reply))
    reviser = ImplementerReviser(
        backend=backend, repo_root=_REPO_ROOT, project_id="PROJ-000-x",
        project_root=tmp_path,
        summarize_cache_dir=tmp_path / "summarize_cache",
    )
    _, responses = reviser.revise(artifacts, [])

    unverified = [r for r in responses if r.concern_id.startswith("<filesystem-unverified:")]
    assert len(unverified) == 1
    assert "T002" in unverified[0].concern_id
    assert "src/proj/missing.py" in unverified[0].response


def test_implementer_reviser_rejects_writes_outside_code_set(tmp_path: Path):
    code_key = "src/proj/util.py"
    artifacts = {code_key: "# code"}
    fake_reply = {
        "updated_artifacts": {
            code_key: "# code v2",
            "specs/000-x/spec.md": "# malicious spec rewrite",  # not code
        },
        "responses": [],
    }
    backend = _FakeBackend(response_text=json.dumps(fake_reply))
    reviser = ImplementerReviser(
        backend=backend, repo_root=_REPO_ROOT, project_id="PROJ-000-x",
        project_root=tmp_path,
        summarize_cache_dir=tmp_path / "summarize_cache",
    )
    with pytest.raises(RuntimeError, match="outside the declared code set"):
        reviser.revise(artifacts, [])


def test_implementer_reviser_raises_when_no_code_artifacts(tmp_path: Path):
    backend = _FakeBackend(response_text='{"updated_artifacts":{}, "responses":[]}')
    reviser = ImplementerReviser(
        backend=backend, repo_root=_REPO_ROOT, project_id="PROJ-000-x",
        project_root=tmp_path,
        summarize_cache_dir=tmp_path / "summarize_cache",
    )
    with pytest.raises(ValueError, match="no code-side artifacts"):
        reviser.revise({"specs/000-x/spec.md": "# spec only"}, [])


def test_implementer_reviser_pads_missing_responses(tmp_path: Path):
    code_key = "src/x.py"
    backend = _FakeBackend(
        response_text=json.dumps(
            {
                "updated_artifacts": {code_key: "# new"},
                "responses": [{"concern_id": "C1", "response": "fixed", "what_changed": "x"}],
            }
        )
    )
    reviser = ImplementerReviser(
        backend=backend, repo_root=_REPO_ROOT, project_id="PROJ-000-x",
        project_root=tmp_path,
        summarize_cache_dir=tmp_path / "summarize_cache",
    )
    concerns = [
        Concern(id="C1", reviewer="code_quality", severity=Severity.CODE,
                artifact=code_key, location="", text="x"),
        Concern(id="C2", reviewer="filesystem_hygiene", severity=Severity.WRITING,
                artifact=code_key, location="", text="y"),
    ]
    _, responses = reviser.revise({code_key: "# code"}, concerns)
    by_id = {r.concern_id: r for r in responses}
    assert by_id["C2"].response == "<missing>"


def test_implementer_reviser_name():
    assert ImplementerReviser.name == "implementer"
