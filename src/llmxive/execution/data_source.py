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

import logging
import re
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

_CACHE_NAME = "discovered_data_source.yaml"
_MAX_INTENT_CHARS = 1500


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


def ensure_discovered_source(project_dir: Path) -> dict | None:
    """Discover + cache a VERIFIED real data source for the project (once).

    Returns the cached record. ``status == "verified"`` records carry ``ref``,
    ``access_python``, ``record_count``. A ``status == "none"`` record is cached
    too, so a genuinely-undiscoverable source isn't re-searched every tick (the
    cache can be deleted to force a retry). Never raises — discovery is
    best-effort; a failure just means no block is injected this round.
    """
    cached = load_cached_source(project_dir)
    if cached is not None:
        return cached

    intent, required_fields = _distill_data_need(_raw_data_sections(project_dir))
    record: dict
    if not intent:
        record = {"status": "none", "reason": "no data intent found in planning artifacts"}
    else:
        try:
            from llmxive.librarian.data_source_discovery import discover_data_source

            src = discover_data_source(intent, required_fields=required_fields or None)
            if src is None:
                record = {"status": "none", "intent": intent[:300],
                          "required_fields": required_fields}
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
                }
        except Exception as exc:  # discovery is best-effort
            logger.warning("data-source discovery failed for %s: %s", project_dir.name, exc)
            record = {"status": "error", "reason": str(exc)[:300]}

    cache = _cache_path(project_dir)
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(yaml.safe_dump(record, sort_keys=False), encoding="utf-8")
    return record


def render_feedback_block(record: dict | None) -> str:
    """Render the verified-source section for execution_feedback.md (or '')."""
    if not record or record.get("status") != "verified":
        return ""
    ref = record.get("ref", "")
    recipe = (record.get("access_python") or "").strip()
    count = record.get("record_count")
    fields = ", ".join(record.get("sample_fields") or [])
    lines = [
        "",
        "## ✅ VERIFIED REAL DATA SOURCE — use THIS in the data loader",
        "",
        "Do NOT invent or guess a download URL/API (a hallucinated endpoint "
        "will 404). A real, installable source was discovered AND verified by "
        "actually loading data from it:",
        "",
        f"- **Install**: add `{ref}` to the project's `requirements.txt` and "
        f"`pip install {ref}`.",
        f"- **Verified**: this loads **{count}** real records"
        + (f" with fields: {fields}." if fields else "."),
        "- **Working access recipe** (this EXACT code was executed and returned "
        "real data — base the loader on it):",
        "",
        "```python",
        recipe,
        "```",
        "",
        "Write the loader to use this package/recipe, persist the records to the "
        "declared raw/processed data files, and DELETE any old code that fetches "
        "from a website endpoint.",
    ]
    return "\n".join(lines)


__all__ = [
    "ensure_discovered_source",
    "load_cached_source",
    "project_data_intent",
    "render_feedback_block",
]
