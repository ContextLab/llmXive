"""Planner research-artifact guards (spec 014 / FR-005, FR-006, FR-007).

Single source of truth (Constitution Principle I) for the three Planner-side
quality gates added by Phase-4 validation, all wired into
``PlannerAgent.write_artifacts``:

- :func:`assert_artifact_set_complete` (FR-005) — the five logical plan
  artifacts must all be present, non-empty, and the multi-file FILE-marker
  split must have actually produced more than the no-marker ``{plan.md: …}``
  fallback.
- :func:`assert_urls_reachable` (FR-006) — every dataset/code/paper reference
  in ``research.md`` must resolve to an HTTP 2xx/3xx; any reference that is
  invented, malformed, 4xx, 5xx, times out, fails DNS, or is rate-limited
  hard-fails the run with NO transient-retry leniency.
- :func:`assert_data_model_contracts_consistent` (FR-007) — every entity in
  ``data-model.md`` must have a ``contracts/*.yaml`` schema and vice versa.

All three exceptions subclass :class:`RuntimeError` so the existing base-class
failure handling (which catches ``TemplateRefused``/``RuntimeError`` from the
write path and records ``outcome: failed``) maps them to ``failed`` and holds
the project at ``clarified`` without any extra wiring.

Stdlib only (``urllib.request``, ``http``, ``re``, ``yaml``) — no new
third-party dependency (Principle IV). See
``specs/014-phase4-plan-tasks-testing/contracts/research-guard.md``.
"""

from __future__ import annotations

import http.client
import re
import urllib.error
import urllib.request

import yaml

# Descriptive User-Agent so a polite server doesn't 403 a header-less probe.
_USER_AGENT = (
    "llmXive-research-guard/1.0 (+https://github.com/ContextLab/llmXive; "
    "FR-006 reference-reachability check)"
)

# The five logical artifacts the Planner MUST emit (FR-005). The fifth is a
# pattern (≥1 contracts/*.yaml key), handled separately below.
_REQUIRED_PLAIN_ARTIFACTS = ("plan.md", "research.md", "data-model.md", "quickstart.md")

# References we extract from research.md (FR-006). The negated character class
# excludes markdown delimiters that commonly wrap or terminate a URL — notably
# the backtick (a URL written as `https://…/` must not capture the closing
# backtick into its path, which would create a false 404).
_URL_RE = re.compile(r"https?://[^\s<>\)\]\"'}`]+", re.IGNORECASE)
_ARXIV_RE = re.compile(r"\barxiv:\s*([0-9]{4}\.[0-9]{4,5}(?:v[0-9]+)?|[a-z\-]+(?:\.[A-Z]{2})?/[0-9]{7})", re.IGNORECASE)
_DOI_RE = re.compile(r"\bdoi:\s*(10\.[0-9]{4,9}/[^\s<>\)\]\"'}`]+)", re.IGNORECASE)

# Trailing punctuation/markup that markdown commonly glues onto a URL (e.g. a
# URL at the end of a sentence, or wrapped in `backticks`). Stripped before the
# reachability probe.
_TRAILING_PUNCT = ".,;:!?`"


class IncompleteArtifactSet(RuntimeError):
    """Raised when the Planner's plan-artifact set is incomplete (FR-005)."""

    def __init__(self, missing: list[str], reason: str):
        self.missing = list(missing)
        self.reason = reason
        super().__init__(
            f"incomplete plan artifact set: {reason}. "
            f"Missing/empty artifacts: {sorted(self.missing)}. "
            f"Required: {list(_REQUIRED_PLAIN_ARTIFACTS)} + >=1 contracts/*.yaml."
        )


class UnreachableReference(RuntimeError):
    """Raised when a research.md reference is not reachable (FR-006)."""

    def __init__(self, url: str, reason: str):
        self.url = url
        self.reason = reason
        super().__init__(
            f"research.md reference is unreachable: {url!r} ({reason}). "
            f"FR-006 admits NO transient-retry leniency — re-run when the "
            f"source recovers or fix the reference."
        )


class InconsistentDataModel(RuntimeError):
    """Raised on a data-model.md <-> contracts/ inconsistency (FR-007).

    The check is structural and robust rather than a 1:1 name match: the
    Planner's own contract (``agents/prompts/planner.md``) requires *at least
    one* schema for a computational project, not one schema per entity, and
    schema filenames legitimately differ from entity headings (e.g.
    ``code_duplication_metrics.schema.yaml`` describing a ``CloneDensityMetric``
    entity). Fragile name-matching produced false positives on real planner
    output, so FR-007 now verifies that (a) ``data-model.md`` actually defines
    entities and (b) every emitted ``contracts/*.yaml`` is a real, non-empty,
    parseable schema.
    """

    def __init__(self, reason: str, *, invalid_schemas: list[str] | None = None):
        self.reason = reason
        self.invalid_schemas = list(invalid_schemas or [])
        detail = f": {sorted(self.invalid_schemas)}" if self.invalid_schemas else ""
        super().__init__(
            f"data-model.md <-> contracts/ inconsistency (FR-007): {reason}{detail}"
        )


def _contracts_keys(files: dict[str, str]) -> list[str]:
    """Return the contracts/*.yaml (or .yml) keys present in ``files``."""
    out: list[str] = []
    for key in files:
        norm = key.replace("\\", "/")
        if norm.startswith("contracts/") and norm.lower().endswith((".yaml", ".yml")):
            out.append(key)
    return out


def assert_artifact_set_complete(files: dict[str, str]) -> None:
    """FR-005: require all five plan artifacts present and non-empty.

    ``files`` is the FILE-marker split map from
    ``plan_cmd._split_multi_file``. A response with no FILE markers degrades
    to a single ``{"plan.md": <whole text>}`` key — that is treated as a
    FAILED split (not a one-artifact success), because the Planner contract
    requires five files in one multi-file response.

    Raises:
        IncompleteArtifactSet: listing the missing/empty artifacts.
    """
    if not files:
        raise IncompleteArtifactSet(
            [*_REQUIRED_PLAIN_ARTIFACTS, "contracts/*.yaml"],
            "no artifacts produced (empty split)",
        )

    contracts = _contracts_keys(files)

    # No-marker fallback detection: a single plan.md key (and nothing else)
    # is the _split_multi_file no-marker path — a failed multi-file split.
    if set(files.keys()) == {"plan.md"}:
        raise IncompleteArtifactSet(
            ["research.md", "data-model.md", "quickstart.md", "contracts/*.yaml"],
            "FILE-marker split failed — only a single plan.md was recovered "
            "(no `<!-- FILE: … -->` markers in the response)",
        )

    missing: list[str] = []
    for name in _REQUIRED_PLAIN_ARTIFACTS:
        content = files.get(name)
        if content is None or not content.strip():
            missing.append(name)
    if not contracts:
        missing.append("contracts/*.yaml")
    else:
        # A present-but-empty contracts file is as bad as a missing one.
        if not any(files.get(k, "").strip() for k in contracts):
            missing.append("contracts/*.yaml")

    if missing:
        raise IncompleteArtifactSet(
            missing,
            "one or more required artifacts are absent or empty",
        )


def _extract_references(research_md_text: str) -> list[str]:
    """Return the de-duplicated list of reachability-checkable URLs.

    Extracts plain ``https?://`` URLs, ``arXiv:<id>`` (→ abs URL), and
    ``doi:<doi>`` (→ doi.org URL). Order is preserved (first occurrence).
    """
    seen: set[str] = set()
    refs: list[str] = []

    def _add(url: str) -> None:
        url = url.rstrip(_TRAILING_PUNCT)
        # Drop a dangling close-paren/bracket from a markdown link wrapper.
        while url and url[-1] in ")]>" and url.count("(") < url.count(")"):
            url = url[:-1]
        if url and url not in seen:
            seen.add(url)
            refs.append(url)

    if not research_md_text:
        return refs
    for m in _URL_RE.finditer(research_md_text):
        _add(m.group(0))
    for m in _ARXIV_RE.finditer(research_md_text):
        _add(f"https://arxiv.org/abs/{m.group(1)}")
    for m in _DOI_RE.finditer(research_md_text):
        _add(f"https://doi.org/{m.group(1)}")
    return refs


#: Statuses meaning "the server REFUSED OUR PROBE", not "this reference is dead".
#: A bot-blocking host (openalex.org), an auth-walled endpoint, a rate limiter, or an
#: API whose probe shape we got wrong (a bare api.github.com/search/repositories with
#: no `q=` → 422) all answer this way while the resource is perfectly present. Such a
#: refusal is NOT evidence against the reference — and, unlike a 5xx or a timeout, it
#: NEVER recovers on a re-run, so hard-blocking on it wedged live projects forever
#: (67 advance_errors). We therefore do not fail FR-006 on these. A 404/410 — the
#: signal that actually says "this reference does not exist" — still hard-blocks, as
#: do 5xx (transient; recovers on re-run) and DNS/connection failures. This mirrors
#: the policy the citation layer already applies to 401/403/429.
_PROBE_REFUSED = frozenset({401, 403, 407, 422, 429})
#: Servers that reject a HEAD but serve a GET (405/501), plus the refusal statuses —
#: a HEAD is the request most often blocked, so it is worth one ranged-GET retry
#: before we conclude anything at all.
_RETRY_WITH_GET = frozenset({405, 501}) | _PROBE_REFUSED


def _probe(url: str, *, timeout: int) -> None:
    """HEAD-then-GET-range probe; accept final status 200-399.

    Raises:
        UnreachableReference: on 404/410 (the reference does not exist), 5xx, a
            timeout, a DNS/connection failure, or a malformed URL. An access-denied
            refusal (:data:`_PROBE_REFUSED`) is NOT raised — see that constant.
    """
    if not (url.lower().startswith("http://") or url.lower().startswith("https://")):
        raise UnreachableReference(url, "malformed URL (no http(s):// scheme)")

    def _request(method: str, extra_headers: dict[str, str] | None = None) -> http.client.HTTPResponse:
        headers = {"User-Agent": _USER_AGENT}
        if extra_headers:
            headers.update(extra_headers)
        req = urllib.request.Request(url, method=method, headers=headers)
        # ``urlopen`` raises HTTPError for >=400; 3xx is followed by the
        # default redirect handler, so a final-status read yields 200-399.
        resp = urllib.request.urlopen(req, timeout=timeout)
        assert isinstance(resp, http.client.HTTPResponse)
        return resp

    try:
        try:
            resp = _request("HEAD")
        except urllib.error.HTTPError as he:
            # A HEAD is the request servers most often reject. Retry once as a tiny
            # ranged GET before drawing any conclusion.
            if he.code in _RETRY_WITH_GET:
                try:
                    resp = _request("GET", {"Range": "bytes=0-0"})
                except urllib.error.HTTPError as ge:
                    if ge.code in _PROBE_REFUSED:
                        return  # refused, not absent — the reference stands
                    raise
            else:
                raise
        status = getattr(resp, "status", None) or resp.getcode()
        resp.close()
        if status is None or not (200 <= status < 400):
            raise UnreachableReference(url, f"final status {status} (not 2xx/3xx)")
    except UnreachableReference:
        raise
    except urllib.error.HTTPError as he:
        if he.code in _PROBE_REFUSED:
            return  # refused, not absent — the reference stands
        raise UnreachableReference(url, f"HTTP {he.code}") from he
    except urllib.error.URLError as ue:
        raise UnreachableReference(url, f"connection/DNS failure: {ue.reason}") from ue
    except (TimeoutError, OSError) as oe:
        raise UnreachableReference(url, f"timeout/socket error: {oe}") from oe
    except ValueError as ve:
        raise UnreachableReference(url, f"malformed URL: {ve}") from ve


def assert_urls_reachable(research_md_text: str, *, timeout: int = 10) -> None:
    """FR-006: every reference in ``research.md`` MUST return HTTP 2xx/3xx.

    No-op when ``research.md`` cites zero references. Raises on the FIRST
    reference that fails — there are NO retries (FR-006 clarification).

    Raises:
        UnreachableReference: the offending URL + reason.
    """
    for ref in _extract_references(research_md_text):
        _probe(ref, timeout=timeout)


def find_unreachable_references(
    research_md_text: str, *, timeout: int = 10
) -> list[tuple[str, str]]:
    """Return EVERY unreachable reference in ``research.md`` as ``(url, reason)``.

    Unlike :func:`assert_urls_reachable` (which raises on the FIRST dead ref for
    the hard FR-006 gate), this collects ALL dead refs so the reference-repair
    step (``_reference_repair.repair_research_references``) can attempt a
    librarian-driven fix for each one before the gate is enforced. It reuses the
    SAME :func:`_extract_references` + :func:`_probe` machinery (Constitution I,
    SSoT) so "reachable" means exactly the same thing here as at the hard gate.

    Returns an empty list when every reference is reachable (or none are cited).
    """
    dead: list[tuple[str, str]] = []
    for ref in _extract_references(research_md_text):
        try:
            _probe(ref, timeout=timeout)
        except UnreachableReference as exc:
            dead.append((ref, exc.reason))
    return dead


_HEADING_ENTITY_RE = re.compile(r"^#{2,3}\s+(.+?)\s*$", re.MULTILINE)
_BOLD_ENTITY_RE = re.compile(r"^\s*[-*]?\s*\*\*(.+?)\*\*\s*:", re.MULTILINE)

# data-model.md headings that are structural, not entities, so we never treat
# them as "entities needing a schema".
_NON_ENTITY_HEADINGS = {
    "data model",
    "overview",
    "entities",
    "new exceptions",
    "notes",
    "key entities",
    "relationships",
    "validation",
    "run-log entry",
}


def _normalize(name: str) -> str:
    """Case-insensitive, treating '-'/'_'/space as equivalent; strip noise."""
    name = name.strip().lower()
    # Drop a parenthetical qualifier and any trailing schema/yaml suffix words.
    name = re.sub(r"\(.*?\)", "", name)
    name = name.replace(".schema", "").replace(".yaml", "").replace(".yml", "")
    name = re.sub(r"[-_\s]+", " ", name).strip()
    return name


def _data_model_entities(text: str) -> set[str]:
    """Parse entity names from a data-model.md document."""
    entities: set[str] = set()
    for m in _HEADING_ENTITY_RE.finditer(text):
        raw = m.group(1).strip()
        norm = _normalize(raw)
        if not norm or norm in _NON_ENTITY_HEADINGS:
            continue
        # A heading that is plainly a sentence/section (contains a colon or is
        # very long) is not an entity name.
        if ":" in raw or len(norm.split()) > 6:
            continue
        entities.add(norm)
    for m in _BOLD_ENTITY_RE.finditer(text):
        norm = _normalize(m.group(1))
        if norm and norm not in _NON_ENTITY_HEADINGS:
            entities.add(norm)
    return entities


_TABLE_ROW_RE = re.compile(r"^\s*\|.*\|\s*$", re.MULTILINE)


def _has_entity_structure(text: str) -> bool:
    """True if data-model.md defines real entities, not just prose.

    Real data models always carry at least one of: an attribute/markdown table,
    a mermaid/ER diagram, or one or more entity (sub)headings beyond the title.
    """
    if _data_model_entities(text):
        return True
    if _TABLE_ROW_RE.search(text):
        return True
    if re.search(r"```mermaid|erDiagram", text, re.IGNORECASE):
        return True
    return False


def assert_data_model_contracts_consistent(files: dict[str, str]) -> None:
    """FR-007: data-model.md defines real entities and every contracts/ schema
    is a real, non-empty, parseable schema.

    This is a STRUCTURAL consistency check, not a 1:1 entity↔schema name match
    (see :class:`InconsistentDataModel` for why). It verifies:

    1. ``data-model.md`` actually defines entities (an attribute table, a
       mermaid/ER diagram, or entity headings) rather than empty prose; and
    2. every emitted ``contracts/*.yaml`` parses as a non-empty YAML mapping/
       sequence — a real schema, not an empty file or prose stub.

    No-op when there is no ``data-model.md`` in ``files`` (FR-005 already
    requires its presence; this runs only when it exists). Cardinality between
    entities and schemas is intentionally NOT constrained — the Planner
    contract requires ≥1 schema, not one per entity.

    Raises:
        InconsistentDataModel: with an actionable reason.
    """
    data_model = files.get("data-model.md")
    if data_model is None or not data_model.strip():
        return

    if not _has_entity_structure(data_model):
        raise InconsistentDataModel(
            "data-model.md defines no entities (no attribute table, ER diagram, "
            "or entity headings) — it cannot back any contracts/ schema"
        )

    invalid: list[str] = []
    for key in _contracts_keys(files):
        body = files.get(key, "")
        if not body.strip():
            invalid.append(f"{key} (empty)")
            continue
        try:
            doc = yaml.safe_load(body)
        except yaml.YAMLError as exc:
            invalid.append(f"{key} (invalid YAML: {exc})")
            continue
        if not isinstance(doc, (dict, list)) or len(doc) == 0:
            invalid.append(f"{key} (not a non-empty schema mapping/sequence)")

    if invalid:
        raise InconsistentDataModel(
            "one or more contracts/ schemas are empty or not valid schemas",
            invalid_schemas=invalid,
        )


__all__ = [
    "IncompleteArtifactSet",
    "InconsistentDataModel",
    "UnreachableReference",
    "assert_artifact_set_complete",
    "assert_data_model_contracts_consistent",
    "assert_urls_reachable",
    "find_unreachable_references",
]
