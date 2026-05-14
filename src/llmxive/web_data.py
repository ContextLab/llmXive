"""Build the web/data/projects.json payload (v2 schema, FR-027 ff).

Pure functions: input is the repo state on disk; output is a dict that
matches specs/002-website-integration/contracts/web-data-v2.schema.yaml.

Called by the Status-Reporter Agent after every successful pipeline cycle
(see agents/status_reporter.py::regenerate_web_data).
"""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from llmxive.state import project as project_store
from llmxive.types import Project, ReviewerKind, Stage

SCHEMA_VERSION = "2.0.0"

GITHUB_BLOB_BASE = "https://github.com/ContextLab/llmXive/blob/main"
GITHUB_RAW_BASE = "https://raw.githubusercontent.com/ContextLab/llmXive/main"
REGISTRY_GITHUB_URL = f"{GITHUB_BLOB_BASE}/agents/registry.yaml"

# Known prompt/agent role names — a contributor row's `name` MUST NEVER be one
# of these (they're roles, not who/what did the work). Used to keep the
# Contributors list pointing at models + GitHub usernames + "unattributed".
# (Derived dynamically from agents/registry.yaml in `_load_agent_names`; this
# literal set is a belt-and-suspenders fallback for the few legacy review
# frontmatters that predate the registry.)
_KNOWN_ROLE_PREFIXES = ("research_reviewer", "paper_reviewer", "paper_", "latex_")
_KNOWN_ROLE_NAMES = frozenset({
    "brainstorm", "flesh_out", "research_question_validator", "idea_selector",
    "project_initializer", "librarian", "specifier", "clarifier", "planner",
    "tasker", "implementer", "research_reviewer", "reference_validator",
    "paper_initializer", "proofreader", "status_reporter", "repository_hygiene",
    "task_atomizer", "task_joiner", "reviewer", "submission_intake", "agent",
})

UNATTRIBUTED = "unattributed"

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


# --- Agent registry + pipeline-step blocks (FR-003, FR-004, FR-006) ---------

def _load_registry(repo: Path) -> dict[str, Any]:
    reg_path = repo / "agents" / "registry.yaml"
    if not reg_path.exists():
        return {"agents": []}
    try:
        return yaml.safe_load(reg_path.read_text(encoding="utf-8")) or {"agents": []}
    except yaml.YAMLError:
        return {"agents": []}


_AGENT_NAMES_CACHE: dict[str, set[str]] = {}
_ALIAS_CACHE: dict[str, dict[str, dict[str, Any]]] = {}


def _load_contributor_aliases(repo: Path) -> dict[str, dict[str, Any]]:
    """Load `state/contributor_aliases.yaml` and return a flat lookup
    ``{lowercased_alias: {canonical, kind, github}}`` so any GH username /
    paper-author display-name pair the user has registered as the same person
    merges into a single contributor entry.

    The file is OPTIONAL — if it doesn't exist or is malformed, dedup just
    doesn't happen (and the build still succeeds).
    """
    key = str(repo)
    cached = _ALIAS_CACHE.get(key)
    if cached is not None:
        return cached
    path = repo / "state" / "contributor_aliases.yaml"
    lookup: dict[str, dict[str, Any]] = {}
    if path.is_file():
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError:
            data = {}
        for entry in (data.get("aliases") or []):
            canonical = str(entry.get("canonical", "")).strip()
            kind = str(entry.get("kind", "human")).strip() or "human"
            github = str(entry.get("github", "")).strip() or None
            if not canonical:
                continue
            # The canonical name itself counts as an alias (self-match).
            names = list(entry.get("aliases") or [])
            names.append(canonical)
            for n in names:
                k = str(n).strip().lower()
                if k:
                    lookup[k] = {"canonical": canonical, "kind": kind, "github": github}
    _ALIAS_CACHE[key] = lookup
    return lookup


def _resolve_alias(name: str, kind: str, repo: Path) -> tuple[str, str]:
    """Map ``(name, kind)`` to its canonical form via contributor_aliases.yaml.

    Returns ``(canonical_name, canonical_kind)``. If no alias rule applies
    (or the file is absent), returns the inputs unchanged.

    **Simulated-persona guard** (spec 008 / FR-011): a name ending in
    ``" (simulated)"`` is NEVER mapped to its real-name canonical, even if
    an alias-table entry would otherwise do so. This prevents
    ``Daniel Kahneman (simulated)`` from being merged into the real
    ``Daniel Kahneman`` contributor entry — the simulated-persona-vs-real-
    person distinction must survive every contributor-list rebuild.
    The string-suffix check is the class-wide invariant; per-pair exclusion
    entries are unnecessary.
    """
    if not name:
        return name, kind
    # Spec 008 FR-011 guard — applied BEFORE any alias lookup so it is
    # impossible to defeat via an accidental alias-table entry.
    if name.strip().endswith(" (simulated)"):
        return name, kind
    lookup = _load_contributor_aliases(repo)
    entry = lookup.get(name.strip().lower())
    if entry is None:
        return name, kind
    return entry["canonical"], entry["kind"] or kind


def _load_agent_names(repo: Path) -> set[str]:
    """Every agent name in the registry — these are roles, never contributors.

    Cached per repo path (read-once during a build)."""
    key = str(repo)
    cached = _AGENT_NAMES_CACHE.get(key)
    if cached is not None:
        return cached
    reg = _load_registry(repo)
    names = {str(a.get("name", "")).strip() for a in reg.get("agents", []) if a.get("name")}
    _AGENT_NAMES_CACHE[key] = names
    return names


def _looks_like_role(name: str, *, registry_names: set[str]) -> bool:
    """True if `name` is a pipeline agent/prompt role rather than a model/human."""
    n = (name or "").strip()
    if not n:
        return True
    if n in registry_names or n in _KNOWN_ROLE_NAMES:
        return True
    nl = n.lower()
    return any(nl.startswith(p) for p in _KNOWN_ROLE_PREFIXES)


def _build_agents_block(repo: Path) -> list[dict[str, Any]]:
    """One entry per agents/registry.yaml agent (E1)."""
    reg = _load_registry(repo)
    out: list[dict[str, Any]] = []
    for a in reg.get("agents", []):
        name = str(a.get("name", "")).strip()
        if not name:
            continue
        prompt_path = str(a.get("prompt_path", "")).strip() or None
        out.append({
            "name": name,
            "purpose": str(a.get("purpose", "")).strip(),
            "prompt_path": prompt_path,
            "prompt_github_url": (f"{GITHUB_BLOB_BASE}/{prompt_path}" if prompt_path else None),
            "prompt_raw_url": (f"{GITHUB_RAW_BASE}/{prompt_path}" if prompt_path else None),
            "registry_github_url": REGISTRY_GITHUB_URL,
            "tools": list(a.get("tools", []) or []),
            "default_backend": a.get("default_backend"),
            "default_model": a.get("default_model"),
            "inputs": list(a.get("inputs", []) or []),
            "outputs": list(a.get("outputs", []) or []),
        })
    return out


# Display metadata for each pipeline stage shown in the About-page diagram.
# `description`/`inputs`/`outputs` live here (moved out of web/index.html so the
# prose is defined in one place — Constitution I). Keys MUST match the
# `data-step` attributes on the .stage circles in index.html.
_PIPELINE_STAGE_DISPLAY: list[dict[str, Any]] = [
    # Research lane
    {"key": "brainstormed", "name": "Brainstormed", "lane": "research", "stage": Stage.BRAINSTORMED,
     "description": "A one-paragraph idea seed — a research question and a hint of how it might be tackled. Generated by the brainstorm agent (or submitted by a human).",
     "inputs": ["A research field"], "outputs": ["`idea/<slug>.md` — a short raw idea"]},
    {"key": "flesh_out", "name": "Flesh-out", "lane": "research", "stage": Stage.FLESH_OUT_COMPLETE,
     "description": "The raw seed is expanded into a structured idea grounded in primary literature: motivation, prior work, the precise question, a sketch of an approach, and what success would look like. A research-question validator then audits it for phenomenon-vs-method confusion, circularity, and triviality.",
     "inputs": ["A brainstormed `idea/<slug>.md`"], "outputs": ["An expanded `idea/<slug>.md` with citations", "A validator verdict (validated / revise / rejected)"]},
    {"key": "specified", "name": "Specified", "lane": "research", "stage": Stage.SPECIFIED,
     "description": "The project gets its own Spec Kit scaffold and a `spec.md` — user stories, functional requirements, success criteria — written by the specifier agent (the agentic equivalent of `/speckit-specify`).",
     "inputs": ["A validated idea", "The project's `.specify/` scaffold"], "outputs": ["`specs/NNN-<slug>/spec.md`"]},
    {"key": "clarified", "name": "Clarified", "lane": "research", "stage": Stage.CLARIFIED,
     "description": "Open questions and ambiguities in the spec are surfaced and resolved (the agentic `/speckit-clarify`). Each clarification is recorded back into `spec.md`.",
     "inputs": ["`spec.md` with `[NEEDS CLARIFICATION]` markers"], "outputs": ["`spec.md` with a `## Clarifications` section, no open markers"]},
    {"key": "planned", "name": "Planned", "lane": "research", "stage": Stage.PLANNED,
     "description": "The implementation plan: architecture, data model, contracts, research notes (the agentic `/speckit-plan`).",
     "inputs": ["A clarified `spec.md`"], "outputs": ["`plan.md`, `data-model.md`, `contracts/`, `research.md`"]},
    {"key": "tasked", "name": "Tasked", "lane": "research", "stage": Stage.TASKED,
     "description": "The plan is decomposed into an ordered, dependency-aware task list (`/speckit-tasks`), then cross-checked for consistency (`/speckit-analyze`).",
     "inputs": ["`plan.md` + contracts"], "outputs": ["`tasks.md`", "An analyze report (0 critical issues to proceed)"]},
    {"key": "in_progress", "name": "In progress", "lane": "research", "stage": Stage.IN_PROGRESS,
     "description": "The implementer agent executes the task list — writing code, running real tests, collecting data — ticking tasks off until the plan is complete. The librarian agent verifies citations along the way.",
     "inputs": ["`tasks.md`"], "outputs": ["Code under `projects/<id>/code/`", "Data under `projects/<id>/data/`", "All tasks checked off → research_complete"]},
    {"key": "research_review", "name": "Research review", "lane": "research", "stage": Stage.RESEARCH_REVIEW,
     "description": "Seven specialist reviewers (idea quality, creativity, implementation correctness, completeness, code quality, data quality, filesystem hygiene) each vote. Acceptance requires both the points threshold and an accept verdict from every specialist. Human reviews count double.",
     "inputs": ["A research_complete project"], "outputs": ["Review records under `projects/<id>/reviews/research/`", "A verdict (accepted / minor revision / full revision / rejected)"]},
    # Paper lane
    {"key": "paper_init", "name": "Paper init", "lane": "paper", "stage": Stage.PAPER_DRAFTING_INIT,
     "description": "A research-accepted project gets a second Spec Kit scaffold — for the paper that reports the work.",
     "inputs": ["A research-accepted project"], "outputs": ["`projects/<id>/paper/.specify/` scaffold"]},
    {"key": "paper_spec", "name": "Paper spec", "lane": "paper", "stage": Stage.PAPER_SPECIFIED,
     "description": "The paper's specification: which sections, which figures, which claims, what evidence each rests on.",
     "inputs": ["The paper Spec Kit scaffold", "The research artifacts (code, data, results)"], "outputs": ["`paper/specs/NNN-<slug>/spec.md`"]},
    {"key": "paper_plan", "name": "Paper plan", "lane": "paper", "stage": Stage.PAPER_PLANNED,
     "description": "The paper plan and contracts (clarify + plan for the paper pipeline).",
     "inputs": ["The paper `spec.md`"], "outputs": ["`paper/.../plan.md`, contracts"]},
    {"key": "paper_tasks", "name": "Paper tasks", "lane": "paper", "stage": Stage.PAPER_TASKED,
     "description": "Writing, figure-generation, and statistics sub-tasks (tasks + analyze for the paper pipeline).",
     "inputs": ["The paper `plan.md`"], "outputs": ["`paper/.../tasks.md`", "Paper analyze report"]},
    {"key": "paper_drafting", "name": "Drafting", "lane": "paper", "stage": Stage.PAPER_IN_PROGRESS,
     "description": "The paper-writing, figure-generation, and statistics agents draft the LaTeX, generate figures from the data, and run the analyses; LaTeX is built and citations are verified.",
     "inputs": ["`paper/.../tasks.md`", "The research data"], "outputs": ["`paper/source/main.tex` + figures", "A compiled PDF", "Verified citations"]},
    {"key": "paper_complete", "name": "Paper complete", "lane": "paper", "stage": Stage.PAPER_COMPLETE,
     "description": "The draft compiles cleanly, all citations are verified, and the proofreader is satisfied — ready for paper review.",
     "inputs": ["A drafted paper"], "outputs": ["A review-ready PDF + sources"]},
    {"key": "paper_review", "name": "Paper review", "lane": "paper", "stage": Stage.PAPER_REVIEW,
     "description": "Twelve specialist reviewers (writing, logic, claims, over-reach, safety/ethics, evidence, statistics, code, data, formatting, figures, jargon) each vote. Acceptance requires both the points threshold and an accept verdict from every specialist.",
     "inputs": ["A paper-complete project"], "outputs": ["Review records under `projects/<id>/paper/reviews/`", "A verdict (accepted / minor / major-writing / major-science / fundamental flaws)"]},
    {"key": "posted", "name": "Posted", "lane": "paper", "stage": Stage.POSTED,
     "description": "The paper is published — the PDF is final and an announcement goes out. The project is done.",
     "inputs": ["A paper-accepted project"], "outputs": ["A public PDF", "A posted announcement"]},
]

# Tool-style agents a stage uses in addition to its primary owner.
_STAGE_EXTRA_AGENTS: dict[str, list[str]] = {
    "flesh_out": ["research_question_validator", "idea_selector"],
    "in_progress": ["librarian", "reference_validator"],
    "research_review": [
        "research_reviewer_idea_quality", "research_reviewer_creativity",
        "research_reviewer_implementation_correctness", "research_reviewer_implementation_completeness",
        "research_reviewer_code_quality_research", "research_reviewer_data_quality_research",
        "research_reviewer_filesystem_hygiene",
    ],
    "paper_drafting": ["paper_writing", "paper_figure_generation", "paper_statistics",
                       "proofreader", "latex_build", "latex_fix", "reference_validator"],
    "paper_review": [
        "paper_reviewer_writing_quality", "paper_reviewer_logical_consistency",
        "paper_reviewer_claim_accuracy", "paper_reviewer_overreach", "paper_reviewer_safety_ethics",
        "paper_reviewer_scientific_evidence", "paper_reviewer_statistical_analysis",
        "paper_reviewer_code_quality_paper", "paper_reviewer_data_quality_paper",
        "paper_reviewer_text_formatting", "paper_reviewer_figure_critic", "paper_reviewer_jargon_police",
    ],
    "posted": ["status_reporter"],
}

# Which stages count a project as "at or past" a given pipeline step (for the
# example-artifacts list). Ordered roughly by lifecycle position.
_STAGES_AT_OR_PAST: dict[str, list[Stage]] = {}


def _build_pipeline_steps_block(repo: Path, projects: list[Project], agent_names: set[str]) -> list[dict[str, Any]]:
    """One entry per pipeline stage shown in the diagram (E2)."""
    # Lazy import — keeps web_data importable without the heavy speckit deps
    # unless this block is actually built.
    try:
        from llmxive.pipeline.graph import STAGE_TO_AGENT
    except Exception:  # pragma: no cover - defensive
        STAGE_TO_AGENT = {}

    # Order index for each Stage value (for the "at or past" computation).
    stage_order = {s: i for i, s in enumerate(Stage)}

    # Group projects by current stage.
    by_stage: dict[Stage, list[Project]] = {}
    for p in projects:
        by_stage.setdefault(p.current_stage, []).append(p)

    out: list[dict[str, Any]] = []
    for order, disp in enumerate(_PIPELINE_STAGE_DISPLAY):
        stage = disp["stage"]
        key = disp["key"]
        # Primary owning agent + extras (filtered to agents that exist).
        agents: list[str] = []
        primary = STAGE_TO_AGENT.get(stage)
        if primary:
            agents.append(primary)
        for extra in _STAGE_EXTRA_AGENTS.get(key, []):
            if extra not in agents:
                agents.append(extra)
        agents = [a for a in agents if a in agent_names or a == primary]

        # Example artifacts: most-recent projects at or past this stage.
        threshold = stage_order.get(stage, 0)
        at_or_past = [p for p in projects if stage_order.get(p.current_stage, -1) >= threshold]
        at_or_past.sort(key=lambda p: p.updated_at, reverse=True)
        examples = [
            {
                "project_id": p.id,
                "title": p.title,
                "github_url": f"https://github.com/ContextLab/llmXive/tree/main/projects/{p.id}",
            }
            for p in at_or_past[:5]
        ]
        out.append({
            "key": key,
            "name": disp["name"],
            "lane": disp["lane"],
            "order": order,
            "description": disp["description"],
            "inputs": list(disp["inputs"]),
            "outputs": list(disp["outputs"]),
            "agents": agents,
            "example_artifacts": examples,
        })
    return out


# --- per-project current_artifact (E3, FR-009) ------------------------------

def _current_artifact(repo: Path, project: Project, links: dict[str, str | None]) -> dict[str, Any]:
    """Resolve the artifact to display in the project modal.

    Priority: a published paper PDF → else the most-advanced text artifact for
    the project's stage → else "none". `type == "pdf"` iff a PDF exists.
    """
    def make(kind: str, rel: str | None) -> dict[str, Any]:
        if not rel:
            return {"type": "none", "repo_path": None, "github_url": None, "raw_url": None}
        return {
            "type": kind,
            "repo_path": rel,
            "github_url": f"{GITHUB_BLOB_BASE}/{rel}",
            "raw_url": f"{GITHUB_RAW_BASE}/{rel}",
        }

    # 1. Published PDF wins.
    if links.get("paper_pdf"):
        return make("pdf", links["paper_pdf"])

    # 2. Otherwise pick the most-advanced text artifact present, by stage.
    #    LaTeX source → paper tasks/plan/spec → research tasks/plan/spec → idea.
    if links.get("paper_source"):
        return make("latex", links["paper_source"])
    for key in ("paper_tasks", "paper_plan", "paper_spec", "tasks", "plan", "spec"):
        if links.get(key):
            return make("markdown", links[key])
    if links.get("citations"):
        return make("yaml", links["citations"])
    if links.get("idea"):
        return make("markdown", links["idea"])
    return make("none", None)


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
    paper_source_supplement = pdir / "paper" / "source" / "supplement.tex"
    # Look for the compiled PDF in two canonical locations:
    #   paper/pdf/*.pdf   — used when a separate publish step copies it
    #   paper/source/main.pdf — used when pdflatex runs in-place
    #
    # The pdf/ dir may contain BOTH the main PDF and a supplement (when the
    # paper has supplementary materials). Pick the main one explicitly so the
    # supplement PDF doesn't shadow it. Filename precedence for main:
    #   main-llmxive.pdf → main.pdf → first *.pdf that doesn't look like a
    #   supplement.
    paper_pdf = None
    paper_supplement_pdf = None
    pdf_dir = pdir / "paper" / "pdf"
    if pdf_dir.exists():
        candidates = sorted(pdf_dir.glob("*.pdf"))
        # Identify supplement (anything with "supplement" in the stem).
        for c in candidates:
            if "supplement" in c.stem.lower() and paper_supplement_pdf is None:
                paper_supplement_pdf = c
        # Identify main: explicit preferred names, then anything not the supplement.
        for name in ("main-llmxive.pdf", "main.pdf"):
            cand = pdf_dir / name
            if cand.exists():
                paper_pdf = cand
                break
        if paper_pdf is None:
            for c in candidates:
                if c != paper_supplement_pdf:
                    paper_pdf = c
                    break
    if paper_pdf is None and (pdir / "paper" / "source" / "main.pdf").exists():
        paper_pdf = pdir / "paper" / "source" / "main.pdf"
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
        "paper_supplement_source": rel(paper_source_supplement) if paper_source_supplement.exists() else None,
        "paper_pdf": rel(paper_pdf) if paper_pdf else None,
        "paper_supplement": rel(paper_supplement_pdf) if paper_supplement_pdf else None,
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
            "model": _normalize_model_name(e.get("model_name", "") or ""),
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


def _project_submitter(repo: Path, project_id: str) -> str | None:
    """Identify the submitter (GitHub username or model name) from idea front-matter."""
    pdir = _project_dir(repo, project_id)
    idea = next(iter(pdir.glob("idea/*.md")), None)
    if idea is None or not idea.exists():
        return None
    text = idea.read_text(encoding="utf-8", errors="replace")
    if not text.startswith("---"):
        return None
    try:
        end = text.index("---", 3)
        front = yaml.safe_load(text[3:end]) or {}
    except (ValueError, yaml.YAMLError):
        return None
    sub = front.get("submitter") or front.get("submitted_by") or front.get("author")
    if sub:
        return str(sub).strip() or None
    # Legacy bodies: "Model: Qwen/Qwen2.5-3B-Instruct"
    m = re.search(r"\*Model:\s*([^\n*]+)", text)
    if m:
        return m.group(1).strip()
    return None


def _project_description(repo: Path, project_id: str, *, max_chars: int = 320) -> str:
    """Card-level description excerpt extracted from the idea Markdown body."""
    pdir = _project_dir(repo, project_id)
    idea = next(iter(pdir.glob("idea/*.md")), None)
    if idea is None or not idea.exists():
        return ""
    text = idea.read_text(encoding="utf-8", errors="replace")
    if text.startswith("---"):
        try:
            text = text[text.index("---", 3) + 3:]
        except ValueError:
            pass
    lines: list[str] = []
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        s = s.replace("**", "").replace("__", "")
        lines.append(s)
        if sum(len(x) + 1 for x in lines) >= max_chars:
            break
    blob = " ".join(lines)
    if len(blob) > max_chars:
        blob = blob[:max_chars].rsplit(" ", 1)[0] + "…"
    return blob


def _project_authors(repo: Path, project_id: str) -> list[dict[str, str]]:
    """All entities (models + humans) that contributed to the project.

    Aggregates from:
      - idea/<slug>.md frontmatter (submitter)
      - state/run-log/**/*.jsonl entries with project_id matching
      - projects/<id>/reviews/research/*.md frontmatter (reviewer_name + kind)
      - projects/<id>/paper/reviews/*.md frontmatter
      - projects/<id>/reviews/paper/*.md frontmatter

    Each author entry includes:
      - name: the model id, github username, or "human:<name>"
      - kind: "llm" | "human"
      - role: comma-joined list of roles (brainstorm, flesh_out, specifier,
              tasker, implementer, research_reviewer_*, paper_reviewer_*, ...)
      - contributions: count of distinct contributions

    De-duplicated and sorted by contribution count descending.
    """
    bucket: dict[tuple[str, str], dict[str, Any]] = {}
    registry_names = _load_agent_names(repo)

    def add(name: str, kind: str, role: str) -> None:
        if not name:
            return
        # Resolve aliases FIRST (handles the GH-username vs full-name dup case),
        # then normalize. This way one person's GitHub login and paper-author
        # display name collapse into a single contributor entry.
        canonical, canonical_kind = _resolve_alias(name, kind, repo)
        key = (_normalize_model_name(canonical), canonical_kind)
        row = bucket.setdefault(
            key,
            {"name": _normalize_model_name(canonical), "kind": canonical_kind,
             "roles": set(), "contributions": 0},
        )
        row["roles"].add(role)
        row["contributions"] += 1

    pdir = _project_dir(repo, project_id)

    # 1. Idea submitter
    submitter = _project_submitter(repo, project_id)
    if submitter and not submitter.startswith(("system:", "legacy:", "agent:")):
        kind = "llm" if (
            "/" in submitter
            or any(p in submitter.lower() for p in ("qwen", "gemma", "claude", "tinyllama", "gpt", "mistral", "llama"))
            or "." in submitter.split("-")[0]
        ) else "human"
        add(submitter, kind, "brainstorm_submitter")

    # 1b. Paper authors (parsed from the paper itself by `submission_intake`)
    #     — the user's rule: credit on a submitted paper goes to its *authors*,
    #     separately from whoever submitted it. The `paper_authors:` list lives
    #     in the idea front-matter and gets surfaced here as kind="human"
    #     contributors with a `paper_author` role.
    idea = next(iter(pdir.glob("idea/*.md")), None) if pdir.exists() else None
    if idea is not None and idea.exists():
        text = idea.read_text(encoding="utf-8", errors="replace")
        if text.startswith("---"):
            try:
                fm = yaml.safe_load(text[3:text.index("---", 3)]) or {}
            except (ValueError, yaml.YAMLError):
                fm = {}
            for author in (fm.get("paper_authors") or []):
                name = str(author).strip()
                if name:
                    add(name, "human", "paper_author")

    # 2. Run-log: every successful agent invocation contributes its model
    runlog_root = repo / "state" / "run-log"
    if runlog_root.is_dir():
        for month_dir in runlog_root.iterdir():
            if not month_dir.is_dir() or month_dir.name.startswith("."):
                continue
            for jsonl in month_dir.glob("*.jsonl"):
                for line in jsonl.read_text(encoding="utf-8", errors="ignore").splitlines():
                    if not line.strip():
                        continue
                    try:
                        e = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if e.get("project_id") != project_id:
                        continue
                    if e.get("outcome") != "success":
                        continue
                    model = (e.get("model_name") or "").strip()
                    role = (e.get("agent_name") or "").strip()
                    if model:
                        add(model, "llm", role or "agent")

    # 3. Review records (both stages)
    for sub in ("reviews/research", "paper/reviews", "reviews/paper"):
        rdir = pdir / sub
        if not rdir.is_dir():
            continue
        for md in rdir.rglob("*.md"):
            try:
                text = md.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            if not text.startswith("---"):
                continue
            try:
                end = text.index("---", 3)
                fm = yaml.safe_load(text[3:end]) or {}
            except (ValueError, yaml.YAMLError):
                continue
            kind_raw = str(fm.get("reviewer_kind", "")).strip()
            role = str(fm.get("reviewer_name") or "reviewer").strip()
            if kind_raw == "human":
                # reviewer_name is the GitHub username for a human review.
                name = str(fm.get("reviewer_name", "")).strip()
                kind = "human"
                if not name or _looks_like_role(name, registry_names=registry_names):
                    name, kind = UNATTRIBUTED, "unattributed"
            else:
                # LLM review: the model is in model_name; reviewer_name is the
                # reviewer *role* — never use it as the contributor identity.
                raw_model = str(fm.get("model_name", "")).strip()
                if raw_model:
                    name, kind = _normalize_model_name(raw_model), "llm"
                else:
                    name, kind = UNATTRIBUTED, "unattributed"
            add(name, kind, role)

    out = []
    for r in sorted(bucket.values(), key=lambda r: -r["contributions"]):
        out.append({
            "name": r["name"],
            "kind": r["kind"],
            "roles": sorted(r["roles"]),
            "contributions": r["contributions"],
        })
    return out


def _project_to_entry(repo: Path, project: Project) -> dict[str, Any]:
    research_total = float(sum(project.points_research.values()))
    paper_total = float(sum(project.points_paper.values()))
    links = _build_artifact_links(repo, project)
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
        "description": _project_description(repo, project.id),
        "submitter": _project_submitter(repo, project.id),
        "authors": _project_authors(repo, project.id),
        "speckit_research_dir": project.speckit_research_dir,
        "speckit_paper_dir": project.speckit_paper_dir,
        "artifact_links": links,
        "current_artifact": _current_artifact(repo, project, links),
        "citation_summary": _citation_summary(repo, project.id),
        "last_run_log": _last_run_log(repo, project.id),
    }


def _aggregates(projects: list[Project], contributors: list[dict[str, Any]],
                reviews_by_kind: dict[ReviewerKind, set[str]]) -> dict[str, int]:
    """Aggregates derived from the *final* contributor list, so the headline
    numbers and the Contributors table can never disagree (FR-008)."""
    active = sum(1 for p in projects if p.current_stage not in TERMINAL_STAGES)
    posted = sum(1 for p in projects if p.current_stage == Stage.POSTED)

    total_contribs = sum(int(c.get("contribution_count", 0)) for c in contributors)
    total_contributors = len(contributors)
    human_contributors = sum(1 for c in contributors if c.get("kind") == "human")
    ai_contributors = sum(1 for c in contributors if c.get("kind") == "llm")
    # "Collaborations" ≈ distinct human reviewers (the human-in-the-loop signal).
    humans = reviews_by_kind.get(ReviewerKind.HUMAN, set())
    return {
        "total_contributions": total_contribs,
        "active_projects": active,
        "papers_posted": posted,
        "total_contributors": total_contributors,
        "human_contributors": human_contributors,
        "ai_contributors": ai_contributors,
        "total_collaborations": len(humans),
    }


def _collect_reviews(repo: Path) -> tuple[dict[ReviewerKind, set[str]], list[dict[str, Any]]]:
    """Walk every projects/<PROJ-ID>/reviews tree and collect contributor rows.

    FR-007 / FR-008: a contributor row's `name` is a *model* (for LLM reviews,
    from the review-frontmatter `model_name`) or a *GitHub username* (for human
    reviews, from `reviewer_name`) — never the review-agent role
    (`research_reviewer_idea_quality`, `paper_reviewer_jargon_police`, …),
    which is what `reviewer_name` holds for LLM reviews. If an LLM review has
    no `model_name`, the contribution still counts — under the single
    `"unattributed"` bucket — it's never dropped and never shown under a role.
    """
    by_kind: dict[ReviewerKind, set[str]] = {ReviewerKind.LLM: set(), ReviewerKind.HUMAN: set()}
    contributor_rows: dict[tuple[str, str], dict[str, Any]] = {}
    fields = _project_fields(repo)
    registry_names = _load_agent_names(repo)
    proj_root = repo / "projects"
    if not proj_root.is_dir():
        return by_kind, []

    def bump(name: str, kind: str, field: str) -> None:
        key = (name, kind)
        row = contributor_rows.setdefault(
            key, {"name": name, "kind": kind, "contribution_count": 0, "areas": set()}
        )
        row["contribution_count"] += 1
        if field and field != "general":
            row["areas"].add(field)

    for pdir in proj_root.glob("PROJ-*"):
        field = fields.get(pdir.name, "")
        for sub in ("reviews/research", "paper/reviews", "reviews/paper"):
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
                kind_raw = str(fm.get("reviewer_kind", "")).strip()
                try:
                    rkind = ReviewerKind(kind_raw)
                except ValueError:
                    continue
                if rkind == ReviewerKind.HUMAN:
                    # The reviewer_name for a human review IS the GitHub username.
                    name = str(fm.get("reviewer_name", "")).strip()
                    if not name or _looks_like_role(name, registry_names=registry_names):
                        name = UNATTRIBUTED
                        ckind = "unattributed"
                    else:
                        ckind = "human"
                        by_kind[ReviewerKind.HUMAN].add(name)
                else:
                    # LLM review: the model is in `model_name`; `reviewer_name`
                    # is the reviewer *role* — never use it as the contributor.
                    raw_model = str(fm.get("model_name", "")).strip()
                    if raw_model:
                        name = _normalize_model_name(raw_model)
                        ckind = "llm"
                        by_kind[ReviewerKind.LLM].add(name)
                    else:
                        name = UNATTRIBUTED
                        ckind = "unattributed"
                bump(name, ckind, field)

    rows = []
    for r in contributor_rows.values():
        r["areas"] = sorted(r["areas"])
        rows.append(r)
    return by_kind, rows


def _project_fields(repo: Path) -> dict[str, str]:
    """Map PROJ-NNN id → research field, used to label contributor areas."""
    out: dict[str, str] = {}
    for p in project_store.list_all(repo_root=repo):
        out[p.id] = (p.field or "").strip().lower() or "general"
    return out


def _agent_contributors(repo: Path) -> list[dict[str, Any]]:
    """Aggregate AI contributors from successful run-log entries.

    Identity = model name (e.g. ``qwen.qwen3.5-122b``), NOT the agent
    role (``tasker``/``implementer``). Multiple roles using the same
    model collapse into a single contributor row. Areas reflect the
    research field of the project worked on, NOT the pipeline step.

    FR-008 — `contribution_count` is a count of *distinct artifacts*, not of
    run-log lines: a model that re-ran the implementer 56 times on one project
    (each retry / continuation appended a line) produced one logical
    contribution, not 56. We dedup by ``(model, project_id, agent_name)`` —
    "this model did this role's work on this project" counts once. (Idea
    submissions and review files are counted once each elsewhere — in
    `_submitter_contributors` / `_collect_reviews` — so the merged total has
    no double-counting.)
    """
    runlog_root = repo / "state" / "run-log"
    fields = _project_fields(repo)
    # (model, project_id, agent_name) tuples, deduped.
    seen: set[tuple[str, str, str]] = set()
    areas_by_model: dict[str, set[str]] = {}
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
                    model = (e.get("model_name") or "").strip()
                    if not model:
                        # Skip entries with no model attribution. The
                        # agent_name (e.g. "tasker") would mislead.
                        continue
                    model = _normalize_model_name(model)
                    pid = e.get("project_id") or ""
                    agent_name = (e.get("agent_name") or "").strip()
                    seen.add((model, pid, agent_name))
                    field = fields.get(pid, "")
                    if field and field != "general":
                        areas_by_model.setdefault(model, set()).add(field)
    counts: dict[str, int] = {}
    for model, _pid, _agent in seen:
        counts[model] = counts.get(model, 0) + 1
    out = []
    for model, n in counts.items():
        out.append({
            "name": model,
            "kind": "llm",
            "contribution_count": n,
            "areas": sorted(areas_by_model.get(model, set())),
        })
    return out


def _normalize_model_name(name: str) -> str:
    """Collapse alias forms of the same model.

    e.g. "Qwen/Qwen2.5-3B-Instruct" → "Qwen2.5-3B-Instruct" so it
    aggregates with the bare form in the contributor list.
    """
    name = name.strip()
    if "/" in name:
        return name.split("/", 1)[1]
    return name


def _submitter_contributors(repo: Path, projects: list) -> list[dict[str, Any]]:
    """Each project's idea submitter counts as one contribution.

    Distinguishes:
      - GitHub usernames (kind=human) — anything matching a typical
        username pattern without dots/slashes is treated as human.
      - Model names (kind=llm) — strings containing slashes (e.g.
        "Qwen/Qwen2.5-3B-Instruct") or dots-then-name (e.g.
        "google.gemma-3-27b-it") or any of the known model family
        prefixes (TinyLlama, Qwen, Claude, GPT, Gemma, Mistral).
      - Anything starting with "system:" or "legacy:" or
        "agent:" is skipped (no real attribution).
    """
    rows: dict[tuple[str, str], dict[str, Any]] = {}
    model_prefixes = (
        "tinyllama", "qwen", "claude", "gpt", "gemma", "mistral",
        "google.", "qwen.", "openai.", "anthropic.",
    )
    for p in projects:
        sub = _project_submitter(repo, p.id)
        if not sub:
            continue
        if sub.startswith(("system:", "legacy:", "agent:")):
            continue
        low = sub.lower()
        is_model = (
            "/" in sub
            or any(low.startswith(pre) or pre in low for pre in model_prefixes)
            or "." in sub.split("-")[0]
        )
        kind = "llm" if is_model else "human"
        if kind == "llm":
            sub = _normalize_model_name(sub)
        # Apply alias resolution so a GH-username submitter doesn't show up
        # separately from their paper-author display name.
        sub, kind = _resolve_alias(sub, kind, repo)
        key = (sub, kind)
        row = rows.setdefault(
            key, {"name": sub, "kind": kind, "contribution_count": 0, "areas": set()}
        )
        row["contribution_count"] += 1
        field = (p.field or "").strip().lower()
        if field and field != "general":
            row["areas"].add(field)
    return [
        {
            "name": r["name"],
            "kind": r["kind"],
            "contribution_count": r["contribution_count"],
            "areas": sorted(r["areas"]),
        }
        for r in rows.values()
    ]


def _paper_author_contributors(repo: Path, projects: list) -> list[dict[str, Any]]:
    """Each `paper_authors:` entry in a project's idea front-matter counts as
    one contribution by that human author (FR-007 + the user's "credit goes to
    the paper's authors not just the submitter" rule). Surfaced in the
    top-level contributors list as kind="human".
    """
    rows: dict[tuple[str, str], dict[str, Any]] = {}
    for p in projects:
        idea_dir = repo / "projects" / p.id / "idea"
        if not idea_dir.is_dir():
            continue
        for md in idea_dir.glob("*.md"):
            text = md.read_text(encoding="utf-8", errors="replace")
            if not text.startswith("---"):
                continue
            try:
                fm = yaml.safe_load(text[3:text.index("---", 3)]) or {}
            except (ValueError, yaml.YAMLError):
                continue
            for author in (fm.get("paper_authors") or []):
                name = str(author).strip()
                if not name:
                    continue
                # Merge GH-username submitter ↔ paper-author display name.
                canon, kind = _resolve_alias(name, "human", repo)
                key = (canon, kind)
                row = rows.setdefault(
                    key, {"name": canon, "kind": kind, "contribution_count": 0, "areas": set()}
                )
                row["contribution_count"] += 1
                field = (p.field or "").strip().lower()
                if field and field != "general":
                    row["areas"].add(field)
    return [
        {"name": r["name"], "kind": r["kind"],
         "contribution_count": r["contribution_count"], "areas": sorted(r["areas"])}
        for r in rows.values()
    ]


def _build_personalities_block(repo: Path) -> list[dict[str, Any]]:
    """Emit the ``personalities`` array consumed by the website's About-page
    Personality Registry modal (spec 008 / FR-024).

    Walks ``agents/prompts/personalities/*.md``, parses each front-matter,
    and returns one entry per well-formed file sorted by slug. The schema
    is in ``specs/008-personality-agents/contracts/website-personalities-block.schema.json``.

    Malformed files are skipped (same policy as the rotation pool —
    Story 2 scenario 2 / FR-001). New persona files added to the
    directory show up here on the next data-build with no code change
    (FR-020 + Story 2 scenario 1 + SC-010).
    """
    from llmxive.agents import personality as _persona

    pool_dir = repo / _persona.POOL_PATH
    if not pool_dir.is_dir():
        return []
    result = _persona.load_pool(pool_dir)
    out: list[dict[str, Any]] = []
    for p in result.personalities:
        prompt_repo_path = f"{_persona.POOL_PATH}/{p.slug}.md"
        out.append({
            "slug": p.slug,
            "display_name": p.display_name,
            "summary": p.summary,
            "sources": list(p.sources),
            "prompt_repo_path": prompt_repo_path,
            "prompt_raw_url": f"{GITHUB_RAW_BASE}/{prompt_repo_path}",
            "prompt_github_url": f"{GITHUB_BLOB_BASE}/{prompt_repo_path}",
        })
    return out


def build_payload(repo: Path) -> dict[str, Any]:
    """Top-level builder: returns the dict to be serialized to projects.json."""
    # Clear the per-build registry-name cache (a long-lived process building
    # multiple repos / fixtures must not see a stale set).
    _AGENT_NAMES_CACHE.clear()
    _ALIAS_CACHE.clear()
    registry_names = _load_agent_names(repo)
    projects = project_store.list_all(repo_root=repo)
    by_kind, human_rows = _collect_reviews(repo)
    ai_rows = _agent_contributors(repo)
    submitter_rows = _submitter_contributors(repo, projects)
    paper_author_rows = _paper_author_contributors(repo, projects)

    # FR-007: drop any row whose `name` is a pipeline agent/prompt role (a
    # belt-and-suspenders sweep — _collect_reviews/_agent_contributors already
    # avoid emitting roles, but legacy data or future code paths shouldn't be
    # able to leak one through). A role-named row's contributions are folded
    # into the single "unattributed" bucket so they're never lost.
    def _scrub(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for r in rows:
            if r.get("kind") in ("llm", "human") and _looks_like_role(r["name"], registry_names=registry_names):
                out.append({"name": UNATTRIBUTED, "kind": "unattributed",
                            "contribution_count": r["contribution_count"], "areas": list(r.get("areas", []))})
            else:
                out.append(r)
        return out

    # Merge human reviewer rows + AI agent rows + per-project submitters.
    rows_by_key: dict[tuple[str, str], dict[str, Any]] = {}
    for r in _scrub(ai_rows) + _scrub(human_rows) + _scrub(submitter_rows) + _scrub(paper_author_rows):
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
    # Sort: real contributors by count desc; the "unattributed" bucket always last.
    contributors = sorted(
        rows_by_key.values(),
        key=lambda r: (r["kind"] == "unattributed", -r["contribution_count"], r["name"]),
    )

    aggregates = _aggregates(projects, contributors, by_kind)

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": datetime.now(UTC).isoformat(),
        "aggregates": aggregates,
        "projects": [_project_to_entry(repo, p) for p in projects],
        "contributors": contributors,
        "agents": _build_agents_block(repo),
        "personalities": _build_personalities_block(repo),
        "pipeline_steps": _build_pipeline_steps_block(repo, projects, registry_names),
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
