"""One grounded personality turn: pick a real artifact, read it, comment or abstain.

The 2026-10-09 incremental-value audit of the old lane measured what it had
produced: 1,045 attempts, 535 committed outcomes (529 comments, 5 arXiv stubs,
1 feedback) and 410 surviving review files, every one of them hardcoded
``minor_revision``. The audit's finding was not that persona framing is
worthless -- a persona uniquely supplied a shuffled/constant-pose negative
control and a translation-direction error that neither matched neutral output
produced -- but that the lane could not be grounded:

* it was shown a CATALOG of 30 projects with two 140-character artifact
  previews each, and asked to critique from that. 140 characters is not an
  artifact, so critiques invented issues the artifact did not have;
* it could write new projects and feedback records nothing consumed;
* it spent a second model call on a rubric retry;
* it recorded a hardcoded model name rather than the one that answered.

So a turn now: selects ONE substantive artifact of ONE active authored project
BEFORE generating anything, reads it under an explicit byte budget with
truncation flagged, is shown the ordinary reviews of that artifact so it does
not restate them, and may only COMMENT or ABSTAIN. One model call. Provenance
is whatever the router actually returned.

Quote anchoring is EVIDENCE ANCHORING, not factual validation: a quote proving
the comment refers to text that exists says nothing about whether the comment
is right. The record says so, and the telemetry leaves novelty, factuality and
applied status unassessed unless something independent observes them.

Advisory only. A comment here never becomes a scientific gate, never rewrites
scope, and never displaces a human's feedback or an ordinary review.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

#: A turn reads ONE artifact. The budget is per-artifact and generous enough to
#: carry a whole spec or a paper section, where the old lane's 140 characters
#: could not carry a sentence.
MAX_ARTIFACT_BYTES = 24_000
#: Context beyond the artifact: the idea, and the ordinary reviews of it.
MAX_IDEA_BYTES = 4_000
MAX_REVIEW_BYTES = 6_000
MAX_REVIEWS = 4
#: Below this an artifact is a stub, not something to critique. The audit found
#: the lane commenting on URL-only intake stubs.
MIN_SUBSTANTIVE_BYTES = 600

#: Stages where authored work is live enough that a comment can still matter.
ACTIVE_STAGES = frozenset({
    "brainstormed", "flesh_out_in_progress", "flesh_out_complete", "validated",
    "project_initialized", "specified", "clarified", "planned", "tasked",
    "analyzed", "in_progress", "research_review", "research_complete",
    "research_accepted", "paper_planned", "paper_tasked", "paper_in_progress",
    "paper_review", "paper_complete",
})

#: Artifact kinds a turn may be given, most substantive first. `paper/source`
#: and the Spec Kit documents are prose a reader can engage with; a PDF is not
#: (it was a placeholder string in the old catalog).
ARTIFACT_PATTERNS: tuple[tuple[str, str], ...] = (
    ("specs/*/spec.md", "spec"),
    ("specs/*/plan.md", "plan"),
    ("specs/*/tasks.md", "tasks"),
    ("paper/source/main.tex", "paper_source"),
    ("idea/fleshed_out.md", "idea"),
    ("idea/*.md", "idea"),
)

#: A URL-only stub: an intake record whose body is a link and nothing else.
_URL_ONLY_RE = re.compile(r"^\s*(?:#[^\n]*\n)?\s*(?:<?https?://\S+>?\s*)+$")


@dataclass(frozen=True)
class Target:
    """The one artifact this turn is about."""

    project_id: str
    title: str
    stage: str
    artifact_rel: str
    kind: str
    artifact_text: str
    artifact_truncated: bool
    idea_text: str
    idea_truncated: bool
    #: (path, text) of the ORDINARY reviews of this project, so a turn can see
    #: what has already been said and not restate it.
    reviews: tuple[tuple[str, str], ...] = ()
    reviews_truncated: bool = False


@dataclass
class TurnOutcome:
    """What a turn produced. ``comment`` is empty for an abstention."""

    action: str
    comment: str = ""
    quotes: tuple[str, ...] = ()
    reason: str = ""
    #: Quotes that do NOT appear in the numbered source. Anchoring evidence,
    #: never a factual verdict.
    unanchored: tuple[str, ...] = ()
    model: str = ""
    provenance: dict[str, Any] = field(default_factory=dict)


ACTION_COMMENT = "comment"
ACTION_ABSTAIN = "abstain"


# --- selection -----------------------------------------------------------

def _is_substantive(text: str) -> bool:
    """Whether ``text`` is something a reader can engage with.

    Rejects a URL-only intake stub and anything under
    :data:`MIN_SUBSTANTIVE_BYTES`, measured on the body with front matter and
    blank lines removed, so a long YAML header cannot make a stub look full.
    """
    body = re.sub(r"^---\s*\n.*?\n---\s*\n", "", text, count=1, flags=re.DOTALL)
    stripped = "\n".join(ln for ln in body.splitlines() if ln.strip())
    if not stripped.strip():
        return False
    if _URL_ONLY_RE.match(stripped):
        return False
    return len(stripped.encode("utf-8")) >= MIN_SUBSTANTIVE_BYTES


def _read(path: Path, limit: int) -> tuple[str, bool]:
    """``(text, truncated)`` — never a silent cut."""
    try:
        raw = path.read_bytes()
    except OSError:
        return "", False
    if len(raw) <= limit:
        return raw.decode("utf-8", errors="replace"), False
    return raw[:limit].decode("utf-8", errors="replace"), True


def _ordinary_reviews(project_dir: Path) -> tuple[list[tuple[str, str]], bool]:
    """The project's ordinary (non-personality) reviews, newest first."""
    found: list[tuple[float, str, str]] = []
    for pattern in ("reviews/research/*.md", "paper/reviews/*.md"):
        for path in project_dir.glob(pattern):
            if not path.is_file():
                continue
            name = path.name.lower()
            # A personality review is this lane's OWN output: excluded, so a
            # turn is never deduped or anchored against itself.
            if "simulated" in name or "persona" in name:
                continue
            try:
                found.append((path.stat().st_mtime, path.name, path.read_text(
                    encoding="utf-8", errors="replace")[:MAX_REVIEW_BYTES]))
            except OSError:
                continue
    found.sort(key=lambda row: -row[0])
    kept = [(name, text) for _mtime, name, text in found[:MAX_REVIEWS]]
    return kept, len(found) > MAX_REVIEWS


def select_target(repo_root: Path, *, project_ids: list[str] | None = None) -> Target | None:
    """The one artifact this turn is about, or ``None`` when there is nothing.

    Deterministic and model-free: the most recently updated ACTIVE AUTHORED
    project that has a substantive artifact. "Authored" excludes an ingested
    preprint — llmXive did not write those, and the lane's job is to engage
    with the platform's own work. Returning ``None`` means the turn abstains
    BEFORE any model call.
    """
    from llmxive.state import project as project_store

    repo_root = Path(repo_root)
    try:
        projects = project_store.list_all(repo_root=repo_root)
    except Exception:
        return None
    projects.sort(key=lambda p: p.updated_at, reverse=True)
    for project in projects:
        if project_ids is not None and project.id not in project_ids:
            continue
        stage = getattr(project.current_stage, "value", str(project.current_stage))
        if stage not in ACTIVE_STAGES:
            continue
        project_dir = repo_root / "projects" / project.id
        if (project_dir / "paper" / "preprint.json").is_file():
            continue  # an ingested third-party paper, not authored here
        resolved_project = project_dir.resolve()
        for pattern, kind in ARTIFACT_PATTERNS:
            for path in sorted(project_dir.glob(pattern)):
                if not path.is_file() or path.is_symlink():
                    continue  # a link can point anywhere; read only real files
                try:
                    if not path.resolve().is_relative_to(resolved_project):
                        continue  # confined to the project, whatever the path says
                except OSError:
                    continue
                text, truncated = _read(path, MAX_ARTIFACT_BYTES)
                if not _is_substantive(text):
                    continue
                idea_path = next(iter(sorted(project_dir.glob("idea/*.md"))), None)
                idea_text, idea_truncated = (
                    _read(idea_path, MAX_IDEA_BYTES) if idea_path else ("", False)
                )
                reviews, reviews_truncated = _ordinary_reviews(project_dir)
                return Target(
                    project_id=project.id,
                    title=project.title or project.id,
                    stage=stage,
                    artifact_rel=path.relative_to(repo_root).as_posix(),
                    kind=kind,
                    artifact_text=text,
                    artifact_truncated=truncated,
                    idea_text=idea_text,
                    idea_truncated=idea_truncated,
                    reviews=tuple(reviews),
                    reviews_truncated=reviews_truncated,
                )
    return None


# --- dedupe --------------------------------------------------------------

def context_digest(target: Target) -> str:
    """A digest of what the turn was SHOWN, for unchanged-context dedupe.

    Covers the artifact and the ordinary reviews — the material a comment
    responds to. It deliberately excludes this lane's own previous output and
    all metadata (stage, timestamps, the persona), so the same persona is not
    asked to re-read an unchanged artifact, while a NEW ordinary review on it
    does make the context fresh again.
    """
    hasher = hashlib.sha256()
    hasher.update(target.project_id.encode("utf-8"))
    hasher.update(b"\0")
    hasher.update(target.artifact_rel.encode("utf-8"))
    hasher.update(b"\0")
    hasher.update(target.artifact_text.encode("utf-8"))
    for name, text in target.reviews:
        hasher.update(b"\0")
        hasher.update(name.encode("utf-8"))
        hasher.update(text.encode("utf-8"))
    return hasher.hexdigest()


# --- prompt --------------------------------------------------------------

_NEUTRAL_LENS = (
    "You are an attentive domain reader of this artifact. Judge it on its own "
    "terms: whether what it claims follows from what it shows, whether the "
    "method answers the question asked, and whether a stated number, control "
    "or comparison is actually established."
)


def numbered_source(text: str) -> str:
    """``text`` with 1-based line numbers, so a comment can cite a line."""
    return "\n".join(f"{i:4d}| {line}" for i, line in enumerate(text.splitlines(), 1))


def render_prompt(target: Target, *, persona_framing: str = "") -> str:
    """The single prompt for the turn.

    The neutral domain lens is the DEFAULT. A persona, when supplied, is an
    optional framing layered on top of it — never a replacement, because the
    audit could not show the framing alone produces better critiques, only that
    it sometimes produces different ones.
    """
    parts = [
        "=== HOW TO READ THIS ===",
        _NEUTRAL_LENS,
    ]
    if persona_framing:
        parts += [
            "",
            "=== OPTIONAL FRAMING ===",
            "Read in the voice and preoccupations below. The framing may change "
            "WHAT YOU NOTICE; it must not change the standard of evidence, and "
            "it is never a reason to assert something the artifact does not show.",
            persona_framing.strip(),
        ]
    parts += [
        "",
        "=== PROJECT ===",
        f"id: {target.project_id}",
        f"title: {target.title}",
        f"stage: {target.stage}",
    ]
    if target.idea_text:
        parts += [
            "",
            "--- the project's idea"
            + (" (TRUNCATED)" if target.idea_truncated else "")
            + " ---",
            target.idea_text,
        ]
    parts += [
        "",
        f"=== THE ARTIFACT UNDER REVIEW: {target.artifact_rel} ({target.kind}) ==="
        + (" [TRUNCATED — do not infer anything from the cut]"
           if target.artifact_truncated else ""),
        numbered_source(target.artifact_text),
    ]
    if target.reviews:
        parts += ["", "=== REVIEWS THIS ARTIFACT ALREADY HAS ==="]
        parts.append(
            "Do not restate these. Say something they do not, or abstain."
            + (" (older reviews omitted)" if target.reviews_truncated else "")
        )
        for name, text in target.reviews:
            parts += [f"--- {name} ---", text]
    parts += [
        "",
        "=== YOUR TURN ===",
        "Return ONE JSON object and nothing else:",
        '{"action": "comment", "comment": "<your remark>", '
        '"quotes": ["<verbatim span from the numbered artifact>", ...]}',
        'or {"action": "abstain", "reason": "<why you have nothing to add>"}',
        "",
        "Rules:",
        "- ABSTAIN unless you have something specific and new. An abstention is "
        "a good outcome; a generic remark is not.",
        "- Every quote must be copied VERBATIM from the artifact above. A quote "
        "shows which text you mean; it does not make your point true.",
        "- Comment on THIS artifact. Do not propose a new project, request "
        "work, or rewrite the project's scope — your remark is advisory.",
        "- OUTPUT MUST BE IN ENGLISH. No prose outside the JSON.",
    ]
    return "\n".join(parts)


# --- parsing -------------------------------------------------------------

class TurnParseError(ValueError):
    """The reply was not a usable comment-or-abstain object."""


_JSON_SPAN_RE = re.compile(r"\{.*\}", re.DOTALL)


def parse_turn(raw: str, target: Target, *, model: str = "") -> TurnOutcome:
    """Parse a reply into a comment or an abstention.

    Only those two. The old lane could also emit ``contribute`` and
    ``propose_arxiv``, which wrote records nothing consumed; a reply asking for
    either is a malformed turn now, not a silent no-op.
    """
    text = (raw or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\s*|\s*```$", "", text).strip()
    match = _JSON_SPAN_RE.search(text)
    if not match:
        raise TurnParseError("no JSON object in the reply")
    try:
        data = json.loads(match.group(0))
    except ValueError as exc:
        raise TurnParseError(f"unparsable JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise TurnParseError("the reply's JSON is not an object")

    action = str(data.get("action") or "").strip().lower()
    if action == ACTION_ABSTAIN:
        return TurnOutcome(
            action=ACTION_ABSTAIN,
            reason=str(data.get("reason") or "").strip(),
            model=model,
        )
    if action != ACTION_COMMENT:
        raise TurnParseError(
            f"action must be {ACTION_COMMENT!r} or {ACTION_ABSTAIN!r}, got {action!r}"
        )

    comment = str(data.get("comment") or "").strip()
    if not comment:
        raise TurnParseError("a comment action carries no comment text")
    raw_quotes = data.get("quotes") or []
    if not isinstance(raw_quotes, list):
        raise TurnParseError("quotes must be a list")
    quotes = tuple(str(q).strip() for q in raw_quotes if str(q).strip())
    unanchored = tuple(q for q in quotes if q not in target.artifact_text)
    return TurnOutcome(
        action=ACTION_COMMENT,
        comment=comment,
        quotes=quotes,
        unanchored=unanchored,
        model=model,
        provenance={
            "artifact": target.artifact_rel,
            "artifact_truncated": target.artifact_truncated,
            "context_digest": context_digest(target),
            "ordinary_reviews_shown": [name for name, _ in target.reviews],
            # Said plainly so no later reader mistakes one for the other.
            "quote_anchoring": "quotes located in the artifact; NOT factual validation",
            "novelty": "unassessed",
            "factuality": "unassessed",
            "applied": "unassessed",
        },
    )


__all__ = [
    "ACTION_ABSTAIN",
    "ACTION_COMMENT",
    "MAX_ARTIFACT_BYTES",
    "MIN_SUBSTANTIVE_BYTES",
    "Target",
    "TurnOutcome",
    "TurnParseError",
    "context_digest",
    "numbered_source",
    "parse_turn",
    "render_prompt",
    "select_target",
]
