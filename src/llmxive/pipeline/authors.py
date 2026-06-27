"""Author management for revised papers (spec 013 / FR-006..FR-008).

Authorship is by MODEL — the thing that did the cognition — not by agent
role. Operations:

  - `collect_contributor_models()` / `sync_paper_authors()`: reconcile
    `paper/metadata.json::authors` to the original humans plus one entry per
    DISTINCT model that produced paper content (collected from the run-log).
    Idempotent and self-migrating from the older per-agent scheme.

  - `update_latex_author_block()`: rewrite the LaTeX `\\author{...}` macro
    so original authors are preserved verbatim and the model contributors
    appear after a `\\par\\hrule\\par \\textit{Revised by:}` separator.

Original (human) author entries are always preserved verbatim
(FR-006 + Edge Case 5).
"""

from __future__ import annotations

import json
import os
import re
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

from llmxive.types import AuthorEntry


def author_display_name(entry: Any) -> str:
    """Canonical display name for ONE `metadata.json::authors[]` entry.

    Authorship entries are heterogeneous on disk (Single Source of Truth for
    rendering them anywhere a byline is built): an entry is either a plain
    string (the original arXiv-parsed human author) OR a structured mapping
    `{"name": ..., "kind": ...}` (a synced model/agent contributor, see
    `sync_paper_authors`). A bare `str()` over a mapping leaks the whole dict
    repr into the byline (`"{'name': ...}"`) and, when joined with `str.join`,
    raises `TypeError: sequence item N: expected str instance, dict found`.
    This normalizes BOTH shapes to the human-readable name and never raises.
    """
    if isinstance(entry, dict):
        return str(entry.get("name") or "").strip()
    return str(entry or "").strip()


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(tmp, path)
    except Exception:
        Path(tmp).unlink(missing_ok=True)
        raise


def collect_contributor_models(
    project_id: str,
    *,
    repo_root: Path | None = None,
    also: tuple[str, str, datetime] | None = None,
) -> list[AuthorEntry]:
    """Every distinct MODEL that produced paper content, as LLM ``AuthorEntry``\\ s.

    Authorship is by model (the cognition), not agent role: the run-log records
    which model each paper-content contribution used, and
    :func:`runlog.paper_contributor_models` collapses them to one
    ``(backend, first_contributed_at)`` per distinct model. Each becomes an
    ``AuthorEntry`` whose ``name`` IS the model (per the "list model not agent"
    contract). ``also`` injects the CURRENT contribution ``(model, backend,
    at)`` — the in-flight run isn't in the run-log yet when its own author sync
    fires. Sorted by first-contribution time then name (deterministic byline).
    """
    from llmxive.state import runlog as runlog_store

    models = runlog_store.paper_contributor_models(project_id, repo_root=repo_root)
    if also is not None:
        a_model, a_backend, a_at = also
        if a_model:
            prev = models.get(a_model)
            if prev is None or a_at < prev[1]:
                models[a_model] = (a_backend, a_at)
    entries = [
        AuthorEntry(
            name=model,
            kind="llm",
            model_name=model,
            backend=backend,
            first_contributed_at=at,
        )
        for model, (backend, at) in models.items()
    ]
    entries.sort(key=lambda e: (e.first_contributed_at or datetime.min, e.name))
    return entries


def sync_paper_authors(
    metadata_path: Path,
    project_id: str,
    *,
    repo_root: Path | None = None,
    also: tuple[str, str, datetime] | None = None,
) -> list[AuthorEntry]:
    """Reconcile ``metadata.json::authors`` to: original humans + one entry per
    distinct MODEL that worked on the paper. Returns the full author list.

    Human authors (the submitting/original byline) are preserved verbatim and
    always lead. The LLM block is REBUILT from the run-log every call (a clean,
    model-keyed list), so it is idempotent and self-migrating: stale per-agent
    LLM entries from the older ``add_implementer`` scheme are replaced by the
    canonical per-model entries. Non-``authors`` metadata fields are untouched
    (FR-016).
    """
    data: dict[str, Any] = {}
    if metadata_path.is_file():
        data = json.loads(metadata_path.read_text(encoding="utf-8")) or {}
    existing = data.get("authors") or []
    if not isinstance(existing, list):
        raise ValueError(
            f"metadata.json::authors must be a list, got {type(existing).__name__}"
        )
    # Preserve EVERY original author. Entries are heterogeneous on disk: the
    # arXiv-parsed originals are bare strings, structured humans are dicts.
    # Keep both (normalizing strings to the structured form so the merged list
    # is homogeneous) and drop ONLY the prior llm entries — those are rebuilt
    # from the run-log below. Dropping string humans here would WIPE an
    # arXiv paper's real byline.
    humans: list[dict[str, Any]] = []
    for e in existing:
        if isinstance(e, dict):
            if e.get("kind") == "llm":
                continue  # rebuilt from the run-log below
            humans.append(e)
        elif isinstance(e, str) and e.strip():
            humans.append({"name": e.strip(), "kind": "human"})
    model_authors = collect_contributor_models(
        project_id, repo_root=repo_root, also=also
    )
    merged = humans + [e.model_dump(mode="json") for e in model_authors]
    data["authors"] = merged
    _atomic_write(
        metadata_path,
        json.dumps(data, indent=2, sort_keys=False) + "\n",
    )
    out: list[AuthorEntry] = []
    for r in merged:
        try:
            out.append(AuthorEntry.model_validate(r))
        except Exception:
            try:
                out.append(AuthorEntry(name=str(r.get("name", "")), kind="human"))
            except Exception:
                continue
    return out


def list_authors(metadata_path: Path) -> list[AuthorEntry]:
    """Read `metadata.json::authors` and return validated entries.
    Legacy untyped entries are coerced to `kind='human'`. Malformed
    entries are skipped (Edge Case 5)."""
    if not metadata_path.is_file():
        return []
    data = json.loads(metadata_path.read_text(encoding="utf-8")) or {}
    raw = data.get("authors") or []
    out: list[AuthorEntry] = []
    for r in raw:
        if isinstance(r, str):
            # Original arXiv-parsed author stored as a bare string — coerce to a
            # human AuthorEntry so it is NEVER dropped from the byline/publisher.
            if r.strip():
                out.append(AuthorEntry(name=r.strip(), kind="human"))
            continue
        if not isinstance(r, dict):
            continue
        try:
            out.append(AuthorEntry.model_validate(r))
        except Exception:
            # Try with default kind=human if a bare {"name": "..."} entry
            try:
                out.append(AuthorEntry(name=str(r.get("name", "")), kind="human"))
            except Exception:
                continue
    return out


def _format_human_byline(entries: list[AuthorEntry]) -> str:
    """Format the human-author block exactly as the original author list
    would appear in LaTeX. We use the simplest form (comma-separated
    names with `\\and` between them) so the result is robust across
    document classes; downstream classes that want richer layout can
    inject affiliations via their own footnote machinery."""
    return r" \and ".join(e.name for e in entries) if entries else ""


def _format_llm_byline(entries: list[AuthorEntry]) -> str:
    """Format the LLM-contributor block. One per line; canonical display
    string is `name (model on backend, YYYY-MM-DD)` per the
    research.md §4 contract."""
    parts: list[str] = []
    for e in entries:
        date = (e.first_contributed_at.strftime("%Y-%m-%d")
                if e.first_contributed_at else "")
        if e.model_name and e.name == e.model_name and e.backend and date:
            # Model-as-author (the canonical "list model not agent" form):
            # don't repeat the model name as both byline and parenthetical.
            parts.append(f"{e.model_name} \\textit{{(via {e.backend}, {date})}}")
        elif e.model_name and e.backend and date:
            parts.append(
                f"{e.name} \\textit{{({e.model_name} on {e.backend}, {date})}}"
            )
        else:
            parts.append(e.name)
    return r" \\ ".join(parts)


_AUTHOR_BLOCK_RE = re.compile(r"\\author\s*\{", re.DOTALL)


def _find_balanced_brace_end(text: str, start: int) -> int:
    """Given `start` pointing one past a `{`, return the index of the
    matching `}` (with brace-counting). Raises if no match."""
    depth = 1
    i = start
    n = len(text)
    while i < n:
        c = text[i]
        if c == "\\":  # escape next char
            i += 2
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    raise ValueError("unbalanced `\\author{...}` block")


def update_latex_author_block(tex_path: Path, authors: list[AuthorEntry]) -> bool:
    """Rewrite the `\\author{...}` macro in the LaTeX source so it
    contains the original (human) authors followed by a separator and
    the LLM contributors in chronological order. Returns True if the
    file was changed; False if the resulting block is byte-identical
    to the existing one (idempotent re-runs).

    Layout:
        \\author{
          <original authors via \\and>
          \\par\\hrule\\par
          \\textit{Revised by:}\\\\
          <LLM contributor 1>\\\\
          <LLM contributor 2>...
        }

    If `authors` is empty, the existing `\\author{...}` is left
    untouched. If the source has no `\\author{...}` macro at all, the
    function inserts one before `\\begin{document}`.
    """
    if not authors:
        return False
    src = tex_path.read_text(encoding="utf-8")
    humans = [a for a in authors if a.kind == "human"]
    llms = sorted(
        [a for a in authors if a.kind == "llm"],
        key=lambda a: a.first_contributed_at or datetime.min,
    )

    body_parts = []
    if humans:
        body_parts.append(_format_human_byline(humans))
    if llms:
        body_parts.append(r"\par\hrule\par")
        body_parts.append(r"\textit{Revised by:}\\")
        body_parts.append(_format_llm_byline(llms))
    new_arg = "\n  " + "\n  ".join(body_parts) + "\n"

    m = _AUTHOR_BLOCK_RE.search(src)
    if m:
        arg_start = m.end()
        arg_end = _find_balanced_brace_end(src, arg_start)
        new_src = src[: m.start()] + r"\author{" + new_arg + "}" + src[arg_end + 1 :]
    else:
        # Insert before \begin{document}.
        idx = src.find(r"\begin{document}")
        if idx < 0:
            raise ValueError(
                f"no \\author{{...}} macro and no \\begin{{document}} in {tex_path}"
            )
        new_src = src[:idx] + r"\author{" + new_arg + "}" + "\n" + src[idx:]

    if new_src == src:
        return False
    _atomic_write(tex_path, new_src)
    return True
