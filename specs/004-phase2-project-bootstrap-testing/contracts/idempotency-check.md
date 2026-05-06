# Contract: Idempotency-check pytest harness

**File**: `tests/phase1/test_idempotency.py`
**Produced by**: this spec's `/speckit-implement` workflow (US3 / SC-009)
**Consumed by**: pytest in CI, the maintainer running US3 audits
**Purpose**: Verify FR-011 / SC-009 — full byte-level idempotency of `project_initializer` on a sibling already at `project_initialized`.

## Test inventory

| Test name | Purpose | Source: spec scenario |
|-|-|-|
| `test_init_speckit_in_idempotent_on_complete_tree` | Run `init_speckit_in` twice on a complete `.specify/` tree (templates + scripts + memory); assert all 9 mechanical files have unchanged sha256 | US3 acceptance scenario 1 |
| `test_project_initializer_skips_existing_constitution` | Instantiate `ProjectInitializerAgent` directly; call `handle_response` with mock LLM-output text on a tree that already has `.specify/memory/constitution.md`; assert the file's sha256 is unchanged | US3 acceptance scenario 2 |
| `test_project_initializer_writes_on_first_invocation` | Same agent on a fresh project_dir; assert the constitution IS written and matches the LLM-output (regression: don't break the happy path with the new skip-if-exists guard) | US3 implicit (negative-control) |
| `test_full_tree_idempotent_after_two_agent_invocations` | End-to-end: two consecutive `handle_response` calls; assert ALL 10 files (9 mechanical + 1 constitution) are byte-identical | FR-011 / SC-009 |

## Test pattern

```python
import hashlib
from pathlib import Path

import pytest

from llmxive.agents.base import AgentContext
from llmxive.agents.project_initializer import ProjectInitializerAgent
from llmxive.backends.base import ChatResponse
from llmxive.speckit.runner import init_speckit_in
from llmxive.types import AgentRegistryEntry


def _sha256_tree(root: Path) -> dict[str, str]:
    """Return {relpath: sha256} for every regular file under root."""
    out: dict[str, str] = {}
    for p in root.rglob("*"):
        if p.is_file():
            out[str(p.relative_to(root))] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def test_init_speckit_in_idempotent_on_complete_tree(tmp_path: Path):
    """SC-009: scaffold tree must be byte-identical after second init."""
    project_dir = tmp_path / "PROJ-test-idem"
    init_speckit_in(project_dir)
    before = _sha256_tree(project_dir / ".specify")
    init_speckit_in(project_dir)
    after = _sha256_tree(project_dir / ".specify")
    assert before == after, f"divergence: {set(before.items()) ^ set(after.items())}"


def test_project_initializer_skips_existing_constitution(tmp_path: Path, monkeypatch):
    """US3 acceptance 2: re-running the agent on a project with a pre-existing
    constitution must NOT overwrite it (skip-if-exists guard from Q3)."""
    # Pre-stage a project_dir with a constitution already in place.
    project_dir = tmp_path / "PROJ-test-skip"
    init_speckit_in(project_dir)
    constitution_path = project_dir / ".specify" / "memory" / "constitution.md"
    constitution_path.parent.mkdir(parents=True, exist_ok=True)
    pre_existing_text = "# Test Constitution\n\n**Project ID**: PROJ-test-skip | **Field**: testing | **Ratified**: 2026-05-05\n"
    constitution_path.write_text(pre_existing_text, encoding="utf-8")
    pre_hash = hashlib.sha256(constitution_path.read_bytes()).hexdigest()

    # Build a context pointing at this project; the agent's handle_response
    # should detect the existing file and skip.
    entry = AgentRegistryEntry(
        name="project_initializer",
        purpose="test",
        prompt_path="agents/prompts/project_initializer.md",
        prompt_version="1.0.0",
        default_backend="dartmouth",
        fallback_backends=[],
        default_model="qwen.qwen3.5-122b",
        wall_clock_budget_seconds=300,
    )
    agent = ProjectInitializerAgent(entry)

    # Monkeypatch the project_dir resolution to point at tmp_path.
    # (The exact mechanism depends on how the agent computes project_dir;
    # the fix in research.md Decision 2 reads it from `repo / "projects" / ctx.project_id`,
    # so we set ctx.project_id to a path that resolves there.)
    ctx = AgentContext(
        project_id="PROJ-test-skip",
        metadata={"title": "Test", "field": "testing", "principal_agent_name": "flesh_out"},
        inputs=[],
    )
    monkeypatch.setattr(
        "llmxive.agents.project_initializer.Path",
        lambda *a: tmp_path / "fake-repo-root" if False else Path(*a),
    )  # see note below — actual monkeypatching shape depends on the fix

    # Simulate the LLM having returned different text from what's on disk.
    response = ChatResponse(
        text="# Different Constitution\n\nThis would corrupt the existing one.\n",
        model="qwen.qwen3.5-122b",
        backend="dartmouth",
        cost_estimate_usd=0.0,
    )
    agent.handle_response(ctx, response)

    post_hash = hashlib.sha256(constitution_path.read_bytes()).hexdigest()
    assert pre_hash == post_hash, "skip-if-exists guard failed: constitution was overwritten"


def test_project_initializer_writes_on_first_invocation(tmp_path: Path, monkeypatch):
    """Negative control: with no pre-existing constitution, the agent MUST write one.
    Ensures the skip-if-exists guard didn't break the happy path."""
    # ... similar setup, but constitution_path.is_file() is False going in.
    # Assert that after handle_response, the file exists and contains the LLM response text.


def test_full_tree_idempotent_after_two_agent_invocations(tmp_path: Path, monkeypatch):
    """FR-011 / SC-009 end-to-end: two consecutive agent invocations leave the
    full .specify/ tree byte-identical at file-content level."""
    # ... runs the agent twice, computes _sha256_tree before and after the
    # SECOND invocation, asserts equality.
```

## Notes on the monkeypatching

The harness needs to redirect `project_dir = repo / "projects" / ctx.project_id` to a `tmp_path`-based root. The cleanest mechanism is to factor the path resolution out of `ProjectInitializerAgent.handle_response` into a small helper that accepts an explicit `project_root`, then passing `tmp_path` in tests. The patch in research.md Decision 2 should add this seam if it doesn't already exist; if not, the alternative is to monkeypatch the `Path(__file__).resolve().parent.parent.parent.parent` calculation that yields `repo`. Either approach is acceptable; the test contract requires that the harness can run without writing into the actual repository.

## Run-cost expectation

Pytest collection: <1s. Each test: <2s on a developer workstation (no network, no LLM, no large file copies). Total module wall-clock: <10s. Suitable for CI without time budget concerns.

## Acceptance evidence (referenced from §3.X.5 of the diagnostic report)

When the harness passes:

```text
$ pytest tests/phase1/test_idempotency.py -v
============================= test session starts ==============================
collected 4 items

tests/phase1/test_idempotency.py::test_init_speckit_in_idempotent_on_complete_tree PASSED
tests/phase1/test_idempotency.py::test_project_initializer_skips_existing_constitution PASSED
tests/phase1/test_idempotency.py::test_project_initializer_writes_on_first_invocation PASSED
tests/phase1/test_idempotency.py::test_full_tree_idempotent_after_two_agent_invocations PASSED

============================== 4 passed in 4.21s ===============================
```

This block is quoted verbatim into the diagnostic report as evidence for SC-009.
