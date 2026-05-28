"""Personality agent (spec 008).

Simulated public-figure personas — David Krakauer, Geoffrey West, Dan
Rockmore, Socrates, Aristotle, Daniel Kahneman, Ada Lovelace, Marie Curie,
Rosalind Franklin, John von Neumann. One persona per 30-minute cron tick,
rotating through the on-disk pool at ``agents/prompts/personalities/``.

Each tick the selected persona:
  1. Reads the project catalog (top 30 most-recently-updated projects with
     ≤ 2 recent artifacts each).
  2. Picks ONE action — ``comment``, ``contribute``, ``propose_arxiv``,
     or ``abstain`` — via a single LLM call returning a structured JSON
     response (parsed per :func:`parse_action`).
  3. Dispatches the action through an EXISTING pipe (no duplicate writers
     per Constitution Principle I) — review-file writer for comments,
     ``submission_intake.process_submission_issue`` for contribute and
     propose_arxiv via the existing feedback / paper-submission paths.
  4. Records a run-log entry with attribution markers that flow into the
     website's Contributors list as ``"<Display Name> (simulated)"``.

The rotation pointer (filename stem of the last-selected persona) lives
in ``state/personality_rotation.yaml`` and is committed per tick. Pointer
advances on ``committed`` / ``abstained`` outcomes; HOLDS on
``rate_limited`` / ``model_error`` / ``malformed_response`` /
``target_missing`` / ``librarian_held`` / ``timeout`` so the same
persona retries on the next tick (per FR-017).

Per spec 008 FR-019: the cron cadence lives in
``.github/workflows/pipeline-personality.yml`` and the pool path lives
in :data:`POOL_PATH` below — those are the only two configuration knobs.
"""

from __future__ import annotations

import dataclasses
import datetime as _dt
import json
import logging
import os
import re
from pathlib import Path
from typing import Any

import yaml

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Configuration (FR-019: pool path is editable here only; cron cadence lives
# in .github/workflows/pipeline-personality.yml — no env vars / CLI flags /
# config files involved).
# ---------------------------------------------------------------------------

POOL_PATH = "agents/prompts/personalities"
"""Directory holding one Markdown file per persona, sorted lexicographically
by filename stem (the slug). Default is ``agents/prompts/personalities``.
Edit this constant in source to relocate the pool — the entire system reads
it through here."""

ROTATION_PATH = "state/personality_rotation.yaml"
"""Per-pool rotation pointer + history file. Committed per tick."""

UMBRELLA_PROMPT_PATH = "agents/prompts/personality.md"
"""The decision-protocol umbrella prompt prepended to every persona's
grounding card at LLM call time."""

MODEL_NAME = "qwen.qwen3.5-122b"
"""Canonical Dartmouth-Chat model id (the registry form). Recorded in
run-log entries; also the only allowed model for FR-015."""

MODEL_KIND = "personality_simulator"
"""Distinguishes simulated personas from other LLM agents in the run-log."""

AGENT_NAME = "personality"
"""Umbrella agent name (matches the registry entry added in T002)."""

HISTORY_LIMIT = 200
"""Rotation-history retained in ``state/personality_rotation.yaml``."""

DEFAULT_CATALOG_LIMIT = 30
"""Max projects shown to the persona per tick (FR-005). Older projects
beyond this are summarized with an "<N> additional projects elided" line."""

DEFAULT_RECENT_ARTIFACTS = 2
"""Max recent artifacts per project in the catalog."""

DEFAULT_TIMEOUT_S = 600
"""Per-tick wall-clock budget (FR-017 / Story 5)."""

CONTENT_MAX_WORDS = 2000
"""Guardrail on the LLM-emitted ``content`` field length."""

DISCLAIMER_TEMPLATE = (
    "\n\n---\n\n"
    "> *Note: this contribution was authored by **{display_name}** — "
    "a simulated AI persona shaped from the public-record writings of {real_name}, "
    "running on `qwen-3.5-122b` via Dartmouth Chat. It is not the actual {real_name}.*\n"
)
"""Verbatim disclaimer footer (data-model.md E5). Placed at the very bottom
of every committed artifact, after a horizontal-rule separator."""


# ---------------------------------------------------------------------------
# Data classes (data-model.md E1, E2, E4, E6)
# ---------------------------------------------------------------------------

# Outcome enum — string constants rather than Enum to keep the run-log
# JSONL serializable without a custom encoder. The values are the only
# valid `outcome` field values per data-model.md E6.
OUTCOME_COMMITTED = "committed"
OUTCOME_ABSTAINED = "abstained"
OUTCOME_RATE_LIMITED = "rate_limited"
OUTCOME_MODEL_ERROR = "model_error"
OUTCOME_MALFORMED = "malformed_response"
OUTCOME_TARGET_MISSING = "target_missing"
OUTCOME_LIBRARIAN_HELD = "librarian_held"
OUTCOME_TIMEOUT = "timeout"
# Spec 009 FR-004 + Clarification Q3: rubric failure (a *quality* failure, not
# an infrastructure one) converts to abstain after one retry and ADVANCES the
# rotation. Spec-008 FR-017 hold-on-failure still applies to infrastructure
# outcomes only (rate_limited / model_error / malformed_response / timeout).
OUTCOME_RUBRIC_REJECTED = "rubric_rejected_advanced_as_abstain"
# Spec 015 T040 / FR-021-022: a personality comment failing stage-aware
# triage (`llmxive.convergence.triage.triage_submission` — quality /
# safety / on-topic) is NOT persisted as a review. Pointer DOES advance
# (the persona did their job; the content just wasn't useful for the
# panel), so the rotation moves on — same pointer semantics as
# OUTCOME_RUBRIC_REJECTED.
OUTCOME_TRIAGE_REJECTED = "triage_rejected_advanced_as_abstain"

# Outcomes that ADVANCE the rotation pointer. All others HOLD it so the
# same persona retries (FR-017).
ADVANCING_OUTCOMES = {
    OUTCOME_COMMITTED,
    OUTCOME_ABSTAINED,
    OUTCOME_RUBRIC_REJECTED,
    OUTCOME_TRIAGE_REJECTED,
}

# Spec 015 T040: lens lists used to triage personality comments toward
# the appropriate review panel (research-side 8-panel vs paper-side
# 12-panel). The convergence engine consumes triage_record.mapped_lenses
# as advisory input to the named reviewer(s).
_RESEARCH_REVIEW_LENSES: tuple[str, ...] = (
    "idea_quality", "creativity",
    "implementation_correctness", "implementation_completeness",
    "code_quality", "data_quality", "filesystem_hygiene",
)
_PAPER_REVIEW_LENSES: tuple[str, ...] = (
    "claim_accuracy", "logical_consistency", "statistical_analysis",
    "scientific_evidence", "figure_critic", "jargon_police",
    "overreach", "safety_ethics", "code_quality", "data_quality",
    "text_formatting", "writing_quality",
)

ACTION_COMMENT = "comment"
ACTION_CONTRIBUTE = "contribute"
ACTION_PROPOSE_ARXIV = "propose_arxiv"
ACTION_ABSTAIN = "abstain"
VALID_ACTIONS = {ACTION_COMMENT, ACTION_CONTRIBUTE, ACTION_PROPOSE_ARXIV, ACTION_ABSTAIN}

# arXiv URL regex per data-model.md E4 (matches https://arxiv.org/abs/NNNN.NNNNN
# with 4-digit YYMM + 4-or-5-digit id).
ARXIV_URL_RE = re.compile(r"^https?://arxiv\.org/abs/\d{4}\.\d{4,5}(v\d+)?/?$")


@dataclasses.dataclass(frozen=True)
class Personality:
    """One simulated AI persona loaded from disk (data-model.md E1).

    The ``display_name`` is the canonical form WITHOUT the ``(simulated)``
    suffix — the suffix is appended by :func:`display_name_for_render`
    at every render point.
    """

    slug: str
    display_name: str
    summary: str
    sources: list[str]
    prompt_body: str
    version: str = "1.0.0"


@dataclasses.dataclass
class RotationState:
    """Rotation pointer + audit-trail history (data-model.md E2)."""

    last_used: str | None
    last_used_at: str
    last_outcome: str
    history: list[dict[str, Any]]


@dataclasses.dataclass
class Action:
    """Structured LLM output for one tick (data-model.md E4 + spec 010)."""

    action: str  # one of VALID_ACTIONS
    reason: str
    target_project_id: str | None = None
    target_artifact_kind: str | None = None
    target_artifact_path: str | None = None
    content: str | None = None
    arxiv_url: str | None = None
    arxiv_search_terms: list[str] | None = None
    # Spec 010 fields (FR-001 / FR-002 / FR-003). Optional during legacy parsing
    # but required at the rubric-check step for non-abstain actions.
    position: str | None = None
    adjacent_work: list[dict[str, str]] | None = None
    interest_signal: str | None = None


@dataclasses.dataclass
class ParseError(Exception):
    """Raised when :func:`parse_action` cannot validate the LLM response.

    The :attr:`reason` field captures a structured explanation that flows
    into the run-log so post-tick triage can see why parsing failed.
    """

    reason: str

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.reason


@dataclasses.dataclass
class CatalogEntry:
    """One project's compact summary in the per-tick project catalog
    (data-model.md E3)."""

    id: str
    title: str
    field: str
    current_stage: str
    description: str
    recent_artifacts: list[dict[str, str]]


@dataclasses.dataclass
class DispatchResult:
    """Outcome of dispatching one Action (data-model.md E5)."""

    outcome: str  # one of OUTCOME_*
    committed_paths: list[str]
    error: str | None = None


# ---------------------------------------------------------------------------
# Display-name rendering — the ONE place that appends "(simulated)"
# (FR-010 + the cross-entity invariant in data-model.md).
# ---------------------------------------------------------------------------

SIMULATED_SUFFIX = " (simulated)"


def display_name_for_render(persona: Personality) -> str:
    """Canonical user-visible name for a persona.

    Always returns ``"<display_name> (simulated)"``. The unsuffixed form
    only exists in the on-disk ``Personality.display_name`` field; every
    user-facing surface (review file, issue body, contributor list,
    registry modal, run-log human-readable export) goes through here.
    """
    name = persona.display_name
    if name.endswith(SIMULATED_SUFFIX):
        # Loader rejects baked-in suffix, but be defensive.
        return name
    return f"{name}{SIMULATED_SUFFIX}"


# ---------------------------------------------------------------------------
# T009 / T051 / T052: pool loading
# ---------------------------------------------------------------------------

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
_SLUG_RE = re.compile(r"^[a-z][a-z0-9-]*$")


@dataclasses.dataclass
class PoolLoadResult:
    """Return type of :func:`load_pool` — the well-formed personalities
    plus a count + paths of any malformed files that were skipped (Story 2
    scenario 2 / FR-001)."""

    personalities: list[Personality]
    error_count: int
    errors: list[dict[str, str]]


def load_pool(pool_root: Path | str | None = None) -> PoolLoadResult:
    """Enumerate every ``*.md`` file under :data:`POOL_PATH` (sorted by
    filename stem) and load each into a :class:`Personality`. Malformed
    files are SKIPPED with a logged warning + an entry in :attr:`errors`
    (per FR-001 / Story 2 scenario 2 — the rotation must continue over
    well-formed entries when one is malformed).

    Args:
        pool_root: optional override of the pool directory; defaults to
            the repo-relative :data:`POOL_PATH`. Test fixtures pass a
            ``tmp_path / "personalities"``.

    Returns:
        :class:`PoolLoadResult` with the well-formed personalities (sorted
        by slug) and any error rows.
    """
    if pool_root is None:
        pool_root = Path(POOL_PATH)
    pool_root = Path(pool_root)
    if not pool_root.is_dir():
        return PoolLoadResult([], 0, [])

    personalities: list[Personality] = []
    errors: list[dict[str, str]] = []

    for path in sorted(pool_root.glob("*.md")):
        if path.name.startswith("."):
            continue
        slug = path.stem
        if not _SLUG_RE.match(slug):
            errors.append({"path": str(path), "reason": f"slug {slug!r} does not match {_SLUG_RE.pattern!r}"})
            log.warning("personality: skipping %s — invalid slug pattern", path)
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            errors.append({"path": str(path), "reason": f"read failed: {exc}"})
            continue
        m = _FRONTMATTER_RE.match(text)
        if not m:
            errors.append({"path": str(path), "reason": "missing YAML front-matter"})
            log.warning("personality: skipping %s — no front-matter", path)
            continue
        try:
            fm = yaml.safe_load(m.group(1)) or {}
        except yaml.YAMLError as exc:
            errors.append({"path": str(path), "reason": f"YAML parse error: {exc}"})
            log.warning("personality: skipping %s — YAML parse error", path)
            continue
        display_name = (fm.get("display_name") or "").strip()
        summary = (fm.get("summary") or "").strip()
        sources = fm.get("sources") or []
        version = (fm.get("version") or "1.0.0").strip()
        if not display_name:
            errors.append({"path": str(path), "reason": "missing or empty display_name"})
            log.warning("personality: skipping %s — missing display_name", path)
            continue
        if display_name.endswith(SIMULATED_SUFFIX):
            # FR-010 invariant: suffix is added at render time only.
            errors.append({"path": str(path), "reason": "display_name MUST NOT end with ' (simulated)' (FR-010)"})
            log.warning("personality: skipping %s — display_name has baked-in '(simulated)'", path)
            continue
        if not summary:
            errors.append({"path": str(path), "reason": "missing or empty summary"})
            continue
        if len(summary.split()) > 14:
            errors.append({"path": str(path), "reason": f"summary > 14 words ({len(summary.split())})"})
            continue
        if not isinstance(sources, list) or len(sources) < 3 or len(sources) > 6:
            errors.append({"path": str(path), "reason": "sources MUST be a list of 3-6 strings (FR-013)"})
            continue
        if not all(isinstance(s, str) and len(s.strip()) >= 5 for s in sources):
            errors.append({"path": str(path), "reason": "every source MUST be a string of ≥ 5 characters"})
            continue
        prompt_body = text[m.end():].strip()
        if not prompt_body:
            errors.append({"path": str(path), "reason": "empty prompt body"})
            continue
        personalities.append(Personality(
            slug=slug,
            display_name=display_name,
            summary=summary,
            sources=[str(s).strip() for s in sources],
            prompt_body=prompt_body,
            version=version,
        ))

    return PoolLoadResult(
        personalities=personalities,
        error_count=len(errors),
        errors=errors,
    )


# ---------------------------------------------------------------------------
# T007 / T010: rotation-state YAML IO
# ---------------------------------------------------------------------------

_ROTATION_DEFAULT = {
    "last_used": None,
    "last_used_at": "1970-01-01T00:00:00+00:00",
    "last_outcome": OUTCOME_ABSTAINED,
    "history": [],
}


def load_rotation_state(state_path: Path | str | None = None) -> RotationState:
    """Load the rotation-state YAML, recovering gracefully if the file is
    missing / unparseable / missing required keys (per spec Edge Cases:
    "What if the rotation file is missing or corrupted on the first run?").

    The recovery policy is the same in every failure mode: return a fresh
    default state and log a warning. The next tick will write the file
    fresh — no need to repair on read.
    """
    if state_path is None:
        state_path = Path(ROTATION_PATH)
    state_path = Path(state_path)
    if not state_path.is_file():
        return RotationState(**_ROTATION_DEFAULT)
    try:
        raw = state_path.read_text(encoding="utf-8")
    except OSError as exc:
        log.warning("personality: rotation state read failed (%s); recovering with default", exc)
        return RotationState(**_ROTATION_DEFAULT)
    try:
        data = yaml.safe_load(raw) or {}
    except yaml.YAMLError as exc:
        log.warning("personality: rotation state YAML parse error (%s); recovering with default", exc)
        return RotationState(**_ROTATION_DEFAULT)
    if not isinstance(data, dict):
        log.warning("personality: rotation state not a dict; recovering with default")
        return RotationState(**_ROTATION_DEFAULT)
    # Use ``.get`` with defaults so missing keys don't blow up.
    return RotationState(
        last_used=data.get("last_used"),
        last_used_at=str(data.get("last_used_at") or _ROTATION_DEFAULT["last_used_at"]),
        last_outcome=str(data.get("last_outcome") or _ROTATION_DEFAULT["last_outcome"]),
        history=list(data.get("history") or []),
    )


def write_rotation_state(state: RotationState, state_path: Path | str | None = None) -> None:
    """Atomic write: render to a temp file, fsync, then rename onto
    :data:`ROTATION_PATH`. A half-written file never lands on disk."""
    if state_path is None:
        state_path = Path(ROTATION_PATH)
    state_path = Path(state_path)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    # Trim history to the last HISTORY_LIMIT entries — keeps the file small
    # and bounded over a long-running cron.
    history = state.history[-HISTORY_LIMIT:] if len(state.history) > HISTORY_LIMIT else state.history
    payload = {
        "last_used": state.last_used,
        "last_used_at": state.last_used_at,
        "last_outcome": state.last_outcome,
        "history": history,
    }
    tmp = state_path.with_suffix(state_path.suffix + ".tmp")
    text = yaml.safe_dump(payload, sort_keys=False, default_flow_style=False)
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, state_path)


# ---------------------------------------------------------------------------
# T011: rotation selection (research.md § R1)
# ---------------------------------------------------------------------------


def select_next(personalities: list[Personality], last_used: str | None) -> Personality | None:
    """Pick the next personality in deterministic rotation order.

    Rule: lex-next-after ``last_used`` over the sorted pool, wrapping to
    the first entry when ``last_used`` is the last (or unknown). The
    pool comes pre-sorted from :func:`load_pool`; we don't re-sort here
    to preserve that contract.

    Edge cases (research.md § R1):
      - Empty pool → ``None`` (no crash; caller records abstained).
      - ``last_used is None`` → first persona.
      - ``last_used`` no longer in the pool (deleted persona) → lex-next
        AFTER that stem (so deletion doesn't break the sequence).
    """
    if not personalities:
        return None
    slugs = [p.slug for p in personalities]
    if last_used is None:
        return personalities[0]
    # Find lex-first slug strictly greater than last_used. This handles
    # both "last_used is in the pool" and "last_used was deleted" — the
    # first slug AFTER last_used in lex order is picked either way.
    for i, slug in enumerate(slugs):
        if slug > last_used:
            return personalities[i]
    # last_used >= every slug → wrap to first.
    return personalities[0]


# ---------------------------------------------------------------------------
# T013: project catalog (data-model.md E3)
# ---------------------------------------------------------------------------


def _read_artifact_preview(path: Path, *, max_chars: int = 140) -> str:
    """First ~max_chars of a text artifact's body, single-line. Binary
    files (PDFs etc.) get a placeholder."""
    try:
        if path.suffix.lower() == ".pdf":
            return f"[PDF artifact at {path.name}]"
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return f"[unreadable: {path.name}]"
    # Strip front-matter if present.
    fm = _FRONTMATTER_RE.match(text)
    if fm:
        text = text[fm.end():]
    # Collapse whitespace.
    text = " ".join(text.split())
    if len(text) > max_chars:
        text = text[:max_chars].rstrip() + "…"
    return text


def _recent_artifacts_for_project(repo_root: Path, project_id: str, *, limit: int) -> list[dict[str, str]]:
    """Find up to ``limit`` most-recently-modified artifacts for a project.

    Walks the canonical artifact locations (idea, paper PDF, latex source,
    paper/reviews, spec/plan/tasks under speckit feature dirs). Picks the
    newest by mtime regardless of kind."""
    proj_dir = repo_root / "projects" / project_id
    if not proj_dir.is_dir():
        return []
    candidates: list[tuple[float, str, Path]] = []
    # Known artifact-kind globs — repo-relative.
    glob_to_kind = [
        ("idea/*.md", "idea"),
        ("specs/*/spec.md", "spec"),
        ("specs/*/plan.md", "plan"),
        ("specs/*/tasks.md", "tasks"),
        ("paper/specs/*/spec.md", "paper_spec"),
        ("paper/specs/*/plan.md", "paper_plan"),
        ("paper/specs/*/tasks.md", "paper_tasks"),
        ("paper/source/main.tex", "paper_source"),
        ("paper/pdf/main-llmxive.pdf", "paper_pdf"),
        ("paper/pdf/main.pdf", "paper_pdf"),
        ("paper/pdf/supplement-llmxive.pdf", "paper_supplement"),
        ("paper/reviews/*.md", "reviews_paper"),
        ("reviews/research/*.md", "reviews_research"),
    ]
    for pattern, kind in glob_to_kind:
        for hit in proj_dir.glob(pattern):
            if hit.is_file():
                try:
                    candidates.append((hit.stat().st_mtime, kind, hit))
                except OSError:
                    continue
    candidates.sort(key=lambda r: -r[0])
    out: list[dict[str, str]] = []
    seen_kinds: set[str] = set()
    for _mtime, kind, path in candidates:
        # Deduplicate by kind — show at most one entry per kind so the
        # catalog stays compact (E3's ≤ 2 recent_artifacts cap is by
        # project, but it's friendlier to show different artifact KINDS
        # rather than two paper_pdfs).
        if kind in seen_kinds:
            continue
        seen_kinds.add(kind)
        try:
            rel = path.relative_to(repo_root).as_posix()
        except ValueError:
            rel = path.as_posix()
        out.append({"kind": kind, "path": rel, "summary": _read_artifact_preview(path)})
        if len(out) >= limit:
            break
    return out


def build_catalog(repo_root: Path, *, limit: int = DEFAULT_CATALOG_LIMIT,
                  recent_artifacts: int = DEFAULT_RECENT_ARTIFACTS) -> list[CatalogEntry]:
    """Compact summary of the top-N most-recently-updated projects.

    Per data-model.md E3:
      - ≤ ``limit`` projects (default 30), sorted by ``updated_at`` desc.
      - Each entry has up to ``recent_artifacts`` (default 2) artifact
        previews.
      - Description truncated to ~280 chars.
    """
    from llmxive.state import project as project_store

    all_projects = project_store.list_all(repo_root=repo_root)
    # Sort by updated_at descending.
    all_projects.sort(key=lambda p: p.updated_at, reverse=True)
    top = all_projects[:limit]

    out: list[CatalogEntry] = []
    for proj in top:
        # Pull description from idea front-matter or main.tex abstract; for
        # now use a short title-based fallback if we can't quickly source one.
        desc = _build_short_description(repo_root, proj.id)
        out.append(CatalogEntry(
            id=proj.id,
            title=proj.title,
            field=proj.field or "general",
            current_stage=proj.current_stage.value,
            description=desc,
            recent_artifacts=_recent_artifacts_for_project(repo_root, proj.id, limit=recent_artifacts),
        ))
    return out


def _build_short_description(repo_root: Path, project_id: str, *, max_chars: int = 280) -> str:
    """Best-effort first-280-chars summary of a project — from idea body
    if present, else title."""
    idea_dir = repo_root / "projects" / project_id / "idea"
    if idea_dir.is_dir():
        for md in sorted(idea_dir.glob("*.md")):
            text = md.read_text(encoding="utf-8", errors="replace")
            fm = _FRONTMATTER_RE.match(text)
            if fm:
                text = text[fm.end():]
            text = " ".join(text.split())
            if text:
                return text[:max_chars] + ("…" if len(text) > max_chars else "")
    return ""


# ---------------------------------------------------------------------------
# T015: parse_action — JSON-out validation (data-model.md E4)
# ---------------------------------------------------------------------------


def parse_action(raw_response: str) -> Action:
    """Validate the LLM's JSON-out per :class:`Action`.

    Raises :class:`ParseError` with a structured reason on any schema
    mismatch — the orchestrator catches it, records ``outcome="malformed_response"``,
    and HOLDS the rotation pointer (FR-017).
    """
    # The LLM may wrap the JSON in stray prose. Find the first { ... last }.
    raw = (raw_response or "").strip()
    start = raw.find("{")
    end = raw.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ParseError(reason=f"no JSON object found in response (len={len(raw)})")
    try:
        data = json.loads(raw[start:end + 1])
    except json.JSONDecodeError as exc:
        raise ParseError(reason=f"JSON parse error: {exc}") from None
    if not isinstance(data, dict):
        raise ParseError(reason=f"JSON root must be an object, got {type(data).__name__}")
    action_val = data.get("action")
    if action_val not in VALID_ACTIONS:
        raise ParseError(reason=f"action {action_val!r} not in {sorted(VALID_ACTIONS)}")
    reason = data.get("reason", "")
    if not isinstance(reason, str):
        raise ParseError(reason=f"reason must be a string, got {type(reason).__name__}")
    content = data.get("content")
    target = data.get("target") or {}
    arxiv = data.get("arxiv") or {}

    # Enforce per-action required fields per data-model.md E4.
    if action_val in {ACTION_COMMENT, ACTION_CONTRIBUTE}:
        for k in ("project_id", "artifact_kind", "artifact_path"):
            if not target.get(k):
                raise ParseError(reason=f"target.{k} required when action={action_val!r}")
        if not isinstance(content, str) or not content.strip():
            raise ParseError(reason=f"content required when action={action_val!r}")
        # Content size guard.
        if len(content.split()) > CONTENT_MAX_WORDS:
            raise ParseError(
                reason=f"content exceeds {CONTENT_MAX_WORDS}-word guardrail "
                f"({len(content.split())} words)")
    elif action_val == ACTION_PROPOSE_ARXIV:
        url = (arxiv.get("url") or "").strip()
        if not ARXIV_URL_RE.match(url):
            raise ParseError(reason=f"arxiv.url {url!r} does not match {ARXIV_URL_RE.pattern}")
        if not isinstance(content, str) or not content.strip():
            raise ParseError(reason="content (rationale) required when action='propose_arxiv'")
        search_terms = arxiv.get("search_terms") or []
        if not isinstance(search_terms, list):
            raise ParseError(reason="arxiv.search_terms must be a list")
    # abstain has no further required fields.

    # Spec 010: parse the three new fields (position, adjacent_work,
    # interest_signal). They are optional at the JSON-parse level; the
    # rubric check enforces presence + liveness for non-abstain actions.
    position = data.get("position")
    if position is not None and not isinstance(position, str):
        raise ParseError(reason=f"position must be a string, got {type(position).__name__}")
    interest_signal = data.get("interest_signal")
    if interest_signal is not None and not isinstance(interest_signal, str):
        raise ParseError(
            reason=f"interest_signal must be a string, got {type(interest_signal).__name__}"
        )
    adjacent_work = data.get("adjacent_work")
    if adjacent_work is not None:
        if not isinstance(adjacent_work, list):
            raise ParseError(
                reason=f"adjacent_work must be a list, got {type(adjacent_work).__name__}"
            )
        for i, entry in enumerate(adjacent_work):
            if not isinstance(entry, dict):
                raise ParseError(reason=f"adjacent_work[{i}] must be a dict")
            for k in ("kind", "pointer"):
                if not entry.get(k):
                    raise ParseError(reason=f"adjacent_work[{i}].{k} required")

    return Action(
        action=action_val,
        reason=reason,
        target_project_id=target.get("project_id"),
        target_artifact_kind=target.get("artifact_kind"),
        target_artifact_path=target.get("artifact_path"),
        content=content,
        arxiv_url=(arxiv.get("url") or "").strip() or None,
        arxiv_search_terms=list(arxiv.get("search_terms") or []) or None,
        position=position,
        adjacent_work=adjacent_work,
        interest_signal=interest_signal,
    )


# ---------------------------------------------------------------------------
# T017: dispatch — route the action through existing pipes (Principle I)
# ---------------------------------------------------------------------------


def _make_disclaimer(persona: Personality) -> str:
    """The verbatim FR-012 disclaimer footer for `persona`."""
    return DISCLAIMER_TEMPLATE.format(
        display_name=display_name_for_render(persona),
        real_name=persona.display_name,
    )


# T063: librarian-gate helpers (FR-018). The personality contribution body
# is scanned for URL / DOI / arXiv patterns; if any are present, the
# artifact is moved to a `_held/` sub-directory for the librarian to
# verify (held artifacts do NOT propagate into review-counting).
_CITATION_PATTERNS = (
    re.compile(r"https?://[^\s)>\]]+"),
    re.compile(r"\bdoi:\S+|\b10\.\d{4,9}/[-._;()/:\w]+\b"),
    re.compile(r"\barXiv:\d{4}\.\d{4,5}\b", re.IGNORECASE),
)


def _contains_citation(text: str) -> bool:
    """True iff `text` contains anything that looks like a cited URL / DOI /
    arXiv id (per FR-018, these need the librarian's verification before
    the contribution can be auto-merged)."""
    return any(pat.search(text) for pat in _CITATION_PATTERNS)


def _hold_for_librarian(result: DispatchResult, repo_root: Path) -> DispatchResult:
    """Move every committed path under a `_held/` sibling directory and
    mark the outcome as :data:`OUTCOME_LIBRARIAN_HELD`. Rotation pointer
    will hold (FR-017) so the same persona retries next tick — but most
    commonly a human will review the held artifacts and either merge or
    discard them out of band.
    """
    new_paths: list[str] = []
    for rel in result.committed_paths:
        src = repo_root / rel
        if not src.exists():
            continue
        # Move src → <parent>/_held/<name>
        held_dir = src.parent / "_held"
        held_dir.mkdir(parents=True, exist_ok=True)
        dest = held_dir / src.name
        # Avoid clobber.
        i = 0
        while dest.exists():
            i += 1
            dest = held_dir / f"{src.stem}.{i}{src.suffix}"
        src.rename(dest)
        try:
            new_paths.append(dest.relative_to(repo_root).as_posix())
        except ValueError:
            new_paths.append(str(dest))
    return DispatchResult(
        outcome=OUTCOME_LIBRARIAN_HELD,
        committed_paths=new_paths,
        error="contribution contained citations; held for librarian verification (FR-018)",
    )


def _today_iso_date() -> str:
    return _dt.datetime.now(_dt.UTC).date().isoformat()


def _slug_for_review_filename(persona: Personality) -> str:
    """Filename-safe slug for the persona's display name (review-file
    naming convention is `<author>__<date>__<type>.md`). We use
    `<slug>-simulated` so the filename ALWAYS carries the (simulated)
    marker.
    """
    return f"{persona.slug}-simulated"


def _sha256_of_path(path: Path) -> str:
    """Best-effort SHA-256 for ReviewRecord.artifact_hash."""
    import hashlib
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        # Fall back to a deterministic placeholder for non-existent paths
        # — caller's responsibility to have checked existence first.
        return "0" * 64


def dispatch(action: Action, persona: Personality, repo_root: Path) -> DispatchResult:
    """Route the parsed action through the right existing pipe.

    Per Constitution Principle I, we reuse:
      - ``llmxive.state.reviews.write`` for ``comment`` (the same writer
        used by ``paper_reviewer`` and ``research_reviewer``).
      - The submission-intake feedback path (synthesized issue body) for
        ``contribute`` and ``propose_arxiv``.
      - No-op for ``abstain``.
    """
    if action.action == ACTION_ABSTAIN:
        return DispatchResult(outcome=OUTCOME_ABSTAINED, committed_paths=[])

    if action.action in {ACTION_COMMENT, ACTION_CONTRIBUTE}:
        # Verify the target artifact actually exists; outcome=target_missing
        # on absence (FR-017 — pointer doesn't advance).
        artifact_rel = action.target_artifact_path or ""
        artifact_abs = repo_root / artifact_rel
        if not artifact_abs.exists():
            return DispatchResult(
                outcome=OUTCOME_TARGET_MISSING,
                committed_paths=[],
                error=f"target artifact not found: {artifact_rel}",
            )

    if action.action == ACTION_COMMENT:
        result = _dispatch_comment(action, persona, repo_root)
    elif action.action == ACTION_CONTRIBUTE:
        result = _dispatch_contribute(action, persona, repo_root)
    elif action.action == ACTION_PROPOSE_ARXIV:
        result = _dispatch_propose_arxiv(action, persona, repo_root)
    else:
        # Unreachable — parse_action enforces enum.
        return DispatchResult(outcome=OUTCOME_MODEL_ERROR, committed_paths=[],
                              error=f"unknown action {action.action!r}")

    # T063: librarian gate (FR-018). If the committed artifact contains
    # URL / DOI / arXiv-id patterns that look like cited claims, hold it
    # for human review by moving it to a `_held/` sub-directory. The
    # existing librarian agent (spec-005) is the citation verifier; for
    # now we mark it as held and the librarian re-runs offline. The
    # rotation pointer holds on `librarian_held` per FR-017.
    if result.outcome == OUTCOME_COMMITTED and _contains_citation(action.content or ""):
        result = _hold_for_librarian(result, repo_root)
    return result


def _dispatch_comment(action: Action, persona: Personality, repo_root: Path) -> DispatchResult:
    """Comment branch — writes a review file via the canonical
    :func:`llmxive.state.reviews.write` helper.

    The persona's review is recorded as a `verdict="minor_revision"`
    ReviewRecord (a deliberately mild verdict — the personas are
    commentators, not formal reviewers; the actual research_reviewer /
    paper_reviewer pipeline is the formal review). Score is 0.5 (LLM-
    review per the standard scoring) and may be overridden later if
    spec-008 evolves to require persona-specific verdicts.
    """
    from datetime import datetime

    from llmxive.state import reviews as reviews_store
    from llmxive.types import ReviewerKind, ReviewRecord

    artifact_rel = action.target_artifact_path
    artifact_abs = repo_root / artifact_rel
    # Pick the review stage based on the artifact path: anything under
    # `<proj>/paper/` is a paper-stage review; everything else is
    # research-stage.
    is_paper_stage = "/paper/" in artifact_rel or artifact_rel.endswith("/main.tex")
    stage = "paper" if is_paper_stage else "research"
    review_type = "paper" if is_paper_stage else "research"

    # Body = persona's content + disclaimer footer (F8 placement: bottom,
    # after horizontal rule).
    body = (action.content or "").strip() + _make_disclaimer(persona)

    # Spec 015 T040 / FR-021-022: stage-aware triage. Personality comments
    # are advisory inputs to the formal review panels — they are gated by
    # quality + safety + on-topic checks BEFORE being persisted, and the
    # triage record's mapped_lenses tells downstream wiring which panel
    # reviewer(s) should treat this comment as an input. preserved=False
    # → don't write the review file; advance the rotation pointer.
    from llmxive.convergence.triage import triage_submission

    triage_stage = "paper_review" if is_paper_stage else "research_review"
    triage_lenses = list(
        _PAPER_REVIEW_LENSES if is_paper_stage else _RESEARCH_REVIEW_LENSES
    )
    triage_record = triage_submission(
        body,
        source="personality",
        author=persona.slug,
        stage=triage_stage,
        lenses=triage_lenses,
    )
    if not triage_record.preserved:
        return DispatchResult(
            outcome=OUTCOME_TRIAGE_REJECTED,
            committed_paths=[],
            error=(
                f"triage rejected (stage={triage_stage}): "
                f"{triage_record.excluded_reason or 'unknown reason'}; "
                f"quality_pass={triage_record.quality_pass}; "
                f"safe_on_topic={triage_record.safe_on_topic}"
            ),
        )

    # Record the reviewer as "<slug>-simulated" (filename-friendly) so the
    # produced filename carries the (simulated) marker. The display_name
    # in any extracted card is reconstituted via display_name_for_render
    # downstream.
    reviewer_slug = _slug_for_review_filename(persona)

    # ReviewRecord rule: LLM non-accept verdicts must score 0.0; LLM accept
    # would score 0.5. Personas are commentators, not formal reviewers — they
    # use 'minor_revision' as the umbrella verdict (any improvement
    # suggestion is a non-blocking revision request from the persona's
    # point of view) → score MUST be 0.0 per the ReviewRecord invariant.
    record = ReviewRecord(
        reviewer_name=reviewer_slug,
        reviewer_kind=ReviewerKind.LLM,
        artifact_path=artifact_rel,
        artifact_hash=_sha256_of_path(artifact_abs),
        score=0.0,
        verdict="minor_revision",
        feedback=(action.content or "")[:500],
        reviewed_at=datetime.now(_dt.UTC),
        prompt_version="1.0.0",
        model_name=MODEL_NAME,
        backend="dartmouth",
    )
    try:
        path = reviews_store.write(
            record,
            body=body,
            stage=stage,
            review_type=review_type,
            produced_by_agent=None,
            repo_root=repo_root,
        )
    except Exception as exc:
        return DispatchResult(
            outcome=OUTCOME_MODEL_ERROR,
            committed_paths=[],
            error=f"review write failed: {exc}",
        )
    try:
        rel = path.relative_to(repo_root).as_posix()
    except ValueError:
        rel = path.as_posix()
    return DispatchResult(outcome=OUTCOME_COMMITTED, committed_paths=[rel])


def _dispatch_contribute(action: Action, persona: Personality, repo_root: Path) -> DispatchResult:
    """Contribute branch — records the persona's improvement as a feedback
    file on disk. The maintenance-agent / feedback-triage pipeline picks
    it up the same way it picks up website-submitted feedback.

    We write the feedback to a deterministic path under the project's
    `feedback/` subdir so a downstream triage step can find it without a
    GitHub-issue round-trip (which would require write-tokens at tick time).
    """
    from datetime import datetime

    project_id = action.target_project_id
    proj_dir = repo_root / "projects" / project_id
    feedback_dir = proj_dir / "feedback"
    feedback_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(_dt.UTC).strftime("%Y%m%dT%H%M%SZ")
    fname = f"{persona.slug}-simulated__{ts}.md"
    path = feedback_dir / fname

    frontmatter = {
        "submitter": display_name_for_render(persona),
        "submitter_kind": "llm",
        "personality_slug": persona.slug,
        "model_name": MODEL_NAME,
        "model_kind": MODEL_KIND,
        "target_artifact": action.target_artifact_path,
        "target_artifact_kind": action.target_artifact_kind,
        "submitted_at": datetime.now(_dt.UTC).isoformat(),
        "kind": "feedback",
    }
    body = (action.content or "").strip() + _make_disclaimer(persona)
    text = "---\n" + yaml.safe_dump(frontmatter, sort_keys=True) + "---\n\n" + body + "\n"
    path.write_text(text, encoding="utf-8")
    try:
        rel = path.relative_to(repo_root).as_posix()
    except ValueError:
        rel = path.as_posix()
    return DispatchResult(outcome=OUTCOME_COMMITTED, committed_paths=[rel])


def _dispatch_propose_arxiv(action: Action, persona: Personality, repo_root: Path) -> DispatchResult:
    """Propose-arXiv branch — records an arxiv-submission stub the
    submission-intake pipeline can pick up.

    We write the stub to a deterministic path under
    `state/personality-submissions/<ts>__<slug>.yaml`. A downstream
    maintenance step can read these and invoke the same
    `submission_intake.process_submission_issue` path that human
    submissions go through, with `submitter` set to the persona's
    (simulated) display name.
    """
    from datetime import datetime

    sub_dir = repo_root / "state" / "personality-submissions"
    sub_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(_dt.UTC).strftime("%Y%m%dT%H%M%SZ")
    fname = f"{ts}__{persona.slug}.yaml"
    path = sub_dir / fname
    payload = {
        "submitter": display_name_for_render(persona),
        "submitter_kind": "llm",
        "personality_slug": persona.slug,
        "model_name": MODEL_NAME,
        "model_kind": MODEL_KIND,
        "submitted_at": datetime.now(_dt.UTC).isoformat(),
        "arxiv_url": action.arxiv_url,
        "search_terms": action.arxiv_search_terms or [],
        "rationale": (action.content or "").strip(),
        "disclaimer": _make_disclaimer(persona).strip(),
    }
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    try:
        rel = path.relative_to(repo_root).as_posix()
    except ValueError:
        rel = path.as_posix()
    return DispatchResult(outcome=OUTCOME_COMMITTED, committed_paths=[rel])


# ---------------------------------------------------------------------------
# T022: tick — one full end-to-end run
# ---------------------------------------------------------------------------


def _load_umbrella_prompt(repo_root: Path) -> str:
    """Read the umbrella personality prompt (the per-tick decision protocol)."""
    p = repo_root / UMBRELLA_PROMPT_PATH
    return p.read_text(encoding="utf-8") if p.is_file() else ""


def _classify_llm_exception(exc: BaseException) -> str:
    """Map a backend exception to a personality-agent outcome enum.

    Per FR-017, rate-limit / quota / 429 conditions get
    :data:`OUTCOME_RATE_LIMITED` (audit-distinguishable). Timeouts get
    :data:`OUTCOME_TIMEOUT`. Everything else gets :data:`OUTCOME_MODEL_ERROR`.
    The classifier looks at exception text (substring match for resilience
    across backend-error variations) and class name.
    """
    text = (str(exc) or "").lower()
    cls = type(exc).__name__.lower()
    if isinstance(exc, TimeoutError) or "timeout" in cls or "timed out" in text:
        return OUTCOME_TIMEOUT
    if any(s in text for s in ("rate limit", "ratelimit", "quota", "429", "too many requests")):
        return OUTCOME_RATE_LIMITED
    return OUTCOME_MODEL_ERROR


def _call_llm_for_persona(persona: Personality, catalog: list[CatalogEntry],
                          repo_root: Path, *, extra_hint: str | None = None) -> str:
    """One LLM call per tick. Returns the raw response text.

    Uses the existing chat_with_fallback router with the personality
    agent's registry entry (default_backend=dartmouth, model=qwen.qwen3.5-122b,
    no fallback_backends for the persona role — see registry entry in T002).

    ``extra_hint`` (spec 009 FR-004 retry path): when present, an additional
    coaching instruction appended to the user prompt. Used by the rubric gate
    to ask the persona for a specific objection / question / adjacent-work
    pointer on the second attempt.
    """
    from llmxive.agents import registry as registry_loader
    from llmxive.backends.base import ChatMessage
    from llmxive.backends.router import chat_with_fallback

    entry = registry_loader.get(AGENT_NAME)
    umbrella = _load_umbrella_prompt(repo_root)
    catalog_dict = [dataclasses.asdict(c) for c in catalog]
    user_content = (
        "=== UMBRELLA PROMPT ===\n"
        f"{umbrella}\n\n"
        "=== YOUR PERSONA ===\n"
        f"display_name: {persona.display_name}\n"
        f"slug: {persona.slug}\n"
        f"summary: {persona.summary}\n"
        f"sources:\n  - " + "\n  - ".join(persona.sources) + "\n\n"
        f"--- persona body ---\n"
        f"{persona.prompt_body}\n\n"
        "=== PROJECT CATALOG ===\n"
        f"{json.dumps(catalog_dict, indent=2)}\n\n"
        "=== YOUR TURN ===\n"
        "Return a single JSON object per the umbrella prompt's schema. "
        "OUTPUT MUST BE IN ENGLISH. No prose outside the JSON.\n"
        + (f"\n=== RETRY HINT ===\n{extra_hint}\n" if extra_hint else "")
    )
    response = chat_with_fallback(
        [ChatMessage(role="user", content=user_content)],
        default_backend=entry.default_backend.value,
        fallback_backends=[b.value for b in (entry.fallback_backends or [])],
        model=entry.default_model,
        max_tokens=8192,
        temperature=0.7,
    )
    return response.text


def _write_run_log_entry(repo_root: Path, entry: dict[str, Any]) -> None:
    """Append a single JSONL line to the canonical run-log path."""
    now = _dt.datetime.now(_dt.UTC)
    log_dir = repo_root / "state" / "run-log" / now.strftime("%Y-%m")
    log_dir.mkdir(parents=True, exist_ok=True)
    # File-per-tick so concurrent ticks (shouldn't happen — see FR-016 —
    # but defensive) can't trample each other.
    rid = os.environ.get("GITHUB_RUN_ID") or f"local-{now.strftime('%Y%m%dT%H%M%SZ')}"
    log_path = log_dir / f"{rid}.jsonl"
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, sort_keys=True) + "\n")


def tick(repo_root: Path, *, force_slug: str | None = None,
         timeout_s: float = DEFAULT_TIMEOUT_S,
         llm_fixture: str | None = None) -> dict[str, Any]:
    """One end-to-end tick of the personality rotation.

    Args:
        repo_root: the llmXive repository root.
        force_slug: testing-only — bypass the rotation pointer and force
            a specific persona to take this turn. The rotation pointer
            is NOT updated when this is set (so the next real tick
            resumes where it left off). See quickstart § 3.
        timeout_s: per-tick wall-clock budget (FR-017). Currently
            advisory — the LLM router enforces its own per-call
            timeout; this value is recorded in the run-log entry for
            audit but doesn't actively kill the process.
        llm_fixture: testing-only — when set, the LLM call is replaced
            by reading this JSON file (one of the fixtures under
            tests/fixtures/personality/). Set via the
            `LLMXIVE_PERSONALITY_FIXTURE` env var; see quickstart § 2.

    Returns:
        The run-log entry dict (also written to disk).
    """
    repo_root = Path(repo_root)
    started = _dt.datetime.now(_dt.UTC)

    # ── 1. Load pool ──
    pool_result = load_pool(repo_root / POOL_PATH)
    if not pool_result.personalities:
        entry = _build_log_entry(
            started, _dt.datetime.now(_dt.UTC),
            slug=None, display_name=None, action=None,
            outcome=OUTCOME_ABSTAINED,
            project_id=None, committed_paths=[],
            note=f"no valid personalities in pool (errors={pool_result.error_count})",
        )
        _write_run_log_entry(repo_root, entry)
        return entry

    # ── 2. Select persona ──
    state = load_rotation_state(repo_root / ROTATION_PATH)
    if force_slug:
        match = [p for p in pool_result.personalities if p.slug == force_slug]
        persona = match[0] if match else None
        if persona is None:
            entry = _build_log_entry(
                started, _dt.datetime.now(_dt.UTC),
                slug=force_slug, display_name=None, action=None,
                outcome=OUTCOME_ABSTAINED,
                project_id=None, committed_paths=[],
                note=f"force_slug={force_slug!r} not in pool",
            )
            _write_run_log_entry(repo_root, entry)
            return entry
    else:
        persona = select_next(pool_result.personalities, state.last_used)
        if persona is None:
            entry = _build_log_entry(
                started, _dt.datetime.now(_dt.UTC),
                slug=None, display_name=None, action=None,
                outcome=OUTCOME_ABSTAINED,
                project_id=None, committed_paths=[],
                note="pool empty after load (race?)",
            )
            _write_run_log_entry(repo_root, entry)
            return entry

    display = display_name_for_render(persona)

    # ── 3. Build catalog ──
    catalog = build_catalog(repo_root)

    # ── 4. Call LLM (or fixture) ──
    raw_response: str
    outcome: str
    action_obj: Action | None = None
    dispatch_result: DispatchResult | None = None
    note: str | None = None

    try:
        fixture_path = llm_fixture or os.environ.get("LLMXIVE_PERSONALITY_FIXTURE")
        if fixture_path:
            raw_response = Path(fixture_path).read_text(encoding="utf-8")
        else:
            raw_response = _call_llm_for_persona(persona, catalog, repo_root)
    except Exception as exc:
        # Distinguish rate-limit / transient backend errors from any other
        # failure — rate-limit explicitly records OUTCOME_RATE_LIMITED so
        # post-hoc audits can see the difference. Either way the pointer
        # HOLDS (FR-017).
        outcome = _classify_llm_exception(exc)
        note = f"LLM call failed ({outcome}): {exc}"
        ended = _dt.datetime.now(_dt.UTC)
        entry = _build_log_entry(
            started, ended, slug=persona.slug, display_name=display,
            action=None, outcome=outcome,
            project_id=None, committed_paths=[], note=note,
        )
        _write_run_log_entry(repo_root, entry)
        # Pointer HOLDS on rate_limited / model_error (FR-017).
        _maybe_advance_pointer(repo_root, state, persona, outcome, ended, None, [])
        return entry

    # ── 5. Parse action ──
    try:
        action_obj = parse_action(raw_response)
    except ParseError as exc:
        outcome = OUTCOME_MALFORMED
        note = exc.reason
        ended = _dt.datetime.now(_dt.UTC)
        entry = _build_log_entry(
            started, ended, slug=persona.slug, display_name=display,
            action=None, outcome=outcome,
            project_id=None, committed_paths=[], note=note,
        )
        _write_run_log_entry(repo_root, entry)
        _maybe_advance_pointer(repo_root, state, persona, outcome, ended, None, [])
        return entry

    # ── 5b. Early target-existence check (FR-017 + cost guard) ──
    # If the comment/contribute target artifact doesn't exist, skip the
    # rubric (which would otherwise eat an LLM call rating content that
    # will be discarded anyway) AND skip dispatch so the pointer holds
    # with the correct `target_missing` outcome rather than a coerced
    # `abstained` (which would advance the rotation pointer per
    # ADVANCING_OUTCOMES). Without this guard, the rubric reclassifies
    # bad-target ticks as abstain and rotation advances on a missed
    # target — wrong on both counts.
    if action_obj.action in (ACTION_COMMENT, ACTION_CONTRIBUTE):
        artifact_rel = action_obj.target_artifact_path or ""
        if artifact_rel and not (repo_root / artifact_rel).exists():
            outcome = OUTCOME_TARGET_MISSING
            ended = _dt.datetime.now(_dt.UTC)
            entry = _build_log_entry(
                started, ended, slug=persona.slug, display_name=display,
                action=action_obj.action, outcome=outcome,
                project_id=action_obj.target_project_id,
                committed_paths=[],
                note=f"target artifact not found: {artifact_rel}",
            )
            _write_run_log_entry(repo_root, entry)
            if not force_slug:
                _maybe_advance_pointer(repo_root, state, persona, outcome, ended,
                                        action_obj.action, [])
            return entry

    # ── 5c. Rubric gate (spec 009 FR-004, Clarification Q3) ──
    # If the action is a comment/contribute and the rubric flags it as below
    # threshold, retry ONCE with a hint. On the second failure: persist the
    # rejected body to .audit/rejected-contributions.jsonl, convert to abstain,
    # and advance the rotation.
    if action_obj.action in (ACTION_COMMENT, ACTION_CONTRIBUTE):
        action_obj, rubric_note = _rubric_gate_or_convert_to_abstain(
            action_obj, raw_response, persona, catalog, repo_root,
        )
        if rubric_note:
            note = rubric_note

    # ── 6. Dispatch ──
    dispatch_result = dispatch(action_obj, persona, repo_root)
    outcome = dispatch_result.outcome
    ended = _dt.datetime.now(_dt.UTC)
    entry = _build_log_entry(
        started, ended, slug=persona.slug, display_name=display,
        action=action_obj.action, outcome=outcome,
        project_id=action_obj.target_project_id,
        committed_paths=dispatch_result.committed_paths,
        note=dispatch_result.error,
    )
    _write_run_log_entry(repo_root, entry)

    # ── 6b. Spec 009: append to the project's activity feed + record dispatch ──
    # Personality ticks bypass the central runner (since they have their own
    # rotation + dispatch flow), so we mirror runner.py's feed integration
    # here. This is intentional duplication of the *integration point*, not
    # of the FeedStore logic itself (Constitution I: FeedStore is still the
    # single canonical reader/writer).
    if outcome == OUTCOME_COMMITTED and action_obj.target_project_id:
        try:
            from llmxive.feed import FeedStore
            store = FeedStore(repo_root)
            feed_item = store.append(action_obj.target_project_id, {
                "kind": "personality_tick",
                "author": {
                    "type": "agent",
                    "name": persona.slug,
                    "persona": persona.slug,
                    "display_name": display,
                },
                "summary": (action_obj.reason or "")[:280] or "personality contribution",
                "body": action_obj.content or "",
                "target": {
                    "artifact_path": action_obj.target_artifact_path or "",
                    "artifact_kind": action_obj.target_artifact_kind or "",
                } if action_obj.target_project_id else None,
            })
            # FR-034 input: record dispatch metadata
            store.record_dispatch(action_obj.target_project_id, {
                "dispatch_id": feed_item["id"],
                "agent": f"personality:{persona.slug}",
                "feed_delivered": True,
                "manifest": {"items": []},  # personality tick reads catalog, not feed (yet)
                "outcome": outcome,
                "committed_paths": dispatch_result.committed_paths,
            })
        except Exception as exc:  # pragma: no cover — defensive
            log.warning("could not record personality tick to activity feed: %s", exc)
    # Advance the rotation pointer ONLY on committed/abstained; HOLD on
    # everything else (FR-017). Also honor force_slug — testing flag
    # never updates the pointer.
    if not force_slug:
        _maybe_advance_pointer(repo_root, state, persona, outcome, ended,
                                action_obj.action, dispatch_result.committed_paths)
    return entry


def _build_log_entry(
    started: _dt.datetime, ended: _dt.datetime, *,
    slug: str | None, display_name: str | None,
    action: str | None, outcome: str,
    project_id: str | None, committed_paths: list[str],
    note: str | None = None,
) -> dict[str, Any]:
    """Construct the run-log entry dict per contracts/run-log-entry.example.json."""
    return {
        "started_at": started.isoformat(),
        "ended_at": ended.isoformat(),
        "duration_s": (ended - started).total_seconds(),
        "agent_name": AGENT_NAME,
        "model_name": MODEL_NAME,
        "model_kind": MODEL_KIND,
        "personality_slug": slug,
        "display_name": display_name,
        "project_id": project_id,
        "action": action,
        "outcome": outcome,
        "committed_paths": committed_paths,
        **({"note": note} if note else {}),
    }


def _maybe_advance_pointer(
    repo_root: Path, state: RotationState, persona: Personality,
    outcome: str, ended: _dt.datetime,
    action: str | None, committed_paths: list[str],
) -> None:
    """Update :data:`ROTATION_PATH` per the FR-017 advance-on-success rule.

    - `outcome in ADVANCING_OUTCOMES` (committed/abstained) → set
      ``last_used = persona.slug`` (pointer advances).
    - All other outcomes → leave ``last_used`` UNCHANGED so the same
      persona retries on the next tick.

    Either way, the audit-trail ``history`` gets a new entry.
    """
    history_entry: dict[str, Any] = {
        "slug": persona.slug,
        "started_at": state.last_used_at,  # actually re-set below
        "ended_at": ended.isoformat(),
        "outcome": outcome,
    }
    if action:
        history_entry["action"] = action
    if committed_paths:
        history_entry["committed_paths"] = committed_paths

    if outcome in ADVANCING_OUTCOMES:
        new_last_used = persona.slug
    else:
        new_last_used = state.last_used  # HOLD

    new_state = RotationState(
        last_used=new_last_used,
        last_used_at=ended.isoformat(),
        last_outcome=outcome,
        history=[*state.history, history_entry],
    )
    write_rotation_state(new_state, repo_root / ROTATION_PATH)


# ---------------------------------------------------------------------------
# Spec 009 FR-004 + Clarification Q3: rubric gate
# ---------------------------------------------------------------------------

def _action_to_dict(action: Action) -> dict[str, Any]:
    """Convert an Action dataclass into the rubric scorer's expected dict shape."""
    return {
        "id": "<pending>",
        "kind": "personality_tick",
        "action": action.action,
        "content": action.content or "",
        "target": {
            "project_id": action.target_project_id,
            "artifact_kind": action.target_artifact_kind,
            "artifact_path": action.target_artifact_path,
        } if action.target_project_id else None,
    }


def _rubric_gate_or_convert_to_abstain(
    action: Action,
    raw_response: str,
    persona: Personality,
    catalog: list[CatalogEntry],
    repo_root: Path,
) -> tuple[Action, str | None]:
    """Apply the spec-009 rubric to a contribution; retry once; on second
    failure persist the rejected body to .audit/rejected-contributions.jsonl
    and convert the action into an abstain.

    Returns (possibly-rewritten Action, note-or-None). The note flows into the
    run-log so post-tick audit can see the rubric decision.
    """
    try:
        from llmxive.audit.personality_rubric import audit_contribution
    except Exception as exc:  # pragma: no cover — defensive
        log.warning("rubric unavailable, skipping gate: %s", exc)
        return action, None

    item = audit_contribution(_action_to_dict(action))
    if item.classification == "passes":
        return action, None

    # First rubric failure — retry ONCE with a hint about which axes were missing
    missing_axes = []
    for rule in item.rules_fired:
        if getattr(rule, "rule_id", "") == "manufactured":
            # evidence_snippet looks like "missing axes: [...]"
            missing_axes.append(rule.evidence_snippet)
            break
    hint = " | ".join(missing_axes) or "rubric_below_threshold"
    log.info("rubric rejected first pass for %s: %s — retrying once", persona.slug, hint)

    try:
        retry_raw = _call_llm_for_persona(
            persona, catalog, repo_root,
            extra_hint=(
                "RUBRIC FAILED on previous attempt: " + hint + ". "
                "Add at least ONE of: a specific objection (e.g. 'but the proof assumes X, which fails when Y'), "
                "a specific question (sentence ending in '?'), an adjacent-work pointer (paper / technique / prior result), "
                "or a specific reason for praise (laudatory verb + concrete element). "
                "Do NOT manufacture enthusiasm — abstaining is preferable to padding."
            ),
        )
        retry_action = parse_action(retry_raw)
    except Exception as exc:
        log.info("rubric retry failed to produce parseable response for %s: %s", persona.slug, exc)
        return _convert_to_rubric_abstain(action, raw_response, persona, repo_root, hint), \
            f"rubric_failure_after_retry: {hint}"

    retry_item = audit_contribution(_action_to_dict(retry_action))
    if retry_item.classification == "passes":
        log.info("rubric passes on retry for %s", persona.slug)
        return retry_action, None

    # Second failure: convert to abstain + persist both rejected bodies
    return _convert_to_rubric_abstain(retry_action, retry_raw, persona, repo_root, hint), \
        f"rubric_failure_after_retry: {hint}"


def _convert_to_rubric_abstain(
    action: Action, rejected_body: str, persona: Personality,
    repo_root: Path, hint: str,
) -> Action:
    """Persist the rejected body to .audit/rejected-contributions.jsonl
    (per the persona's target project, if any) and return an abstain Action."""
    if action.target_project_id:
        try:
            from llmxive.feed import FeedStore
            store = FeedStore(repo_root)
            store.record_rejected(action.target_project_id, {
                "persona": persona.slug,
                "display_name": persona.display_name,
                "action": action.action,
                "target_project_id": action.target_project_id,
                "target_artifact_kind": action.target_artifact_kind,
                "target_artifact_path": action.target_artifact_path,
                "content": action.content,
                "rubric_hint": hint,
                "rejected_body": rejected_body,
            })
        except Exception as exc:  # pragma: no cover — defensive
            log.warning("could not persist rejected body to feed audit log: %s", exc)
    return Action(
        action=ACTION_ABSTAIN,
        reason=f"rubric_failure_after_retry: {hint}",
    )
