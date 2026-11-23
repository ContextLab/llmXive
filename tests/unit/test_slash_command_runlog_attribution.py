"""Spec 026 F3: the Spec Kit failure path must never FABRICATE run-log
attribution. ``agents/base.py`` already records ``backend=None,
model_name=None`` for any run that fails before a real ``ChatResponse`` comes
back (spec 026 slice 7 / D4 — the field feeds paper authorship, so nothing
truthful can be written until a model actually answers). This mirrors that
same guarantee for ``SlashCommandAgent.run()`` (the Specifier/Clarifier/
Planner/Tasker/Implementer base class), which previously seeded
``backend_used = BackendName.DARTMOUTH`` / ``model_used = "unknown"`` as
placeholders — writing a fabricated backend/model into the run log even when
no backend was ever contacted.

Three distinct failure points are covered (matching the review finding):
  (a) failure BEFORE ``chat_with_fallback`` is reached (prompt construction).
  (b) selection failure before any backend contact (``ModelUnavailable``,
      raised by ``select()`` — no candidate was ever dispatched).
  (c) a real candidate WAS attempted (``execute()`` dispatched at least one
      candidate to a live backend) but exhausted before producing a
      ``ChatResponse`` (``ChainExhausted``).

Per the decision documented alongside ``backend_used``/``model_used`` in
``slash_command.py``: both (b) and (c) record NO attribution. Even though (c)
means SOME backend was actually dialed, that candidate produced no content
that fed any artifact — recording its model would misleadingly claim
authorship for a call that contributed nothing, which is exactly what D4
forbids. This test asserts that both surfaces behave identically to (a).

``route_chat`` is imported INSIDE ``chat_with_fallback`` at call time (a
function-local import, to dodge a module cycle), so monkeypatching the
``llmxive.model_selection.route`` module's ``route_chat`` attribute lets us
drive the REAL ``chat_with_fallback`` — including its real
``ModelUnavailable``/``ChainExhausted`` -> ``BackendUnavailable`` translation
— rather than replacing ``chat_with_fallback`` itself.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from llmxive.backends.base import BackendUnavailable, ChatMessage, ChatResponse
from llmxive.model_selection.execute import ChainExhausted
from llmxive.model_selection.types import ModelUnavailable
from llmxive.speckit.slash_command import SlashCommandAgent, SlashCommandContext
from llmxive.types import Outcome


class _RunnableSlashAgent(SlashCommandAgent):
    """Minimal concrete agent — every abstract method is a trivial real impl."""

    def slash_command_name(self) -> str:
        return "speckit.test"

    def mechanical_step(self, ctx: SlashCommandContext) -> dict[str, Any]:
        return {}

    def build_prompt(self, ctx, mechanical_output):  # type: ignore[no-untyped-def]
        return [ChatMessage(role="user", content="hi")]

    def write_artifacts(self, ctx, mechanical_output, llm_response):  # type: ignore[no-untyped-def]
        return []


class _PromptBuildFailsAgent(_RunnableSlashAgent):
    """Fails BEFORE ``chat_with_fallback`` is ever reached (case a)."""

    def build_prompt(self, ctx, mechanical_output):  # type: ignore[no-untyped-def]
        raise ValueError("prompt construction blew up")


class _WritesAnOutputAgent(_RunnableSlashAgent):
    """Really writes one artifact. A run that writes nothing is recorded as
    SKIPPED, so the success path needs a genuine output."""

    def write_artifacts(self, ctx, mechanical_output, llm_response):  # type: ignore[no-untyped-def]
        out = ctx.project_dir / "notes" / "reply.txt"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(llm_response.text, encoding="utf-8")
        return [str(out.relative_to(ctx.project_dir.parent.parent))]


def _ctx(project_dir: Path | None = None) -> SlashCommandContext:
    return SlashCommandContext(
        project_id="PROJ-001-test",
        project_dir=project_dir or Path("/tmp/llmxive-test/projects/PROJ-001-test"),
        run_id="r",
        task_id="t",
        inputs=[],
        expected_outputs=[],
        prompt_template_path=Path("/tmp/x.md"),
        profile="standard_generation",
        prompt_version="1.0.0",
        agent_name="a",
    )


def _capture_entries(monkeypatch) -> list[Any]:
    captured: list[Any] = []
    monkeypatch.setattr(
        "llmxive.speckit.slash_command.runlog.append_entry",
        lambda entry, **kw: captured.append(entry),
    )
    return captured


def test_a_prompt_construction_failure_records_no_attribution(monkeypatch):
    entries = _capture_entries(monkeypatch)

    with pytest.raises(ValueError, match="prompt construction blew up"):
        _PromptBuildFailsAgent().run(_ctx())

    assert len(entries) == 1
    entry = entries[0]
    assert entry.outcome == Outcome.FAILED
    assert entry.backend is None
    assert entry.model_name is None


def test_b_selection_failure_before_backend_contact_records_no_attribution(monkeypatch):
    """``select()`` raises ``ModelUnavailable`` — no candidate was EVER
    dispatched to a real backend. ``chat_with_fallback`` translates this to
    ``BackendUnavailable`` (its documented outage-classification contract);
    the run log must still record no backend/model."""
    entries = _capture_entries(monkeypatch)

    def _raise_model_unavailable(*a, **k):
        raise ModelUnavailable("no eligible candidate for profile")

    monkeypatch.setattr(
        "llmxive.model_selection.route.route_chat", _raise_model_unavailable
    )

    with pytest.raises(BackendUnavailable):
        _RunnableSlashAgent().run(_ctx())

    assert len(entries) == 1
    entry = entries[0]
    assert entry.outcome == Outcome.FAILED
    assert entry.backend is None
    assert entry.model_name is None


def test_c_candidate_attempted_but_exhausted_records_no_attribution(monkeypatch):
    """``execute()`` dispatched at least one REAL candidate (that's exactly
    what ``ChainExhausted`` means — selection succeeded, dispatch was
    attempted, every candidate exhausted) but no ``ChatResponse`` ever came
    back. Per the D4-aligned decision, this STILL records no attribution:
    an attempted-but-failed candidate produced no content that fed any
    artifact, so crediting it would be exactly the fabrication D4 forbids."""
    entries = _capture_entries(monkeypatch)

    def _raise_chain_exhausted(*a, **k):
        raise ChainExhausted("every candidate exhausted after real dispatch")

    monkeypatch.setattr(
        "llmxive.model_selection.route.route_chat", _raise_chain_exhausted
    )

    with pytest.raises(BackendUnavailable):
        _RunnableSlashAgent().run(_ctx())

    assert len(entries) == 1
    entry = entries[0]
    assert entry.outcome == Outcome.FAILED
    assert entry.backend is None
    assert entry.model_name is None


def test_success_still_records_real_attribution(monkeypatch, tmp_path):
    """Sanity check: the happy path is unaffected — a real ``ChatResponse``
    still gets its real backend/model recorded (never ``None``)."""
    entries = _capture_entries(monkeypatch)
    monkeypatch.setattr(
        "llmxive.speckit.slash_command.chat_with_fallback",
        lambda messages, **kw: ChatResponse(text="ok", model="real-model", backend="dartmouth"),
    )

    project_dir = tmp_path / "projects" / "PROJ-001-test"
    project_dir.mkdir(parents=True)
    _WritesAnOutputAgent().run(_ctx(project_dir))

    assert (project_dir / "notes" / "reply.txt").read_text(encoding="utf-8") == "ok"
    assert len(entries) == 1
    entry = entries[0]
    assert entry.outcome == Outcome.SUCCESS
    assert entry.outputs == ["projects/PROJ-001-test/notes/reply.txt"]
    assert entry.backend is not None and entry.backend.value == "dartmouth"
    assert entry.model_name == "real-model"
