"""Review-only pipeline for a Reviewed Preprint (2026-07-01 ethics change).

A Reviewed Preprint is a third-party paper llmXive has REVIEWED but never
MODIFIED. This module runs the paper-review specialist panel **once** over the
paper — NO convergence loop, NO revise round, NO accept/reject (a preprint is
not ours to accept). Each lens writes a normal ``ReviewRecord`` under
``paper/reviews/``; the reviewers' concerns are consolidated into a single
human-readable ``paper/action_items.md`` that drives the peer-review PDF + the
dashboard card.

The panel + dispatch are the SAME ones the pipeline uses for an llmXive-authored
paper under review — ``llmxive.agents.paper_reviewer.PaperReviewerAgent`` run via
``llmxive.agents.runner.run_agent`` (Constitution I: one review mechanism, never a
per-flow re-implementation). A preprint review therefore is a *genuine* peer
review; it differs only in that we never invoke the Advancement-Evaluator, so
nothing advances and no revision is ever demanded of the original authors.

Precondition (enforced by the caller — intake / migration): the paper source on
disk is the ORIGINAL work, with any prior llmXive ``*-llmxive.*`` modifications
already discarded. The reviewers read whatever ``paper/source`` holds, so the
caller is responsible for presenting the untouched original.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from uuid import uuid4

from llmxive.config import repo_root as _repo_root
from llmxive.types import Project

# The consolidated action-item digest the peer-review PDF + dashboard render.
_ACTION_ITEMS_NAME = "action_items.md"


@dataclass
class PreprintReviewResult:
    """Outcome of a one-shot preprint review."""

    project_id: str
    #: Registry names of every lens that produced a review record this run.
    reviewers_run: list[str] = field(default_factory=list)
    #: Registry names whose dispatch raised (non-fatal — the panel continues).
    reviewers_failed: list[str] = field(default_factory=list)
    #: Path to the consolidated ``paper/action_items.md`` (always written).
    action_items_path: Path | None = None
    #: Total number of action items across all lenses.
    num_action_items: int = 0


def paper_reviewer_agent_names(repo_root: Path) -> list[str]:
    """The paper-review panel: every ``paper_reviewer*`` registry entry.

    Includes the generic ``paper_reviewer`` (a holistic summary review) plus the
    specialist lenses — the SAME set the graph dispatches on a project's first
    review round. Ordered as the registry lists them (deterministic)."""
    from llmxive.agents import registry as registry_loader

    return [
        n
        for n in registry_loader.list_names(repo_root=repo_root)
        if n == "paper_reviewer" or n.startswith("paper_reviewer_")
    ]


def _project_dir(project: Project, repo_root: Path) -> Path:
    from llmxive.paper_reprocess.reprocess import project_dir

    return project_dir(project, repo_root)


def run_preprint_review(
    project: Project,
    *,
    repo_root: Path | None = None,
    run_id: str | None = None,
    agent_names: list[str] | None = None,
) -> PreprintReviewResult:
    """Run the paper-review panel ONCE over ``project``'s paper; write records.

    For each ``paper_reviewer*`` lens: instantiate the SAME ``PaperReviewerAgent``
    the pipeline uses, dispatch it via ``run_agent`` (which writes the lens's
    ``ReviewRecord`` under ``paper/reviews/``), then consolidate every reviewer's
    action items into ``paper/action_items.md``. Individual lens failures are
    non-fatal (logged; the rest of the panel still votes) — mirroring the graph's
    review-dispatch policy. Returns a :class:`PreprintReviewResult`.

    No convergence, no revise, no accept/reject: this is peer-review FEEDBACK only.
    """
    import logging

    from llmxive.agents.base import AgentContext
    from llmxive.agents.paper_reviewer import PaperReviewerAgent
    from llmxive.agents.runner import run_agent

    log = logging.getLogger(__name__)
    repo = repo_root or _repo_root()
    rid = run_id or f"preprint-review-{uuid4().hex[:8]}"
    names = agent_names if agent_names is not None else paper_reviewer_agent_names(repo)

    result = PreprintReviewResult(project_id=project.id)
    from llmxive.agents import registry as registry_loader

    for an in names:
        try:
            entry = registry_loader.get(an, repo_root=repo)
        except KeyError:
            log.warning("preprint review: unknown reviewer %r (skipped)", an)
            continue
        agent = PaperReviewerAgent(entry)
        ctx = AgentContext(
            project_id=project.id,
            run_id=rid,
            task_id=str(uuid4()),
            inputs=[],
            metadata={"title": project.title, "field": project.field},
        )
        try:
            run_agent(agent, ctx, repo_root=repo)
            result.reviewers_run.append(an)
        except Exception as exc:  # one lens must not sink the panel
            log.warning("preprint review: reviewer %r failed: %s", an, exc)
            result.reviewers_failed.append(an)

    path, count = consolidate_action_items(project, repo_root=repo)
    result.action_items_path = path
    result.num_action_items = count
    return result


def consolidate_action_items(
    project: Project, *, repo_root: Path | None = None
) -> tuple[Path, int]:
    """Aggregate every ``paper/reviews`` record's action items into one digest.

    Writes ``paper/action_items.md`` grouped by reviewer, each with its verdict
    and the reviewer's structured action items (or the review feedback when a
    reviewer accepted with none). Returns ``(path, total_action_items)``.
    """
    from llmxive.state import reviews as reviews_store

    repo = repo_root or _repo_root()
    pdir = _project_dir(project, repo)
    records = reviews_store.list_for(project.id, stage="paper", repo_root=repo)

    lines: list[str] = [
        f"# Automated-review action items — {project.title}",
        "",
        (
            "This is llmXive's automated review of an ingested preprint. The LLM "
            "panel reviewed the paper once and recorded the concerns below. It is "
            "**advisory feedback for the authors** — llmXive does not modify the "
            "paper and nothing is accepted or rejected on its basis."
        ),
        "",
    ]
    total = 0
    if not records:
        lines.append("_No review records were produced._")
    for rec in sorted(records, key=lambda r: r.reviewer_name):
        lines.append(f"## {rec.reviewer_name} — verdict: {rec.verdict}")
        lines.append("")
        if rec.action_items:
            for item in rec.action_items:
                total += 1
                text = (item.text or "").strip()
                sev = getattr(item.severity, "value", item.severity)
                lines.append(f"- **[{sev}]** {text}")
            lines.append("")
        else:
            fb = (rec.feedback or "").strip()
            lines.append(fb if fb else "_(no action items)_")
            lines.append("")

    out = pdir / "paper" / _ACTION_ITEMS_NAME
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return out, total


__all__ = [
    "PreprintReviewResult",
    "consolidate_action_items",
    "paper_reviewer_agent_names",
    "run_preprint_review",
]
