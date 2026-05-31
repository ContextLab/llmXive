"""Bounded planner revision-with-feedback loop (plan_cmd).

A malformed planner artifact (e.g. a contracts schema with an internal `---`
multi-document marker, or an unquoted `: ` that breaks YAML) used to hard-crash
`PlannerAgent.write_artifacts` on the first deterministic-guard failure, marking
the run FAILED and stranding the project at ``clarified`` with no retry.

These tests drive the REAL ``write_artifacts`` / ``_write_and_validate`` code
path with a constructed ``PlannerAgent`` and a fake backend supplied ONLY as a
collaborator (the subject under test is plan_cmd's retry logic, not the LLM).
They are fully offline: no real network/LLM call is ever issued, and the
backend is injected via ``make_backend`` monkeypatch.

Covers:
- retry-and-succeed: invalid first contracts schema → valid second response.
- exhaust-retries: invalid on every attempt → last guard exception re-raised,
  no partial artifacts left on disk (fail-closed preserved).
- no-backend: ``make_backend`` returns None + invalid first response → raises
  immediately, never retries (offline-safety gate).
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


# ──────────────────────────────────────────────────────────────────────
# Shared fixtures / builders
# ──────────────────────────────────────────────────────────────────────

def _valid_five_file_block(*, bad_contract: str | None = None) -> str:
    """Return a 5-file FILE-marker block. When ``bad_contract`` is given it
    replaces the FIRST contracts schema body, so we can inject an invalid
    schema while leaving every other artifact valid (isolating the guard
    under test)."""
    plan = (
        "# Implementation Plan: Code Duplication Study\n\n"
        "## Summary\n\nWe measure clone density against LLM perplexity using an "
        "AST detector and a pretrained code model, then correlate.\n\n"
        "## Constitution Check\n\n"
        "Principle I (single source of truth): the detector lives in one module. "
        "Principle II (evidence): every claim cites a metric. "
        "Principle III (real tests): we run on a real corpus.\n\n"
        "## Technical Context\n\nPython 3.11, tree-sitter, transformers.\n"
    )
    research = (
        "# Research\n\n## Decisions\n\n"
        "We use tree-sitter for AST parsing because it is fast and language-agnostic. "
        "The corpus is drawn from public Python repositories.\n"
    )
    data_model = (
        "# Data Model\n\n## Clone Cluster\n\nA set of duplicated code spans.\n\n"
        "## Perplexity Record\n\nPer-file perplexity from the code model.\n"
    )
    quickstart = (
        "# Quickstart\n\n## Setup\n\nInstall deps then run the pipeline against a "
        "checked-out corpus directory; results land in results/.\n"
    )
    contract_a = (
        bad_contract
        if bad_contract is not None
        else "title: Clone Cluster\ntype: object\nproperties:\n  files:\n    type: array\n"
    )
    contract_b = "title: Perplexity Record\ntype: object\nproperties:\n  value:\n    type: number\n"
    return (
        "<!-- FILE: plan.md -->\n" + plan + "\n"
        "<!-- FILE: research.md -->\n" + research + "\n"
        "<!-- FILE: data-model.md -->\n" + data_model + "\n"
        "<!-- FILE: quickstart.md -->\n" + quickstart + "\n"
        "<!-- FILE: contracts/clone-cluster.schema.yaml -->\n" + contract_a + "\n"
        "<!-- FILE: contracts/perplexity-record.schema.yaml -->\n" + contract_b + "\n"
    )


# Two real PROJ-552 failure modes for an invalid contracts schema:
#   1. an internal `---` makes it a multi-document YAML (safe_load → not a
#      single mapping/sequence).
#   2. an unquoted description with a bare `: ` ("mapping values are not
#      allowed here") is a YAML scalar-grammar error.
_BAD_CONTRACT_MULTI_DOC = (
    "title: Clone Cluster\ntype: object\n---\ntitle: Sneaky Second Doc\ntype: object\n"
)
_BAD_CONTRACT_UNQUOTED_COLON = (
    "title: Clone Cluster\ntype: object\nproperties:\n  files:\n    type: array\n"
    "    description: list of spans (target: >=95%)\n"
)


def _make_planner_ctx(tmp_path: Path):
    """Build a SlashCommandContext + mechanical_output for the Planner.

    Mirrors tests/integration/test_phase4_plan_tasks.py::_make_planner_ctx so
    write_artifacts' repo-root resolution and the template-vs-real guard run
    exactly as in a real repo.
    """
    from llmxive.speckit.slash_command import SlashCommandContext
    from llmxive.types import BackendName

    proj_id = "PROJ-TEST-plan-revloop"
    proj_dir = tmp_path / "projects" / proj_id
    feature_dir = proj_dir / "specs" / "001-test"
    feature_dir.mkdir(parents=True)
    tmpl_dst = tmp_path / ".specify" / "templates"
    tmpl_dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(REPO_ROOT / ".specify" / "templates", tmpl_dst)
    # The corrective re-call genuinely runs build_prompt → render_prompt, which
    # reads agents/prompts/planner.md relative to the (tmp) repo root. Copy the
    # real agents/ tree so the re-call renders against the real prompt (real
    # inputs — the subject under test is the retry loop, not the prompt).
    shutil.copytree(REPO_ROOT / "agents", tmp_path / "agents")
    (feature_dir / "spec.md").write_text(
        "# Feature Specification: Test\n\n## Functional Requirements\n\n"
        "- **FR-001**: System MUST do a thing.\n",
        encoding="utf-8",
    )
    # A minimal project constitution so build_prompt has real content to render.
    mem = proj_dir / ".specify" / "memory"
    mem.mkdir(parents=True, exist_ok=True)
    (mem / "constitution.md").write_text(
        "# Constitution\n\n## Principle I\n\nSingle source of truth.\n",
        encoding="utf-8",
    )
    ctx = SlashCommandContext(
        project_id=proj_id, project_dir=proj_dir, run_id="r", task_id="t",
        inputs=[], expected_outputs=[],
        prompt_template_path=tmp_path / "ignored.md",
        default_backend=BackendName.DARTMOUTH, fallback_backends=[],
        default_model="m", prompt_version="1.0.0", agent_name="planner",
    )
    # dataset_block="" so build_prompt skips the live dataset resolver.
    mech = {
        "feature_dir": str(feature_dir),
        "spec_path": str(feature_dir / "spec.md"),
        "dataset_block": "",
    }
    return ctx, mech, feature_dir


class _FakeBackend:
    """A collaborator backend whose ``chat`` returns canned multi-file replies.

    Substitutes the LLM only — this is NOT a mock of the unit under test
    (plan_cmd's retry loop). Records every call so a test can assert how many
    corrective re-calls fired.
    """

    def __init__(self, replies: list[str]):
        self._replies = list(replies)
        self.calls: list[dict] = []

    def chat(self, messages, **kwargs):
        from llmxive.backends.base import ChatResponse

        self.calls.append({"messages": messages, "kwargs": kwargs})
        if not self._replies:
            raise AssertionError("FakeBackend.chat called more times than expected")
        text = self._replies.pop(0)
        return ChatResponse(text=text, model="m", backend="dartmouth")


def _leftover_artifacts(feature_dir: Path) -> list[str]:
    return [
        p.name
        for p in feature_dir.rglob("*")
        if p.is_file() and p.name != "spec.md"
    ]


@pytest.fixture(autouse=True)
def _stub_plan_panel(monkeypatch: pytest.MonkeyPatch):
    """The live 4-lens plan panel needs a real backend and is out of scope for
    the retry-loop tests; stub it to a no-op so a successful write returns
    cleanly without a network call."""
    from llmxive.speckit.plan_cmd import PlannerAgent

    monkeypatch.setattr(
        PlannerAgent, "_run_plan_panel", lambda self, ctx, feature_dir, repo: None
    )


# ──────────────────────────────────────────────────────────────────────
# Retry-and-succeed
# ──────────────────────────────────────────────────────────────────────

class TestRetryAndSucceed:
    @pytest.mark.parametrize(
        "bad_contract",
        [_BAD_CONTRACT_MULTI_DOC, _BAD_CONTRACT_UNQUOTED_COLON],
        ids=["internal-multi-doc", "unquoted-colon"],
    )
    def test_invalid_first_then_valid_second_succeeds(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, bad_contract: str
    ) -> None:
        import llmxive.backends.router as router
        from llmxive.backends.base import ChatResponse
        from llmxive.speckit.plan_cmd import PlannerAgent

        ctx, mech, feature_dir = _make_planner_ctx(tmp_path)

        # The corrective re-call (attempt 2) returns a fully-valid block.
        fake = _FakeBackend(replies=[_valid_five_file_block()])
        monkeypatch.setattr(router, "make_backend", lambda name: fake)
        # plan_cmd imports make_backend lazily from the router module, so
        # patching the router attribute is sufficient.

        first = ChatResponse(
            text=_valid_five_file_block(bad_contract=bad_contract),
            model="m", backend="dartmouth",
        )
        agent = PlannerAgent()
        written = agent.write_artifacts(ctx, mech, first)

        # Succeeded → returns the written file list and valid artifacts on disk.
        assert written, "expected a non-empty written-file list after retry"
        assert (feature_dir / "plan.md").is_file()
        assert (feature_dir / "contracts" / "clone-cluster.schema.yaml").is_file()
        # The retried (valid) contract is what landed on disk, not the bad one.
        on_disk = (feature_dir / "contracts" / "clone-cluster.schema.yaml").read_text(
            encoding="utf-8"
        )
        assert "Sneaky Second Doc" not in on_disk
        assert "target: >=95%" not in on_disk
        # Exactly one corrective re-call fired (initial response was the arg).
        assert len(fake.calls) == 1, f"expected 1 corrective re-call, got {len(fake.calls)}"
        # The corrective message quotes the guard error so the model can fix it.
        last_user = fake.calls[0]["messages"][-1]
        assert last_user.role == "user"
        assert "FR-007" in last_user.content or "contracts" in last_user.content.lower()


# ──────────────────────────────────────────────────────────────────────
# Exhaust retries → fail-closed
# ──────────────────────────────────────────────────────────────────────

class TestExhaustRetries:
    def test_all_invalid_raises_last_guard_and_leaves_no_partial(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import llmxive.backends.router as router
        from llmxive.backends.base import ChatResponse
        from llmxive.speckit._research_guard import InconsistentDataModel
        from llmxive.speckit.plan_cmd import MAX_PLAN_REVISION_RETRIES, PlannerAgent

        ctx, mech, feature_dir = _make_planner_ctx(tmp_path)

        bad_block = _valid_five_file_block(bad_contract=_BAD_CONTRACT_MULTI_DOC)
        # Every corrective re-call also returns an invalid block.
        fake = _FakeBackend(replies=[bad_block] * (MAX_PLAN_REVISION_RETRIES + 1))
        monkeypatch.setattr(router, "make_backend", lambda name: fake)

        first = ChatResponse(text=bad_block, model="m", backend="dartmouth")
        agent = PlannerAgent()
        with pytest.raises(InconsistentDataModel):
            agent.write_artifacts(ctx, mech, first)

        # Fail-closed: no partial artifacts remain on disk.
        assert _leftover_artifacts(feature_dir) == [], (
            f"partial artifacts left after exhausting retries: "
            f"{_leftover_artifacts(feature_dir)}"
        )
        # Exactly MAX_PLAN_REVISION_RETRIES corrective re-calls fired.
        assert len(fake.calls) == MAX_PLAN_REVISION_RETRIES


# ──────────────────────────────────────────────────────────────────────
# No backend → never retries (offline-safety gate)
# ──────────────────────────────────────────────────────────────────────

class TestNoBackendNoRetry:
    def test_no_backend_raises_immediately_without_retry(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import llmxive.backends.router as router
        from llmxive.backends.base import ChatResponse
        from llmxive.speckit._research_guard import InconsistentDataModel
        from llmxive.speckit.plan_cmd import PlannerAgent

        ctx, mech, feature_dir = _make_planner_ctx(tmp_path)

        # No usable backend → the loop must NOT attempt a corrective re-call.
        monkeypatch.setattr(router, "make_backend", lambda name: None)

        first = ChatResponse(
            text=_valid_five_file_block(bad_contract=_BAD_CONTRACT_MULTI_DOC),
            model="m", backend="dartmouth",
        )
        agent = PlannerAgent()
        with pytest.raises(InconsistentDataModel):
            agent.write_artifacts(ctx, mech, first)

        # Fail-closed and offline-safe: nothing written, no retry happened.
        assert _leftover_artifacts(feature_dir) == []

    def test_make_backend_raising_also_fails_closed(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import llmxive.backends.router as router
        from llmxive.backends.base import ChatResponse
        from llmxive.speckit._research_guard import InconsistentDataModel
        from llmxive.speckit.plan_cmd import PlannerAgent

        ctx, mech, feature_dir = _make_planner_ctx(tmp_path)

        def _boom(name):
            raise RuntimeError("backend construction failed (offline)")

        monkeypatch.setattr(router, "make_backend", _boom)

        first = ChatResponse(
            text=_valid_five_file_block(bad_contract=_BAD_CONTRACT_MULTI_DOC),
            model="m", backend="dartmouth",
        )
        agent = PlannerAgent()
        with pytest.raises(InconsistentDataModel):
            agent.write_artifacts(ctx, mech, first)
        assert _leftover_artifacts(feature_dir) == []
