"""Author management for revised papers (spec 013 / FR-006..FR-008).

Two operations:

  - `add_implementer()`: append an LLM-implementer to
    `paper/metadata.json::authors`, deduplicated by (name, agent_version)
    so re-runs of the same agent never produce duplicate entries.

  - `update_latex_author_block()`: rewrite the LaTeX `\\author{...}` macro
    so original authors are preserved verbatim and LLM contributors
    appear after a `\\par\\hrule\\par \\textit{Revised by:}` separator.

Both operations are append-only on the original-author entries
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


def add_implementer(
    metadata_path: Path,
    *,
    agent_name: str,
    agent_version: str,
    model_name: str,
    backend: str,
    first_contributed_at: datetime,
) -> bool:
    """Idempotently add an LLM-implementer to `paper/metadata.json::authors`.
    Returns True if a new entry was appended; False if the (name,
    agent_version) was already present.

    The dedupe key is `(name, agent_version)` per FR-008. Other implementer
    agents (different name or different version) DO produce new entries.
    Non-`authors` fields of metadata.json are NEVER modified (FR-016).
    """
    data: dict[str, Any] = {}
    if metadata_path.is_file():
        data = json.loads(metadata_path.read_text(encoding="utf-8")) or {}
    authors = data.get("authors") or []
    if not isinstance(authors, list):
        raise ValueError(
            f"metadata.json::authors must be a list, got {type(authors).__name__}"
        )

    for entry in authors:
        if (
            isinstance(entry, dict)
            and entry.get("name") == agent_name
            and entry.get("agent_version") == agent_version
        ):
            return False  # already present — no-op (FR-008)

    new_entry = AuthorEntry(
        name=agent_name,
        kind="llm",
        agent_version=agent_version,
        model_name=model_name,
        backend=backend,
        first_contributed_at=first_contributed_at,
    )
    authors.append(new_entry.model_dump(mode="json"))
    data["authors"] = authors
    _atomic_write(
        metadata_path,
        json.dumps(data, indent=2, sort_keys=False) + "\n",
    )
    return True


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
        if e.model_name and e.backend and date:
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
