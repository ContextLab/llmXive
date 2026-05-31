"""Citation strip/flag guard (spec 015 / #239 / F-18).

A GENERAL pass that ensures pipeline stages never publish fabricated or
unresolvable references. It is the enforcement arm of Constitution
Principle II (``.specify/memory/constitution.md``): every external reference
must be verified against its primary source and, if unverifiable, REMOVED or
explicitly marked ``[UNVERIFIED: ...]`` with a reason — never silently kept
and never "resolved" by inventing a different (also-fake) number.

WHY THIS EXISTS (the bug it closes)
-----------------------------------
PROJ-552's spec.md attached a fabricated ``Lee et al. 2024, arXiv:2402.13``
citation to a (correct) knot count. ``arXiv:2402.13`` is malformed (real ids
are ``\\d{4}.\\d{4,5}``) and 404s. The convergence panel flagged it, but the
reviser "resolved" the concern by fabricating a DIFFERENT wrong number plus a
second fake citation. The guard runs EARLY — before the panel reviews a doc —
so the panel never asks the reviser to "fix" a fake citation in the first
place, breaking the fabrication cascade at its source.

DECOMPOSITION (testable without the network — no mocks)
-------------------------------------------------------
* :func:`apply_citation_verdicts` — a PURE function. Given doc text + a list of
  :class:`CitationVerdict`, it rewrites only the FAILED references in-place with
  a greppable ``[UNVERIFIED: <ref> — <reason>]`` marker, keeps the surrounding
  claim text (and, for markdown links, the human-readable title), and leaves
  verified refs byte-for-byte untouched. Returns ``(cleaned_text, GuardReport)``.
  No I/O, fully deterministic — this is what the offline unit tests exercise.

* :func:`verify_and_clean` — the network-driven orchestrator. Extracts EVERY
  reference (reusing :func:`reference_validator.extract_citations`, hardened for
  malformed arXiv ids — markdown-link + bare URLs, arXiv ids, and DOIs), resolves
  each against its primary source via the registrar-AGNOSTIC
  :func:`llmxive.librarian.verify.resolve_reference` (a ``doi.org`` / ``arxiv.org``
  / URL HEAD-with-GET-fallback that follows redirects), builds verdicts, and calls
  the pure function. This is the ONLY place real HTTP runs.

  Resolving DOIs through ``doi.org`` (the DOI proxy's own redirect) rather than a
  Crossref-only metadata lookup is the load-bearing fix: Crossref does NOT know
  about DataCite-minted DOIs (Zenodo ``10.5281/zenodo.*``, PsyArXiv/OSF
  ``10.31234/*`` / ``10.31219/*``), so a Crossref lookup 404s on them and would
  FALSE-FLAG real references as fabricated. ``doi.org`` resolves EVERY registrar
  uniformly (Crossref, DataCite, mEDRA, …). It also drops the guard's call into
  the soft-deprecated ``citation_fetcher.fetch_citation`` — satisfying FR-022's
  no-new-duplicate-caller rule.

* :func:`strip_unresolvable_offline` — a fast, network-free pass used inside the
  convergence reviser loop: it flags only STRUCTURALLY unresolvable refs (a
  malformed arXiv id can be judged fabricated with zero HTTP), so a
  reviser-introduced fake is marked before the next panel round WITHOUT slowing
  the loop down with HTTP or breaking offline reviser tests.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from llmxive.agents.reference_validator import extract_citations
from llmxive.librarian.verify import resolve_reference
from llmxive.types import CitationKind

# A well-formed modern arXiv id; anything captured as ARXIV that does NOT match
# this (and is not an old-style ``archive.SUBJ/NNNNNNN`` id) is structurally
# unresolvable and can be flagged with zero network I/O.
_WELLFORMED_ARXIV_RE = re.compile(r"^\d{4}\.\d{4,5}(v\d+)?$")
_OLDSTYLE_ARXIV_RE = re.compile(r"^[a-z\-]+(?:\.[A-Z]{2})?/\d{7}$")


@dataclass(frozen=True, slots=True)
class CitationVerdict:
    """A per-reference verification outcome the rewriter acts on.

    ``ok=True`` means the reference resolved against its primary source and is
    left untouched. ``ok=False`` means it failed (unreachable / not-found /
    malformed); the rewriter marks it ``[UNVERIFIED: <ref> — <reason>]``.
    """

    value: str
    kind: CitationKind
    ok: bool
    reason: str = ""


@dataclass(slots=True)
class GuardReport:
    """Audit summary of one guard pass (counts + which refs were flagged)."""

    verified_count: int = 0
    flagged_count: int = 0
    flagged_values: list[str] = field(default_factory=list)
    flagged_reasons: dict[str, str] = field(default_factory=dict)


# --- reference → display form ------------------------------------------------


def _display_ref(value: str, kind: CitationKind) -> str:
    """The human-readable token to echo inside the ``[UNVERIFIED: ...]`` marker."""
    if kind == CitationKind.ARXIV:
        return f"arXiv:{value}"
    # DOI / URL: echo the raw value verbatim (the original prefix, if any,
    # stays in the surrounding prose).
    return value


# Spec 016 / FR-019: the unified claim-marker REPLACES F-18's legacy
# ``[UNVERIFIED:`` marker. ``claims.gate`` is now the SINGLE source of truth for
# the marker syntax and the block scanners; F-18 emits that same unified marker
# (so it operates as a resolver within the claim-verification layer). The
# ``UNVERIFIED_*`` names are retained as the F-18 resolver's view of the unified
# marker so existing importers keep working without a parallel implementation.
from llmxive.claims.gate import (  # noqa: E402
    CLAIM_MARKER_PREFIX as UNVERIFIED_MARKER_PREFIX,
)
from llmxive.claims.gate import (  # noqa: E402
    find_unresolved_claims as find_unverified_markers,
)
from llmxive.claims.gate import (  # noqa: E402
    has_unresolved_claims as has_unverified_markers,
)


def _marker(value: str, kind: CitationKind, reason: str) -> str:
    ref = _display_ref(value, kind)
    if reason:
        return f"{UNVERIFIED_MARKER_PREFIX} {ref} — {reason}]"
    return f"{UNVERIFIED_MARKER_PREFIX} {ref}]"


# Patterns that locate a reference TOKEN in the doc so we can replace it in
# place without disturbing the surrounding prose. Each captures the exact
# substring(s) we substitute for the marker.
def _arxiv_occurrence_re(value: str) -> re.Pattern[str]:
    # Match ``arXiv:<value>`` with optional whitespace after the colon, but
    # NOT if it is already inside an ``[UNVERIFIED: ...]`` marker (idempotency).
    esc = re.escape(value)
    return re.compile(rf"\barXiv:\s*{esc}(?![0-9A-Za-z.\-/])", re.IGNORECASE)


def _doi_occurrence_re(value: str) -> re.Pattern[str]:
    esc = re.escape(value)
    return re.compile(rf"(?:doi:\s*)?{esc}", re.IGNORECASE)


def _md_link_occurrence_re(url: str) -> re.Pattern[str]:
    esc = re.escape(url)
    return re.compile(rf"\[(?P<title>[^\]]+)\]\(\s*{esc}\s*\)")


def _bare_url_occurrence_re(url: str) -> re.Pattern[str]:
    esc = re.escape(url)
    return re.compile(esc)


def apply_citation_verdicts(
    text: str, verdicts: list[CitationVerdict]
) -> tuple[str, GuardReport]:
    """PURE rewriter: mark FAILED references in ``text`` ``[UNVERIFIED: ...]``.

    For each ``ok=False`` verdict, the matching reference token is replaced
    in-place by ``[UNVERIFIED: <ref> — <reason>]``:

    * Bare arXiv (``arXiv:2402.13``) / DOI tokens → replaced by the marker; the
      surrounding claim text is preserved.
    * Markdown links (``[title](url)``) whose URL failed → the human-readable
      ``title`` is kept and the ``(url)`` target is replaced by the marker
      (``[title] [UNVERIFIED: url — reason]``), so the prose stays readable but
      the unresolvable target is gone and greppable.
    * Bare URLs → replaced by the marker in place.

    Verified (``ok=True``) references are left byte-for-byte untouched. The
    rewrite is idempotent: a reference already inside an ``[UNVERIFIED: ...]``
    marker is not re-wrapped.

    Returns ``(cleaned_text, GuardReport)``.
    """
    report = GuardReport()
    cleaned = text
    for v in verdicts:
        if v.ok:
            report.verified_count += 1
            continue
        before = cleaned
        cleaned = _flag_one(cleaned, v)
        if cleaned != before:
            report.flagged_count += 1
            report.flagged_values.append(v.value)
            report.flagged_reasons[v.value] = v.reason
    return cleaned, report


# Already inside an ``[UNVERIFIED: ...]`` marker, immediately before the match
# start? Then it has already been flagged — skip it (idempotency).
def _inside_marker(text: str, start: int) -> bool:
    head = text.rfind(UNVERIFIED_MARKER_PREFIX, 0, start)
    if head == -1:
        return False
    close = text.find("]", head)
    return close == -1 or close >= start


def _flag_one(text: str, v: CitationVerdict) -> str:
    """Replace EVERY unmarked occurrence of one failed reference with its marker.

    All occurrences are flagged (not just the first) so a fabricated id that a
    doc cites four times is fully scrubbed. Occurrences already inside an
    existing ``[UNVERIFIED: ...]`` marker are skipped, which makes re-running
    the guard idempotent.
    """
    marker = _marker(v.value, v.kind, v.reason)

    # A literal-marker replacement that skips matches already inside a marker.
    # Using a function (not a string) means the marker text — which may contain
    # ``\d`` from a regex-quoting reason — is inserted VERBATIM, never
    # re-interpreted as a ``re.sub`` replacement template.
    def _sub(m: re.Match[str]) -> str:
        if _inside_marker(m.string, m.start()):
            return m.group(0)
        return marker

    if v.kind == CitationKind.ARXIV:
        return _arxiv_occurrence_re(v.value).sub(_sub, text)
    if v.kind == CitationKind.DOI:
        return _doi_occurrence_re(v.value).sub(_sub, text)
    # URL — for every markdown-link occurrence keep the title + append the
    # marker; for bare-URL occurrences replace in place.
    def _link_sub(m: re.Match[str]) -> str:
        if _inside_marker(m.string, m.start()):
            return m.group(0)
        return f"[{m.group('title')}] {marker}"

    text = _md_link_occurrence_re(v.value).sub(_link_sub, text)
    return _bare_url_occurrence_re(v.value).sub(_sub, text)


# --- network-free structural pass (used inside the reviser loop) ------------


def _is_structurally_unresolvable(value: str, kind: CitationKind) -> str | None:
    """Return a failure reason if the reference is unresolvable WITHOUT any
    network call, else None.

    Currently only arXiv ids are judgeable offline: a token that is neither a
    well-formed modern id nor a valid old-style id is fabricated/malformed.
    """
    if kind == CitationKind.ARXIV:
        if _WELLFORMED_ARXIV_RE.match(value) or _OLDSTYLE_ARXIV_RE.match(value):
            return None
        return r"malformed arXiv id (expected \d{4}.\d{4,5}); unresolvable"
    return None


def strip_unresolvable_offline(text: str) -> tuple[str, GuardReport]:
    """Flag ONLY structurally-unresolvable references (no network).

    Used inside the convergence reviser loop so a reviser-introduced fabricated
    arXiv id is marked ``[UNVERIFIED]`` before the next panel round, with zero
    HTTP (keeps the loop fast and offline reviser tests network-free). Verified
    or merely-need-network refs are left untouched here; full verification runs
    at the stage-production point via :func:`verify_and_clean`.
    """
    verdicts: list[CitationVerdict] = []
    for ext in extract_citations(text):
        reason = _is_structurally_unresolvable(ext.value, ext.kind)
        if reason is not None:
            verdicts.append(
                CitationVerdict(value=ext.value, kind=ext.kind, ok=False, reason=reason)
            )
    if not verdicts:
        return text, GuardReport()
    return apply_citation_verdicts(text, verdicts)


# --- network-driven orchestrator --------------------------------------------


def verify_and_clean(
    text: str,
    *,
    summary: str | None = None,
    repo_root: Path,
    project_id: str,
    artifact_path: str,
) -> tuple[str, GuardReport]:
    """Extract → resolve (real HTTP) → mark unresolvable refs ``[UNVERIFIED]``.

    This is the ONLY function here that touches the network. It:

    1. Extracts EVERY reference (markdown-link + bare URLs, arXiv ids — including
       malformed ones — and DOIs).
    2. Resolves each against its primary source via the registrar-AGNOSTIC
       ``llmxive.librarian.verify.resolve_reference`` (a ``doi.org`` /
       ``arxiv.org`` / URL HEAD-with-GET-fallback that follows redirects). This
       handles every DOI registrar uniformly — Crossref journal DOIs AND
       DataCite/Crossref-minted Zenodo / bioRxiv / medRxiv / PsyArXiv / OSF
       DOIs alike — so a real Zenodo or PsyArXiv reference is never false-flagged
       as fabricated (a Crossref-only lookup would 404 those and wrongly flag
       them). FR-022: this guard does NOT call the soft-deprecated
       ``agents/tools/citation_fetcher.fetch_citation``.
    3. Marks every reference that does NOT exist (``unreachable``) with an
       ``[UNVERIFIED: <ref> — <reason>]`` marker (in-place; claim text kept). A
       reference that exists but is access-gated (paywall/rate-limit ⇒
       ``present_ambiguous``) is treated as PRESENT and left untouched — this is
       an existence/anti-fabrication check, not a paywall gate.

    ``summary`` / ``repo_root`` / ``project_id`` / ``artifact_path`` are accepted
    so the orchestrator can be wired alongside the persistence layer; they let
    callers correlate this pass with the citations store without a second
    extraction. Returns ``(cleaned_text, GuardReport)``.
    """
    # Structurally-unresolvable refs (malformed arXiv) need no HTTP — judge them
    # first so a fabricated id is flagged even if the network is down.
    extracted = extract_citations(text)
    if not extracted:
        return text, GuardReport()

    verdicts: list[CitationVerdict] = []
    for ext in extracted:
        offline_reason = _is_structurally_unresolvable(ext.value, ext.kind)
        if offline_reason is not None:
            verdicts.append(
                CitationVerdict(value=ext.value, kind=ext.kind, ok=False, reason=offline_reason)
            )
            continue
        try:
            outcome = resolve_reference(ext.kind.value, ext.value)
        except Exception as exc:  # resolver blew up → treat as unverifiable
            verdicts.append(
                CitationVerdict(
                    value=ext.value, kind=ext.kind, ok=False,
                    reason=f"resolver error: {type(exc).__name__}: {exc}",
                )
            )
            continue
        # ``present`` covers both ``resolved`` and ``present_ambiguous`` (a real
        # but paywalled/rate-limited source still EXISTS — do not flag it).
        ok = outcome.present
        verdicts.append(
            CitationVerdict(
                value=ext.value, kind=ext.kind, ok=ok,
                reason="" if ok else (outcome.reason or "primary source unreachable"),
            )
        )
    return apply_citation_verdicts(text, verdicts)


# --- project-level governing-artifact scan (the advancement / graph gates) ---

# Glob patterns (relative to ``projects/<id>/``) for the produced documents that
# govern each accept transition. These are the artifacts whose published content
# must be free of unverified-citation markers before the project may advance.
_RESEARCH_ARTIFACT_GLOBS: tuple[str, ...] = (
    "specs/*/spec.md",
    "specs/*/plan.md",
    "specs/*/research.md",
    "specs/*/data-model.md",
    "specs/*/quickstart.md",
    "specs/*/tasks.md",
    "specs/*/contracts/*.md",
    "results.md",
)
_PAPER_ARTIFACT_GLOBS: tuple[str, ...] = (
    "paper/source/*.tex",
    "paper/source/**/*.tex",
    "paper/specs/*/spec.md",
    "paper/specs/*/plan.md",
    "paper/specs/*/research.md",
    "paper/specs/*/tasks.md",
)


def _project_dir(project_id: str, repo_root: Path | None) -> Path:
    from llmxive.config import repo_root as _resolve_repo_root

    root = repo_root if repo_root is not None else _resolve_repo_root()
    return root / "projects" / project_id


def _scan_globs_for_markers(base: Path, globs: tuple[str, ...]) -> list[str]:
    """Return every unverified-marker body found across ``base``'s ``globs``.

    Reads each matching file and accumulates its marker bodies (deduped,
    in discovery order). Missing files / globs that match nothing are skipped —
    this is an existence-aware gate, not a presence requirement."""
    seen: set[str] = set()
    bodies: list[str] = []
    for pattern in globs:
        for path in sorted(base.glob(pattern)):
            if not path.is_file():
                continue
            try:
                content = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            for body in find_unverified_markers(content):
                key = f"{path}::{body}"
                if key not in seen:
                    seen.add(key)
                    bodies.append(f"{path.name}: {body}")
    return bodies


def project_unverified_markers(
    project_id: str, *, track: str, repo_root: Path | None = None
) -> list[str]:
    """Marker bodies present in a project's governing ``track`` artifacts.

    ``track`` is ``"research"`` or ``"paper"`` and selects which produced
    documents are scanned (research specs/plan/tasks/results vs. paper
    source/specs). An empty list means no produced doc carries an
    ``[UNVERIFIED: ...]`` marker. The advancement evaluator and the
    paper-complete graph gate call :func:`project_artifacts_have_markers`
    (the boolean form) to HARD-BLOCK advancement when this is non-empty."""
    if track == "research":
        globs = _RESEARCH_ARTIFACT_GLOBS
    elif track == "paper":
        globs = _PAPER_ARTIFACT_GLOBS
    else:
        raise ValueError(f"unknown track {track!r}; expected 'research' or 'paper'")
    return _scan_globs_for_markers(_project_dir(project_id, repo_root), globs)


def project_artifacts_have_markers(
    project_id: str, *, track: str, repo_root: Path | None = None
) -> bool:
    """True iff the project's governing ``track`` artifacts carry any
    unverified-citation marker (the boolean hard-block predicate)."""
    return bool(project_unverified_markers(project_id, track=track, repo_root=repo_root))


__all__ = [
    "UNVERIFIED_MARKER_PREFIX",
    "CitationVerdict",
    "GuardReport",
    "apply_citation_verdicts",
    "find_unverified_markers",
    "has_unverified_markers",
    "project_artifacts_have_markers",
    "project_unverified_markers",
    "strip_unresolvable_offline",
    "verify_and_clean",
]
