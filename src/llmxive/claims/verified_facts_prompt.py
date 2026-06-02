"""Feed canonical verified facts back into the GENERATION agents.

Phase 2 of the trustworthiness fix. A prior phase persists every resolved
numeric/entity fact to ``projects/<id>/.specify/memory/verified_facts.yaml``
(see ``claims.service._persist_verified_facts``). This module reads that file
and renders a SELF-INSTRUCTING markdown block that the specifier, the spec/plan
convergence revisers, and the planner append to their USER prompts — so they
cite the verified value and never invent a contradicting one.

Design constraints:
- Best-effort: a missing/corrupt/unreadable file yields ``[]`` (never raises).
- Pure addition: when there are no facts, the rendered block is the empty
  string, so a prompt that appends it is BYTE-IDENTICAL to today.
- Dependency-light: only stdlib + PyYAML (already a project dependency).

The persisted YAML is a mapping ``subject_key -> {value, source_id, url,
quote}`` where ``subject_key`` has the shape
``"<qualifier-number tokens>|<subject keyword tokens>"`` (see
``claims.canonical.subject_key``). We reconstruct a human-readable subject from
that key.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

__all__ = [
    "load_verified_facts",
    "project_dir_for",
    "render_verified_facts_block",
]

_FACTS_RELPATH = Path(".specify") / "memory" / "verified_facts.yaml"


def load_verified_facts(project_dir: Path | None) -> list[dict[str, Any]]:
    """Read ``<project_dir>/.specify/memory/verified_facts.yaml``.

    Returns a list of fact dicts, each carrying the persisted fields plus a
    derived human-readable ``subject``. Best-effort: a ``None`` project_dir, a
    missing file, an unreadable file, or a corrupt/unexpected payload all yield
    ``[]`` — this never raises so it can never break a render.
    """
    if project_dir is None:
        return []
    path = Path(project_dir) / _FACTS_RELPATH
    if not path.is_file():
        return []
    try:
        import yaml

        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:  # corrupt YAML, IO error, bad encoding, ...
        logger.warning(
            "verified_facts_prompt: could not load %s (%s)", path, exc
        )
        return []

    if not isinstance(raw, dict):
        return []

    facts: list[dict[str, Any]] = []
    for key, entry in raw.items():
        if not isinstance(entry, dict):
            continue
        value = entry.get("value")
        if value is None or str(value).strip() == "":
            # A fact with no value can't instruct the agent toward an exact
            # value; skip it rather than emit a misleading "= None".
            continue
        facts.append(
            {
                "subject_key": str(key),
                "subject": _humanize_subject(str(key)),
                "value": str(value),
                "source_id": _str_or_empty(entry.get("source_id")),
                "url": _str_or_empty(entry.get("url")),
                "quote": _str_or_empty(entry.get("quote")),
            }
        )
    # Stable order for deterministic prompts (the YAML is already sorted, but
    # don't depend on the loader preserving that).
    facts.sort(key=lambda f: f["subject_key"])
    return facts


def render_verified_facts_block(facts: list[dict[str, Any]]) -> str:
    """Render a self-instructing markdown block from ``facts``.

    Empty string when ``facts`` is empty (pure-addition guarantee). Otherwise a
    block that (a) states each verified value with its source + url and (b)
    instructs the agent to use the EXACT value, cite the source, and NOT invent
    a reconciliation between a wrong value and the verified one.
    """
    if not facts:
        return ""

    lines = [
        "## VERIFIED FACTS — authoritative; use these EXACT values and cite "
        "the given source",
        "",
        "These values were verified against fetched authoritative sources. "
        "When you state any of these facts you MUST use the exact value and "
        "cite the given source; you MUST NOT state a different value, and you "
        "MUST NOT invent a reconciliation (e.g. calling a wrong value a "
        '"full count" vs a "subset"). If your prior text disagrees with a '
        "verified value, correct it to the verified value.",
        "",
    ]
    for fact in facts:
        lines.append(_render_fact_line(fact))
    return "\n".join(lines)


# --- internal helpers -------------------------------------------------------


def _render_fact_line(fact: dict[str, Any]) -> str:
    subject = fact.get("subject") or fact.get("subject_key") or "(subject)"
    value = fact.get("value", "")
    source_id = fact.get("source_id") or ""
    url = fact.get("url") or ""

    source_bits = [b for b in (source_id, url) if b]
    source = f"  (source: {', '.join(source_bits)})" if source_bits else ""
    return f"- {subject} = {value}{source}"


def _humanize_subject(subject_key: str) -> str:
    """Turn a ``"<qualifiers>|<keywords>"`` subject key into readable prose.

    Example: ``"13|crossing knots number prime"`` ->
    ``"crossing knots number prime (13)"``. A key without the ``|`` separator
    (defensive) is returned as-is.
    """
    if "|" not in subject_key:
        return subject_key.strip()
    qualifiers, _, keywords = subject_key.partition("|")
    keywords = keywords.strip()
    qualifiers = qualifiers.strip()
    if keywords and qualifiers:
        return f"{keywords} ({qualifiers})"
    return keywords or qualifiers or subject_key.strip()


def _str_or_empty(value: Any) -> str:
    return "" if value is None else str(value)


def project_dir_for(
    repo_root: Path, project_id: str, *, artifact_path: str | None = None
) -> Path | None:
    """Locate a project directory under ``repo_root``.

    Mirrors ``claims.service._project_dir`` (which we must not import — it lives
    in a module a prior phase owns): prefer a ``projects/<slug>/...``
    ``artifact_path`` prefix, else match a ``projects/<id>*`` child by
    ``project_id`` prefix. Returns ``None`` when nothing matches.
    """
    repo_root = Path(repo_root)
    if artifact_path:
        parts = Path(artifact_path).parts
        if len(parts) >= 2 and parts[0] == "projects":
            return repo_root / "projects" / parts[1]
    projects_root = repo_root / "projects"
    if projects_root.is_dir():
        for child in sorted(projects_root.iterdir()):
            if child.is_dir() and child.name.startswith(project_id):
                return child
    return None
