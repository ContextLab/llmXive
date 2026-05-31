"""Factual-grounding verification pass (spec 015 / #239 / F-19).

WHY THIS EXISTS (the gap F-18 left open)
----------------------------------------
F-18's :mod:`llmxive.agents.citation_guard` verifies that a *reference resolves*
— a DOI/arXiv/URL exists — and flags unresolvable ones ``[UNVERIFIED: ...]`` (a
hard-block via F-18c). It does NOT catch two distinct fabrications the PROJ-552
trail exhibited:

  (a) a WRONG NUMBER attached to an otherwise-plausible citation, and
  (b) a FREE-TEXT author-year citation with NO resolvable identifier.

The real bug: a reviewer flagged the (CORRECT) knot count ``9,988`` as
"implausibly high"; the convergence reviser "resolved" the concern by
FABRICATING a wrong number (``1,296``) attached to a free-text citation
("Kauffman & Lambropoulou 2004") — and the panel PASSED it because F-18 only
checks reference *existence*, not whether the cited source *substantiates the
claim*. F-19 closes that gap with a heavy factual-grounding pass.

WHAT IT DOES
------------
For a produced document + a backend, it:

1. **Extracts** (LLM, "heavy"): every factual claim EXPLICITLY ATTRIBUTED TO AN
   EXTERNAL SOURCE — a statistic/number/empirical fact appearing WITH a citation
   or phrased "per/from/according to <author year / DOI / arXiv / URL>". A strict
   SCOPE GUARD biases hard toward precision: design parameters, thresholds
   (``p<0.05``, ``R²≥0.05``, ``1200x900``), requirement/task ids, dates, and any
   uncited number are NEVER extracted — a spec is full of legitimate uncited
   numbers that must pass untouched. (See the prompt block.)

2. **Grounds** each claim (real HTTP):
   * free-text-only source (no resolvable DOI/arXiv/URL) → UNGROUNDED → flag
     (this alone catches the trail's case);
   * resolvable source unreachable → flag;
   * resolvable + reachable → fetch the source's title/abstract and check
     grounding (reusing :func:`librarian.verify.verify_citation`'s summary
     grounding with the claim text as the ``summary``); AND when the claim has a
     NUMBER, require that exact number (or an obviously-equivalent form) to
     appear in the fetched source text. If neither grounds → flag.

3. **Rewrites**: flagged claims become ``[UNVERIFIED: ...]`` using the SAME F-18
   marker (:data:`citation_guard.UNVERIFIED_MARKER_PREFIX`), so the existing
   F-18c gates (engine + advancement + paper_complete) hard-block them — no new
   gate is invented. Idempotent; surrounding prose preserved.

DECOMPOSITION (testable without the network — no mocks)
-------------------------------------------------------
* :func:`apply_grounding_verdicts` — PURE rewriter (no I/O). Given parsed claims
  + grounding verdicts, marks exactly the ungrounded claims. This is what the
  offline unit tests exercise.
* :func:`classify_source` — PURE. Maps a source string to a resolvable
  (kind, value) or ``(None, None)`` for free-text-only.
* :func:`extract_cited_claims` — the LLM extraction (one backend call).
* :func:`ground_claim` — the network grounding of one claim (real HTTP).
* :func:`verify_grounding_and_clean` — the orchestrator that wires them.

Real calls only; bounded timeouts; never crash a revision. On a HARD error the
policy is to FLAG (or fail-loud-log), NEVER to silently accept — a verification
that itself failed must not be read as "grounded".
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from llmxive.agents.citation_guard import (
    UNVERIFIED_MARKER_PREFIX,
    GuardReport,
    _inside_marker,
)
from llmxive.agents.prompts import load_prompt
from llmxive.types import CitationKind

logger = logging.getLogger(__name__)

_EXTRACTION_BLOCK_PATH = "agents/prompts/_shared/factual_grounding_extraction_block.md"

# qwen3.5-122b (default panel/reviser model) is a reasoning model whose hidden
# chain-of-thought counts against the response budget; mirror F-13's
# reasoning-safe budget so the extraction call is not truncated.
_REASONING_MAX_TOKENS = 131_072

# The repo-wide default chat model (mirrors librarian/* + reviser fallbacks).
# Real backends (Dartmouth) require ``model`` as a non-optional kwarg, so when a
# caller threads ``model=None`` (the reviser path may, see ``spec_reviser`` which
# itself falls back to this) the extraction call resolves to this default rather
# than crashing with a missing-kwarg TypeError.
_DEFAULT_MODEL = "qwen.qwen3.5-122b"


@dataclass(frozen=True, slots=True)
class CitedClaim:
    """A factual claim explicitly attributed to an external source.

    ``claim_text`` is the verbatim sentence/phrase making the claim (used to
    locate it in the doc for rewriting and as the grounding "summary").
    ``number`` is the salient numeric value (digits only) when the claim hinges
    on a number, else ``None``. ``source_str`` is the source attribution copied
    verbatim from the doc. ``source_kind`` / ``source_value`` are the resolvable
    identifier parsed out of ``source_str`` (``None`` when the source is
    free-text-only — e.g. an author-year citation with no DOI/arXiv/URL).
    """

    claim_text: str
    number: str | None = None
    source_str: str = ""
    source_kind: CitationKind | None = None
    source_value: str | None = None


@dataclass(frozen=True, slots=True)
class GroundingVerdict:
    """Per-claim grounding outcome the rewriter acts on.

    ``ok=True`` means the cited source substantiates the claim (leave it
    untouched). ``ok=False`` means it does not (free-text-only source,
    unreachable source, or the source does not contain the claim/number) — the
    rewriter marks the claim ``[UNVERIFIED: <claim> — <reason>]``.
    """

    claim: CitedClaim
    ok: bool
    reason: str = ""


# --- source classification (PURE) -------------------------------------------

_ARXIV_IN_TEXT_RE = re.compile(r"arXiv:\s*(?P<id>[0-9][0-9A-Za-z.\-/]*)", re.IGNORECASE)
_DOI_IN_TEXT_RE = re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+", re.IGNORECASE)
_MD_LINK_IN_TEXT_RE = re.compile(r"\[[^\]]+\]\((?P<url>https?://[^\s)]+)\)")
_BARE_URL_IN_TEXT_RE = re.compile(r"https?://[^\s<>()\[\]\"']+", re.IGNORECASE)


def classify_source(source_str: str) -> tuple[CitationKind | None, str | None]:
    """Parse a resolvable identifier out of a source attribution string.

    Returns ``(kind, value)`` for the FIRST resolvable identifier found — an
    arXiv id, a DOI, or a URL (markdown-link target preferred over a bare URL).
    Returns ``(None, None)`` when the source is free-text-only (e.g. an
    author-year citation such as ``"Kauffman & Lambropoulou 2004"``), which is
    UNGROUNDABLE — the source cannot be fetched to substantiate the claim.

    PURE: no I/O. A malformed arXiv id (``2402.13``) is still returned as
    ARXIV-kind — the resolver will 404 it (→ flagged) downstream, matching F-18.
    """
    s = source_str or ""
    m = _ARXIV_IN_TEXT_RE.search(s)
    if m:
        return CitationKind.ARXIV, m.group("id").rstrip(".,;:)")
    m = _DOI_IN_TEXT_RE.search(s)
    if m:
        return CitationKind.DOI, m.group(0).rstrip(".,;:)")
    m = _MD_LINK_IN_TEXT_RE.search(s)
    if m:
        return CitationKind.URL, m.group("url").rstrip(".,;:")
    m = _BARE_URL_IN_TEXT_RE.search(s)
    if m:
        return CitationKind.URL, m.group(0).rstrip(".,;:")
    return None, None


# --- number-equivalence (PURE) ----------------------------------------------

_DIGITS_RE = re.compile(r"\d")


def _normalize_number(value: str) -> str:
    """Reduce a numeric token to bare digits (drop separators/units/sign)."""
    return "".join(_DIGITS_RE.findall(value or ""))


_NUMBER_TOKEN_RE = re.compile(r"[-+]?\d[\d,_ ]*(?:\.\d+)?")


def _clean_number_token(value: str) -> str | None:
    """Extract the salient numeric token, preserving a decimal point.

    Strips thousands separators (``,`` / ``_`` / spaces) and surrounding units
    but KEEPS a trailing decimal (``28.4`` stays ``28.4``, ``9,988`` → ``9988``)
    so decimal grounding works (digit-only normalization would turn ``28.4`` into
    ``284`` and falsely fail to ground). Returns ``None`` when no number found.
    """
    m = _NUMBER_TOKEN_RE.search(value or "")
    if not m:
        return None
    tok = m.group(0).strip()
    int_part, dot, frac = tok.partition(".")
    int_digits = "".join(ch for ch in int_part if ch.isdigit())
    if not int_digits:
        return None
    return f"{int_digits}.{frac}" if dot and frac else int_digits


def number_appears_in(number: str, text: str) -> bool:
    """True iff ``number`` (or an obviously-equivalent form) appears in ``text``.

    Matches:
    * the number's ORIGINAL form (preserving a decimal point — ``28.4`` matches
      ``28.4``, not the digit-run ``284``), as a standalone numeric token;
    * the bare-digit form (``9988``) for integers;
    * common thousands-separator forms (``9,988`` / ``9 988``).

    Conservative: every form must match as a whole numeric token (digit
    boundaries), never as a loose substring, so ``988`` does not match inside
    ``19884`` and ``284`` does not spuriously match ``28.4``.
    """
    haystack = text or ""
    # 1) Original form, as a standalone numeric token (keeps decimals/sign).
    raw = (number or "").strip()
    raw_token = raw.lstrip("+-").strip()
    if raw_token and re.search(
        rf"(?<![\d.]){re.escape(raw_token)}(?![\d])", haystack
    ):
        return True

    norm = _normalize_number(number)
    if not norm:
        return False
    # 2) For INTEGER claims only, accept the bare-digit + grouped-thousands forms.
    # Skip this for decimals (raw contained a '.'), where '284' must NOT ground
    # '28.4' — that is the decimal-vs-digit-run false-match this guards against.
    if "." in raw_token:
        return False
    if re.search(rf"(?<!\d){re.escape(norm)}(?!\d)", haystack):
        return True
    if len(norm) > 3:
        grouped = _group_thousands(norm)
        for sep in (",", " "):
            token = grouped.replace(",", sep)
            if re.search(rf"(?<![\d.]){re.escape(token)}(?![\d])", haystack):
                return True
    return False


def _group_thousands(digits: str) -> str:
    out: list[str] = []
    for i, ch in enumerate(reversed(digits)):
        if i and i % 3 == 0:
            out.append(",")
        out.append(ch)
    return "".join(reversed(out))


# --- pure rewriter ----------------------------------------------------------


def apply_grounding_verdicts(
    text: str, verdicts: list[GroundingVerdict]
) -> tuple[str, GuardReport]:
    """PURE rewriter: mark UNGROUNDED claims in ``text`` ``[UNVERIFIED: ...]``.

    For each ``ok=False`` verdict, the claim's verbatim text is replaced in
    place by ``<claim> [UNVERIFIED: <number-or-claim-snippet> — <reason>]`` (the
    claim prose is preserved; the marker is appended so the assertion stays
    readable but the fabrication is greppable and hard-blocked by F-18c).
    Grounded (``ok=True``) claims are left byte-for-byte untouched. Idempotent:
    a claim already followed by an ``[UNVERIFIED: ...]`` marker is not re-marked.

    Returns ``(cleaned_text, GuardReport)``. Reuses the F-18 marker prefix so the
    same gates that block fabricated references also block ungrounded claims.
    """
    report = GuardReport()
    cleaned = text
    for v in verdicts:
        if v.ok:
            report.verified_count += 1
            continue
        before = cleaned
        cleaned = _flag_claim(cleaned, v)
        if cleaned != before:
            report.flagged_count += 1
            label = v.claim.number or _snippet(v.claim.claim_text)
            report.flagged_values.append(label)
            report.flagged_reasons[label] = v.reason
    return cleaned, report


def _snippet(claim_text: str, *, limit: int = 60) -> str:
    one = " ".join((claim_text or "").split())
    return one if len(one) <= limit else one[: limit - 1].rstrip() + "…"


def _marker_for(v: GroundingVerdict) -> str:
    label = v.claim.number or _snippet(v.claim.claim_text)
    if v.reason:
        return f"{UNVERIFIED_MARKER_PREFIX} {label} — {v.reason}]"
    return f"{UNVERIFIED_MARKER_PREFIX} {label}]"


def _flag_claim(text: str, v: GroundingVerdict) -> str:
    """Append the ``[UNVERIFIED: ...]`` marker after the claim's first unmarked
    occurrence. Locating by the claim's number (the load-bearing fabricated
    token) is most robust; fall back to the literal claim text.
    """
    marker = _marker_for(v)
    claim = v.claim

    # Prefer anchoring on the number token (the fabricated value) when present —
    # it is short, stable, and uniquely identifies the claim in the doc.
    if claim.number:
        anchor_re = _number_anchor_re(claim.number)
        if anchor_re is not None:
            new_text, n = _append_marker_after(text, anchor_re, marker)
            if n:
                return new_text

    # Fall back to the verbatim claim text.
    literal = (claim.claim_text or "").strip()
    if literal and literal in text and not _followed_by_marker(text, literal):
        idx = text.index(literal)
        end = idx + len(literal)
        return text[:end] + " " + marker + text[end:]
    return text


def _number_anchor_re(number: str) -> re.Pattern[str] | None:
    raw = (number or "").strip().lstrip("+-")
    forms: list[str] = []
    if raw:
        # original form first (preserves a decimal point: 28.4 stays 28.4)
        forms.append(rf"(?<![\d.]){re.escape(raw)}(?![\d])")
    norm = _normalize_number(number)
    if norm and "." not in raw:
        forms.append(rf"(?<!\d){re.escape(norm)}(?!\d)")
        if len(norm) > 3:
            grouped = re.escape(_group_thousands(norm))
            forms.append(grouped.replace(",", "[ ,]"))
    if not forms:
        return None
    return re.compile("|".join(forms))


def _append_marker_after(
    text: str, anchor_re: re.Pattern[str], marker: str
) -> tuple[str, int]:
    for m in anchor_re.finditer(text):
        end = m.end()
        if _inside_marker(text, m.start()):
            continue
        if _marker_immediately_follows(text, end):
            continue
        return text[:end] + " " + marker + text[end:], 1
    return text, 0


def _marker_immediately_follows(text: str, pos: int) -> bool:
    """True if an ``[UNVERIFIED: ...]`` marker already follows ``pos`` (within the
    same clause), so we don't double-mark a claim on re-run (idempotency)."""
    tail = text[pos : pos + 200]
    idx = tail.find(UNVERIFIED_MARKER_PREFIX)
    if idx == -1:
        return False
    # only treat as "already marked" when nothing but whitespace/punctuation/
    # the rest of this short clause sits between the anchor and the marker
    return "\n\n" not in tail[:idx]


def _followed_by_marker(text: str, literal: str) -> bool:
    idx = text.find(literal)
    if idx == -1:
        return False
    return _marker_immediately_follows(text, idx + len(literal))


# --- LLM extraction ---------------------------------------------------------


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


def _cited_claim_from_fields(entry: dict[str, str]) -> CitedClaim | None:
    """Map one recovered ``{claim_text, source, number}`` dict to a CitedClaim.

    Returns ``None`` when the entry lacks the required ``claim_text``+``source``
    (an unattributed claim is out of F-19 scope).
    """
    claim_text = (entry.get("claim_text") or "").strip()
    source_str = (entry.get("source") or "").strip()
    if not claim_text or not source_str:
        return None
    num_raw = entry.get("number")
    number = (
        _clean_number_token(str(num_raw))
        if num_raw not in (None, "", "null")
        else None
    )
    kind, value = classify_source(source_str)
    return CitedClaim(
        claim_text=claim_text,
        number=number or None,
        source_str=source_str,
        source_kind=kind,
        source_value=value,
    )


def _recover_cited_claims(raw: str) -> list[CitedClaim]:
    """Tolerant recovery when strict YAML fails / yields no usable claims.

    Reuses the SHARED line-oriented field parser
    (:func:`claims.extract.tolerant_field_entries`) — the SAME recovery the claim
    extractor uses — so an embedded-quote reply (a cited title like
    ``"A Census of Knots."`` that breaks YAML's quoted-scalar grammar) recovers
    the cited claim here too instead of silently dropping every claim.
    """
    from llmxive.claims.extract import tolerant_field_entries

    out: list[CitedClaim] = []
    for entry in tolerant_field_entries(raw):
        claim = _cited_claim_from_fields(entry)
        if claim is not None:
            out.append(claim)
    if out:
        logger.info("grounding-guard: tolerant recovery parsed %d claim(s)", len(out))
    return out


def _parse_extraction_reply(reply_text: str) -> list[CitedClaim]:
    """Parse the model's YAML extraction reply into :class:`CitedClaim`s.

    Strips a ```yaml fence, requires a ``claims`` list mapping. Each entry must
    carry ``claim_text`` + ``source``; ``number`` is optional. Resolvable ids in
    ``source`` are parsed here via :func:`classify_source`.

    Tolerant: on a YAML parse failure OR a structurally-unusable result (no
    ``claims`` list, or every entry mangled by an embedded quote), falls back to
    the SHARED :func:`tolerant_field_entries` recovery instead of dropping every
    claim — the same embedded-quote robustness the claim extractor has. Returns
    an EMPTY list (the strict-path "no claims" outcome, e.g. ``claims: []``) only
    when both the strict and tolerant paths genuinely find nothing.
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
            "grounding-guard: YAML parse failed (%s); attempting tolerant recovery",
            exc,
        )
        return _recover_cited_claims(raw)

    if not isinstance(obj, dict) or "claims" not in obj:
        return _recover_cited_claims(raw)
    claims_raw = obj.get("claims")
    # An explicit empty list is a valid "no claims" outcome — do NOT recover.
    if claims_raw == []:
        return []
    if not isinstance(claims_raw, list):
        return _recover_cited_claims(raw)

    out: list[CitedClaim] = []
    for entry in claims_raw:
        if not isinstance(entry, dict):
            continue
        claim = _cited_claim_from_fields(
            {str(k): ("" if v is None else str(v)) for k, v in entry.items()}
        )
        if claim is not None:
            out.append(claim)
    # If strict YAML parsed but produced no usable claims (e.g. every entry's
    # text was truncated by an embedded quote), try the tolerant path as a
    # backstop rather than dropping everything.
    if not out:
        return _recover_cited_claims(raw)
    return out


def extract_cited_claims(
    text: str, *, backend: Any, model: str | None, repo_root: Path
) -> list[CitedClaim]:
    """Extract source-attributed factual claims via ONE LLM call (heavy).

    On ANY failure (backend error, empty/unparseable reply, missing prompt
    block) returns ``[]`` and logs a warning — a failed EXTRACTION must not
    crash the pipeline, and an empty list simply means "no claims to ground"
    (the grounding pass then no-ops). NOTE this is biased toward precision by
    the prompt's scope guard, NOT toward silent acceptance: the GROUNDING step
    (not extraction) is where a hard verification failure flags.
    """
    from llmxive.backends.base import ChatMessage
    from llmxive.config import repo_root as _real_repo_root

    # The extraction prompt block is a repo-installed asset that lives under the
    # real checkout, NOT the per-run cache ``repo_root`` (which may be a tmp dir
    # for isolation). Resolve it under ``repo_root`` first, then fall back to the
    # real repo root so prompt loading never depends on the cache location.
    try:
        try:
            block = load_prompt(_EXTRACTION_BLOCK_PATH, repo_root=repo_root)
        except FileNotFoundError:
            block = load_prompt(_EXTRACTION_BLOCK_PATH, repo_root=_real_repo_root())
    except Exception as exc:
        logger.warning("grounding-guard: extraction prompt missing (%s); skipping", exc)
        return []
    messages = [
        ChatMessage(role="system", content="You extract source-attributed factual claims for grounding.\n\n" + block),
        ChatMessage(role="user", content="# Document to audit\n\n" + text + "\n\n# Task\n\nExtract the claims per the contract above; return the single YAML document."),
    ]
    try:
        response = _chat_reasoning_safe(backend, messages, model or _DEFAULT_MODEL)
        reply = getattr(response, "text", "") or ""
        if not reply.strip():
            raise ValueError("extraction reply was empty")
        return _parse_extraction_reply(reply)
    except Exception as exc:
        logger.warning(
            "grounding-guard: claim extraction failed (%s: %s); no claims grounded this pass",
            type(exc).__name__, exc,
        )
        return []


# --- network grounding of one claim -----------------------------------------


def _service_ground(
    claim: CitedClaim, *, backend: Any, model: str | None, repo_root: Path
) -> GroundingVerdict:
    """Lazy seam onto the full-text grounding service (F-19 v2).

    Imported function-locally to avoid an import cycle: ``grounding.service``
    (and ``grounding.entailment``) import names FROM this module at their module
    top, so this module must not import the service at import time.
    """
    from llmxive.grounding.service import ground_cited_claim

    return ground_cited_claim(claim, backend=backend, model=model, repo_root=repo_root)


def ground_claim(
    claim: CitedClaim,
    *,
    backend: Any,
    model: str | None,
    repo_root: Path,
) -> GroundingVerdict:
    """Verify the cited source SUBSTANTIATES the claim via the full-text service.

    Free-text-only sources (no resolvable DOI/arXiv/URL) short-circuit to a FLAG
    here — there is nothing to fetch, so the service is never consulted (this
    alone catches the PROJ-552 trail's free-text fabrication). Resolvable sources
    delegate the network retrieval + entailment grounding to
    :func:`llmxive.grounding.service.ground_cited_claim`.
    """
    if claim.source_kind is None or claim.source_value is None:
        return GroundingVerdict(
            claim=claim, ok=False,
            reason="cited source is free-text only (no resolvable DOI/arXiv/URL); cannot substantiate this claim/number",
        )
    return _service_ground(claim, backend=backend, model=model, repo_root=repo_root)


# --- orchestrator -----------------------------------------------------------


def verify_grounding_and_clean(
    text: str, *, backend: Any, model: str | None, repo_root: Path
) -> tuple[str, GuardReport]:
    """Extract → ground (real HTTP) → mark ungrounded claims ``[UNVERIFIED]``.

    The full F-19 pass for one document. Returns ``(cleaned_text, GuardReport)``.
    Never raises — a failed extraction yields no claims (no-op); a failed
    grounding of an individual claim FLAGS it (no silent pass). Reuses the F-18
    marker so flagged claims hard-block via the existing F-18c gates.
    """
    claims = extract_cited_claims(text, backend=backend, model=model, repo_root=repo_root)
    if not claims:
        return text, GuardReport()
    verdicts = [
        ground_claim(c, backend=backend, model=model, repo_root=repo_root)
        for c in claims
    ]
    return apply_grounding_verdicts(text, verdicts)


__all__ = [
    "CitedClaim",
    "GroundingVerdict",
    "apply_grounding_verdicts",
    "classify_source",
    "extract_cited_claims",
    "ground_claim",
    "number_appears_in",
    "verify_grounding_and_clean",
]
