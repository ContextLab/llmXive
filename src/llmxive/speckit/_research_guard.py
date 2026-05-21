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

# References we extract from research.md (FR-006).
_URL_RE = re.compile(r"https?://[^\s<>\)\]\"'}]+", re.IGNORECASE)
_ARXIV_RE = re.compile(r"\barxiv:\s*([0-9]{4}\.[0-9]{4,5}(?:v[0-9]+)?|[a-z\-]+(?:\.[A-Z]{2})?/[0-9]{7})", re.IGNORECASE)
_DOI_RE = re.compile(r"\bdoi:\s*(10\.[0-9]{4,9}/[^\s<>\)\]\"'}]+)", re.IGNORECASE)

# Trailing punctuation that markdown commonly glues onto a URL (e.g. a URL at
# the end of a sentence). Stripped before the reachability probe.
_TRAILING_PUNCT = ".,;:!?"


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
    """Raised on a data-model.md <-> contracts/ mismatch (FR-007)."""

    def __init__(self, missing_schemas: list[str], orphan_schemas: list[str]):
        self.missing_schemas = list(missing_schemas)
        self.orphan_schemas = list(orphan_schemas)
        parts: list[str] = []
        if self.missing_schemas:
            parts.append(
                f"entities with no contracts/ schema: {sorted(self.missing_schemas)}"
            )
        if self.orphan_schemas:
            parts.append(
                f"contracts/ schemas with no data-model.md entity: {sorted(self.orphan_schemas)}"
            )
        super().__init__(
            "data-model.md <-> contracts/ mismatch (FR-007): " + "; ".join(parts)
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


def _probe(url: str, *, timeout: int) -> None:
    """HEAD-then-GET-range probe; accept final status 200-399 only.

    Raises:
        UnreachableReference: on any 4xx/5xx, timeout, DNS/connection
            failure, or malformed URL.
    """
    if not (url.lower().startswith("http://") or url.lower().startswith("https://")):
        raise UnreachableReference(url, "malformed URL (no http(s):// scheme)")

    def _request(method: str, extra_headers: dict[str, str] | None = None):
        headers = {"User-Agent": _USER_AGENT}
        if extra_headers:
            headers.update(extra_headers)
        req = urllib.request.Request(url, method=method, headers=headers)
        # ``urlopen`` raises HTTPError for >=400; 3xx is followed by the
        # default redirect handler, so a final-status read yields 200-399.
        return urllib.request.urlopen(req, timeout=timeout)

    try:
        try:
            resp = _request("HEAD")
        except urllib.error.HTTPError as he:
            # Some servers reject HEAD with 405/501 — fall back to a tiny GET.
            if he.code in (405, 501):
                resp = _request("GET", {"Range": "bytes=0-0"})
            else:
                raise
        status = getattr(resp, "status", None) or resp.getcode()
        resp.close()
        if status is None or not (200 <= status < 400):
            raise UnreachableReference(url, f"final status {status} (not 2xx/3xx)")
    except UnreachableReference:
        raise
    except urllib.error.HTTPError as he:
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


def _schema_names(files: dict[str, str]) -> set[str]:
    """Parse schema names from contracts/*.yaml filenames + yaml title/$id."""
    names: set[str] = set()
    for key in _contracts_keys(files):
        stem = key.replace("\\", "/").split("/")[-1]
        for suffix in (".schema.yaml", ".schema.yml", ".yaml", ".yml"):
            if stem.lower().endswith(suffix):
                stem = stem[: -len(suffix)]
                break
        norm = _normalize(stem)
        if norm:
            names.add(norm)
        # Also mine the YAML body for title / $id.
        try:
            doc = yaml.safe_load(files[key])
        except yaml.YAMLError:
            doc = None
        if isinstance(doc, dict):
            for field in ("title", "$id", "name"):
                val = doc.get(field)
                if isinstance(val, str) and val.strip():
                    val_norm = _normalize(val.split("/")[-1])
                    if val_norm:
                        names.add(val_norm)
    return names


def assert_data_model_contracts_consistent(files: dict[str, str]) -> None:
    """FR-007: every data-model.md entity has a contracts/ schema and vice versa.

    No-op when there is no ``data-model.md`` in ``files`` (the FR-005 guard
    already requires its presence; this guard only runs the consistency check
    when both sides exist).

    Raises:
        InconsistentDataModel: with the missing-schema / orphan-schema lists.
    """
    data_model = files.get("data-model.md")
    if data_model is None or not data_model.strip():
        return

    entities = _data_model_entities(data_model)
    schemas = _schema_names(files)

    # A schema name is satisfied by an entity if either contains the other
    # (handles "Plan Artifact Set" entity vs "plan-artifact" schema stems).
    def _matched(target: str, pool: set[str]) -> bool:
        for other in pool:
            if target == other or target in other or other in target:
                return True
        return False

    missing_schemas = sorted(e for e in entities if not _matched(e, schemas))
    orphan_schemas = sorted(s for s in schemas if not _matched(s, entities))

    if missing_schemas or orphan_schemas:
        raise InconsistentDataModel(missing_schemas, orphan_schemas)


__all__ = [
    "IncompleteArtifactSet",
    "InconsistentDataModel",
    "UnreachableReference",
    "assert_artifact_set_complete",
    "assert_data_model_contracts_consistent",
    "assert_urls_reachable",
]
