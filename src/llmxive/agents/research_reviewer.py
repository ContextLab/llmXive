"""Research-Reviewer Agent (T064).

Reads the project's implementation artifacts and writes a review
record under
`projects/<PROJ-ID>/reviews/research/<reviewer-name>__<YYYY-MM-DD>__research.md`
with frontmatter validated against `contracts/review-record.schema.yaml`.

Stage transitions are NOT handled here — the Advancement-Evaluator
Agent reads the accumulated review records and decides whether the
project advances to `research_accepted` / `research_minor_revision` /
`research_full_revision` / `research_rejected`.
"""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path

import yaml
from pydantic import ValidationError

from llmxive.agents.base import Agent, AgentContext, MalformedResponseError
from llmxive.agents.prompts import render_prompt
from llmxive.backends.base import ChatMessage, ChatResponse
from llmxive.config import repo_root as _repo_root
from llmxive.state import reviews as reviews_store
from llmxive.state import runlog as runlog_store
from llmxive.types import (
    AgentRegistryEntry,
    ReviewerKind,
    ReviewRecord,
    action_items_from_text,
)

_FRONTMATTER_RE = re.compile(
    r"^---\s*\n(?P<frontmatter>.*?)\n---\s*\n(?P<body>.*)$",
    re.DOTALL,
)

# Appended to the retry prompt when output validation rejects a response
# (issue #294 typed-boundary work; see base.MalformedResponseError).
_FORMAT_REMINDER = (
    "Your response MUST start with a line containing exactly `---`, "
    "followed by the YAML frontmatter fields required by the review-record "
    "contract in the system prompt, followed by a line containing exactly "
    "`---`, followed by the markdown review body."
)


#: Directories/artifacts that are NOT part of a project's authored source and
#: must never crowd out real files in the reviewer's tree view. A virtualenv
#: alone is thousands of files; with the old 25-file cap it (and __pycache__)
#: hid the project's actual source, producing false "this file is missing"
#: reviews that blocked advancement.
_TREE_SKIP_DIRS = frozenset(
    {
        "__pycache__", ".venv", "venv", "env", ".env", "site-packages",
        "node_modules", ".git", ".pytest_cache", ".mypy_cache", ".ruff_cache",
        ".ipynb_checkpoints", ".tox", "build", "dist",
    }
)


def _summarize_tree(root: Path, *, max_files: int = 400) -> str:
    """Bulleted listing of a project's AUTHORED files under `root` with sizes.

    Excludes virtualenvs, caches, and compiled artifacts so the reviewer sees the
    real project structure. The cap is high enough to show an entire project's
    source + docs; only pathological trees hit it (and then we say how many were
    omitted, so a reviewer never silently mistakes truncation for absence).
    """
    if not root.is_dir():
        return "(no files)"

    def _skip(path: Path) -> bool:
        for part in path.relative_to(root).parts:
            if part in _TREE_SKIP_DIRS or part.startswith("."):
                return True
            if part.endswith((".egg-info", ".dist-info")):
                return True
        return path.suffix in {".pyc", ".pyo"}

    files = [p for p in sorted(root.rglob("*")) if p.is_file() and not _skip(p)]
    lines = [
        f"- `{p.relative_to(root).as_posix()}` ({p.stat().st_size} bytes)"
        for p in files[:max_files]
    ]
    if len(files) > max_files:
        lines.append(f"- ... ({len(files) - max_files} more authored files)")
    return "\n".join(lines) if lines else "(empty)"


def _doc_contents(
    project_dir: Path,
    *,
    prioritize_text: str = "",
    max_total: int = 48000,
    max_per_file: int = 2400,
) -> str:
    """Concatenate the CONTENT of documentation/reproducibility files so a
    reviewer can VERIFY them, not merely see that they exist. Listings alone made
    data_quality / filesystem reviewers withhold accept ('content not shown —
    cannot verify the license/provenance doc').

    Projects can accumulate 100+ reproducibility docs (redundant narratives,
    addenda) — far more than any fixed prompt budget can hold. With a naive
    alphabetical scan the budget is exhausted by early/verbose files and the
    concise, SPEC-MANDATED artifacts the review actually turns on (counts tables,
    validation status) are silently omitted, so the reviewer falsely infers them
    absent. Order candidates by (referenced-in-spec/tasks first, then SMALLEST
    first) so the substantive concise docs are shown IN FULL and only long
    redundant narratives are truncated/omitted when the bounded budget is hit."""
    cands: list[Path] = []
    rdir = project_dir / "docs" / "reproducibility"
    if rdir.is_dir():
        cands += sorted(rdir.glob("*.md"))
    for name in ("README.md", "LICENSE.md", "LICENSE", "CONTRIBUTING.md"):
        p = project_dir / name
        if p.is_file():
            cands.append(p)

    ref = prioritize_text.lower()
    # One-hop expansion: a spec/tasks-referenced doc usually points to a sibling
    # for detail (e.g. validation_scope.md → "counts are in dataset_counts.md").
    # Fold those directly-named docs' bodies into the priority corpus so the
    # pointed-TO artifact is prioritized too — not just the pointer. (A few small
    # re-reads; the main loop reads them again below.)
    for p in cands:
        if p.name.lower() in ref or p.stem.lower() in ref:
            try:
                ref += "\n" + p.read_text(encoding="utf-8", errors="replace").lower()
            except OSError:
                pass

    def _priority(p: Path) -> tuple[int, int]:
        try:
            size = p.stat().st_size
        except OSError:
            size = 1 << 30
        named = p.name.lower() in ref or p.stem.lower() in ref
        return (0 if named else 1, size)  # referenced first, then smallest-first

    cands.sort(key=_priority)

    out: list[str] = []
    total = 0
    omitted = 0
    for p in cands:
        try:
            txt = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        rel = p.relative_to(project_dir).as_posix()
        block = f"### `{rel}` ({len(txt)} bytes)\n{txt[:max_per_file]}" + (
            "\n…(truncated)" if len(txt) > max_per_file else ""
        )
        if total + len(block) > max_total:
            omitted += 1
            continue  # keep scanning — a later, smaller doc may still fit
        out.append(block)
        total += len(block)
    if omitted:
        out.append(
            f"…({omitted} additional long/low-priority doc file(s) omitted for "
            "length — do NOT infer their content is absent; only raise a Required "
            "Change if a SPECIFIC claim genuinely cannot be verified from what is "
            "shown)"
        )
    return "\n\n".join(out) if out else "(no documentation files found)"


def _execution_evidence(project_id: str, repo: Path) -> str:
    """Factual evidence of whether the analysis run-book actually executed and
    produced real artifacts, so reviewers judging implementation correctness /
    completeness don't have to infer it from a file listing (and don't hedge on
    'does it actually run')."""
    path = repo / "state" / "execution_status" / f"{project_id}.json"
    try:
        d = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return "(no execution-gate record — the analysis run-book has not been gated yet)"
    ok = bool(d.get("ok"))
    artifacts = d.get("artifacts") or []
    if ok:
        head = (
            "PASSED — the dedicated execution gate ran the project's quickstart "
            "run-book end-to-end in its venv and recorded ok=True (real data + "
            "figures were produced; results are not hallucinated)."
        )
    else:
        head = f"NOT yet passed (ok=False): {str(d.get('reason', ''))[:200]}"
    lines = [f"- Execution gate: {head}", f"- Artifacts produced ({len(artifacts)}):"]
    lines += [f"  - {a}" for a in artifacts[:50]]
    if len(artifacts) > 50:
        lines.append(f"  - ... ({len(artifacts) - 50} more)")
    return "\n".join(lines)


def _read_optional(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


class ResearchReviewerAgent(Agent):
    """Casts a single research-quality vote on a project's tasks.md."""

    #: Deterministic verdicts (Constitution VI reliability): same artifact ->
    #: same verdict, so the unanimous-accept gate stops flapping run-to-run.
    chat_temperature = 0.0

    def __init__(self, registry_entry: AgentRegistryEntry) -> None:
        super().__init__(registry_entry)

    def _project_dir(self, ctx: AgentContext) -> Path:
        repo = _repo_root()
        return repo / "projects" / ctx.project_id

    def _feature_dir(self, project_dir: Path) -> Path | None:
        # Canonical resolution shared with advancement.verdict_coverage —
        # the reviewer's artifact_hash and the coverage check's notion of
        # "the live artifact" must agree (spec 023 / FR-004).
        from llmxive.state.project import feature_dir_for

        return feature_dir_for(project_dir, track="research")

    def build_messages(self, ctx: AgentContext) -> list[ChatMessage]:
        repo = _repo_root()
        project_dir = self._project_dir(ctx)
        feature_dir = self._feature_dir(project_dir)
        if feature_dir is None:
            raise FileNotFoundError(f"no specs/ feature dir in {project_dir}")

        spec_text = _read_optional(feature_dir / "spec.md")
        plan_text = _read_optional(feature_dir / "plan.md")
        tasks_text = _read_optional(feature_dir / "tasks.md")
        code_summary = _summarize_tree(project_dir / "code")
        data_summary = _summarize_tree(project_dir / "data")
        # docs/ holds the reproducibility documentation (FR-007 etc.). Omitting it
        # made implementation reviewers falsely report those docs "missing".
        docs_summary = _summarize_tree(project_dir / "docs")
        # Show the docs the spec/tasks reference first (then smallest-first) so a
        # 100+-doc project can't bury the concise spec-mandated artifacts.
        doc_contents = _doc_contents(
            project_dir, prioritize_text=f"{spec_text}\n{tasks_text}"
        )
        results_summary = _read_optional(project_dir / "results.md")
        execution_evidence = _execution_evidence(ctx.project_id, repo)

        # Prior research-stage reviews (if any). Split the GATING specialist
        # panel (research_reviewer_*) from ADVISORY input (human reviewers +
        # simulated-personality commenters). Advisory comments do NOT directly
        # generate revision tasks (advancement._consolidate_action_items filters
        # them out) — instead they are surfaced HERE so each gating reviewer can
        # weigh them and fold any genuine in-lens point into its own review.
        prior = reviews_store.list_for(ctx.project_id, stage="research", repo_root=repo)
        gating_prior = [r for r in prior if r.reviewer_name.startswith("research_reviewer_")]
        advisory = [r for r in prior if not r.reviewer_name.startswith("research_reviewer_")]
        prior_block = (
            "\n\n".join(
                f"- {r.reviewer_name} ({r.reviewer_kind.value}): {r.verdict} — {r.feedback[:120]}"
                for r in gating_prior
            )
            or "(no prior specialist reviews)"
        )
        advisory_block = (
            "\n\n".join(
                f"### {r.reviewer_name} ({r.reviewer_kind.value})\n{(r.feedback or '').strip()[:1200]}"
                for r in advisory
            )
            or "(no advisory comments submitted)"
        )

        # Use the registry entry's prompt_path so specialist reviewers
        # (research_reviewer_idea_quality, _creativity, etc.) load
        # their own focused prompts. The generic research_reviewer
        # agent falls back to agents/prompts/research_reviewer.md.
        prompt_path = self.entry.prompt_path or "agents/prompts/research_reviewer.md"
        system = render_prompt(
            prompt_path,
            {"project_id": ctx.project_id, "reviewer_name": self.entry.name},
            repo_root=repo,
        )

        # Re-review diff-check (mirrors the paper-side FR-014 protocol). When THIS
        # specialist has reviewed THIS project before, prepend the shared research
        # re-review block listing its OWN most-recent action items, so the verdict
        # becomes a deterministic "are my prior concerns resolved?" diff-check
        # rather than a fresh, stochastic critique — concerns only get resolved
        # across rounds, so the panel converges to accept once the bar is met.
        try:
            prior_for_self = reviews_store.prior_reviews_for_specialist(
                ctx.project_id, self.entry.name, stage="research", repo_root=repo,
            )
        except Exception:
            prior_for_self = []
        if prior_for_self:
            most_recent = prior_for_self[-1]
            prior_items_yaml = (
                yaml.safe_dump(
                    [{"id": ai.id, "text": ai.text, "severity": ai.severity}
                     for ai in most_recent.action_items],
                    sort_keys=False,
                )
                if most_recent.action_items else "[]\n"
            )
            snippet_path = (
                repo / "agents" / "prompts" / "_shared" / "rereview_block_research.md"
            )
            try:
                snippet = snippet_path.read_text(encoding="utf-8")
            except OSError:
                snippet = ""
            if snippet:
                system = (
                    snippet.replace("{prior_action_items_yaml}", prior_items_yaml.strip())
                    + "\n\n"
                    + system
                )

        # Every NON-accept research review must end with a parseable,
        # blocking-only "## Required Changes" section — one bullet per defect,
        # each naming the exact file + the exact change. This makes the verdict
        # SPECIFIC and hands the action-item extractor a curated task list
        # instead of forcing it to shred the whole prose body (which mixes in
        # section headers + positive observations). Injected here (not duplicated
        # into all ~7 specialist prompts) so the requirement has one source.
        rc_path = (
            repo / "agents" / "prompts" / "_shared"
            / "required_changes_block_research.md"
        )
        try:
            rc_block = rc_path.read_text(encoding="utf-8")
        except OSError:
            rc_block = ""
        if rc_block:
            system = system + "\n\n" + rc_block

        user = (
            f"# project_id\n{ctx.project_id}\n\n"
            f"# spec.md\n\n{spec_text}\n\n"
            f"# plan.md\n\n{plan_text}\n\n"
            f"# tasks.md\n\n{tasks_text}\n\n"
            f"# code summary\n\n{code_summary}\n\n"
            f"# data summary\n\n{data_summary}\n\n"
            f"# docs summary (incl. docs/reproducibility/)\n\n{docs_summary}\n\n"
            f"# documentation contents (verify these — do not assume from the listing)\n\n{doc_contents}\n\n"
            f"# execution evidence\n\n{execution_evidence}\n\n"
            f"# results summary\n\n{results_summary}\n\n"
            f"# prior specialist reviews (the gating panel)\n\n{prior_block}\n\n"
            f"# advisory comments (human + simulated-personality — ADVISORY input)\n\n"
            f"{advisory_block}\n\n"
            "# Task\n\n"
            "1. Review the project in YOUR lens and reach a verdict.\n"
            "2. Then CONSIDER the advisory comments above. They are NOT binding and "
            "do NOT, by themselves, block the project — but if any raises a genuine, "
            "in-lens concern you agree with, fold it into your review and action "
            "items so it carries real weight; ignore the rest (out-of-lens, "
            "stylistic, or unfounded points).\n"
            "3. Return the review record per the contract, revised as you see fit."
        )
        return [
            ChatMessage(role="system", content=system),
            ChatMessage(role="user", content=user),
        ]

    def handle_response(self, ctx: AgentContext, response: ChatResponse) -> list[str]:
        repo = _repo_root()
        text = response.text.strip()
        match = _FRONTMATTER_RE.match(text)
        if not match:
            raise MalformedResponseError(
                "research_reviewer: response missing YAML frontmatter",
                format_reminder=_FORMAT_REMINDER,
            )
        try:
            front = yaml.safe_load(match.group("frontmatter"))
        except yaml.YAMLError as exc:
            raise MalformedResponseError(
                f"research_reviewer: frontmatter is not valid YAML ({exc})",
                format_reminder=_FORMAT_REMINDER,
            ) from exc
        body = match.group("body").strip()
        if not isinstance(front, dict):
            raise MalformedResponseError(
                "research_reviewer: frontmatter must be a YAML mapping",
                format_reminder=_FORMAT_REMINDER,
            )

        # Force the runtime-known fields onto the record (LLM may echo
        # placeholder values that we replace authoritatively).
        front["reviewer_name"] = self.entry.name
        front["reviewer_kind"] = ReviewerKind.LLM.value
        front["model_name"] = response.model
        front["backend"] = response.backend
        front["prompt_version"] = self.entry.prompt_version
        front["reviewed_at"] = datetime.now(UTC).isoformat()

        # Compute the artifact_hash from the live tasks.md.
        project_dir = self._project_dir(ctx)
        feature_dir = self._feature_dir(project_dir)
        if feature_dir is not None:
            tasks_path = feature_dir / "tasks.md"
            if tasks_path.exists():
                from llmxive.state.project import hash_file

                front["artifact_hash"] = hash_file(tasks_path)
                front["artifact_path"] = str(tasks_path.relative_to(repo))

        # A non-accept verdict with NO structured action_items stalls the
        # convergence engine (advancement finds nothing to revise → infinite
        # no-op at research_review) and is outright rejected by the ReviewRecord
        # schema at prompt_version >= 1.1.0. Weak models reliably write their
        # findings as body prose while leaving the YAML list empty — reshape that
        # prose into items BEFORE validation so the record is both schema-valid
        # and actionable for every downstream consumer.
        _verdict = front.get("verdict")
        if (
            isinstance(_verdict, str)
            and _verdict != "accept"
            and not (front.get("action_items") or [])
            and body
        ):
            synth = action_items_from_text(body, verdict=_verdict)
            if synth:
                front["action_items"] = [it.model_dump() for it in synth]

        try:
            record = ReviewRecord.model_validate(front)
        except ValidationError as exc:
            raise MalformedResponseError(
                f"research_reviewer: frontmatter failed ReviewRecord schema "
                f"validation: {exc}",
                format_reminder=_FORMAT_REMINDER,
            ) from exc

        # Self-review prevention (discrepancy #7 / #49): resolve the agent that
        # actually produced the reviewed artifact from the run-log so
        # reviews_store refuses a reviewer reviewing its own output. (For the
        # research panel the producer is the tasker/implementer — disjoint from
        # the research_reviewer* names — so this is defense-in-depth; None when
        # the run-log has no record of the artifact, preserving prior behavior.)
        producer = runlog_store.producer_of_artifact(
            ctx.project_id, record.artifact_path, repo_root=repo
        )
        path = reviews_store.write(
            record,
            body=body,
            stage="research",
            review_type="research",
            produced_by_agent=producer,
            repo_root=repo,
        )
        return [str(path.relative_to(repo))]


__all__ = ["ResearchReviewerAgent"]
