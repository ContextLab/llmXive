"""T016 — Claim extraction (spec 016, US1).

extract_claims(text, *, artifact_path, backend, model, repo_root) -> list[Claim]

One LLM call rendering prompts/claim_extraction.md; parses a YAML response
into Claim objects. Precision-favored: the prompt instructs to skip design
choices, thresholds, parameters, and subjective statements. A post-parse
filter (_filter_check_worthy) applies deterministic safety-net rules.
"""

from __future__ import annotations

import datetime
import logging
import re
from pathlib import Path
from typing import Any

from llmxive.claims.classify import classify
from llmxive.claims.models import Claim, ClaimStatus, compute_claim_id

logger = logging.getLogger(__name__)

_PROMPT_PATH = "prompts/claim_extraction.md"
_REASONING_MAX_TOKENS = 131_072
_DEFAULT_MODEL = "qwen.qwen3.5-122b"

# ---------------------------------------------------------------------------
# Post-parse deterministic filter
# ---------------------------------------------------------------------------

# Patterns that mark a candidate as a design choice / parameter / non-claim.
_DESIGN_CHOICE_PATTERNS = [
    # Threshold / p-value / statistical threshold
    re.compile(r"\bp\s*[<>=!]+\s*0\.\d+", re.IGNORECASE),
    # R-squared threshold
    re.compile(r"\bR[²²²]?\s*[≥>=]\s*0\.\d+", re.IGNORECASE),
    # Explicit learning rate, rate=, weight decay etc.
    re.compile(r"\b(learning\s+rate|weight\s+decay|dropout|batch\s+size)\s+(is\s+)?(set\s+to\s+)?[\d.]+", re.IGNORECASE),
    # Resolution pattern like 1200x900 (the multiplication-sign glyph in the
    # character class is intentional — it appears in real resolution strings).
    re.compile(r"\b\d{3,4}\s*[xX×]\s*\d{3,4}\b"),  # noqa: RUF001
    # Requirement/task/feature IDs: FR-001, SC-003, T013, US1, R2, etc.
    re.compile(r"\b(FR|SC|T|US|R)-?\d+\b"),
    # "set to <number>" / "use a <X> of <number>" design parameter phrasing
    re.compile(r"\b(set\s+to|use\s+a\s+\w+\s+of|configured\s+as|default\s+to)\s+[\d.]+", re.IGNORECASE),
    # Timeout / retry / window sizes
    re.compile(r"\b(timeout|retry|window|budget|cap)\s+(of\s+)?[\d.]+\s*(second|minute|token|attempt)", re.IGNORECASE),
]

# Subjective / hedged language that disqualifies a claim as check-worthy.
# Includes promotional "standing" language ("well-established", "peer-reviewed",
# "gold standard", …): a statement whose ONLY content is that a source is
# reputable has no crisp checkable core and cannot be substantiated, so it would
# leave a residual [UNRESOLVED-CLAIM:] marker and block convergence (PROJ-552
# root cause 5). A statement with a salient NUMBER or explicit citation still
# passes (see _filter_check_worthy) so "9988 prime knots (OEIS A002863)" survives.
_SUBJECTIVE_PATTERNS = [
    re.compile(r"\b(elegant|well.?suited|promising|novel|interesting|simple|"
               r"straightforward|intuitive|natural|effective|efficient|powerful|"
               r"robust|flexible|scalable)\b", re.IGNORECASE),
    re.compile(r"\b(well.?established|peer.?reviewed|community.?standard|"
               r"widely.?used|well.?known|established\s+reference|"
               r"gold\s+standard)\b", re.IGNORECASE),
]

# Minimum length for a candidate to be considered a real claim.
_MIN_CLAIM_CHARS = 10


def _filter_check_worthy(candidates: list[str]) -> list[str]:
    """Deterministic post-parse filter — drops obvious non-claims.

    Removes:
    - Empty or very short strings.
    - Design choices / parameter settings matching _DESIGN_CHOICE_PATTERNS.
    - Pure subjective statements (no numeric or attributable content) matching
      _SUBJECTIVE_PATTERNS.
    """
    result: list[str] = []
    for text in candidates:
        if not text or len(text.strip()) < _MIN_CLAIM_CHARS:
            continue
        stripped = text.strip()
        # Drop design-choice patterns.
        if any(p.search(stripped) for p in _DESIGN_CHOICE_PATTERNS):
            continue
        # Drop purely subjective statements (only drop when NO number present
        # and no external attribution signal — pure opinion).
        if any(p.search(stripped) for p in _SUBJECTIVE_PATTERNS):
            # A subjective statement still passes if it contains a number or
            # an explicit citation (it might be a hedge around a real claim).
            has_number = bool(re.search(r"\b\d[\d,.]*\b", stripped))
            has_citation = bool(re.search(
                r"\b(doi:|arxiv:|https?://|[A-Z][a-z]+\s+et\s+al\.?|[A-Z][a-z]+\s+\d{4})\b",
                stripped,
            ))
            if not has_number and not has_citation:
                continue
        result.append(stripped)
    return result


# ---------------------------------------------------------------------------
# LLM call helpers
# ---------------------------------------------------------------------------

def _chat_reasoning_safe(backend: Any, messages: list[Any], model: str | None) -> Any:
    kwargs: dict[str, Any] = {"max_tokens": _REASONING_MAX_TOKENS}
    if model is not None:
        kwargs["model"] = model
    try:
        return backend.chat(messages, **kwargs)
    except TypeError:
        kwargs.pop("max_tokens", None)
        try:
            return backend.chat(messages, **kwargs)
        except TypeError:
            return backend.chat(messages)


def _now_iso() -> str:
    return datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# YAML response parser
# ---------------------------------------------------------------------------

def _strip_outer_quotes(value: str) -> str:
    """Strip a single layer of matching surrounding quotes, keeping inner ones.

    ``'"For ... "A Census of Knots." ..."'`` → ``'For ... "A Census of Knots." ...'``
    Embedded quotes are preserved verbatim — only one outer matched pair is removed.
    """
    v = value.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in ("'", '"'):
        return v[1:-1]
    return v


# Recognized field keys in the extraction contract (Output format §).
_FIELD_RE = re.compile(
    r"^\s*-?\s*(claim_text|canonical|context|number|source)\s*:\s*(.*)$"
)


def tolerant_field_entries(raw: str) -> list[dict[str, str]]:
    """Line-oriented field recovery for a quote-fragile YAML claims reply.

    The extraction model frequently emits a verbatim ``claim_text`` containing
    embedded double-quotes (e.g. a cited paper title — ``"A Census of Knots."``),
    which breaks YAML's quoted-scalar grammar and would otherwise drop EVERY
    claim in the document (a silent fabrication-passthrough). This recovers each
    entry as a plain ``dict[str, str]`` by scanning for the known field keys
    (``claim_text`` / ``canonical`` / ``context`` / ``number`` / ``source``) and
    taking the remainder of the line as the value (one outer quote pair
    stripped), without relying on quote-balanced YAML. A new entry begins at each
    ``claim_text`` key.

    SHARED by :func:`_tolerant_parse_claims` (claims/extract) and the grounding
    guard's ``_parse_extraction_reply`` recovery path — a single tolerant parser
    so the embedded-quote fix cannot silently regress in one of two twins.
    PURE — no IO.
    """
    entries: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    for line in raw.splitlines():
        m = _FIELD_RE.match(line)
        if not m:
            continue
        key, val = m.group(1), _strip_outer_quotes(m.group(2))
        if key == "number":
            # The prompt's example carries an inline "# ..." comment; strip it
            # ONLY here (claim_text/canonical/context may legitimately contain #).
            val = val.split("#", 1)[0].strip()
            val = _strip_outer_quotes(val)
        if key == "claim_text":
            if current is not None:
                entries.append(current)
            current = {"claim_text": val}
        elif current is not None:
            current[key] = val
    if current is not None:
        entries.append(current)
    return entries


def _tolerant_parse_claims(raw: str, artifact_path: str) -> list[Claim]:
    """Recover :class:`Claim` objects when ``yaml.safe_load`` fails.

    Thin wrapper over :func:`tolerant_field_entries` (the shared line-oriented
    field recovery) that maps each recovered entry into a PENDING ``Claim``.
    """
    now = _now_iso()
    entries = tolerant_field_entries(raw)

    out: list[Claim] = []
    for entry in entries:
        claim_text = (entry.get("claim_text") or "").strip()
        if not claim_text:
            continue
        canonical = (entry.get("canonical") or claim_text).strip()
        context = (entry.get("context") or "").strip()
        kind = classify(claim_text, canonical)
        claim_id = compute_claim_id(kind, canonical, context)
        out.append(Claim(
            claim_id=claim_id,
            kind=kind,
            raw_text=claim_text,
            canonical=canonical,
            context=context,
            artifact_path=artifact_path,
            source_type="external",
            status=ClaimStatus.PENDING,
            resolved_value=None,
            evidence=None,
            resolver=None,
            attempts=0,
            updated_at=now,
        ))
    if out:
        logger.info("claim_extract: tolerant recovery parsed %d claim(s)", len(out))
    return out


def _parse_extraction_reply(reply_text: str, artifact_path: str) -> list[Claim]:
    """Parse the model's YAML extraction reply into :class:`Claim` objects.

    Tries strict YAML first; on a parse failure or a structurally-unusable
    result, falls back to :func:`_tolerant_parse_claims` (robust to the common
    embedded-quote failure mode). Returns an empty list (not an exception) only
    when BOTH paths recover nothing.
    """
    import yaml

    raw = (reply_text or "").strip()
    if raw.startswith("```"):
        lines = raw.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        raw = "\n".join(lines).strip()

    try:
        obj = yaml.safe_load(raw)
    except Exception as exc:
        logger.warning(
            "claim_extract: YAML parse failed (%s); attempting tolerant recovery", exc
        )
        return _tolerant_parse_claims(raw, artifact_path)

    if not isinstance(obj, dict) or "claims" not in obj:
        return _tolerant_parse_claims(raw, artifact_path)

    claims_raw = obj.get("claims") or []
    if not isinstance(claims_raw, list):
        return _tolerant_parse_claims(raw, artifact_path)

    now = _now_iso()
    out: list[Claim] = []
    for entry in claims_raw:
        if not isinstance(entry, dict):
            continue
        claim_text = str(entry.get("claim_text") or "").strip()
        if not claim_text:
            continue
        canonical = str(entry.get("canonical") or claim_text).strip()
        context = str(entry.get("context") or "").strip()
        kind = classify(claim_text, canonical)
        claim_id = compute_claim_id(kind, canonical, context)
        out.append(Claim(
            claim_id=claim_id,
            kind=kind,
            raw_text=claim_text,
            canonical=canonical,
            context=context,
            artifact_path=artifact_path,
            source_type="external",
            status=ClaimStatus.PENDING,
            resolved_value=None,
            evidence=None,
            resolver=None,
            attempts=0,
            updated_at=now,
        ))
    # If strict YAML yielded a dict but no usable claims (e.g. every entry's
    # text was mangled by quote-truncation), try the tolerant path as a backstop.
    if not out:
        return _tolerant_parse_claims(raw, artifact_path)
    return out


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

# Headings whose CONTENT is citation/survey prose about OTHER works, not THIS
# document's own testable claims. Extracting numeric claims from these yields
# garbage "facts": a citation YEAR ("…knots and links (2022) — …"), a referenced
# paper's arXiv-header date, or a coincidental OEIS sequence hit on a title number
# — none of which is a commitment of this document. They are excluded from
# extraction only; the rendered artifact is unchanged (render/pointer use the full
# text), so the prose still appears in the document.
_NONCLAIM_SECTION_TITLES = frozenset({
    "references",
    "bibliography",
    "related work",
    "related works",
    "works cited",
    "citations",
    "sources",
    "prior work",
    "further reading",
    "see also",
    "acknowledgments",
    "acknowledgements",
})

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")
_FENCE_RE = re.compile(r"^\s*(?:```|~~~)")


def _normalize_heading_title(title: str) -> str:
    """Normalise a markdown heading's title for non-claim-section matching.

    Strips emphasis markers and trailing parentheticals (e.g. ``*(mandatory)*``,
    ``(Priority: P1)``), lowercases, drops punctuation, collapses whitespace. So
    ``## Related Work`` -> ``related work`` and ``## Requirements *(mandatory)*``
    -> ``requirements``. PURE.
    """
    cleaned = re.sub(r"\*+", "", title)            # bold/italic markers
    cleaned = re.sub(r"\(.*?\)", "", cleaned)      # "(mandatory)", "(Priority …)"
    cleaned = re.sub(r"[^a-z0-9 ]", " ", cleaned.lower())
    return " ".join(cleaned.split())


def strip_nonclaim_sections(text: str) -> str:
    """Remove citation/survey sections (References, Related Work, …) for EXTRACTION.

    A markdown heading whose normalised title is in
    :data:`_NONCLAIM_SECTION_TITLES` opens an excluded region that runs to the
    next heading of the SAME OR HIGHER level (``#`` count ≤ the excluded heading's)
    or end-of-text; the heading and its body are dropped. Everything else —
    including all body sections (Requirements, Success Criteria, Assumptions) — is
    preserved byte-for-byte, so claim spans extracted from the body still resolve
    against the full document. Headings inside fenced code blocks are ignored.
    PURE.
    """
    out: list[str] = []
    skip_level = 0  # 0 = emitting; else the '#' count of the open excluded heading
    in_fence = False
    for line in text.splitlines(keepends=True):
        body = line.rstrip("\n")
        if _FENCE_RE.match(body):
            in_fence = not in_fence
            if not skip_level:
                out.append(line)
            continue
        heading = None if in_fence else _HEADING_RE.match(body)
        if heading is not None:
            level = len(heading.group(1))
            # A heading at the same-or-higher level closes the excluded region.
            if skip_level and level <= skip_level:
                skip_level = 0
            if not skip_level and _normalize_heading_title(heading.group(2)) in (
                _NONCLAIM_SECTION_TITLES
            ):
                skip_level = level
                continue  # drop the excluded heading line itself
        if skip_level:
            continue
        out.append(line)
    return "".join(out)


def extract_claims(
    text: str,
    *,
    artifact_path: str,
    backend: Any,
    model: str | None,
    repo_root: Path,
) -> list[Claim]:
    """Extract check-worthy claims from ``text`` via one LLM call.

    Returns a list of :class:`Claim` objects with ``status=PENDING``.
    On any failure (backend error, unparseable reply, missing prompt) returns
    ``[]`` and logs a warning — a failed extraction must not crash the pipeline.
    """
    from llmxive.agents.prompts import load_prompt
    from llmxive.backends.base import ChatMessage
    from llmxive.config import repo_root as _real_repo_root

    # Load the extraction prompt (prefer repo_root, fall back to real checkout).
    try:
        try:
            prompt_block = load_prompt(_PROMPT_PATH, repo_root=repo_root)
        except FileNotFoundError:
            prompt_block = load_prompt(_PROMPT_PATH, repo_root=_real_repo_root())
    except Exception as exc:
        logger.warning("claim_extract: prompt not found (%s); skipping extraction", exc)
        return []

    # Exclude citation/survey sections (References, Related Work, …) so their
    # citation years and titles are never extracted as the document's own claims.
    text = strip_nonclaim_sections(text)

    messages = [
        ChatMessage(
            role="system",
            content=(
                "You extract check-worthy, externally-attributable claims "
                "from scientific documents.\n\n" + prompt_block
            ),
        ),
        ChatMessage(
            role="user",
            content=(
                "# Document to extract claims from\n\n"
                + text
                + "\n\n# Task\n\nExtract claims per the contract above. "
                "Return only the YAML document."
            ),
        ),
    ]

    try:
        response = _chat_reasoning_safe(backend, messages, model or _DEFAULT_MODEL)
        reply = getattr(response, "text", "") or ""
        if not reply.strip():
            raise ValueError("extraction reply was empty")
    except Exception as exc:
        logger.warning(
            "claim_extract: LLM call failed (%s: %s); returning []",
            type(exc).__name__, exc,
        )
        return []

    # Parse the raw reply.
    raw_claims = _parse_extraction_reply(reply, artifact_path)

    # Post-parse deterministic filter.
    filtered_texts = _filter_check_worthy([c.raw_text for c in raw_claims])
    filtered_set = set(filtered_texts)
    return [c for c in raw_claims if c.raw_text in filtered_set]


__all__ = [
    "_filter_check_worthy",
    "extract_claims",
    "strip_nonclaim_sections",
    "tolerant_field_entries",
]
