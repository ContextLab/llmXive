"""Bridge: autonomous data-source discovery → the execution-fix loop.

When the dedicated execution stage finds a declared *data* deliverable missing
(e.g. ``data/processed/knots_cleaned.csv``), it usually means the project's data
loader has no real, programmatically-accessible source — the implementer, with
no search/verify ability, hallucinates a fake endpoint (observed on PROJ-552:
``katlas.org/api/v1/knot`` → 404). This module closes that gap: it derives the
project's data intent from its planning artifacts, runs
:func:`llmxive.librarian.data_source_discovery.discover_data_source` (web search
→ LLM proposal → HARD verification), caches the VERIFIED source, and renders a
feedback block naming the real package + a *working, executed* access recipe.
That block is injected into ``execution_feedback.md`` (which the implementer
already reads, spec 023 #25 FIX A), so the next implementer tick writes a loader
that fetches REAL data instead of guessing.
"""

from __future__ import annotations

import hashlib
import logging
import re
from datetime import UTC, datetime
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

_CACHE_NAME = "discovered_data_source.yaml"
_MAX_INTENT_CHARS = 1500

#: Bump to invalidate EVERY cached discovery record when the verification logic
#: changes (a stale "verified"/"none" computed by an older, weaker verifier must
#: not be trusted). Folded into the cache key so a version bump is a global miss.
VERIFIER_VERSION = "2"

#: A ``status == "none"`` (nothing discoverable) is re-searched only after this
#: many days AND only up to ``_NONE_MAX_RETRIES`` total attempts — so a genuinely
#: undiscoverable source isn't re-searched every tick, but a source that appears
#: LATER (a package published, a dataset uploaded) is eventually re-found instead
#: of being poisoned forever. A ``verified`` record is durable (never re-searched).
_NONE_TTL_DAYS = 7.0
_NONE_MAX_RETRIES = 3


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _denoise(text: str) -> str:
    """Strip URLs, markdown-table pipes, and code-file references — they dilute
    the search signal. Keep the prose (domain + field names)."""
    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"`[^`]*`", " ", text)          # `knot_atlas_loader.py` etc.
    text = re.sub(r"[|]+", " ", text)              # table pipes
    text = re.sub(r"-{2,}", " ", text)             # table rules
    return re.sub(r"\s+", " ", text).strip()


def _raw_data_sections(project_dir: Path) -> str:
    """The data-relevant prose from the planning artifacts (denoised)."""
    specs = sorted(project_dir.glob("specs/*/"))
    research = spec = ""
    for d in specs:
        research = research or _read(d / "research.md")
        spec = spec or _read(d / "spec.md")
    chunks: list[str] = []
    sm = re.search(r"###?\s*User Story 1.+?(?:\n###?\s|\Z)", spec, re.S)
    if sm:
        chunks.append(sm.group(0))
    fm = re.search(r"\*\*FR-001\*\*:\s*(.+?)(?:\n-\s|\n\n)", spec, re.S)
    if fm:
        chunks.append(fm.group(1)[:700])
    m = re.search(r"##+\s*Dataset Strategy\s*(.+?)(?:\n##\s|\Z)", research, re.S | re.I)
    if m:
        chunks.append(m.group(1))
    return _denoise(" ".join(chunks))[:2500]


def _distill_data_need(raw: str) -> tuple[str, list[str]]:
    """LLM-distill messy planning prose into (search_query, required_fields).

    The artifacts are noisy (spec boilerplate like "User Story 1 -", "System
    MUST"; a URL table emphasizing a website that is NOT a programmatic source).
    One LLM call extracts BOTH a high-signal search query (data entity + named
    database + fields, biased toward the canonical database over a website) and
    the list of required fields/columns the dataset must contain — the latter
    lets discovery reject a source with the wrong schema (e.g. a name-only
    census). Falls back to (raw prose, []) if the LLM is unavailable/garbled.
    """
    if not raw:
        return "", []
    try:
        import json

        from llmxive.backends.base import ChatMessage
        from llmxive.backends.router import chat_with_fallback

        resp = chat_with_fallback(
            [
                ChatMessage(role="system", content=(
                    "From the described research data need, output STRICT JSON only: "
                    '{"query":"<8-16 word web-search query to find a REAL downloadable '
                    "dataset or pip-installable python package; name the data ENTITY and "
                    "EVERY named dataset/database/catalog mentioned — INCLUDING any "
                    "validation/reference database, not just the primary one — because the "
                    "primary is often a website while a secondary reference database has the "
                    "real downloadable package; favor canonical DATABASE names over website "
                    "names; end with 'python package dataset'>\","
                    '"fields":["<each required data field/column the dataset MUST contain>"]}. '
                    "No prose, no fences.")),
                ChatMessage(role="user", content=raw),
            ],
            default_backend="dartmouth", fallback_backends=["local"],
            model="openai.gpt-oss-120b",
        )
        text = re.sub(r"^```[a-z]*\s*|\s*```$", "", resp.text.strip())
        obj = json.loads(text[text.find("{"): text.rfind("}") + 1])
        query = re.sub(r"\s+", " ", str(obj.get("query", ""))).strip().strip('"')
        fields = [str(f).strip() for f in (obj.get("fields") or []) if str(f).strip()]
        if 3 <= len(query.split()) <= 40:
            return query[:_MAX_INTENT_CHARS], fields[:12]
    except Exception as exc:  # LLM unavailable / unparseable → fall back
        logger.warning("data-need distillation failed (%s); using raw prose", exc)
    return raw[:_MAX_INTENT_CHARS], []


def project_data_intent(project_dir: Path) -> str:
    """The search-optimized data intent for ``project_dir`` (query only)."""
    return _distill_data_need(_raw_data_sections(project_dir))[0]


def _cache_path(project_dir: Path) -> Path:
    return project_dir / ".specify" / "memory" / _CACHE_NAME


def load_cached_source(project_dir: Path) -> dict | None:
    """Return the cached discovery record (``{status, ...}``) or ``None``."""
    p = _cache_path(project_dir)
    if not p.is_file():
        return None
    try:
        return yaml.safe_load(p.read_text(encoding="utf-8")) or None
    except yaml.YAMLError:
        return None


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _age_days(searched_at: object) -> float | None:
    """Age in days of an ISO-8601 ``searched_at`` timestamp, or None if absent/bad."""
    if not searched_at:
        return None
    try:
        dt = datetime.fromisoformat(str(searched_at))
    except (ValueError, TypeError):
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return (datetime.now(UTC) - dt).total_seconds() / 86400.0


def _plan_hash(raw_sections: str) -> str:
    """Stable hash of the project's data-relevant planning prose.

    Included in the cache key so that a CHANGED plan/spec invalidates a stale
    discovery record (a source verified for an old data need must not be reused
    after the need changed). Deterministic (regex over the artifacts), unlike the
    LLM-distilled intent — so the deterministic part of the key is stable across
    ticks even when the LLM query wording drifts slightly.
    """
    return hashlib.sha256(raw_sections.encode("utf-8")).hexdigest()[:16]


def _cache_key(intent: str, required_fields: list[str], plan_hash: str) -> str:
    """A REAL cache key = sha256(intent + sorted(required_fields) + plan-hash +
    VERIFIER_VERSION) — NOT the file path. A record is a valid cache HIT only
    when its stored ``cache_key`` matches; any mismatch (intent / required-field /
    plan / verifier change) is treated as a MISS so the source is re-discovered
    rather than a stale/poisoned record being returned forever."""
    payload = "\x00".join((
        intent.strip(),
        "\x00".join(sorted(f.strip() for f in required_fields)),
        plan_hash,
        VERIFIER_VERSION,
    ))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


_TRANSIENT_TYPES = frozenset({
    "Timeout", "ConnectTimeout", "ReadTimeout", "ConnectionError",
    "ConnectionResetError", "ConnectionAbortedError", "TimeoutError",
    "ProtocolError", "ReadTimeoutError", "MaxRetryError", "NewConnectionError",
    "ChunkedEncodingError", "SSLError",
})
_TRANSIENT_MSG_RE = re.compile(
    r"\b(timed out|timeout|connection (?:reset|aborted|refused)|temporarily "
    r"unavailable|try again|too many requests|429|50[0-4]|502|503|504|"
    r"bad gateway|service unavailable|gateway timeout)\b",
    re.IGNORECASE,
)


def _is_transient_error(exc: BaseException) -> bool:
    """True if ``exc`` looks like a TRANSIENT failure (timeout / connection reset
    / HTTP 5xx / 429) rather than a terminal one — used only to LABEL the returned
    (un-persisted) error record so logs/feedback are actionable. A transient error
    is NEVER cached regardless (see :func:`ensure_discovered_source`)."""
    if type(exc).__name__ in _TRANSIENT_TYPES:
        return True
    if isinstance(exc, (TimeoutError, ConnectionError)):
        return True
    return bool(_TRANSIENT_MSG_RE.search(str(exc)))


def _cache_fresh(cached: dict, key: str) -> bool:
    """Whether a cached record is a valid HIT for ``key`` (else re-discover).

    - key mismatch (or a legacy record with no ``cache_key``) → MISS.
    - ``verified`` → durable HIT.
    - ``none`` → HIT while fresh (age < TTL) OR its bounded retry budget is spent;
      a stale none with retries left → MISS (re-search: the source may exist now).
    - ``error`` (or anything else) → NEVER a HIT: a cached error is poison; always
      re-discover (this also invalidates the legacy write-only error caches).
    """
    if cached.get("cache_key") != key:
        return False
    status = cached.get("status")
    if status == "verified":
        return True
    if status == "none":
        if int(cached.get("retry_count", 0) or 0) >= _NONE_MAX_RETRIES:
            return True  # retry budget exhausted → durable none
        age = _age_days(cached.get("searched_at"))
        if age is None:
            return True  # unknown age → trust it (don't thrash)
        return age < _NONE_TTL_DAYS  # fresh → reuse; stale → re-search
    return False


def _write_cache(project_dir: Path, record: dict) -> None:
    cache = _cache_path(project_dir)
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(yaml.safe_dump(record, sort_keys=False), encoding="utf-8")


def ensure_discovered_source(project_dir: Path) -> dict | None:
    """Discover + cache a VERIFIED real data source for the project.

    Shared by plan time (proactive) and the execution backstop, keyed on a REAL
    cache key (:func:`_cache_key`) stored inside the record — so a stale record
    from a changed plan / different required fields / bumped verifier is a MISS
    and is re-discovered, never returned forever.

    Caching policy:
      - ``status == "verified"`` (``ref`` / ``access_python`` / ``record_count``)
        is durable.
      - ``status == "none"`` carries ``searched_at`` + ``retry_count`` and is
        re-searched after :data:`_NONE_TTL_DAYS` up to :data:`_NONE_MAX_RETRIES`
        times (a source may be published later), then becomes durable.
      - a TRANSIENT error (timeout / connection / HTTP 5xx / 429) — or ANY
        discovery exception — is NOT persisted: the ephemeral error record is
        returned WITHOUT touching the cache, so the NEXT tick retries (a cached
        error used to poison the project permanently).

    Never raises — discovery is best-effort; a failure just injects no block.
    """
    raw = _raw_data_sections(project_dir)
    intent, required_fields = _distill_data_need(raw)
    key = _cache_key(intent, required_fields, _plan_hash(raw))

    cached = load_cached_source(project_dir)
    if cached is not None and _cache_fresh(cached, key):
        return cached

    if not intent:
        # No data need in the artifacts → durable none (nothing to retry for).
        record = {"status": "none", "reason": "no data intent found in planning artifacts",
                  "cache_key": key, "searched_at": _now_iso(),
                  "retry_count": _NONE_MAX_RETRIES}
        _write_cache(project_dir, record)
        return record

    try:
        from llmxive.librarian.data_source_discovery import discover_data_source

        src = discover_data_source(intent, required_fields=required_fields or None)
    except Exception as exc:  # discovery is best-effort — DO NOT cache the error.
        transient = _is_transient_error(exc)
        logger.warning(
            "data-source discovery failed for %s (%s, not cached — will retry): %s",
            project_dir.name, "transient" if transient else "error", exc,
        )
        # Return WITHOUT persisting so the next tick re-discovers; leave any
        # existing (verified/none) cache in place rather than clobbering it.
        return {"status": "error", "reason": str(exc)[:300],
                "transient": transient, "cached": False}

    if src is None:
        prev_retries = 0
        if (cached and cached.get("status") == "none"
                and cached.get("cache_key") == key):
            prev_retries = int(cached.get("retry_count", 0) or 0)
        record = {"status": "none", "intent": intent[:300],
                  "required_fields": required_fields, "cache_key": key,
                  "searched_at": _now_iso(), "retry_count": prev_retries + 1}
    else:
        record = {
            "status": "verified",
            "kind": src.kind,
            "ref": src.ref,
            "access_python": src.access_python,
            "record_count": src.record_count,
            "sample_fields": list(src.sample_fields),
            "field_coverage": round(src.field_coverage, 3),
            "required_fields": required_fields,
            "intent": intent[:300],
            "cache_key": key,
        }
    _write_cache(project_dir, record)
    return record


def render_feedback_block(record: dict | None) -> str:
    """Render the verified-source section for execution_feedback.md (or '').

    Branches on ``record["kind"]`` so the access instruction is CORRECT for the
    source type: a ``pypi_package`` gets a ``pip install`` line; a ``data_url``
    gets a download/stream recipe and is NEVER told to ``pip install <url>``.
    Only ``verified`` records (``record_count > 0`` by construction) render, so it
    never claims "loads 0 real records".
    """
    if not record or record.get("status") != "verified":
        return ""
    kind = str(record.get("kind") or "pypi_package")
    ref = record.get("ref", "")
    recipe = (record.get("access_python") or "").strip()
    count = record.get("record_count")
    fields = ", ".join(record.get("sample_fields") or [])
    field_suffix = f" with fields: {fields}." if fields else "."
    header = [
        "",
        "## ✅ VERIFIED REAL DATA SOURCE — use THIS in the data loader",
        "",
        "Do NOT invent or guess a download URL/API (a hallucinated endpoint "
        "will 404). A real source was discovered AND verified by actually "
        "loading real data from it:",
        "",
    ]
    if kind == "data_url":
        access = [
            f"- **Download / stream** this exact data URL directly (do NOT "
            f"`pip install` it — it is a data file, not a package): `{ref}`",
            f"- **Verified**: streaming a sample yielded **{count}** real "
            f"records{field_suffix}",
        ]
    else:  # pypi_package (default)
        access = [
            f"- **Install**: add `{ref}` to the project's `requirements.txt` and "
            f"`pip install {ref}`.",
            f"- **Verified**: this loads **{count}** real records{field_suffix}",
        ]
    tail = [
        "- **Working access recipe** (this EXACT code was executed and returned "
        "real data — base the loader on it):",
        "",
        "```python",
        recipe,
        "```",
        "",
        "Write the loader to use this source/recipe, persist the records to the "
        "declared raw/processed data files, and DELETE any old code that fetches "
        "from a guessed website endpoint.",
    ]
    return "\n".join(header + access + tail)


def ensure_source_in_requirements(project_dir: Path) -> bool:
    """Add the cached VERIFIED data-source package to ``code/requirements.txt``.

    The implementer is told (via the feedback block) to add the package, but it
    often updates the loader's ``import`` without touching requirements.txt — so
    the per-project venv lacks the package and the loader dies with
    ModuleNotFoundError. Since discovery already PROVED ``pip install <ref>``
    works, the execution stage guarantees the dependency is declared (the normal
    ``sandbox.ensure_venv`` path then installs it on the next run, and it's
    persisted for reproducibility). Returns True iff the file was modified.
    """
    rec = load_cached_source(project_dir)
    if not rec or rec.get("status") != "verified" or rec.get("kind") != "pypi_package":
        return False
    ref = str(rec.get("ref") or "").strip()
    if not ref:
        return False
    req = project_dir / "code" / "requirements.txt"
    existing = req.read_text(encoding="utf-8") if req.is_file() else ""
    # Already declared (bare name match, ignoring version specifiers)?
    bare = re.split(r"[<>=!~\[ ]", ref, maxsplit=1)[0].lower()
    for line in existing.splitlines():
        if re.split(r"[<>=!~\[ ]", line.strip(), maxsplit=1)[0].lower() == bare:
            return False
    req.parent.mkdir(parents=True, exist_ok=True)
    sep = "" if existing.endswith("\n") or not existing else "\n"
    addition = f"{sep}{ref}  # auto-added: verified real data source (discovery)\n"
    req.write_text(existing + addition, encoding="utf-8")
    logger.info("added discovered data source %r to %s", ref, req)
    return True


__all__ = [
    "ensure_discovered_source",
    "ensure_source_in_requirements",
    "load_cached_source",
    "project_data_intent",
    "render_feedback_block",
]
