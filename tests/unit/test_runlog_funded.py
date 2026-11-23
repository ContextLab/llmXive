"""Task 16 (spec 027): run-log entries record the backend that really served
the call and what it really cost.

The cost invariant lets a FUNDED (huggingface) entry carry a non-zero cost
without the paid opt-in (Constitution 1.4.0, "Funded services") while any
other backend's non-zero cost still needs ``LLMXIVE_PAID_OPT_IN``. The three
run-log writers (Agent, SlashCommandAgent, LLMXiveImplementer) record the sum
of the settled cost of every response received and the last response's backend.
"""

from __future__ import annotations

import json
import shutil
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest

from llmxive.agents import base as agent_base
from llmxive.agents import implementer as implementer_mod
from llmxive.agents import registry as registry_loader
from llmxive.agents.base import Agent, AgentContext
from llmxive.agents.implementer import LLMXiveImplementer
from llmxive.backends.base import ChatMessage, ChatResponse
from llmxive.speckit.slash_command import SlashCommandAgent, SlashCommandContext
from llmxive.state import project as project_store
from llmxive.state.runlog import CostInvariantError, append_entry
from llmxive.types import (
    AgentRegistryEntry,
    BackendName,
    Outcome,
    Project,
    RunLogEntry,
    Stage,
)

REAL_REPO = Path(__file__).resolve().parents[2]


def _mk_state(root: Path) -> None:
    (root / "state" / "run-log").mkdir(parents=True, exist_ok=True)


def _entry(backend: BackendName, cost: float) -> RunLogEntry:
    now = datetime.now(UTC)
    return RunLogEntry(
        run_id="11111111-1111-1111-1111-111111111111",
        entry_id=str(uuid4()),
        agent_name="test_agent",
        project_id="PROJ-001-cost",
        task_id="33333333-3333-3333-3333-333333333333",
        inputs=[],
        outputs=[],
        backend=backend,
        model_name="acme/alpha-large:prov-a",
        prompt_version="1.0.0",
        started_at=now,
        ended_at=now,
        outcome=Outcome.SUCCESS,
        cost_estimate_usd=cost,
    )


def test_funded_cost_is_logged_without_paid_opt_in(tmp_path, monkeypatch):
    monkeypatch.delenv("LLMXIVE_PAID_OPT_IN", raising=False)
    _mk_state(tmp_path)
    path = append_entry(_entry(BackendName.HUGGINGFACE, 0.0123), repo_root=tmp_path)
    row = json.loads(path.read_text().splitlines()[-1])
    assert row["backend"] == "huggingface"
    assert row["cost_estimate_usd"] == 0.0123


def test_dartmouth_cost_still_needs_the_opt_in(tmp_path, monkeypatch):
    monkeypatch.delenv("LLMXIVE_PAID_OPT_IN", raising=False)
    _mk_state(tmp_path)
    with pytest.raises(CostInvariantError):
        append_entry(_entry(BackendName.DARTMOUTH, 0.0123), repo_root=tmp_path)


def _hf_response(cost: float, text: str = "VALID") -> ChatResponse:
    return ChatResponse(text, "acme/alpha-large:prov-a", "huggingface", cost_estimate_usd=cost)


class _ProbeAgent(Agent):
    def build_messages(self, ctx):
        return [ChatMessage(role="user", content="go")]

    def handle_response(self, ctx, response):
        return ["ok-artifact"]


def test_agent_run_log_records_the_response_backend_and_cost(monkeypatch):
    monkeypatch.delenv("LLMXIVE_PAID_OPT_IN", raising=False)
    captured: list[RunLogEntry] = []
    monkeypatch.setattr("llmxive.state.runlog.append_entry", lambda e: captured.append(e))
    monkeypatch.setattr(agent_base, "chat_with_fallback", lambda m, **k: _hf_response(0.0123))
    reg = AgentRegistryEntry(
        name="probe",
        purpose="funded run-log probe",
        prompt_path="agents/prompts/research_reviewer.md",
        prompt_version="1.0.0",
        profile="deep_review",
        wall_clock_budget_seconds=60,
        paid_opt_in=False,
    )
    ctx = AgentContext(project_id="PROJ-999-probe", run_id="r", task_id="t", inputs=[])
    _ProbeAgent(reg).run(ctx)
    assert len(captured) == 1
    assert captured[0].backend is BackendName.HUGGINGFACE
    assert captured[0].cost_estimate_usd == 0.0123


def test_agent_malformed_retries_sum_the_cost_of_every_response(monkeypatch):
    captured: list[RunLogEntry] = []
    monkeypatch.setattr("llmxive.state.runlog.append_entry", lambda e: captured.append(e))
    replies = iter([_hf_response(0.01, "bad"), _hf_response(0.02, "VALID")])
    monkeypatch.setattr(agent_base, "chat_with_fallback", lambda m, **k: next(replies))

    class _Picky(_ProbeAgent):
        def handle_response(self, ctx, response):
            if response.text != "VALID":
                raise agent_base.MalformedResponseError("not valid")
            return ["ok"]

    reg = AgentRegistryEntry(
        name="probe", purpose="retry cost probe", prompt_path="agents/prompts/research_reviewer.md",
        prompt_version="1.0.0", profile="deep_review",
        wall_clock_budget_seconds=60, paid_opt_in=False,
    )
    _Picky(reg).run(AgentContext(project_id="PROJ-999-probe", run_id="r", task_id="t", inputs=[]))
    assert captured[0].cost_estimate_usd == pytest.approx(0.03)


class _SlashProbe(SlashCommandAgent):
    def slash_command_name(self) -> str:
        return "speckit.test"

    def mechanical_step(self, ctx):
        return {}

    def build_prompt(self, ctx, mechanical_output):
        return [ChatMessage(role="user", content="hi")]

    def write_artifacts(self, ctx, mechanical_output, llm_response):
        out = ctx.project_dir / "notes" / "reply.txt"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(llm_response.text, encoding="utf-8")
        return [str(out.relative_to(ctx.project_dir.parent.parent))]


def test_slash_command_run_log_records_the_response_backend_and_cost(tmp_path, monkeypatch):
    monkeypatch.delenv("LLMXIVE_PAID_OPT_IN", raising=False)
    captured: list[RunLogEntry] = []
    monkeypatch.setattr(
        "llmxive.speckit.slash_command.runlog.append_entry",
        lambda e, **kw: captured.append(e),
    )
    monkeypatch.setattr(
        "llmxive.speckit.slash_command.chat_with_fallback",
        lambda m, **k: _hf_response(0.0123),
    )
    proj = tmp_path / "projects" / "PROJ-001-test"
    proj.mkdir(parents=True)
    ctx = SlashCommandContext(
        project_id="PROJ-001-test", project_dir=proj, run_id="r", task_id="t",
        inputs=[], expected_outputs=[], prompt_template_path=Path("/tmp/x.md"),
        profile="standard_generation", prompt_version="1.0.0", agent_name="a",
    )
    _SlashProbe().run(ctx)
    assert captured[0].backend is BackendName.HUGGINGFACE
    assert captured[0].cost_estimate_usd == 0.0123


@pytest.fixture
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    (tmp_path / "agents").mkdir()
    shutil.copy(REAL_REPO / "agents" / "registry.yaml", tmp_path / "agents" / "registry.yaml")
    shutil.copytree(REAL_REPO / "agents" / "prompts", tmp_path / "agents" / "prompts")
    for sub in ("projects", "run-log", "locks"):
        (tmp_path / "state" / sub).mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("LLMXIVE_REPO_ROOT", str(tmp_path))
    monkeypatch.delenv("LLMXIVE_PAID_OPT_IN", raising=False)
    return tmp_path


def test_implementer_run_log_attributes_funded_backend_and_cost(repo, monkeypatch):
    proj_id = "PROJ-907-funded"
    source = repo / "projects" / proj_id / "paper" / "source"
    source.mkdir(parents=True)
    (source / "main.tex").write_text(
        "\\documentclass{article}\\begin{document}body\\end{document}\n", encoding="utf-8"
    )
    round_dir = repo / "specs" / "auto-revisions" / proj_id / "round-1"
    round_dir.mkdir(parents=True)
    (round_dir / "tasks.md").write_text(
        "- [ ] T001 [writing] Fix the abstract typo\n"
        "- [ ] T002 [writing] Tighten section 2\n",
        encoding="utf-8",
    )
    now = datetime.now(UTC)
    project_store.save(
        Project(
            id=proj_id, title="funded", field="test", current_stage=Stage.PAPER_REVIEW,
            created_at=now, updated_at=now, artifact_hashes={},
            revision_spec_path=str(round_dir.relative_to(repo)),
        ),
        repo_root=repo,
    )
    costs = iter([0.01, 0.02])
    monkeypatch.setattr(
        implementer_mod, "chat_with_fallback", lambda m, **k: _hf_response(next(costs), "ok")
    )
    agent = LLMXiveImplementer(registry_loader.get("llmxive_implementer", repo_root=repo))
    entry = agent.run(
        AgentContext(project_id=proj_id, run_id=str(uuid4()), task_id=str(uuid4()), inputs=[], metadata={})
    )
    assert entry.backend is BackendName.HUGGINGFACE
    assert entry.model_name == "acme/alpha-large:prov-a"
    assert entry.cost_estimate_usd == pytest.approx(0.03)


# --- Mixed-backend runs: cost is attributed to the backend that served it -----


def _resp(backend: str, cost: float, text: str = "VALID") -> ChatResponse:
    return ChatResponse(text, "acme/alpha-large:prov-a", backend, cost_estimate_usd=cost)


def _rows(root: Path) -> list[dict]:
    return [
        json.loads(line)
        for f in (root / "state" / "run-log").rglob("*.jsonl")
        for line in f.read_text().splitlines()
    ]


def test_breakdown_must_sum_to_total():
    e = _entry(BackendName.HUGGINGFACE, 0.03)
    with pytest.raises(ValueError, match="sum"):
        RunLogEntry(**{**e.model_dump(), "cost_by_backend": {BackendName.HUGGINGFACE: 0.01}})


def test_entry_without_breakdown_stays_valid(tmp_path, monkeypatch):
    monkeypatch.delenv("LLMXIVE_PAID_OPT_IN", raising=False)
    _mk_state(tmp_path)
    from llmxive.contract_validate import validate

    row = _entry(BackendName.DARTMOUTH, 0.0).model_dump(mode="json")
    del row["cost_by_backend"]  # an entry written before the field existed
    validate("run-log-entry", row)
    append_entry(_entry(BackendName.DARTMOUTH, 0.0), repo_root=tmp_path)


class _Picky(_ProbeAgent):
    def handle_response(self, ctx, response):
        if response.text != "VALID":
            raise agent_base.MalformedResponseError("not valid")
        return ["ok"]


def _probe_reg() -> AgentRegistryEntry:
    return AgentRegistryEntry(
        name="probe", purpose="mixed backend probe", prompt_path="agents/prompts/research_reviewer.md",
        prompt_version="1.0.0", profile="deep_review",
        wall_clock_budget_seconds=60, paid_opt_in=False,
    )


def _run_picky(repo: Path, monkeypatch, replies: list[ChatResponse]) -> None:
    it = iter(replies)
    monkeypatch.setattr(agent_base, "chat_with_fallback", lambda m, **k: next(it))
    _Picky(_probe_reg()).run(
        AgentContext(project_id="PROJ-999-probe", run_id=str(uuid4()), task_id=str(uuid4()), inputs=[])
    )


def test_agent_funded_then_free_writes_valid_entry_with_funded_cost(repo, monkeypatch):
    _run_picky(repo, monkeypatch, [_resp("huggingface", 0.01, "bad"), _resp("dartmouth", 0.0)])
    (row,) = _rows(repo)
    assert row["backend"] == "dartmouth"
    assert row["cost_estimate_usd"] == pytest.approx(0.01)
    assert row["cost_by_backend"] == {"huggingface": pytest.approx(0.01)}


def test_agent_paid_then_funded_without_opt_in_is_rejected_for_the_paid_part(repo, monkeypatch):
    with pytest.raises(CostInvariantError):
        _run_picky(repo, monkeypatch, [_resp("dartmouth", 0.02, "bad"), _resp("huggingface", 0.01)])
    assert _rows(repo) == []


def test_agent_funded_then_paid_without_opt_in_is_rejected_for_the_paid_part(repo, monkeypatch):
    with pytest.raises(CostInvariantError):
        _run_picky(repo, monkeypatch, [_resp("huggingface", 0.01, "bad"), _resp("dartmouth", 0.02)])


def test_agent_paid_then_funded_with_opt_in_logs_both_parts(repo, monkeypatch):
    monkeypatch.setenv("LLMXIVE_PAID_OPT_IN", "1")
    _run_picky(repo, monkeypatch, [_resp("dartmouth", 0.02, "bad"), _resp("huggingface", 0.01)])
    (row,) = _rows(repo)
    assert row["cost_by_backend"] == {"dartmouth": pytest.approx(0.02), "huggingface": pytest.approx(0.01)}
    assert row["cost_estimate_usd"] == pytest.approx(0.03)


def _bootstrap_implementer(repo: Path) -> tuple[str, LLMXiveImplementer]:
    proj_id = "PROJ-908-mixed"
    source = repo / "projects" / proj_id / "paper" / "source"
    source.mkdir(parents=True)
    (source / "main.tex").write_text(
        "\\documentclass{article}\\begin{document}body\\end{document}\n", encoding="utf-8"
    )
    round_dir = repo / "specs" / "auto-revisions" / proj_id / "round-1"
    round_dir.mkdir(parents=True)
    (round_dir / "tasks.md").write_text(
        "- [ ] T001 [writing] Fix the abstract typo\n- [ ] T002 [writing] Tighten section 2\n",
        encoding="utf-8",
    )
    now = datetime.now(UTC)
    project_store.save(
        Project(
            id=proj_id, title="mixed", field="test", current_stage=Stage.PAPER_REVIEW,
            created_at=now, updated_at=now, artifact_hashes={},
            revision_spec_path=str(round_dir.relative_to(repo)),
        ),
        repo_root=repo,
    )
    return proj_id, LLMXiveImplementer(registry_loader.get("llmxive_implementer", repo_root=repo))


def _run_impl(repo: Path, monkeypatch, replies: list[ChatResponse]) -> RunLogEntry:
    proj_id, agent = _bootstrap_implementer(repo)
    it = iter(replies)
    monkeypatch.setattr(implementer_mod, "chat_with_fallback", lambda m, **k: next(it))
    return agent.run(
        AgentContext(project_id=proj_id, run_id=str(uuid4()), task_id=str(uuid4()), inputs=[], metadata={})
    )


def test_implementer_funded_then_free_writes_valid_entry_with_funded_cost(repo, monkeypatch):
    entry = _run_impl(repo, monkeypatch, [_resp("huggingface", 0.01, "ok"), _resp("dartmouth", 0.0, "ok")])
    assert entry.backend is BackendName.DARTMOUTH
    assert entry.cost_by_backend == {BackendName.HUGGINGFACE: pytest.approx(0.01)}
    assert entry.cost_estimate_usd == pytest.approx(0.01)


def test_implementer_paid_then_funded_without_opt_in_is_rejected_for_the_paid_part(repo, monkeypatch):
    with pytest.raises(CostInvariantError):
        _run_impl(repo, monkeypatch, [_resp("dartmouth", 0.02, "ok"), _resp("huggingface", 0.01, "ok")])


def test_implementer_funded_then_paid_without_opt_in_is_rejected_for_the_paid_part(repo, monkeypatch):
    with pytest.raises(CostInvariantError):
        _run_impl(repo, monkeypatch, [_resp("huggingface", 0.01, "ok"), _resp("dartmouth", 0.02, "ok")])


def test_the_funded_exemption_follows_the_one_funded_backend_set(tmp_path, monkeypatch):
    """Final review B1: which backends are exempt from the paid opt-in is read from
    ``model_selection.types.FUNDED_BACKENDS``, not a second hardcoded name."""
    import llmxive.state.runlog as runlog_mod

    monkeypatch.delenv("LLMXIVE_PAID_OPT_IN", raising=False)
    _mk_state(tmp_path)
    monkeypatch.setattr(runlog_mod, "FUNDED_BACKENDS", frozenset())  # nothing funded
    with pytest.raises(CostInvariantError):
        append_entry(_entry(BackendName.HUGGINGFACE, 0.0123), repo_root=tmp_path)
