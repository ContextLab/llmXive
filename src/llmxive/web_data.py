"""Build the web/data/projects.json payload (v2 schema, FR-027 ff).

Pure functions: input is the repo state on disk; output is a dict that
matches specs/002-website-integration/contracts/web-data-v2.schema.yaml.

Called by the Status-Reporter Agent after every successful pipeline cycle
(see agents/status_reporter.py::regenerate_web_data).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from llmxive.state import project as project_store
from llmxive.types import Project, ReviewerKind, Stage

SCHEMA_VERSION = "2.0.0"

TERMINAL_STAGES: frozenset[Stage] = frozenset({
    Stage.POSTED,
    Stage.RESEARCH_REJECTED,
    Stage.PAPER_FUNDAMENTAL_FLAWS,
    Stage.BLOCKED,
})

_PHASE_GROUP_BY_STAGE: dict[Stage, str] = {
    Stage.BRAINSTORMED: "idea",
    Stage.FLESH_OUT_IN_PROGRESS: "idea",
    Stage.FLESH_OUT_COMPLETE: "idea",
    Stage.PROJECT_INITIALIZED: "idea",
    Stage.SPECIFIED: "research_speckit",
    Stage.CLARIFY_IN_PROGRESS: "research_speckit",
    Stage.CLARIFIED: "research_speckit",
    Stage.PLANNED: "research_speckit",
    Stage.TASKED: "research_speckit",
    Stage.ANALYZE_IN_PROGRESS: "research_speckit",
    Stage.ANALYZED: "research_speckit",
    Stage.IN_PROGRESS: "research_speckit",
    Stage.RESEARCH_COMPLETE: "research_speckit",
    Stage.RESEARCH_REVIEW: "research_review",
    Stage.RESEARCH_ACCEPTED: "research_review",
    Stage.RESEARCH_MINOR_REVISION: "research_review",
    Stage.RESEARCH_FULL_REVISION: "research_review",
    Stage.RESEARCH_REJECTED: "research_review",
    Stage.PAPER_DRAFTING_INIT: "paper_speckit",
    Stage.PAPER_SPECIFIED: "paper_speckit",
    Stage.PAPER_CLARIFIED: "paper_speckit",
    Stage.PAPER_PLANNED: "paper_speckit",
    Stage.PAPER_TASKED: "paper_speckit",
    Stage.PAPER_ANALYZED: "paper_speckit",
    Stage.PAPER_IN_PROGRESS: "paper_speckit",
    Stage.PAPER_COMPLETE: "paper_speckit",
    Stage.PAPER_REVIEW: "paper_review",
    Stage.PAPER_ACCEPTED: "paper_review",
    Stage.PAPER_MINOR_REVISION: "paper_review",
    Stage.PAPER_MAJOR_REVISION_WRITING: "paper_review",
    Stage.PAPER_MAJOR_REVISION_SCIENCE: "paper_review",
    Stage.PAPER_FUNDAMENTAL_FLAWS: "paper_review",
    Stage.POSTED: "posted",
    Stage.HUMAN_INPUT_NEEDED: "blocked",
    Stage.BLOCKED: "blocked",
}


def phase_group(stage: Stage) -> str:
    return _PHASE_GROUP_BY_STAGE.get(stage, "blocked")


def _project_dir(repo: Path, project_id: str) -> Path:
    return repo / "projects" / project_id


def _first_existing(*paths: Path) -> Path | None:
    for p in paths:
        if p.exists():
            return p
    return None


def _build_artifact_links(repo: Path, project: Project) -> dict[str, str | None]:
    """Best-effort discovery of canonical artifacts.

    Returns a flat string→relpath map used by the website's artifact-log
    dialog. Missing artifacts get a null value.
    """
    pdir = _project_dir(repo, project.id)
    speckit = (
        Path(project.speckit_research_dir)
        if project.speckit_research_dir
        else None
    )
    paper_speckit = (
        Path(project.speckit_paper_dir)
        if project.speckit_paper_dir
        else None
    )

    def rel(p: Path | None) -> str | None:
        if p is None:
            return None
        try:
            return p.relative_to(repo).as_posix()
        except ValueError:
            return p.as_posix()

    idea_md = next(iter(pdir.glob("idea/*.md")), None) if pdir.exists() else None
    spec_md = (repo / speckit / "spec.md") if speckit else None
    plan_md = (repo / speckit / "plan.md") if speckit else None
    tasks_md = (repo / speckit / "tasks.md") if speckit else None
    code_dir = pdir / "code"
    data_dir = pdir / "data"
    paper_spec = (repo / paper_speckit / "spec.md") if paper_speckit else None
    paper_plan = (repo / paper_speckit / "plan.md") if paper_speckit else None
    paper_tasks = (repo / paper_speckit / "tasks.md") if paper_speckit else None
    paper_source_main = pdir / "paper" / "source" / "main.tex"
    paper_pdf = next(iter((pdir / "paper" / "pdf").glob("*.pdf")), None) if (pdir / "paper" / "pdf").exists() else None
    figures_dir = pdir / "paper" / "figures"
    reviews_research = pdir / "reviews" / "research"
    reviews_paper = pdir / "paper" / "reviews"
    citations_file = repo / "state" / "citations" / f"{project.id}.yaml"

    out: dict[str, str | None] = {
        "idea": rel(idea_md) if idea_md else None,
        "spec": rel(spec_md) if (spec_md and spec_md.exists()) else None,
        "plan": rel(plan_md) if (plan_md and plan_md.exists()) else None,
        "tasks": rel(tasks_md) if (tasks_md and tasks_md.exists()) else None,
        "code": rel(code_dir) if code_dir.exists() else None,
        "data": rel(data_dir) if data_dir.exists() else None,
        "paper_spec": rel(paper_spec) if (paper_spec and paper_spec.exists()) else None,
        "paper_plan": rel(paper_plan) if (paper_plan and paper_plan.exists()) else None,
        "paper_tasks": rel(paper_tasks) if (paper_tasks and paper_tasks.exists()) else None,
        "paper_source": rel(paper_source_main) if paper_source_main.exists() else None,
        "paper_pdf": rel(paper_pdf) if paper_pdf else None,
        "paper_figures": rel(figures_dir) if figures_dir.exists() else None,
        "reviews_research": rel(reviews_research) if reviews_research.exists() else None,
        "reviews_paper": rel(reviews_paper) if reviews_paper.exists() else None,
        "citations": rel(citations_file) if citations_file.exists() else None,
    }
    return out


def _citation_summary(repo: Path, project_id: str) -> dict[str, int]:
    cit_file = repo / "state" / "citations" / f"{project_id}.yaml"
    out = {"verified": 0, "mismatch": 0, "unreachable": 0, "pending": 0}
    if not cit_file.exists():
        return out
    try:
        cits = yaml.safe_load(cit_file.read_text(encoding="utf-8")) or []
    except yaml.YAMLError:
        return out
    for c in cits:
        status = (c or {}).get("verification_status")
        if status in out:
            out[status] += 1
    return out


def _last_run_log(repo: Path, project_id: str, *, limit: int = 10) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    log_root = repo / "state" / "run-log"
    if not log_root.is_dir():
        return out
    # Walk months newest-first and collect entries until we have `limit`.
    entries: list[dict[str, Any]] = []
    for month_dir in sorted([d for d in log_root.iterdir() if d.is_dir() and not d.name.startswith(".")], reverse=True):
        for jsonl in sorted(month_dir.glob("*.jsonl"), reverse=True):
            for line in jsonl.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                try:
                    e = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if e.get("project_id") != project_id:
                    continue
                entries.append(e)
        if len(entries) >= limit:
            break
    entries.sort(key=lambda e: e.get("ended_at", ""), reverse=True)
    for e in entries[:limit]:
        try:
            t0 = datetime.fromisoformat(e["started_at"].replace("Z", "+00:00"))
            t1 = datetime.fromisoformat(e["ended_at"].replace("Z", "+00:00"))
            dur = (t1 - t0).total_seconds()
        except Exception:
            dur = 0.0
        out.append({
            "agent": e.get("agent_name", ""),
            "started_at": e.get("started_at", ""),
            "ended_at": e.get("ended_at", ""),
            "outcome": e.get("outcome", ""),
            "duration_s": float(dur),
        })
    return out


def _project_keywords(repo: Path, project_id: str) -> list[str]:
    """Heuristic: pull keywords/tags from the idea Markdown frontmatter."""
    pdir = _project_dir(repo, project_id)
    idea = next(iter(pdir.glob("idea/*.md")), None)
    if idea is None or not idea.exists():
        return []
    text = idea.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return []
    try:
        end = text.index("---", 3)
        front = yaml.safe_load(text[3:end]) or {}
    except (ValueError, yaml.YAMLError):
        return []
    kws = front.get("keywords") or front.get("tags") or []
    if isinstance(kws, str):
        return [k.strip() for k in kws.split(",") if k.strip()]
    if isinstance(kws, list):
        return [str(k) for k in kws]
    return []


def _project_to_entry(repo: Path, project: Project) -> dict[str, Any]:
    research_total = float(sum(project.points_research.values()))
    paper_total = float(sum(project.points_paper.values()))
    return {
        "id": project.id,
        "title": project.title,
        "field": project.field,
        "current_stage": project.current_stage.value,
        "phase_group": phase_group(project.current_stage),
        "points_research_total": research_total,
        "points_paper_total": paper_total,
        "created_at": project.created_at.isoformat(),
        "updated_at": project.updated_at.isoformat(),
        "keywords": _project_keywords(repo, project.id),
        "speckit_research_dir": project.speckit_research_dir,
        "speckit_paper_dir": project.speckit_paper_dir,
        "artifact_links": _build_artifact_links(repo, project),
        "citation_summary": _citation_summary(repo, project.id),
        "last_run_log": _last_run_log(repo, project.id),
    }


def _aggregates(projects: list[Project], runlog_root: Path,
                reviews_by_kind: dict[ReviewerKind, set[str]]) -> dict[str, int]:
    active = sum(1 for p in projects if p.current_stage not in TERMINAL_STAGES)
    posted = sum(1 for p in projects if p.current_stage == Stage.POSTED)

    contribs = 0
    contributor_set: set[str] = set()
    if runlog_root.is_dir():
        for month_dir in runlog_root.iterdir():
            if not month_dir.is_dir() or month_dir.name.startswith("."):
                continue
            for jsonl in month_dir.glob("*.jsonl"):
                for line in jsonl.read_text(encoding="utf-8").splitlines():
                    if not line.strip():
                        continue
                    try:
                        e = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if e.get("outcome") != "success":
                        continue
                    contribs += 1
                    name = e.get("agent_name") or ""
                    if name:
                        contributor_set.add(name)

    humans = reviews_by_kind.get(ReviewerKind.HUMAN, set())
    llms = reviews_by_kind.get(ReviewerKind.LLM, set())
    contributor_set |= humans
    contributor_set |= llms
    total_contribs = contribs + sum(len(s) for s in reviews_by_kind.values())

    # Collaborations = projects that have BOTH a human review and an LLM review.
    # We approximate by counting projects with non-empty reviews_research AND
    # any LLM run-log entry (every successful run-log line is an LLM contribution).
    # For now: number of projects with at least one human reviewer.
    return {
        "total_contributions": total_contribs,
        "active_projects": active,
        "papers_posted": posted,
        "total_contributors": len(contributor_set),
        "human_contributors": len(humans),
        "ai_contributors": len(llms - humans) + len(contributor_set - humans - llms),
        "total_collaborations": len(humans),
    }


def _collect_reviews(repo: Path) -> tuple[dict[ReviewerKind, set[str]], list[dict[str, Any]]]:
    """Walk every projects/<PROJ-ID>/reviews tree and collect contributor names."""
    by_kind: dict[ReviewerKind, set[str]] = {ReviewerKind.LLM: set(), ReviewerKind.HUMAN: set()}
    contributor_rows: dict[tuple[str, str], dict[str, Any]] = {}
    proj_root = repo / "projects"
    if not proj_root.is_dir():
        return by_kind, []
    for pdir in proj_root.glob("PROJ-*"):
        for sub in ("reviews/research", "paper/reviews"):
            rdir = pdir / sub
            if not rdir.is_dir():
                continue
            for md in rdir.rglob("*.md"):
                # Lightweight: parse YAML frontmatter only.
                text = md.read_text(encoding="utf-8", errors="ignore")
                if not text.startswith("---"):
                    continue
                try:
                    end = text.index("---", 3)
                    fm = yaml.safe_load(text[3:end]) or {}
                except (ValueError, yaml.YAMLError):
                    continue
                name = str(fm.get("reviewer_name", "")).strip()
                if not name:
                    continue
                kind_raw = str(fm.get("reviewer_kind", "")).strip()
                try:
                    kind = ReviewerKind(kind_raw)
                except ValueError:
                    continue
                by_kind.setdefault(kind, set()).add(name)
                key = (name, kind.value)
                row = contributor_rows.setdefault(
                    key, {"name": name, "kind": kind.value, "contribution_count": 0, "areas": set()}
                )
                row["contribution_count"] += 1
                row["areas"].add(sub.split("/")[0])
    rows = []
    for r in contributor_rows.values():
        r["areas"] = sorted(r["areas"])
        rows.append(r)
    return by_kind, rows


def _agent_contributors(repo: Path) -> list[dict[str, Any]]:
    """Aggregate AI contributors from successful run-log entries."""
    runlog_root = repo / "state" / "run-log"
    counts: dict[str, dict[str, Any]] = {}
    if runlog_root.is_dir():
        for month_dir in runlog_root.iterdir():
            if not month_dir.is_dir() or month_dir.name.startswith("."):
                continue
            for jsonl in month_dir.glob("*.jsonl"):
                for line in jsonl.read_text(encoding="utf-8").splitlines():
                    if not line.strip():
                        continue
                    try:
                        e = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if e.get("outcome") != "success":
                        continue
                    name = e.get("agent_name") or ""
                    if not name:
                        continue
                    row = counts.setdefault(
                        name,
                        {"name": name, "kind": "llm", "contribution_count": 0, "areas": set()},
                    )
                    row["contribution_count"] += 1
                    # Areas based on outputs[]: "spec.md" → spec, "tasks.md" → tasks, etc.
                    for out_path in (e.get("outputs") or []):
                        op = str(out_path).lower()
                        if "spec" in op:
                            row["areas"].add("spec")
                        elif "plan" in op:
                            row["areas"].add("plan")
                        elif "tasks" in op:
                            row["areas"].add("tasks")
                        elif "review" in op:
                            row["areas"].add("review")
                        elif "/code/" in op or op.endswith(".py"):
                            row["areas"].add("code")
                        elif "/data/" in op:
                            row["areas"].add("data")
                        elif ".tex" in op or "/paper/" in op:
                            row["areas"].add("paper")
    out = []
    for r in counts.values():
        r["areas"] = sorted(r["areas"])
        out.append(r)
    return out


def build_payload(repo: Path) -> dict[str, Any]:
    """Top-level builder: returns the dict to be serialized to projects.json."""
    projects = project_store.list_all(repo_root=repo)
    by_kind, human_rows = _collect_reviews(repo)
    ai_rows = _agent_contributors(repo)

    # Merge human reviewer rows + AI agent rows.
    rows_by_key: dict[tuple[str, str], dict[str, Any]] = {}
    for r in ai_rows + human_rows:
        key = (r["name"], r["kind"])
        if key in rows_by_key:
            rows_by_key[key]["contribution_count"] += r["contribution_count"]
            rows_by_key[key]["areas"] = sorted(set(rows_by_key[key]["areas"]) | set(r["areas"]))
        else:
            rows_by_key[key] = {
                "name": r["name"],
                "kind": r["kind"],
                "contribution_count": r["contribution_count"],
                "areas": sorted(r["areas"]),
            }
    contributors = sorted(rows_by_key.values(), key=lambda r: -r["contribution_count"])

    aggregates = _aggregates(projects, repo / "state" / "run-log", by_kind)

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "aggregates": aggregates,
        "projects": [_project_to_entry(repo, p) for p in projects],
        "contributors": contributors,
    }


def write_payload(repo: Path, *, out_path: Path | None = None) -> Path:
    """Build + write the JSON file. Returns the written path."""
    payload = build_payload(repo)
    out = out_path or (repo / "web" / "data" / "projects.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return out


__all__ = [
    "SCHEMA_VERSION",
    "TERMINAL_STAGES",
    "build_payload",
    "phase_group",
    "write_payload",
]
