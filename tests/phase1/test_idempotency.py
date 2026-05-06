"""Phase 2 idempotency tests (FR-011 / SC-009 / spec 004 US3 acceptance scenarios).

Verifies:
  1. `init_speckit_in` is byte-idempotent on a complete .specify/ tree
     (templates + scripts) on a second invocation.
  2. The skip-if-exists guard at
     ``src/llmxive/agents/project_initializer.py:handle_response`` leaves
     a pre-existing ``.specify/memory/constitution.md`` byte-unchanged
     when the agent is re-invoked. (Per spec 004 Q3 clarification — the
     constitution is a governance document; re-rendering it silently
     mutates downstream Constitution Checks.)
  3. The negative-control: on a fresh project_dir, the agent DOES write
     the constitution from the LLM response (skip-if-exists guard
     doesn't break the happy path).

Per Constitution Principle III: real filesystem (pytest tmp_path), no
mocks. Per Principle V: tests fail fast on any byte-level divergence.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from llmxive.agents.base import AgentContext
from llmxive.agents.project_initializer import ProjectInitializerAgent
from llmxive.backends.base import ChatResponse
from llmxive.speckit.runner import init_speckit_in
from llmxive.types import AgentRegistryEntry

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _sha256_tree(root: Path) -> dict[str, str]:
    """Return {relpath_str: sha256_hex} for every regular file under ``root``."""
    out: dict[str, str] = {}
    for p in sorted(root.rglob("*")):
        if p.is_file():
            out[str(p.relative_to(root))] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def _make_registry_entry() -> AgentRegistryEntry:
    """Construct the same registry entry the production runner builds for
    project_initializer. Mirrors agents/registry.yaml lines 83-97."""
    return AgentRegistryEntry(
        name="project_initializer",
        purpose="Bootstrap a per-project Spec Kit scaffold and render a project constitution.",
        inputs=["idea"],
        outputs=["project_state"],
        prompt_path="agents/prompts/project_initializer.md",
        prompt_version="1.0.0",
        default_backend="dartmouth",
        fallback_backends=["huggingface", "local"],
        default_model="qwen.qwen3.5-122b",
        wall_clock_budget_seconds=300,
        paid_opt_in=False,
    )


def test_init_speckit_in_idempotent_on_complete_tree(tmp_path: Path) -> None:
    """SC-009 first half: scaffold tree byte-identical after second init."""
    project_dir = tmp_path / "PROJ-999-idem-test"
    init_speckit_in(project_dir)

    specify_dir = project_dir / ".specify"
    assert specify_dir.is_dir(), "init_speckit_in must create .specify/"
    assert (specify_dir / "templates").is_dir()
    assert (specify_dir / "scripts").is_dir()
    assert (specify_dir / "memory").is_dir()

    before = _sha256_tree(specify_dir)
    init_speckit_in(project_dir)
    after = _sha256_tree(specify_dir)
    assert before == after, (
        f"init_speckit_in is NOT idempotent at file-content level. "
        f"Diverged keys: {sorted(set(before) ^ set(after)) or '(none)'}, "
        f"changed values: {[k for k in (set(before) & set(after)) if before[k] != after[k]]}"
    )


def test_project_initializer_skips_existing_constitution(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """US3 acceptance scenario 2: re-running the agent on a project with a
    pre-existing constitution must NOT overwrite it (skip-if-exists guard).

    Strategy: monkeypatch the module-level ``__file__`` so the agent computes
    a tmp_path-rooted ``repo`` and creates ``projects/<id>/`` there.
    """
    # Construct a fake repo skeleton where Path(__file__).parent.parent.parent.parent
    # resolves to a tmp_path-rooted directory.
    fake_repo = tmp_path / "fake-repo"
    fake_module_dir = fake_repo / "src" / "llmxive" / "agents"
    fake_module_dir.mkdir(parents=True, exist_ok=True)
    fake_module_file = fake_module_dir / "project_initializer.py"
    fake_module_file.write_text("# placeholder", encoding="utf-8")

    # Also mirror the agents/templates and agents/prompts under the fake repo
    # so render_prompt(...) can find them. (We actually skip render_prompt
    # entirely by exercising only handle_response, which doesn't read those
    # files when the constitution already exists — the skip-if-exists branch
    # is hit BEFORE any template-reading.)
    (fake_repo / ".specify").mkdir()
    (fake_repo / ".specify" / "scripts").mkdir()
    (fake_repo / ".specify" / "templates").mkdir()
    # Copy the real meta-system into the fake repo so init_speckit_in can mirror it.
    import shutil

    real_specify = PROJECT_ROOT / ".specify"
    for sub in ("scripts", "templates"):
        src = real_specify / sub
        dst = fake_repo / ".specify" / sub
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)

    # Pre-stage the project with an existing constitution.
    project_id = "PROJ-test-skip-iter1"
    project_dir = fake_repo / "projects" / project_id
    constitution_path = project_dir / ".specify" / "memory" / "constitution.md"
    constitution_path.parent.mkdir(parents=True, exist_ok=True)
    pre_existing_text = (
        "# Test Constitution — Research Project Constitution\n\n"
        "(deliberately distinct from any LLM output to detect overwrites)\n\n"
        "**Project ID**: PROJ-test-skip-iter1 | **Field**: testing | **Ratified**: 2026-05-05\n"
    )
    constitution_path.write_text(pre_existing_text, encoding="utf-8")
    pre_hash = hashlib.sha256(constitution_path.read_bytes()).hexdigest()

    # Monkeypatch project_initializer's __file__ so its repo calculation
    # lands inside our fake_repo.
    import llmxive.agents.project_initializer as pi_mod

    monkeypatch.setattr(pi_mod, "__file__", str(fake_module_file))

    # Construct agent + ctx + a synthetic ChatResponse whose text would
    # OVERWRITE the constitution if the guard were broken.
    entry = _make_registry_entry()
    agent = ProjectInitializerAgent(entry)
    ctx = AgentContext(
        project_id=project_id,
        run_id="test-run-skip",
        task_id="test-task-skip",
        inputs=[],  # not consulted on the skip-if-exists branch
        metadata={
            "title": "Test",
            "field": "testing",
            "principal_agent_name": "flesh_out",
        },
    )
    response = ChatResponse(
        text="# DIFFERENT Constitution\n\nThis would corrupt a real constitution.\n",
        model="qwen.qwen3.5-122b",
        backend="dartmouth",
        cost_estimate_usd=0.0,
    )

    result = agent.handle_response(ctx, response)
    post_hash = hashlib.sha256(constitution_path.read_bytes()).hexdigest()

    assert pre_hash == post_hash, (
        "skip-if-exists guard FAILED: constitution was overwritten on re-invocation. "
        f"pre={pre_hash[:12]}... post={post_hash[:12]}..."
    )
    # The agent must still return the constitution path (so the orchestrator's
    # state-machine sees a valid output artifact and doesn't treat the no-op
    # as a failure).
    assert result, "handle_response must return a non-empty output list"
    assert any("constitution.md" in p for p in result), result


def test_project_initializer_writes_on_first_invocation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Negative control: with no pre-existing constitution, the agent MUST
    write the LLM response. Ensures the skip-if-exists guard didn't break
    the happy path.
    """
    # Reuse the same fake-repo strategy.
    fake_repo = tmp_path / "fake-repo"
    fake_module_dir = fake_repo / "src" / "llmxive" / "agents"
    fake_module_dir.mkdir(parents=True, exist_ok=True)
    fake_module_file = fake_module_dir / "project_initializer.py"
    fake_module_file.write_text("# placeholder", encoding="utf-8")

    import shutil

    real_specify = PROJECT_ROOT / ".specify"
    (fake_repo / ".specify").mkdir(exist_ok=True)
    for sub in ("scripts", "templates"):
        src = real_specify / sub
        dst = fake_repo / ".specify" / sub
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)

    project_id = "PROJ-test-fresh-iter1"
    # Pre-create the project_dir but NOT the constitution file.
    (fake_repo / "projects" / project_id).mkdir(parents=True)

    import llmxive.agents.project_initializer as pi_mod

    monkeypatch.setattr(pi_mod, "__file__", str(fake_module_file))

    entry = _make_registry_entry()
    agent = ProjectInitializerAgent(entry)
    ctx = AgentContext(
        project_id=project_id,
        run_id="test-run-fresh",
        task_id="test-task-fresh",
        inputs=[],
        metadata={
            "title": "Test",
            "field": "testing",
            "principal_agent_name": "flesh_out",
        },
    )
    expected_text = (
        "# Fresh Constitution — Research Project Constitution\n\n"
        "**Project ID**: PROJ-test-fresh-iter1 | **Field**: testing | **Ratified**: 2026-05-05\n"
    )
    response = ChatResponse(
        text=expected_text,
        model="qwen.qwen3.5-122b",
        backend="dartmouth",
        cost_estimate_usd=0.0,
    )

    agent.handle_response(ctx, response)
    constitution_path = fake_repo / "projects" / project_id / ".specify" / "memory" / "constitution.md"

    assert constitution_path.is_file(), "agent must write constitution on first invocation"
    written = constitution_path.read_text(encoding="utf-8")
    # The agent strips and appends a trailing newline; assert content matches.
    assert written.startswith("# Fresh Constitution"), (
        f"constitution content unexpected: {written[:100]!r}"
    )


def test_full_tree_idempotent_after_two_agent_invocations(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """SC-009 end-to-end: two consecutive handle_response calls on the same
    project_dir leave the FULL .specify/ tree (constitution + 9 mechanical
    files) byte-identical at file-content level.
    """
    fake_repo = tmp_path / "fake-repo"
    fake_module_dir = fake_repo / "src" / "llmxive" / "agents"
    fake_module_dir.mkdir(parents=True, exist_ok=True)
    fake_module_file = fake_module_dir / "project_initializer.py"
    fake_module_file.write_text("# placeholder", encoding="utf-8")

    import shutil

    real_specify = PROJECT_ROOT / ".specify"
    (fake_repo / ".specify").mkdir(exist_ok=True)
    for sub in ("scripts", "templates"):
        src = real_specify / sub
        dst = fake_repo / ".specify" / sub
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)

    project_id = "PROJ-test-fulltree-iter1"
    (fake_repo / "projects" / project_id).mkdir(parents=True)

    import llmxive.agents.project_initializer as pi_mod

    monkeypatch.setattr(pi_mod, "__file__", str(fake_module_file))

    entry = _make_registry_entry()
    agent = ProjectInitializerAgent(entry)
    ctx = AgentContext(
        project_id=project_id,
        run_id="test-run-fulltree",
        task_id="test-task-fulltree",
        inputs=[],
        metadata={
            "title": "Test",
            "field": "testing",
            "principal_agent_name": "flesh_out",
        },
    )
    response_1 = ChatResponse(
        text=(
            "# Fulltree Constitution — Research Project Constitution\n\n"
            "**Project ID**: PROJ-test-fulltree-iter1 | **Field**: testing | **Ratified**: 2026-05-05\n"
        ),
        model="qwen.qwen3.5-122b",
        backend="dartmouth",
        cost_estimate_usd=0.0,
    )
    response_2 = ChatResponse(
        text=(
            "# DIFFERENT Constitution\n\n"
            "would mutate the governance file if guard broken\n"
        ),
        model="qwen.qwen3.5-122b",
        backend="dartmouth",
        cost_estimate_usd=0.0,
    )

    agent.handle_response(ctx, response_1)
    specify_dir = fake_repo / "projects" / project_id / ".specify"
    before = _sha256_tree(specify_dir)
    agent.handle_response(ctx, response_2)
    after = _sha256_tree(specify_dir)

    assert before == after, (
        f"Full .specify/ tree NOT idempotent across two agent invocations. "
        f"Diverged keys: {sorted(set(before) ^ set(after)) or '(none)'}, "
        f"changed values: {[k for k in (set(before) & set(after)) if before[k] != after[k]]}"
    )
