"""Kickback-concern plumbing to the flesh-out agent (#... spec-015 follow-up).

Root cause: a downstream (spec/plan) convergence panel that catches a
methodology/science problem (e.g. a CIRCULAR VALIDATION) kicks the project
back to ``flesh_out_in_progress`` — but the concern body was DELETED with the
``convergence_kickback.yaml`` sentinel before flesh_out re-ran, so the agent
re-elaborated the same flawed idea and the panel kicked it straight back →
infinite loop until the 3-strike human escalation.

These tests pin the two-part fix:

1. REACTIVE plumbing
   - ``graph._decide_next_stage``: when a consumed ``convergence_kickback``
     routes to a CONTENT stage, persist the concern bodies to a durable
     ``projects/<id>/idea/kickback_feedback.md`` BEFORE the sentinel is gone.
   - ``FleshOutAgent.build_messages``: read that file and inject it into the
     user message; NEVER pick it as the idea body.
   - ``FleshOutAgent._persist``: remove the feedback file once consumed.

2. PROMPT contract (``agents/prompts/flesh_out.md``)
   - a "validation independence" rule + an address-downstream-concerns
     instruction, both domain-general (no field-specific jargon).

No mocks of the model: ``build_messages`` is exercised against the REAL prompt
file (copied into a temp repo) with the librarian short-circuited by an empty
title/field query; routing runs the REAL ``_decide_next_stage`` against on-disk
sentinels.
"""

from __future__ import annotations

import shutil
from datetime import UTC, datetime
from pathlib import Path

import pytest
import yaml

from llmxive.agents.base import AgentContext
from llmxive.types import Project, Stage

REAL_REPO = Path(__file__).resolve().parents[2]
FLESH_OUT_PROMPT = REAL_REPO / "agents" / "prompts" / "flesh_out.md"
FEEDBACK_FILENAME = "kickback_feedback.md"


# --------------------------------------------------------------------------
# Part 1a — routing persists the concern to idea/kickback_feedback.md
# --------------------------------------------------------------------------


def _project(stage: Stage = Stage.SPECIFIED) -> Project:
    now = datetime.now(UTC)
    return Project(
        id="PROJ-902-circular-validation",
        title="X",
        field="mathematics",
        current_stage=stage,
        created_at=now,
        updated_at=now,
        speckit_research_dir="specs/001-x",
    )


def _write_convergence_kickback(
    memory_dir: Path,
    *,
    to_stage: str,
    stage: str = "spec",
    concern_texts: list[str],
    reason: str = "panel did not converge",
) -> None:
    memory_dir.mkdir(parents=True, exist_ok=True)
    concerns = [
        {
            "id": f"c{i}",
            "reviewer": "panel_spec_method_soundness",
            "severity": "methodology",
            "artifact": "spec.md",
            "location": "Methodology",
            "text": t,
            "round": 1,
        }
        for i, t in enumerate(concern_texts)
    ]
    (memory_dir / "convergence_kickback.yaml").write_text(
        yaml.safe_dump(
            {
                "to_stage": to_stage,
                "worst_severity": "methodology",
                "reason": reason,
                "stage": stage,
                "unresolved_concerns": concerns,
                "artifact_links": ["spec.md"],
            }
        ),
        encoding="utf-8",
    )


CIRCULAR_CONCERN = (
    "The composite complexity metric is validated against crossing number, "
    "but crossing number is one of the metric's own input components — this is "
    "a circular validation against a mathematically dependent quantity."
)


def test_routing_to_flesh_out_persists_feedback_file(tmp_path: Path) -> None:
    from llmxive.pipeline.graph import _decide_next_stage

    project = _project()
    project_dir = tmp_path / "projects" / project.id
    mem = project_dir / ".specify" / "memory"
    _write_convergence_kickback(
        mem,
        to_stage="flesh_out_in_progress",
        concern_texts=[CIRCULAR_CONCERN],
        reason="methodology concern unresolved",
    )

    nxt = _decide_next_stage(project, project_dir, repo_root=tmp_path)
    assert nxt == Stage.FLESH_OUT_IN_PROGRESS

    feedback = project_dir / "idea" / FEEDBACK_FILENAME
    assert feedback.exists(), "routing must persist the kickback concern for flesh_out"
    text = feedback.read_text(encoding="utf-8")
    # The concern body survives the sentinel deletion.
    assert "circular validation" in text.lower()
    assert "crossing number" in text
    # The reason (provenance) is carried too.
    assert "methodology concern unresolved" in text
    # Clear human/LLM-facing heading.
    assert text.lstrip().startswith("#")


def test_routing_to_brainstormed_persists_feedback_file(tmp_path: Path) -> None:
    from llmxive.pipeline.graph import _decide_next_stage

    project = _project()
    project_dir = tmp_path / "projects" / project.id
    mem = project_dir / ".specify" / "memory"
    _write_convergence_kickback(
        mem,
        to_stage="brainstormed",
        concern_texts=[CIRCULAR_CONCERN],
    )

    nxt = _decide_next_stage(project, project_dir, repo_root=tmp_path)
    assert nxt == Stage.BRAINSTORMED
    feedback = project_dir / "idea" / FEEDBACK_FILENAME
    assert feedback.exists()
    assert "crossing number" in feedback.read_text(encoding="utf-8")


def test_routing_to_noncontent_stage_does_not_persist_feedback(tmp_path: Path) -> None:
    """A kickback that routes to a non-content stage (e.g. ``planned``) must NOT
    drop an idea-stage feedback file — that file is only meaningful to the
    flesh-out / brainstorm content agents."""
    from llmxive.pipeline.graph import _decide_next_stage

    project = _project()
    project_dir = tmp_path / "projects" / project.id
    mem = project_dir / ".specify" / "memory"
    _write_convergence_kickback(
        mem,
        to_stage="planned",
        stage="tasks",
        concern_texts=["some non-idea-stage concern"],
    )

    _decide_next_stage(project, project_dir, repo_root=tmp_path)
    feedback = project_dir / "idea" / FEEDBACK_FILENAME
    assert not feedback.exists()


# --------------------------------------------------------------------------
# Part 1b — FleshOutAgent.build_messages reads + excludes the feedback file
# --------------------------------------------------------------------------


def _flesh_out_agent():
    from types import SimpleNamespace

    from llmxive.agents.idea_lifecycle import FleshOutAgent

    entry = SimpleNamespace(
        name="flesh_out",
        prompt_path="agents/prompts/flesh_out.md",
        default_backend="dartmouth",
        fallback_backends=[],
        default_model="m",
        prompt_version="1.2.0",
    )
    return FleshOutAgent(entry)


def _temp_repo_with_prompt(tmp_path: Path) -> Path:
    """A temp repo containing only the real flesh_out prompt (so render_prompt
    resolves) — keeps build_messages off the real projects/ tree."""
    repo = tmp_path / "repo"
    (repo / "agents" / "prompts").mkdir(parents=True)
    shutil.copyfile(FLESH_OUT_PROMPT, repo / "agents" / "prompts" / "flesh_out.md")
    return repo


def _ctx(project_id: str) -> AgentContext:
    # Empty title/field → build_messages skips the librarian network call.
    return AgentContext(
        project_id=project_id,
        run_id="run-1",
        task_id="task-1",
        inputs=[],
        metadata={},
    )


def test_build_messages_injects_kickback_feedback(tmp_path: Path, monkeypatch) -> None:
    from llmxive.agents import idea_lifecycle

    repo = _temp_repo_with_prompt(tmp_path)
    monkeypatch.setattr(idea_lifecycle, "_repo_root", lambda: repo)

    pid = "PROJ-902-circular-validation"
    idea_dir = repo / "projects" / pid / "idea"
    idea_dir.mkdir(parents=True)
    # A real idea body the agent SHOULD pick up as the idea note.
    (idea_dir / "the-idea.md").write_text(
        "---\nfield: mathematics\n---\n\n# The Idea\n\nA composite metric.\n",
        encoding="utf-8",
    )
    # The downstream feedback file.
    (idea_dir / FEEDBACK_FILENAME).write_text(
        "# Downstream review concerns (address in this revision)\n\n"
        f"- {CIRCULAR_CONCERN}\n",
        encoding="utf-8",
    )

    agent = _flesh_out_agent()
    messages = agent.build_messages(_ctx(pid))
    user = messages[-1].content

    # Feedback is injected and clearly labeled.
    assert "circular validation" in user.lower()
    assert "crossing number" in user
    assert "downstream review concerns" in user.lower()
    # The real idea body is still present...
    assert "A composite metric." in user
    assert "# Current idea note" in user
    # ...and the feedback file content was NOT mistaken FOR the idea body.
    assert "Downstream review concerns" not in _idea_body_of(user)
    assert "A composite metric." in _idea_body_of(user)


def _idea_body_of(user: str) -> str:
    """Extract the text the agent treated as the canonical idea note.

    The idea note is the ``# Current idea note`` user-message section; it runs
    until the next INJECTED top-level section (the trailing ``# Task`` block or
    the appended ``# DOWNSTREAM REVIEW CONCERNS`` block). The idea body may
    itself contain ``# <Title>`` headings, so we split only on those two known
    injected markers — not on every ``# ``.
    """
    if "# Current idea note" not in user:
        return ""
    after = user.split("# Current idea note", 1)[1]
    cut = len(after)
    for marker in ("\n# Task", "\n# DOWNSTREAM REVIEW CONCERNS"):
        idx = after.find(marker)
        if idx != -1:
            cut = min(cut, idx)
    return after[:cut]


def test_build_messages_unchanged_without_feedback(tmp_path: Path, monkeypatch) -> None:
    from llmxive.agents import idea_lifecycle

    repo = _temp_repo_with_prompt(tmp_path)
    monkeypatch.setattr(idea_lifecycle, "_repo_root", lambda: repo)

    pid = "PROJ-903-no-feedback"
    idea_dir = repo / "projects" / pid / "idea"
    idea_dir.mkdir(parents=True)
    (idea_dir / "the-idea.md").write_text(
        "---\nfield: mathematics\n---\n\n# The Idea\n\nA composite metric.\n",
        encoding="utf-8",
    )

    agent = _flesh_out_agent()
    user = agent.build_messages(_ctx(pid))[-1].content
    assert "Downstream review concerns" not in user
    assert "A composite metric." in user


def test_build_messages_feedback_not_selected_as_only_idea_body(
    tmp_path: Path, monkeypatch
) -> None:
    """Even when the feedback file is the ONLY *.md in idea/ (no genuine idea
    body yet), it must not be promoted to the idea-note slot."""
    from llmxive.agents import idea_lifecycle

    repo = _temp_repo_with_prompt(tmp_path)
    monkeypatch.setattr(idea_lifecycle, "_repo_root", lambda: repo)

    pid = "PROJ-904-only-feedback"
    idea_dir = repo / "projects" / pid / "idea"
    idea_dir.mkdir(parents=True)
    (idea_dir / FEEDBACK_FILENAME).write_text(
        "# Downstream review concerns (address in this revision)\n\n"
        f"- {CIRCULAR_CONCERN}\n",
        encoding="utf-8",
    )

    agent = _flesh_out_agent()
    user = agent.build_messages(_ctx(pid))[-1].content
    # The feedback must still be injected as feedback...
    assert "crossing number" in user
    # ...but never as the "# Current idea note" body.
    assert _idea_body_of(user).strip() == ""


# --------------------------------------------------------------------------
# Part 1c — _persist removes the feedback file once consumed
# --------------------------------------------------------------------------


def test_persist_removes_feedback_file(tmp_path: Path, monkeypatch) -> None:
    from llmxive.agents import idea_lifecycle
    from llmxive.backends.base import ChatResponse

    repo = _temp_repo_with_prompt(tmp_path)
    monkeypatch.setattr(idea_lifecycle, "_repo_root", lambda: repo)

    pid = "PROJ-905-cleanup"
    idea_dir = repo / "projects" / pid / "idea"
    idea_dir.mkdir(parents=True)
    (idea_dir / "the-idea.md").write_text(
        "---\nfield: mathematics\n---\n\n# The Idea\n\nbody\n",
        encoding="utf-8",
    )
    feedback = idea_dir / FEEDBACK_FILENAME
    feedback.write_text(
        "# Downstream review concerns (address in this revision)\n\n"
        f"- {CIRCULAR_CONCERN}\n",
        encoding="utf-8",
    )

    agent = _flesh_out_agent()
    ctx = _ctx(pid)
    ctx.metadata["title"] = "The Idea"
    response = ChatResponse(
        text=(
            "# The Idea\n\n## Research question\n\nRevised, non-circular.\n\n"
            "## Methodology sketch\n\n- validate against an independent target\n"
        ),
        model="m",
        backend="dartmouth",
    )
    agent.handle_response(ctx, response)

    assert not feedback.exists(), "_persist must remove the consumed feedback file"
    # The idea body itself was still written.
    assert (idea_dir / "the-idea.md").read_text(encoding="utf-8")


# --------------------------------------------------------------------------
# Part 2 — prompt contract (domain-general)
# --------------------------------------------------------------------------


def test_prompt_has_validation_independence_and_downstream_guidance() -> None:
    text = FLESH_OUT_PROMPT.read_text(encoding="utf-8")
    low = text.lower()
    # Validation-independence rule (proactive).
    assert "validation independence" in low or "independent of the construct" in low
    assert "monotone function" in low or "mathematically determined" in low or \
        "mathematically dependent" in low
    # Address-downstream-concerns instruction (reactive).
    assert "downstream review concern" in low or "kickback_feedback" in low
    # Names the methodology sketch as the part to revise.
    assert "methodology sketch" in low


def test_prompt_guidance_is_domain_general() -> None:
    """The new guidance must not hardcode the field that surfaced the bug."""
    text = FLESH_OUT_PROMPT.read_text(encoding="utf-8")
    low = text.lower()
    for term in ("knot", "braid", "seifert", "crossing number", "jones polynomial"):
        assert term not in low, f"prompt leaked field-specific term: {term!r}"


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(pytest.main([__file__, "-q"]))
