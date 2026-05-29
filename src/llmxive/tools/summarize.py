"""SSoT context-reduction primitive: ``summarize`` / ``desummarize`` (spec 015, #239).

Reduces over-budget content to an on-disk **inode-table pointer hierarchy** so that
no check-critical element (URL, DOI, arXiv id, citation key, FR/SC/task id, number)
is ever silently dropped: the full content lives on disk and is paged back in on
demand by ``desummarize``. Goal-targeted prose summarization (for semantic checks on
large prose) is performed by an injected ``summarize_fn`` so this module stays
backend-agnostic and the no-loss guarantee is deterministic/testable offline.

Generalizes ``agents/paper_reviewer._build_corpus_with_summaries`` (which is
re-pointed to call this). See ``specs/015-pipeline-convergence-protocol/contracts/
summarize-api.md`` and ``data-model.md``.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

__all__ = [
    "desummarize",
    "estimate_tokens",
    "extract_critical",
    "summarize",
    "summarize_to_budget",  # back-compat alias for issue #239's documented name
]

# --- budget ---------------------------------------------------------------

CHARS_PER_TOKEN = 4  # heuristic, consistent with paper_reviewer.py ("180KB ~= 45K tokens")
# Per the Dartmouth API model registry (verified 2026-05-29 via
# https://chat.dartmouth.edu/api/models): every reasoning-capable model
# we use has a 128K+ context window. qwen3.5-122b's actual
# ``max_input_tokens`` is 256K — the old 32K constant was a back-of-the-
# envelope estimate that left ~87% of the context unused. The numbers
# below are the ``max_input_tokens`` reported by the API; subtract the
# completion reserve below to leave room for output + reasoning.
DEFAULT_MODEL_BUDGET = 128_000  # safe fallback for any unknown model
COMPLETION_RESERVE = 0.25  # leave headroom for the model's own output
_MODEL_BUDGETS: dict[str, int] = {
    "qwen.qwen3.5-122b": 200_000,
    "qwen.qwen3-vl:32b": 200_000,
    "openai.gpt-oss-120b": 128_000,
    "google.gemma-3-27b-it": 128_000,
    "google.gemma-4-31B-it": 128_000,
}
_MARKER = "[[LLMXIVE-SUMMARY v1]]"
_SCHEMA = "llmxive-summary/1"


def estimate_tokens(text: str) -> int:
    """Conservative char/4 token estimate (rounds up)."""
    return (len(text) + CHARS_PER_TOKEN - 1) // CHARS_PER_TOKEN


def _usable_budget(model: str, token_budget: int | None) -> int:
    if token_budget is not None:
        return max(1, int(token_budget))
    raw = _MODEL_BUDGETS.get(model, DEFAULT_MODEL_BUDGET)
    return max(1, int(raw * (1.0 - COMPLETION_RESERVE)))


# --- deterministic extraction of check-critical elements ------------------

_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"https?://[^\s)>\]\"']+"),                     # URLs
    re.compile(r"\b10\.\d{4,9}/[^\s)>\]\"']+", re.IGNORECASE),  # DOIs
    re.compile(r"\barXiv:\s*\d{4}\.\d{4,5}(v\d+)?", re.IGNORECASE),  # arXiv ids
    re.compile(r"\\cite[a-z]*\{[^}]+\}"),                       # LaTeX citations
    re.compile(r"\[[A-Za-z][A-Za-z .&-]+\d{4}[a-z]?\]"),        # [Smith2020] keys
    re.compile(r"\b(?:FR|SC)-\d{2,4}\b"),                       # FR-/SC- ids
    re.compile(r"\bT\d{3,4}\b"),                                # task ids
    re.compile(r"-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?%?"),          # numbers
)


def extract_critical(content: str) -> list[str]:
    """Return every check-critical element, verbatim, in document order, deduped.

    A superset-preserving extraction: ALL recognized discrete elements are kept for
    every goal, so a critical element can never be summarized away regardless of the
    preservation contract.
    """
    found: list[tuple[int, str]] = []
    for pat in _PATTERNS:
        for m in pat.finditer(content):
            found.append((m.start(), m.group(0)))
    found.sort(key=lambda t: t[0])
    seen: set[str] = set()
    out: list[str] = []
    for _, tok in found:
        if tok not in seen:
            seen.add(tok)
            out.append(tok)
    return out


# --- boundary-aware chunking (never splits a line/atomic unit) ------------

def _chunk_by_chars(text: str, max_chars: int) -> list[str]:
    """Split into chunks <= max_chars, breaking only at line boundaries (preferring
    blank lines / markdown or LaTeX headings). A single line longer than max_chars is
    emitted as its own chunk (still preserved verbatim on disk)."""
    lines = text.splitlines(keepends=True)
    chunks: list[str] = []
    buf: list[str] = []
    size = 0
    for line in lines:
        ln = len(line)
        if buf and size + ln > max_chars:
            chunks.append("".join(buf))
            buf, size = [], 0
        buf.append(line)
        size += ln
        # prefer to break after a heading/blank boundary once reasonably full
        if size >= max_chars and (line.strip() == "" or line.lstrip().startswith(("#", "===", "\\section", "\\subsection"))):
            chunks.append("".join(buf))
            buf, size = [], 0
    if buf:
        chunks.append("".join(buf))
    return chunks or [text]


# --- manifest (on-disk inode table) ---------------------------------------

def _sha(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]


def _excerpt_summary(chunk: str, limit: int = 600) -> str:
    head = chunk.strip()[:limit]
    suffix = "" if len(chunk.strip()) <= limit else " [... full chunk preserved on disk; desummarize() to retrieve.]"
    return head + suffix


def _build_manifest(
    content: str,
    out_dir: Path,
    *,
    goal: str,
    model: str,
    budget: int,
    summarize_fn: Callable[[str, str], str] | None,
    chunk_max: int | None = None,
) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    # Chunk so each content chunk is ~half the budget in tokens (so it fits the budget);
    # never below a small floor. A single line longer than chunk_max is kept whole.
    if chunk_max is None:
        chunk_max = max(400, budget * CHARS_PER_TOKEN // 2)
    chunks = _chunk_by_chars(content, chunk_max)
    entries: list[dict[str, Any]] = []
    for i, chunk in enumerate(chunks):
        crit = extract_critical(chunk)
        summary = (summarize_fn(chunk, goal) if summarize_fn else _excerpt_summary(chunk))
        finer = max(200, chunk_max // 4)
        # Recurse into a nested manifest (inode pointer) only when the chunk overflows
        # AND can actually be split further; otherwise store it verbatim on disk (still
        # fully recoverable). This bounds recursion (chunk_max shrinks each level).
        if estimate_tokens(chunk) > budget and len(_chunk_by_chars(chunk, finer)) > 1:
            sub = _build_manifest(chunk, out_dir / f"sub_{i:03d}", goal=goal, model=model,
                                  budget=budget, summarize_fn=summarize_fn, chunk_max=finer)
            entries.append({"element_id": f"e{i:03d}", "kind": "pointer",
                            "file": str(sub.relative_to(out_dir)), "critical": crit,
                            "summary": summary})
        else:
            fname = f"chunk_{i:03d}.txt"
            (out_dir / fname).write_text(chunk, encoding="utf-8")
            entries.append({"element_id": f"e{i:03d}", "kind": "content",
                            "file": fname, "critical": crit, "summary": summary})
    manifest = {
        "schema": _SCHEMA,
        "root_hash": _sha(content),
        "goal": goal,
        "model": model,
        "token_budget": budget,
        "created_at": datetime.now(UTC).isoformat(),
        "entries": entries,
    }
    path = out_dir / "manifest.json"
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return path


def _render_pointer_block(manifest_path: Path, *, goal: str, budget: int) -> str:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    entries = manifest["entries"]
    # Dedupe ALL critical elements across every chunk, preserving first-seen
    # order. These MUST appear verbatim in the rendered block a reviewer reads
    # — not merely on disk (issue §3a: "critical elements carried verbatim
    # through every recursion level"). The previous implementation inlined
    # critical elements PER CHUNK and broke out of the loop on budget overflow,
    # so under a tight budget a reviewer could see only some — or zero — of
    # them (everything after the break was dropped from the block).
    all_crit: list[str] = []
    seen: set[str] = set()
    for e in entries:
        for c in e["critical"]:
            if c not in seen:
                seen.add(c)
                all_crit.append(c)
    header = (
        f"{_MARKER} manifest={manifest_path.resolve()}\n"
        f"goal: {goal}\n"
        f"{len(entries)} chunk(s), {len(all_crit)} critical element(s) preserved verbatim. "
        f"Use desummarize() to page in full content.\n\n"
    )
    # Inline the FULL deduped critical-element list FIRST, and UNCONDITIONALLY:
    # even if it alone exceeds the (soft) token budget, silently dropping a
    # URL/DOI/number/id is worse than overflowing the target. Prose
    # chunk-summaries then fill whatever budget remains.
    crit_section = ""
    if all_crit:
        crit_section = (
            "CRITICAL ELEMENTS (verbatim — all preserved):\n"
            + "\n".join(f"- {c}" for c in all_crit)
            + "\n\n"
        )
    notice = ("[... chunk prose-summaries truncated to fit the token budget; ALL "
              "critical elements are listed above and full content is on disk — "
              "call desummarize() to retrieve it.]\n")
    notice_reserve = estimate_tokens(notice)
    body_parts: list[str] = []
    used = estimate_tokens(header) + estimate_tokens(crit_section)
    truncated = False
    for e in entries:
        part = f"## {e['element_id']}\n{e['summary']}\n\n"
        # reserve room for the trailing notice so the prose stays within budget
        if used + estimate_tokens(part) + notice_reserve > budget:
            truncated = True
            break
        body_parts.append(part)
        used += estimate_tokens(part)
    block = header + crit_section + "".join(body_parts)
    if truncated:
        block += notice
    return block


# --- public API -----------------------------------------------------------

def summarize(
    content: str,
    *,
    goal: str,
    model: str = "qwen.qwen3.5-122b",
    token_budget: int | None = None,
    cache_dir: str | Path | None = None,
    summarize_fn: Callable[[str, str], str] | None = None,
) -> str:
    """Return ``content`` verbatim if it fits ``token_budget`` (resolved from ``model``);
    otherwise return a compact pointer block referencing an on-disk inode-table manifest
    that preserves every check-critical element verbatim. ``summarize_fn(text, goal)``
    (optional) produces goal-targeted prose summaries; when absent, a lossless excerpt is
    used (the full content is always on disk regardless).
    """
    budget = _usable_budget(model, token_budget)
    if estimate_tokens(content) <= budget:
        return content
    cache = Path(cache_dir) if cache_dir is not None else Path(".summaries")
    out_dir = cache / _sha(content)
    manifest_path = _build_manifest(content, out_dir, goal=goal, model=model,
                                    budget=budget, summarize_fn=summarize_fn)
    return _render_pointer_block(manifest_path, goal=goal, budget=budget)


def _matches(want: list[str], entry: dict[str, Any], text: str) -> bool:
    for w in want:
        if any(w in c for c in entry["critical"]) or w in text:
            return True
    return False


def _expand_manifest(manifest_path: Path, want: list[str] | None, depth: int) -> str:
    if depth <= 0:
        raise RecursionError(f"summary manifest exceeds max depth: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    base = manifest_path.parent
    out: list[str] = []
    for e in manifest["entries"]:
        target = base / e["file"]
        if not target.exists():
            raise FileNotFoundError(f"dangling summary pointer: {target}")
        if e["kind"] == "content":
            text = target.read_text(encoding="utf-8")
            if want is None or _matches(want, e, text):
                out.append(text)
        else:  # pointer -> nested manifest
            out.append(_expand_manifest(target, want, depth - 1))
    return "\n".join(out)


def desummarize(text: str, *, want: list[str] | None = None, max_depth: int = 16) -> str:
    """Recursively resolve a pointer block produced by ``summarize`` back into the
    underlying content (or just the ``want`` subset). Returns ``text`` unchanged if it is
    not a pointer block. Raises ``FileNotFoundError`` on any dangling pointer."""
    if not text.startswith(_MARKER):
        return text
    first_line = text.splitlines()[0]
    m = re.search(r"manifest=(.+)$", first_line)
    if not m:
        raise ValueError("malformed summary pointer block: no manifest path")
    manifest_path = Path(m.group(1).strip())
    if not manifest_path.exists():
        raise FileNotFoundError(f"dangling summary manifest: {manifest_path}")
    return _expand_manifest(manifest_path, want, max_depth)


# Back-compat alias for the function name documented in issue #239 §3a
# (``summarize_to_budget``). The spec clarification superseded the name
# with the inode-table-based ``summarize``; this alias preserves the
# documented signature so anyone reading the issue can find a callable
# with that exact name.
summarize_to_budget = summarize
