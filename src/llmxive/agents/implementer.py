"""llmXive-implementer agent (spec 013 / US1+US2, FR-001..FR-019;
spec 015 T042 / FR-034 diagnostic failsafe).

Picks projects whose ``current_stage in {PAPER_REVIEW, RESEARCH_REVIEW}``
with a non-empty ``revision_spec_path`` (set by
:func:`llmxive.convergence.revision_adapter.kickback_to_revision_spec`
whenever the convergence engine emits a non-convergence KickbackRecord).
Processes each task in the revision spec's `tasks.md`, applies LLM-
generated edits to `paper/source/main.tex` (and, for science-class
tasks, `projects/<id>/code/`), rolls back per-task on compile failure,
and routes the project back to the source review stage for re-review.

Spec 015 T042: the 5-consecutive-failure failsafe now runs through a
diagnostic mode (:mod:`llmxive.agents.implementer_diagnostics`). On
classifiable failures the implementer synthesizes a fresh round-N+1
revision spec carrying the diagnosed problem as a work-item. Only on
TRULY opaque (``UNKNOWN``) failures does the project halt at
:class:`Stage.AGENT_BLOCKED` — replacing the deleted
``PAPER_REVISION_BLOCKED`` hard-halt with a learning loop.

Contract: specs/013-paper-revision-implementer/contracts/implementer-agent.md
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import shutil
import subprocess
import time
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal, cast
from uuid import uuid4

import yaml

from llmxive.agents.base import Agent, AgentContext
from llmxive.agents.implementer_diagnostics import FailureClassification
from llmxive.agents.prompts import load_prompt, render_prompt
from llmxive.backends.base import ChatMessage, ChatResponse
from llmxive.backends.router import chat_with_fallback
from llmxive.config import repo_root as _repo_root
from llmxive.pipeline import authors as authors_module
from llmxive.state import project as project_state
from llmxive.state import revision_history as rh_state
from llmxive.state import runlog
from llmxive.types import (
    AuthorEntry,
    BackendName,
    ImplementerLog,
    ImplementerLogEntry,
    Outcome,
    RevisionRound,
    RunLogEntry,
    Stage,
)

logger = logging.getLogger(__name__)

# Canonical display identity for author lists, run logs, and the
# revision_history.yaml `implementer_agent` field. NOT the registry
# entry's snake_case `name` (which is `llmxive_implementer`), but the
# human-readable form the journal exposes in author attributions.
CANONICAL_IMPLEMENTER_NAME = "llmXive-implementer-v1.0"


# Section / abstract / bibliography deletion guard (FR-017). A
# `search_and_replace` whose `replace` is empty AND whose `search`
# matches any of these patterns is rejected as `skipped`.
_FORBIDDEN_DELETION_PATTERNS = (
    re.compile(r"\\begin\s*\{\s*abstract\s*\}.*?\\end\s*\{\s*abstract\s*\}", re.DOTALL),
    re.compile(r"\\bibliography\s*\{[^}]*\}"),
    re.compile(r"\\begin\s*\{\s*thebibliography\s*\}.*?\\end\s*\{\s*thebibliography\s*\}", re.DOTALL),
)


@dataclass
class EditResult:
    """Per-task edit outcome. `applied=False` means the edit was rejected
    pre-flight (multi-match / no-match / unsafe-deletion / git-apply-check
    failure) — the file is unchanged."""

    applied: bool
    files_modified: list[str]
    before_hashes: dict[str, str]
    after_hashes: dict[str, str]
    reject_reason: str | None = None


# --- Edit-application helpers (T018, T019) ---------------------------------

def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _is_forbidden_deletion(search: str, replace: str) -> bool:
    """FR-017: refuse to delete the abstract, bibliography, or full
    thebibliography environment."""
    if replace.strip():
        return False  # not a delete-only edit
    return any(p.search(search) for p in _FORBIDDEN_DELETION_PATTERNS)


def _normalize_line(line: str, level: int) -> str:
    """Progressive per-line normalization for flexible matching (aider-style)."""
    if level <= 0:
        return line
    if level == 1:
        return line.rstrip()           # trailing-whitespace drift
    if level == 2:
        return line.strip()            # leading+trailing (indentation) drift
    return " ".join(line.split())      # collapse internal whitespace runs


def _flexible_replace(text: str, search: str, replace: str) -> tuple[str | None, str]:
    """Replace ``search`` with ``replace`` in ``text``, tolerant of the whitespace
    / indentation drift that causes ~62% of real edit failures ('search string
    not found'). LLM-emitted ``search`` blocks rarely reproduce a file's exact
    whitespace, so after an exact attempt we fall back to line-based matching
    under progressively looser per-line normalization — but ONLY apply a match
    that is UNIQUE at that level, so we never silently edit the wrong place
    (mirrors aider's flexible-but-safe patch application).

    Returns ``(new_text, reason)`` on success or ``(None, reason)`` on failure.
    """
    if not search:
        return None, "empty-search"
    exact = text.count(search)
    if exact == 1:
        return text.replace(search, replace, 1), "exact"
    if exact > 1:
        return None, f"ambiguous: search string matches {exact} locations"

    flines = text.splitlines()
    slines = search.splitlines()
    n = len(slines)
    if n == 0 or n > len(flines):
        return None, "no-match: search string not found"
    rep_lines = replace.splitlines()
    for level in (1, 2, 3):
        norm_s = [_normalize_line(s, level) for s in slines]
        hits = [
            i
            for i in range(len(flines) - n + 1)
            if [_normalize_line(flines[i + k], level) for k in range(n)] == norm_s
        ]
        if len(hits) == 1:
            i = hits[0]
            out = "\n".join(flines[:i] + rep_lines + flines[i + n:])
            if text.endswith("\n"):
                out += "\n"
            return out, f"flexible-match(level={level})"
        if len(hits) > 1:
            return None, (
                f"ambiguous: search string matches {len(hits)} locations (flexible)"
            )
    return None, "no-match: search string not found (tried exact + flexible)"


def apply_search_and_replace(
    file_path: Path, search: str, replace: str,
) -> EditResult:
    """Apply a search/replace edit, tolerant of whitespace/indentation drift.

    Returns EditResult applied=False when the file doesn't exist, the search
    can't be located (even flexibly), the match is ambiguous, or the search is a
    forbidden deletion target (abstract/bibliography with empty replace, FR-017).
    """
    if not file_path.is_file():
        return EditResult(False, [], {}, {}, f"file-not-found: {file_path}")
    before_bytes = file_path.read_bytes()
    before_text = before_bytes.decode("utf-8", errors="replace")
    if _is_forbidden_deletion(search, replace):
        return EditResult(
            False, [], {}, {},
            "FR-017: refusing to delete abstract/bibliography/thebibliography",
        )
    after_text, reason = _flexible_replace(before_text, search, replace)
    if after_text is None:
        return EditResult(False, [], {}, {}, reason)
    file_path.write_text(after_text, encoding="utf-8")
    after_bytes = file_path.read_bytes()
    rel = str(file_path)
    return EditResult(
        True, [rel], {rel: _sha256(before_bytes)}, {rel: _sha256(after_bytes)},
    )


def _extract_added_lines(diff: str) -> str | None:
    """Reconstruct a NEW file's contents from a unified diff's added (`+`) lines.

    Used for new-file creation: the `+++ ` header is excluded, every other
    ``+``-prefixed line contributes its content. Returns None if the diff adds
    nothing (then it is not a creatable diff).
    """
    out = [
        ln[1:]
        for ln in diff.splitlines()
        if ln.startswith("+") and not ln.startswith("+++")
    ]
    return ("\n".join(out) + "\n") if out else None


def _diff_hunks_to_replacements(diff: str) -> list[tuple[str, str]]:
    """Convert a unified diff's hunks into (search, replace) pairs.

    Per hunk: context (` `) + removed (`-`) lines form the SEARCH; context (` `)
    + added (`+`) lines form the REPLACE. Used to re-apply an LLM diff flexibly
    when ``git apply`` rejects it over slightly-wrong context/line numbers.
    """
    pairs: list[tuple[str, str]] = []
    search: list[str] = []
    replace: list[str] = []
    in_hunk = False

    def _flush() -> None:
        nonlocal search, replace
        if search or replace:
            pairs.append(("\n".join(search), "\n".join(replace)))
        search, replace = [], []

    for line in diff.splitlines():
        if line.startswith("@@"):
            _flush()
            in_hunk = True
            continue
        if line.startswith(("---", "+++")) or line.startswith("\\"):
            continue
        if not in_hunk:
            continue
        if line.startswith("+"):
            replace.append(line[1:])
        elif line.startswith("-"):
            search.append(line[1:])
        elif line.startswith(" "):
            search.append(line[1:])
            replace.append(line[1:])
        else:  # some models omit the leading space on context lines
            search.append(line)
            replace.append(line)
    _flush()
    return pairs


def _apply_diff_flexibly(text: str, diff: str) -> str | None:
    """Apply a unified diff via whitespace-tolerant hunk matching (fallback for
    when ``git apply`` rejects the diff). Returns the new text if ≥1 hunk applied
    and the content changed; else None."""
    new_text = text
    applied = False
    for search, replace in _diff_hunks_to_replacements(diff):
        if not search.strip() or search == replace:
            continue
        out, _ = _flexible_replace(new_text, search, replace)
        if out is not None:
            new_text = out
            applied = True
    return new_text if (applied and new_text != text) else None


def apply_unified_diff(file_path: Path, diff: str) -> EditResult:
    """Apply a unified diff via `git apply`. Pre-flight `git apply
    --check`; if check fails, return applied=False (skipped). Otherwise
    apply, then return applied=True with hashes.

    The diff is fed via stdin to `git apply`. We don't allow it to
    touch any file other than `file_path` — any path in the diff that
    isn't `file_path` causes a rejection (defensive scope check).

    A diff against a NON-existent target is treated as new-file creation
    (research reviewers frequently ask for a doc that does not exist yet): the
    file is written from the diff's added lines. git-apply's own new-file path
    is cwd/format-fragile, so we reconstruct directly — ``_snapshot``/``_restore``
    already roll a created file back by unlinking it.
    """
    # Defensive: ensure the diff's --- / +++ headers point to this file only.
    # Diffs name the target with a PROJECT/REPO-relative path while `target` is
    # absolute, so compare by path-component-aligned suffix (not equality) — a
    # declared path must be the tail of the absolute target, or its bare name.
    declared = set(re.findall(r"^(?:---|\+\+\+)\s+(?:a/|b/)?(\S+)", diff, re.M))
    # /dev/null marks a new/deleted file; the a/ b/ strip can leave it as
    # "dev/null" too — discard both forms so new-file diffs aren't rejected.
    declared.discard("/dev/null")
    declared.discard("dev/null")
    rel = file_path.as_posix()
    if declared and not all(
        rel == d or rel.endswith("/" + d) or d == file_path.name for d in declared
    ):
        return EditResult(
            False, [], {}, {},
            f"diff references unexpected files: {sorted(declared)}",
        )
    if not file_path.is_file():
        added = _extract_added_lines(diff)
        if added is None:
            return EditResult(False, [], {}, {}, f"file-not-found: {file_path}")
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(added, encoding="utf-8")
        after_bytes = file_path.read_bytes()
        return EditResult(
            True, [str(file_path)],
            {str(file_path): _sha256(b"")},
            {str(file_path): _sha256(after_bytes)},
        )
    before_bytes = file_path.read_bytes()
    # `git apply` resolves the diff's (relative) paths against its cwd. Derive
    # the cwd so the declared path resolves to THIS file: strip the matched
    # declared suffix off the absolute target (e.g. target=/r/proj/code/a.py,
    # declared "code/a.py" -> cwd=/r/proj). Falls back to the file's parent for
    # bare-filename diffs.
    matched = next((d for d in declared if rel == d or rel.endswith("/" + d)), None)
    if matched and rel.endswith("/" + matched):
        apply_cwd = rel[: -(len(matched) + 1)] or "/"
    elif file_path.parent.is_dir():
        apply_cwd = str(file_path.parent)
    else:
        apply_cwd = None
    # `git apply --check` validates without applying.
    proc = subprocess.run(
        ["git", "apply", "--check", "-"],
        input=diff,
        capture_output=True,
        text=True,
        cwd=apply_cwd,
    )
    if proc.returncode != 0:
        # git apply rejected the diff — LLM diffs very often carry slightly-wrong
        # context/line numbers. Fall back to whitespace-tolerant hunk application
        # (treat each hunk as a flexible search/replace) before giving up.
        fb = _apply_diff_flexibly(before_bytes.decode("utf-8", errors="replace"), diff)
        if fb is not None:
            file_path.write_text(fb, encoding="utf-8")
            after_bytes = file_path.read_bytes()
            return EditResult(
                True, [str(file_path)],
                {str(file_path): _sha256(before_bytes)},
                {str(file_path): _sha256(after_bytes)},
            )
        return EditResult(
            False, [], {}, {},
            f"git apply --check failed: {proc.stderr.strip() or proc.stdout.strip()}",
        )
    proc2 = subprocess.run(
        ["git", "apply", "-"],
        input=diff,
        capture_output=True,
        text=True,
        cwd=apply_cwd,
    )
    if proc2.returncode != 0:
        # Restore — `git apply` is supposed to be atomic but be defensive.
        file_path.write_bytes(before_bytes)
        return EditResult(
            False, [], {}, {},
            f"git apply failed unexpectedly after --check passed: {proc2.stderr}",
        )
    after_bytes = file_path.read_bytes()
    return EditResult(
        True, [str(file_path)],
        {str(file_path): _sha256(before_bytes)},
        {str(file_path): _sha256(after_bytes)},
    )


def apply_delete_file(file_path: Path) -> EditResult:
    """Delete a file (e.g. pruning a redundant/duplicate artifact a reviewer
    flagged). Refuses if absent; the caller snapshots for rollback."""
    if not file_path.is_file():
        return EditResult(False, [], {}, {}, f"file-not-found: {file_path}")
    before = file_path.read_bytes()
    file_path.unlink()
    rel = str(file_path)
    # A deleted file has NO after-hash — recording an empty string violates the
    # Sha256Field pattern on ImplementerLogEntry.after_hashes and crashes the
    # whole revision run (ValidationError), turning a LEGITIMATE deletion (e.g.
    # "remove the redundant checksums.csv" — exactly what a data-quality reviewer
    # asks for) into a zero-success round. The deletion is fully captured by
    # files_modified + before_hashes; absence from after_hashes signals removal.
    return EditResult(True, [rel], {rel: _sha256(before)}, {})


def apply_move_file(from_path: Path, to_path: Path) -> EditResult:
    """Move/rename a file (e.g. relocating a misplaced log/checksum manifest a
    reviewer flagged). Refuses if the source is absent; creates dest parents."""
    if not from_path.is_file():
        return EditResult(False, [], {}, {}, f"file-not-found: {from_path}")
    if to_path.exists():
        return EditResult(False, [], {}, {}, f"destination-exists: {to_path}")
    before = from_path.read_bytes()
    to_path.parent.mkdir(parents=True, exist_ok=True)
    to_path.write_bytes(before)
    from_path.unlink()
    rf, rt = str(from_path), str(to_path)
    return EditResult(True, [rf, rt], {rf: _sha256(before)}, {rt: _sha256(before)})


def _verify_changed_python(paths: list[str]) -> str | None:
    """Compile every changed/created ``.py`` file. Returns a human-readable error
    on the FIRST syntax error, else None. The cheap, universal guard against the
    implementer leaving broken Python behind — applied to research code edits so
    a revision can never degrade the analysis into an un-importable state."""
    import py_compile

    for p in paths:
        if not p.endswith(".py"):
            continue
        fp = Path(p)
        if not fp.is_file():
            continue
        try:
            py_compile.compile(str(fp), doraise=True)
        except py_compile.PyCompileError as exc:
            return f"{fp.name}: {str(exc).splitlines()[-1][:160]}"
        except (OSError, ValueError) as exc:  # pragma: no cover - defensive
            return f"{fp.name}: {type(exc).__name__}: {exc}"
    return None


# --- LaTeX compile gate (FR-003 step e, FR-012) ----------------------------

def _compile_paper(source_dir: Path, *, timeout: float = 300.0) -> tuple[bool, str]:
    """Recompile the paper via `lualatex`. Returns (success, log_tail).

    Single-pass compile — fast enough for per-task validation. The
    publisher's final compile (T040 onward) does the full bibtex +
    multi-pass dance.
    """
    main_tex = source_dir / "main.tex"
    if not main_tex.is_file():
        # Try main-llmxive.tex as a fallback name used by the restyle.
        main_tex = source_dir / "main-llmxive.tex"
    if not main_tex.is_file():
        return False, "no main.tex / main-llmxive.tex in source dir"
    proc = subprocess.run(
        ["lualatex", "-interaction=nonstopmode", "-halt-on-error", main_tex.name],
        cwd=source_dir,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    tail = (proc.stdout or "").splitlines()[-30:]
    return proc.returncode == 0, "\n".join(tail)


# --- Per-task snapshot/apply/rollback orchestration ------------------------

def _snapshot(paths: list[Path]) -> dict[Path, bytes]:
    return {p: p.read_bytes() if p.is_file() else b"" for p in paths}


def _restore(snapshot: dict[Path, bytes]) -> None:
    for p, content in snapshot.items():
        if content:
            p.write_bytes(content)
        elif p.is_file():
            p.unlink()


# --- LLM-edit JSON parsing -------------------------------------------------

_JSON_BLOCK_RE = re.compile(
    r"\{(?:[^{}\\\"]|\\.|\"(?:[^\"\\]|\\.)*\")*\}", re.DOTALL
)


#: Edit kinds the implementer understands. search_and_replace / unified_diff
#: modify file content; move_file / delete_file are structural (relocate or prune
#: a file) — needed for review concerns like "relocate logs/ -> docs/" or "prune
#: redundant documents" that pure content edits cannot satisfy.
_EDIT_KINDS = {"search_and_replace", "unified_diff", "move_file", "delete_file"}

# Map an action item's INTENT to the edit KIND that satisfies it. The dominant
# failure mode is the implementer answering EVERY concern with an additive
# new-file edit — so "consolidate the three manifests" or "remove the redundant
# doc" spawns a fourth file and the hygiene/consolidation concern never resolves.
# A deterministic hint (the LLM still produces the actual edit and may override)
# steers it to delete_file / move_file when the concern's verbs call for it.
_OP_PRUNE_RE = re.compile(
    r"\b(consolidat|deduplicat|de-duplicat|redundan|duplicat|remove\b|removal\b|"
    r"delete\b|prune|drop\s+the|collapse\s+(?:the|these|into)|"
    r"merge\s+(?:the\s+|these\s+)?\w+\s+(?:into|files|docs|manifests)|"
    r"single\s+(?:authoritative|source|manifest))",
    re.I,
)
_OP_RELOCATE_RE = re.compile(
    r"\b(relocat|misplac|rename\b|move\s+(?:the\s+)?\S|"
    r"wrong\s+(?:location|place|director|folder)|"
    r"belongs?\s+(?:under|in|elsewhere)|"
    r"should\s+(?:be\s+)?(?:under|in|moved|relocated))",
    re.I,
)
_OP_CREATE_RE = re.compile(
    r"\b(missing\b|absent\b|add\s+a\b|create\s+a\b|provide\s+a\b|introduce\s+a\b|"
    r"there\s+is\s+no\b|no\s+\w+\s+file)",
    re.I,
)

_OP_HINTS: dict[str, str] = {
    "prune": (
        "**Operation hint:** this concern asks you to CONSOLIDATE / REMOVE a "
        "redundant or duplicate artifact. The correct edit is almost certainly "
        "`delete_file` (or `move_file` to merge) targeting the specific file(s) "
        "the concern names — do NOT create a new file or add another document. "
        "Override only if the concern truly requires a different operation."
    ),
    "relocate": (
        "**Operation hint:** this concern asks you to RELOCATE a misplaced file. "
        "The correct edit is `move_file` (current path → correct path) — do NOT "
        "duplicate the content into a new file."
    ),
    "create": (
        "**Operation hint:** this concern names content that is genuinely MISSING. "
        "Prefer modifying / completing an EXISTING file if a suitable one exists "
        "(many 'missing' items are really thin placeholders to fill in); create a "
        "new file (unified_diff against /dev/null) only if none does."
    ),
}

# --- Compute-and-fill: ground "fill in the computed value" tasks in REAL data --
# Research reviewers routinely block on reproducibility docs that still carry
# placeholders requiring analysis-computed numbers ("fill in the actual counts /
# coverage % / VIF"). A text-editing implementer cannot invent those without
# hallucinating (forbidden — empirical values MUST trace to harness output). So
# for such a task we surface the project's REAL execution artifacts (the
# harness-recorded outputs) as a value source, and GUARD that any result-like
# number the edit introduces actually appears in them.

_COMPUTE_CUE = re.compile(
    r"\bfill(?:\s+in|\s+out)?\b|\bpopulate\b|\bplaceholder|\bTBD\b|\bnan\b"
    # "<exact|actual|real|computed|concrete|true> ... <count|number|value|…>"
    r"|\b(?:exact|actual|real|computed|concrete|true)\s+(?:\w+[\s‑-]+){0,3}"
    r"(?:count|number|value|figure|percentage|vif|coverage|total|statistic)"
    # "<insert|report|state|record|provide|specify> the <exact|actual|total|number|count>"
    r"|\b(?:insert|report|state|record|provide|specify|compute)\s+(?:the\s+)?"
    r"(?:exact|actual|total|real|number|count|computed)"
    r"|\bnumber\s+of\b|\btotal\s+(?:number|count|excluded|records|rows|knots|of)\b"
    r"|\bcomputed\b|coverage\s*%|\bcounts?\s+(?:per|of|per‑crossing|per-crossing)\b"
    r"|replace\s+.*\b(?:nan|tbd|placeholder)",
    re.I,
)
# A "result-like" literal: a decimal, or an integer of 3+ digits (thousands-
# separated allowed). Small integers (0,1,2,5,10,90) are too ambiguous to gate —
# they appear as percentages/thresholds in prose and would false-positive.
_RESULT_NUM_RE = re.compile(r"\b\d{1,3}(?:,\d{3})+\b|\b\d+\.\d+\b|\b\d{3,}\b")


def _is_compute_required(text: str) -> bool:
    """True when an action item asks to fill/replace a value that must be
    COMPUTED from the analysis (not authored as prose)."""
    return bool(_COMPUTE_CUE.search(text or ""))


def _result_numbers(text: str) -> set[str]:
    """Normalized result-like numeric tokens in ``text`` (commas stripped)."""
    return {m.group(0).replace(",", "") for m in _RESULT_NUM_RE.finditer(text or "")}


#: Skip artifacts larger than this when building the compute-and-fill context.
#: Raw data dumps (e.g. PROJ-552's 190 MB knot_atlas_raw.json) hold no
#: report-ready values and would be ruinous to load/parse on every fill task.
_COMPUTE_FILE_MAX_BYTES = 8_000_000
#: A small CSV/JSON is a computed REPORT (vif_report.csv, *_report.json) whose
#: cell/leaf VALUES are the point — surface them verbatim and whitelist them.
_COMPUTE_SMALL_CSV_ROWS = 60
#: Recurse leaf-value extraction this deep into small JSON reports.
_COMPUTE_JSON_DEPTH = 3


def _collect_json_numbers(obj: object, *, depth: int) -> list[tuple[str, object]]:
    """Flatten ``(dotted-key, scalar)`` pairs from a small JSON report up to
    ``depth`` levels — so nested computed scalars (e.g. ``{"vif": {"crossing":
    1.07}}``) are surfaced + whitelisted, not just top-level keys."""
    out: list[tuple[str, object]] = []

    def walk(o: object, prefix: str, d: int) -> None:
        if d < 0:
            return
        if isinstance(o, dict):
            for k, v in list(o.items())[:40]:
                walk(v, f"{prefix}.{k}" if prefix else str(k), d - 1)
        elif isinstance(o, list):
            for i, v in enumerate(o[:20]):
                walk(v, f"{prefix}[{i}]", d - 1)
        elif isinstance(o, bool):
            return
        elif isinstance(o, (int, float, str)):
            out.append((prefix, o))

    walk(obj, "", depth)
    return out


def _computation_context(
    project_dir: Path, *, project_id: str, repo: Path, max_chars: int = 6000,
) -> tuple[str, set[str]]:
    """Summarize the project's REAL computed artifacts into a compact block of
    values, plus the set of result-like numeric tokens that literally appear in
    them (the traceability whitelist). Returns ``("", set())`` when nothing is
    available (the implementer then can't fill computed values — and the guard
    rejects any it tries to invent).

    Sources the EXECUTION-recorded primary artifacts AND a bounded scan of the
    project's ``data/`` tree: the analysis writes many computed report files
    (``vif_report.csv``, ``*_report.json``, coverage/count tables) that are not
    in the primary-artifacts list yet hold the EXACT values reviewers ask to
    fill — the PROJ-552 placeholder stall, where VIF/coverage/excluded-count
    placeholders could never be filled because their source files were invisible
    to compute-and-fill.
    """
    from llmxive.state import execution_status

    rec = execution_status.load(project_id, repo_root=repo) or {}
    recorded = [str(a) for a in (rec.get("artifacts") or [])]
    scanned: list[str] = []
    data_dir = project_dir / "data"
    if data_dir.is_dir():
        for p in sorted(data_dir.rglob("*")):
            if p.is_file() and p.suffix.lower() in (".csv", ".json"):
                scanned.append(str(p.relative_to(project_dir)))
    rels = list(dict.fromkeys(recorded + scanned))  # dedup, recorded first

    blocks: list[str] = []
    traceable: set[str] = set()
    for rel in rels:
        p = (project_dir / rel)
        if not p.is_file():
            continue
        suf = p.suffix.lower()
        try:
            if suf in (".csv", ".json") and p.stat().st_size > _COMPUTE_FILE_MAX_BYTES:
                # Raw dump (e.g. 190 MB knot_atlas_raw.json): note it, don't parse.
                blocks.append(f"- `{rel}`: large data file ({p.stat().st_size} bytes; not parsed)")
                continue
            if suf in (".png", ".jpg", ".jpeg", ".pdf", ".svg"):
                blocks.append(f"- `{rel}`: figure artifact")
            elif suf == ".csv":
                import csv

                with p.open(encoding="utf-8", errors="replace", newline="") as f:
                    reader = csv.reader(f)
                    rows = []
                    for i, row in enumerate(reader):
                        rows.append(row)
                        if i >= 50000:  # bound huge artifacts
                            break
                if not rows:
                    continue
                header = rows[0]
                ndata = max(0, len(rows) - 1)
                traceable.add(str(ndata))
                if ndata <= _COMPUTE_SMALL_CSV_ROWS:
                    # Small computed REPORT — the cell values ARE the result
                    # (e.g. vif_report.csv: variable,VIF / crossing_number,1.078).
                    # Surface every cell and whitelist its result-like numbers.
                    blocks.append(f"- `{rel}` ({ndata} data rows):")
                    for r in rows:
                        line = " | ".join(r)
                        blocks.append(f"    {line}")
                        traceable |= _result_numbers(line)
                else:
                    blocks.append(
                        f"- `{rel}`: {ndata} data rows; columns: "
                        f"{', '.join(header[:24])}"
                    )
                    # Per-column non-empty count (real coverage/null stats).
                    for ci, col in enumerate(header[:24]):
                        nonempty = sum(
                            1 for r in rows[1:] if ci < len(r) and r[ci].strip() not in ("", "nan", "NaN", "NA")
                        )
                        if nonempty != ndata:
                            blocks.append(f"    - column `{col}`: {nonempty}/{ndata} non-empty")
                        traceable.add(str(nonempty))
            elif suf == ".json":
                import json as _json

                d = _json.loads(p.read_text(encoding="utf-8", errors="replace"))
                if isinstance(d, list):
                    blocks.append(f"- `{rel}`: JSON array of {len(d)} items")
                    traceable.add(str(len(d)))
                elif isinstance(d, dict):
                    blocks.append(f"- `{rel}`: JSON report; values:")
                    for k, v in _collect_json_numbers(d, depth=_COMPUTE_JSON_DEPTH):
                        if isinstance(v, (int, float)):
                            blocks.append(f"    - {k} = {v}")
                            traceable.add(str(v))
            else:
                continue
        except Exception:
            continue
    text = "\n".join(blocks)
    if len(text) > max_chars:
        text = text[:max_chars] + "\n…(truncated)"
    return text, traceable


def _untraceable_result_numbers(
    before: str, after: str, *, traceable: set[str], allow: set[str],
) -> set[str]:
    """Result-like numbers the edit INTRODUCED that trace to NEITHER the real
    artifacts (``traceable``) NOR text the implementer was legitimately given
    (``allow`` — the action item + the pre-edit file). A non-empty result means
    the edit fabricated a statistic and must be rolled back."""
    introduced = _result_numbers(after) - _result_numbers(before)
    ok = traceable | allow
    return {n for n in introduced if n not in ok}


# --- Regenerate a stale GENERATED report by running its producer script -------
# Reproducibility docs (docs/reproducibility/*.md) are written by project
# scripts (code/analysis/*.py). When a generator EXISTS but was never wired into
# the run-book, its doc ships as a placeholder stub the data-quality reviewer
# (correctly) blocks on — and for a DERIVED value (e.g. a coverage %) the
# anti-fabrication guard rightly forbids the LLM to compute it. The fix is not to
# hand-edit the doc but to RUN its generator: the values then come from the
# project's own analysis of its real data (no hallucination). Fully general — any
# project with a stale generated report.
_PLACEHOLDER_RE = re.compile(
    r"PLACEHOLDER|\bTBD\b|\bTKTK\b|\bFIXME\b|\bXXX\b|<[A-Z_]{3,}>", re.I
)


def _doc_generator(project_dir: Path, doc_rel: str) -> Path | None:
    """Return the UNIQUE ``code/**/*.py`` script whose source references this
    doc's path/basename (it writes the doc), or None when absent/ambiguous."""
    code_dir = project_dir / "code"
    if not code_dir.is_dir():
        return None
    rel_posix = Path(doc_rel).as_posix()
    base = Path(doc_rel).name
    exact: list[Path] = []
    by_name: list[Path] = []
    for p in code_dir.rglob("*.py"):
        sp = str(p)
        if "/.venv/" in sp or "__pycache__" in sp:
            continue
        try:
            src = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if rel_posix in src:
            exact.append(p)
        elif base in src:
            by_name.append(p)
    if len(exact) == 1:
        return exact[0]
    if not exact and len(by_name) == 1:
        return by_name[0]
    return None


def _regenerate_generated_doc(
    project_dir: Path, doc_path: Path, *, timeout_s: int = 600,
) -> tuple[bool, str]:
    """Run the script that produces ``doc_path`` in the project venv to refresh
    it with REAL computed values. Returns (regenerated_with_fewer_placeholders,
    log). Never raises — a missing generator / failed run just returns False."""
    from llmxive import sandbox

    rel = doc_path.relative_to(project_dir).as_posix()
    gen = _doc_generator(project_dir, rel)
    if gen is None:
        return False, f"no unique generator script found for {rel}"
    before = doc_path.read_text(encoding="utf-8", errors="replace") if doc_path.is_file() else ""
    before_ph = len(_PLACEHOLDER_RE.findall(before))
    gen_rel = gen.relative_to(project_dir).as_posix()
    try:
        res = sandbox.run_in_venv(
            project_dir=project_dir, args=[gen_rel], timeout_s=timeout_s,
            extra_env={"PYTHONPATH": str((project_dir / "code").resolve())},
        )
    except Exception as exc:  # never propagate — fall back to the LLM edit
        return False, f"generator `{gen_rel}` errored: {exc}"
    tail = ((res.stdout or "") + "\n" + (res.stderr or ""))[-600:]
    if not res.ok:
        return False, f"generator `{gen_rel}` exited {res.returncode}: {tail}"
    after = doc_path.read_text(encoding="utf-8", errors="replace") if doc_path.is_file() else ""
    after_ph = len(_PLACEHOLDER_RE.findall(after))
    return (after != before and after_ph < before_ph), (
        f"ran `{gen_rel}` (placeholders {before_ph} -> {after_ph})"
    )


def _classify_edit_operation(text: str) -> str | None:
    """Best-effort intent → edit-kind hint key: 'prune' | 'relocate' | 'create'
    | None (modify/default). Prune outranks create (a 'consolidate' concern names
    files to remove, not add); relocate outranks create likewise."""
    t = " ".join((text or "").split())
    if _OP_PRUNE_RE.search(t):
        return "prune"
    if _OP_RELOCATE_RE.search(t):
        return "relocate"
    if _OP_CREATE_RE.search(t):
        return "create"
    return None


def _force_blocker_rereview(project_id: str, *, track: str, repo: Path) -> int:
    """After a successful revision round, clear the review records of every
    specialist whose MOST-RECENT verdict is not ``accept``, so the coverage gate
    re-dispatches exactly those blockers to re-judge the revised artifacts.

    This is the missing link in research-stage convergence: review staleness is
    keyed on the feature ``tasks.md`` hash, but a research revision edits
    code/data/docs (never ``tasks.md``), so a blocking verdict can never go stale
    on its own — the fixed concern is never re-reviewed and the panel loops to
    ``MAX_REVISION_ROUNDS`` without ever converging. Accepts are LEFT in place
    (the research gate accepts on >=1 accept ever; the paper gate on most-recent
    accept), so we never re-roll a reviewer that already passed. Returns the
    number of records cleared.
    """
    from llmxive.state import reviews as reviews_store

    stage = "research" if track == "research" else "paper"
    records = reviews_store.list_for(project_id, stage=stage, repo_root=repo)
    if not records:
        return 0
    latest: dict[str, object] = {}
    for r in records:
        cur = latest.get(r.reviewer_name)
        if cur is None or r.reviewed_at > cur.reviewed_at:  # type: ignore[attr-defined]
            latest[r.reviewer_name] = r
    blockers = {
        name for name, rec in latest.items()
        if rec.verdict != "accept"  # type: ignore[attr-defined]
    }
    if not blockers:
        return 0
    return reviews_store.delete_for_specialists(
        project_id, blockers, stage=stage, repo_root=repo,
    )


def _rerun_analysis_after_code_revision(project_id: str, *, repo: Path) -> bool:
    """After a research revision edits analysis CODE, RE-RUN the project's
    run-book so the change actually EXECUTES.

    This closes the revision-loop gap: the initial implementation runs through
    the IN_PROGRESS execute-and-gate loop, but the post-review revision loop
    only edited files — a revision that ADDS a computation never ran, so the
    value was never produced and the re-review kept seeing it missing. Now a
    code-touching revision re-runs the analysis, which:

      * regenerates real artifacts/values (so compute-and-fill + the re-review
        see the post-revision results), and
      * records any run error to ``execution_status`` so the
        implementation-correctness/completeness reviewers (which surface
        ``execution_evidence``) flag it → the next revision round fixes it
        (self-correcting, bounded by the per-step revision cap).

    Bounded timeouts keep a revision tick affordable. Returns ``ok``.
    """
    from llmxive.execution.analysis_runner import run_analysis
    from llmxive.state import execution_status

    project_dir = repo / "projects" / project_id
    try:
        res = run_analysis(
            project_dir, per_cmd_timeout_s=600, overall_deadline_s=3600.0,
        )
    except Exception as exc:  # never let a re-run crash the revision tick
        logger.warning("post-revision analysis re-run errored for %s: %s", project_id, exc)
        return False
    failures = [
        f"{r.command} -> rc={r.returncode}"
        + (f"\n    {r.tail.strip()[-400:]}" if not r.ok and r.tail else "")
        for r in res.commands if not r.ok
    ]
    execution_status.record(
        project_id, ok=res.ok, reason=res.reason,
        artifacts=res.artifacts_produced, failures=failures, repo_root=repo,
    )
    logger.info(
        "post-revision analysis re-run for %s: ok=%s artifacts=%d",
        project_id, res.ok, len(res.artifacts_produced),
    )
    return res.ok


def _parse_llm_edit(response_text: str) -> dict[str, object] | None:
    """Parse an LLM response into a structured edit dict. Returns None if no valid
    JSON-edit block (one with a recognized ``kind``) is found."""
    # First try the whole response as JSON.
    text = response_text.strip()
    if text.startswith("```"):
        # Strip markdown fences if the model misbehaved.
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```\s*$", "", text)
    try:
        data = json.loads(text)
        if isinstance(data, dict) and data.get("kind") in _EDIT_KINDS:
            return data
    except json.JSONDecodeError:
        pass
    # Fallback: scan for a JSON-shaped substring.
    for m in _JSON_BLOCK_RE.finditer(text):
        try:
            data = json.loads(m.group(0))
            if isinstance(data, dict) and data.get("kind") in _EDIT_KINDS:
                return data
        except json.JSONDecodeError:
            continue
    return None


# --- Path-validation guard (FR-019 + safety) -------------------------------

def _validate_edit_path(
    rel_path: str, *, project_id: str, severity: str, repo_root: Path,
    track: str = "paper",
) -> Path | None:
    """Return the absolute path if the LLM's `file` field is in an
    allowed location for the given severity/track; None otherwise.

    - paper track   — writing: only `projects/<id>/paper/source/`;
                      science: also `projects/<id>/code/` and `.../data/`.
    - research track — a RESEARCH revision has no manuscript; the editable
                      surface is the research artifacts themselves, so allow
                      `projects/<id>/{code,data,specs,docs}/` for ANY severity.
    """
    norm = rel_path.replace("\\", "/")
    if norm.startswith("./"):
        norm = norm[2:]
    if not norm:
        return None
    # The LLM naturally emits PROJECT-relative paths ("paper/source/main.tex"
    # — that's how the prompt names the manuscript). Accept both repo-
    # relative and project-relative forms (spec 023: 21 of 39 real round-1
    # edits were rejected solely for this).
    candidates = [
        (repo_root / norm).resolve(),
        (repo_root / "projects" / project_id / norm).resolve(),
    ]
    proj = repo_root / "projects" / project_id

    if track == "research":
        research_bases = [
            (proj / sub).resolve()
            for sub in ("code", "data", "specs", "docs", "tests")
        ]
        proj_root = proj.resolve()
        specify_dir = (proj / ".specify").resolve()  # state internals — never edit
        for abs_path in candidates:
            try:
                abs_path.relative_to(repo_root.resolve())
            except ValueError:
                continue  # outside repo
            s = str(abs_path)
            if s.startswith(str(specify_dir)):
                continue
            if any(s.startswith(str(base)) for base in research_bases):
                return abs_path
            # Top-level project files (README.md, LICENSE.md, CONTRIBUTING.md …)
            # directly under the project root are legitimate research artifacts.
            if abs_path.parent == proj_root:
                return abs_path
        return None

    paper_src = (proj / "paper" / "source").resolve()
    science_bases = [(proj / sub).resolve() for sub in ("code", "data")]
    for abs_path in candidates:
        try:
            abs_path.relative_to(repo_root.resolve())
        except ValueError:
            continue  # outside repo
        if str(abs_path).startswith(str(paper_src)):
            return abs_path
        if severity == "science" and any(
            str(abs_path).startswith(str(base)) for base in science_bases
        ):
            return abs_path
    return None


def _resolve_edit_target(
    target: Path, *, project_id: str, repo_root: Path, track: str
) -> Path:
    """Resolve a MODIFY edit's declared path to the REAL file when the declared
    one doesn't exist (16.4% of failures: the LLM hardcodes venue-template names
    like ``neurips_2026.tex``/``acl_latex.tex`` or a guessed path instead of the
    project's actual source file). If the declared file exists, returns it
    unchanged. Callers must NOT use this for new-file (/dev/null) diffs.
    """
    if target.is_file():
        return target
    proj = repo_root / "projects" / project_id
    # A wrong .tex name -> the project's actual primary manuscript.
    if target.suffix == ".tex":
        src = proj / "paper" / "source"
        if src.is_dir():
            cand = src / _find_primary_tex(src)
            if cand.is_file():
                return cand
    # Otherwise: a UNIQUE same-basename file within the track's allowed bases.
    if track == "research":
        bases = [proj / s for s in ("code", "data", "specs", "docs", "tests")]
    else:
        bases = [proj / "paper" / "source", proj / "code", proj / "data"]
    hits: list[Path] = []
    for base in bases:
        if base.is_dir():
            hits += [
                p for p in base.rglob(target.name)
                if p.is_file() and "/.venv/" not in str(p)
            ]
    return hits[0] if len(hits) == 1 else target


# --- Implementer agent class -----------------------------------------------

class LLMXiveImplementer(Agent):
    """LLM-driven implementer agent. Picks up `READY_FOR_IMPLEMENTATION`
    projects, processes each task in the revision spec, transitions to
    `PAPER_REVIEW` when done."""

    def build_messages(self, ctx: AgentContext) -> list[ChatMessage]:
        # Implementer dispatches multiple LLM calls (one per task), not
        # one — so the standard build_messages → single-call pattern
        # doesn't apply. We override run() directly. build_messages is
        # required by the ABC; return a sentinel that's never sent.
        return [ChatMessage(role="user", content="(unused — see run())")]

    def handle_response(self, ctx: AgentContext, response: ChatResponse) -> list[str]:
        return []

    def run(self, ctx: AgentContext) -> RunLogEntry:
        started = datetime.now(UTC)
        outcome = Outcome.SUCCESS
        failure_reason: str | None = None
        outputs: list[str] = []
        backend_used = self.entry.default_backend
        model_used = self.entry.default_model
        repo = _repo_root()

        try:
            project = project_state.load(ctx.project_id, repo_root=repo)
            if project is None:
                raise FileNotFoundError(
                    f"no project state for {ctx.project_id}"
                )
            # Spec 015 T042: the 3 transient revision stages are gone.
            # The implementer now picks up any project at PAPER_REVIEW /
            # RESEARCH_REVIEW (or AGENT_BLOCKED — for a one-shot retry
            # after operator unblock) that carries a non-empty
            # ``revision_spec_path`` pointing at an auto-revisions round
            # dir written by the convergence engine's adapter.
            _IMPLEMENTABLE = {
                Stage.PAPER_REVIEW,
                Stage.RESEARCH_REVIEW,
                Stage.AGENT_BLOCKED,
            }
            if project.current_stage not in _IMPLEMENTABLE or not project.revision_spec_path:
                outcome = Outcome.SKIPPED
                failure_reason = (
                    f"current_stage={project.current_stage.value} "
                    f"(expected one of {{paper_review, research_review, "
                    f"agent_blocked}}) or empty revision_spec_path "
                    f"({project.revision_spec_path!r}); no-op"
                )
                return self._emit_run_log(
                    ctx, started, outcome, failure_reason, outputs,
                    backend_used, model_used,
                )

            # Derive the round number from the revision_spec_path the
            # revision_planner set (e.g. `.../round-3` → 3) rather than
            # counting existing dirs. The planner and the implementer
            # share the same `round-N` directory; the implementer writes
            # its log INTO that directory next to the planner's
            # tasks.md + action items.
            round_number = self._derive_round_number(project.revision_spec_path)
            self._round_n_cached = round_number
            project_dir = repo / "projects" / project.id
            paper_dir = project_dir / "paper"
            source_dir = paper_dir / "source"

            # Track determines what the revision edits and whether a paper is
            # compiled. A RESEARCH revision edits the project's research artifacts
            # (code/specs/docs/data) and has NO manuscript to compile; a PAPER
            # revision edits paper/source and recompiles. For an AGENT_BLOCKED
            # retry, infer the track from whether a manuscript exists.
            track = (
                "research"
                if project.current_stage == Stage.RESEARCH_REVIEW
                else "paper"
                if project.current_stage == Stage.PAPER_REVIEW
                else (
                    "paper"
                    if (source_dir / "main.tex").is_file()
                    or (source_dir / "main-llmxive.tex").is_file()
                    else "research"
                )
            )

            tasks = _read_tasks_md(repo / project.revision_spec_path / "tasks.md")
            action_items = _read_action_items(repo / project.revision_spec_path)

            log_entries: list[ImplementerLogEntry] = []
            success_count = 0
            for task in tasks:
                outcome_entry = self._process_task(
                    task=task,
                    action_item=action_items.get(task["id"], {}),
                    project_id=project.id,
                    source_dir=source_dir,
                    repo_root=repo,
                    track=track,
                    project_dir=project_dir,
                )
                log_entries.append(outcome_entry)
                if outcome_entry.status == "done":
                    success_count += 1

            ended = datetime.now(UTC)
            tasks_done = sum(1 for e in log_entries if e.status == "done")
            tasks_failed = sum(1 for e in log_entries if e.status == "compile-failed")
            tasks_skipped = sum(1 for e in log_entries if e.status == "skipped")
            tasks_file_nf = sum(1 for e in log_entries if e.status == "file-not-found")
            tasks_needs_ext = sum(1 for e in log_entries if e.status == "needs-external-data")

            # Final recompile + author add only if ≥1 task succeeded.
            final_compile_ok = False
            compile_deferred = False  # lualatex absent in this lane (see below)
            pdf_hash: str | None = None
            pdf_bytes_n: int | None = None
            author_added = False
            author_entry: AuthorEntry | None = None
            # Paper post-processing (author block, \paperstatus, lualatex recompile)
            # applies ONLY to paper-track revisions. A research revision has no
            # manuscript — success means its edits applied; re-review follows.
            if success_count > 0 and track == "paper":
                # Author addition (FR-006..FR-008).
                metadata_path = paper_dir / "metadata.json"
                author_added = authors_module.add_implementer(
                    metadata_path,
                    agent_name=CANONICAL_IMPLEMENTER_NAME,
                    agent_version=self.entry.prompt_version,
                    model_name=self.entry.default_model,
                    backend=self.entry.default_backend.value,
                    first_contributed_at=ended,
                )
                # Update LaTeX \author{} block.
                all_authors = authors_module.list_authors(metadata_path)
                for tex in source_dir.glob("*.tex"):
                    try:
                        authors_module.update_latex_author_block(tex, all_authors)
                    except ValueError:
                        continue  # no \author{} and no \begin{document} in this file
                # Inject \paperstatus{Auto-Reviewed} (FR-022, US4).
                _inject_paperstatus(source_dir, "Auto-Reviewed")
                if author_added:
                    author_entry = AuthorEntry(
                        name=CANONICAL_IMPLEMENTER_NAME,
                        kind="llm",
                        agent_version=self.entry.prompt_version,
                        model_name=self.entry.default_model,
                        backend=self.entry.default_backend.value,
                        first_contributed_at=ended,
                    )
                # Final recompile (FR-010). Compilation needs lualatex. When it
                # is ABSENT from THIS lane (an environment gap — vs BROKEN LaTeX),
                # DEFER rather than crash: the edits are valid and the
                # authoritative compile + paper_complete gate run in a
                # TeX-equipped lane (paper-compile / paper-write / review).
                # Letting subprocess raise FileNotFoundError here marked good
                # revisions FAILED -> zero-success rounds -> agent_blocked (61
                # real failures). Graceful degradation keeps the revision
                # successful; the compile is just not verified in this lane.
                compile_deferred = shutil.which("lualatex") is None
                if compile_deferred:
                    logger.warning(
                        "%s: lualatex absent in this environment — deferring "
                        "paper compile to a TeX-equipped lane (edits applied, "
                        "re-review proceeds)",
                        project.id,
                    )
                else:
                    ok, _ = _compile_paper(source_dir)
                    final_compile_ok = ok
                    if ok:
                        pdf = source_dir / (Path(_find_primary_tex(source_dir)).stem + ".pdf")
                        if pdf.is_file():
                            pdf_b = pdf.read_bytes()
                            pdf_hash = _sha256(pdf_b)
                            pdf_bytes_n = len(pdf_b)
                            # Replace paper/pdf/main.pdf with the new build.
                            out_pdf = paper_dir / "pdf" / "main.pdf"
                            out_pdf.parent.mkdir(parents=True, exist_ok=True)
                            out_pdf.write_bytes(pdf_b)
                            outputs.append(str(out_pdf.relative_to(repo)))

            # Persist round logs.
            log = ImplementerLog(
                round_number=round_number,
                project_id=project.id,
                revision_spec_path=str(project.revision_spec_path),
                implementer_agent=CANONICAL_IMPLEMENTER_NAME,
                agent_version=self.entry.prompt_version,
                model_name=self.entry.default_model,
                backend=self.entry.default_backend.value,
                canonical_identity=(
                    f"{CANONICAL_IMPLEMENTER_NAME} ({self.entry.default_model} on "
                    f"{self.entry.default_backend.value}, {ended.strftime('%Y-%m-%d')})"
                ),
                started_at=started,
                ended_at=ended,
                duration_s=(ended - started).total_seconds(),
                exit_reason="all-tasks-processed",
                total_tasks=len(tasks),
                tasks_done=tasks_done,
                tasks_compile_failed=tasks_failed,
                tasks_file_not_found=tasks_file_nf,
                tasks_skipped=tasks_skipped,
                tasks_needs_external_data=tasks_needs_ext,
                final_compile_attempted=success_count > 0 and not compile_deferred,
                final_compile_succeeded=final_compile_ok,
                final_compile_pdf_sha256=pdf_hash,
                final_compile_pdf_bytes=pdf_bytes_n,
                author_added=author_added,
                author_entry=author_entry,
                task_outcomes=log_entries,
            )
            rh_state.save_round(project.id, round_number, log, repo_root=repo)
            outputs.append(
                f"specs/auto-revisions/{project.id}/round-{round_number}/implementer-log.yaml"
            )

            # Append summary to revision_history.yaml.
            round_summary = RevisionRound(
                round_number=round_number,
                ran_at=ended,
                implementer_agent=CANONICAL_IMPLEMENTER_NAME,
                canonical_identity=log.canonical_identity,
                tasks_done=tasks_done,
                tasks_failed=tasks_failed + tasks_file_nf + tasks_needs_ext,
                tasks_skipped=tasks_skipped,
                resulting_pdf_sha256=pdf_hash,
                implementer_log_path=outputs[-1],
                task_outcomes=[
                    {
                        "id": e.task_id,
                        "severity": e.action_item_severity or "",
                        "status": e.status,
                        "text": e.action_item_text[:200],
                    }
                    for e in log_entries
                ],
            )
            rh_state.append_round(project.id, round_summary, repo_root=repo)

            # Spec 015 T042 / FR-034: diagnostic-mode failsafe.
            # FR-015 (spec 013) introduced a 3-consecutive-zero-success
            # failsafe that simply halted at the deleted
            # ``PAPER_REVISION_BLOCKED`` stage. With T042, the failsafe
            # now LEARNS: on every consecutive zero-round we collect the
            # round's error context, run it through
            # :func:`implementer_diagnostics.classify_failure`, and:
            #   - On a classifiable failure → synthesize a Concern and
            #     write a fresh round-N+1 revision spec via the engine
            #     adapter so the NEXT implementer pass picks up the
            #     diagnosed problem AS WORK. The project stays in the
            #     active review stage with a refreshed revision spec.
            #   - On UNKNOWN (truly opaque) → halt at
            #     :class:`Stage.AGENT_BLOCKED` for operator triage.
            from llmxive.agents.implementer_diagnostics import (
                FailureClass,
                classify_failure,
                synth_kickback_from_failure,
            )
            from llmxive.convergence.revision_adapter import (
                kickback_to_revision_spec,
            )

            zero_round = success_count == 0
            new_zero_count = _bump_zero_round_counter(
                project.id, zero_round, repo_root=repo,
            )
            # The source review stage to return to depends on where the
            # round came from — paper-side projects go back to
            # PAPER_REVIEW; research-side to RESEARCH_REVIEW. We default
            # to whichever was set on the project before the run.
            source_review_stage = (
                Stage.RESEARCH_REVIEW if track == "research" else Stage.PAPER_REVIEW
            )

            failsafe_triggered = new_zero_count >= 3
            if failsafe_triggered:
                # Aggregate the round's failure context for the classifier.
                error_log_text = "\n".join(
                    (e.error_reason or "") for e in log_entries if e.error_reason
                )
                # The compile gate (lualatex) is the round's LAST command only on
                # the PAPER track. A RESEARCH round never compiles — feeding the
                # classifier "lualatex" mis-diagnoses an edit/run failure as a
                # LaTeX defect and (below) aims the kickback at a nonexistent
                # paper/source/main.tex, looping the project to AGENT_BLOCKED.
                last_command = "lualatex" if track == "paper" else None
                classification = classify_failure(
                    error_log_text, last_command=last_command,
                )
                if classification.cls == FailureClass.UNKNOWN:
                    # Truly opaque → escalate to operator triage.
                    next_stage = Stage.AGENT_BLOCKED
                    # Drop a human_input_needed.yaml so the operator
                    # surface picks it up immediately.
                    self._write_agent_blocked_marker(
                        repo, project.id,
                        classification=classification,
                        zero_count=new_zero_count,
                    )
                    # Spec 023 / FR-017: exhaustion evidence + digest feed.
                    from llmxive.state.escalations import (
                        EscalationRecord,
                        write_record,
                    )
                    try:
                        write_record(
                            EscalationRecord(
                                project_id=project.id,
                                stage=project.current_stage.value,
                                loop="implementer-zero-rounds",
                                bound=3,
                                rounds_used=new_zero_count,
                                attempts=[
                                    {
                                        "round": str(new_zero_count),
                                        "summary": "zero-success revision round",
                                        "outcome": (
                                            classification.evidence or ""
                                        )[:500],
                                    }
                                ],
                                recommended_action=(
                                    "Triage the unclassifiable implementer "
                                    "failure, then `llmxive project "
                                    "unblock-agent`."
                                ),
                            ),
                            repo_root=repo,
                        )
                    except Exception as rec_exc:
                        logger.warning(
                            "escalation-record write failed: %s", rec_exc
                        )
                    project_state.update(
                        project.id,
                        {
                            "current_stage": next_stage.value,
                            "human_escalation_reason": (
                                f"implementer failsafe: {new_zero_count} "
                                f"consecutive zero-success rounds; "
                                f"diagnostic mode could not classify the "
                                f"failure (FailureClass.UNKNOWN). "
                                f"Evidence: {classification.evidence[:200]}"
                            ),
                            "revision_spec_path": None,
                            "updated_at": ended.isoformat(),
                        },
                        repo_root=repo,
                    )
                else:
                    # Classifiable → synthesize a Concern, write a fresh
                    # round dir, route back to the source review stage so
                    # the next implementer pass picks the diagnosis up.
                    # Aim the synthesized kickback at the artifact actually under
                    # review for THIS track: the manuscript on the paper track,
                    # the research spec's tasks.md on the research track. A
                    # research project has NO paper/source/main.tex — targeting
                    # it guarantees file-not-found -> another zero round ->
                    # AGENT_BLOCKED (the PROJ-552 doom loop).
                    if track == "research":
                        research_dir = (
                            project.speckit_research_dir
                            or f"projects/{project.id}/specs"
                        )
                        artifact_rel = f"{research_dir}/tasks.md"
                    else:
                        primary = _find_primary_tex(source_dir) if source_dir.is_dir() else "paper/source/main.tex"
                        artifact_rel = (
                            f"projects/{project.id}/paper/source/{primary}"
                        )
                    next_round = round_number + 1
                    synth_kb = synth_kickback_from_failure(
                        classification,
                        project_id=project.id,
                        artifact_path=artifact_rel,
                        round_num=next_round,
                    )
                    new_spec_dir = kickback_to_revision_spec(
                        synth_kb,
                        project_id=project.id,
                        repo_root=repo,
                        round_num=next_round,
                    )
                    new_rel = new_spec_dir.relative_to(repo)
                    next_stage = source_review_stage
                    project_state.update(
                        project.id,
                        {
                            "current_stage": next_stage.value,
                            "revision_spec_path": str(new_rel),
                            "updated_at": ended.isoformat(),
                        },
                        repo_root=repo,
                    )
                    # Reset the zero-round counter — the failsafe's
                    # learning loop just produced a fresh action item;
                    # the next round STARTS over for counter purposes.
                    _bump_zero_round_counter(
                        project.id, zero_round=False, repo_root=repo,
                    )
            else:
                next_stage = source_review_stage
                # Force re-review of the blockers this round just addressed.
                # Research staleness is keyed on tasks.md (untouched by a
                # research revision), so without clearing the non-accept records
                # the fixed concern is never re-judged and the panel loops to
                # the round cap. Only when edits actually landed.
                if success_count > 0:
                    # If this research round edited analysis CODE, RE-RUN the
                    # run-book so the change actually EXECUTES (produces real
                    # values/artifacts for compute-and-fill + the re-review) and
                    # any run error is recorded for the reviewers + next round.
                    # This is the "write AND run" step for the revision loop —
                    # the initial implementation already runs via the IN_PROGRESS
                    # execute-and-gate loop; a revision that only edited files
                    # would otherwise never execute its new computation.
                    if track == "research" and any(
                        "/code/" in f
                        for e in log_entries
                        for f in (e.files_modified or [])
                    ):
                        ran_ok = _rerun_analysis_after_code_revision(
                            project.id, repo=repo,
                        )
                        logger.info(
                            "%s: post-revision analysis re-run ok=%s",
                            project.id, ran_ok,
                        )
                    cleared = _force_blocker_rereview(
                        project.id, track=track, repo=repo,
                    )
                    if cleared:
                        logger.info(
                            "%s: cleared %d non-accept review(s) to force "
                            "re-review after a successful revision round",
                            project.id, cleared,
                        )
                project_state.update(
                    project.id,
                    {
                        "current_stage": next_stage.value,
                        "revision_spec_path": None,
                        "updated_at": ended.isoformat(),
                    },
                    repo_root=repo,
                )

        except Exception as exc:
            # Agents never propagate: failures are captured into the run log
            # (outcome=FAILED) so the cron sweep continues. A ``return`` in
            # ``finally`` previously swallowed this path *and* overrode the
            # early SKIPPED return above, double-appending run-log entries
            # (B012). Set the outcome here and emit exactly once below.
            outcome = Outcome.FAILED
            failure_reason = f"{type(exc).__name__}: {exc}"
        return self._emit_run_log(
            ctx, started, outcome, failure_reason, outputs,
            backend_used, model_used,
        )

    # --- Helpers --------------------------------------------------------

    def _write_agent_blocked_marker(
        self,
        repo: Path,
        project_id: str,
        *,
        classification: FailureClassification,
        zero_count: int,
    ) -> None:
        """Drop a human_input_needed.yaml marker for the operator surface.

        Called only when the diagnostic mode cannot classify the failure
        (Stage.AGENT_BLOCKED path). The marker is the SAME shape every
        other agent uses for human escalation so the dashboard / CLI
        pickers don't need a new format."""
        marker_dir = repo / "projects" / project_id / ".specify" / "memory"
        marker_dir.mkdir(parents=True, exist_ok=True)
        marker = marker_dir / "human_input_needed.yaml"
        payload = {
            "source": "implementer_diagnostics",
            "reason": (
                f"implementer failsafe: {zero_count} consecutive "
                f"zero-success rounds; diagnostic mode could not "
                f"classify the failure (FailureClass.UNKNOWN)."
            ),
            "classification": str(classification.cls.value),
            "evidence": classification.evidence[:1000],
            "raised_at": datetime.now(UTC).isoformat(),
        }
        marker.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    def _process_task(
        self,
        *,
        task: Mapping[str, object],
        action_item: Mapping[str, object],
        project_id: str,
        source_dir: Path,
        repo_root: Path,
        track: str = "paper",
        project_dir: Path | None = None,
    ) -> ImplementerLogEntry:
        t_started = time.monotonic()
        task_id: str = str(task["id"])
        _sev = action_item.get("severity") or task.get("severity") or "writing"
        severity: str = str(_sev) if _sev else "writing"
        _it = action_item.get("text") or task.get("text") or task.get("title") or ""
        item_text: str = str(_it) if _it else ""

        # Steer edit-kind selection from the concern's intent (consolidate/remove
        # → delete_file; relocate → move_file; missing → fill/create) so the
        # implementer stops answering every concern with an additive new file.
        operation_hint = _OP_HINTS.get(_classify_edit_operation(item_text) or "", "")

        # Build the LLM prompt (track-aware).
        system_prompt = load_prompt("agents/prompts/implementer.md", repo_root=repo_root)
        if track == "research":
            # A RESEARCH revision edits the project's OWN artifacts (code / specs
            # / docs / data) — there is no manuscript. Show the authored file tree
            # plus, when the action item names a file, a window over it.
            from llmxive.agents.research_reviewer import _summarize_tree

            pdir = project_dir if project_dir is not None else source_dir.parent.parent
            # Regenerate-first: a compute-fill concern that targets a GENERATED
            # doc still carrying placeholders is best fixed by RUNNING the doc's
            # producer script (real values from the project's own analysis), not
            # by hand-editing — especially for DERIVED values (e.g. a coverage %)
            # the anti-fabrication guard rightly won't let the LLM invent. This
            # resolves the stale-generated-report stall (a generator that exists
            # but was never wired into the run-book) for ANY project.
            if _is_compute_required(item_text):
                for _m in _RESEARCH_FILE_RE.finditer(item_text):
                    _ref = _m.group(1)
                    if not _ref.endswith((".md", ".rst", ".txt")):
                        continue
                    _cand: Path | None = pdir / _ref
                    if not _cand.is_file():
                        _hits = [
                            p for p in pdir.rglob(Path(_ref).name)
                            if p.is_file() and "/.venv/" not in str(p)
                        ]
                        _cand = _hits[0] if len(_hits) == 1 else None
                    if _cand is None:
                        continue
                    try:
                        _txt = _cand.read_text(encoding="utf-8", errors="replace")
                    except OSError:
                        continue
                    if not _PLACEHOLDER_RE.search(_txt):
                        continue
                    _before_b = _cand.read_bytes()
                    _regenerated, _gen_log = _regenerate_generated_doc(pdir, _cand)
                    logger.info(
                        "%s: regenerate-first for %s — %s",
                        project_id, _ref, _gen_log,
                    )
                    if _regenerated:
                        _after_b = _cand.read_bytes()
                        _rel = str(_cand)
                        return ImplementerLogEntry(
                            task_id=task_id,
                            status="done",
                            action_item_severity=cast(Literal["writing", "science"], severity) if severity in {"writing", "science"} else None,
                            action_item_text=item_text,
                            files_modified=[_rel],
                            before_hashes={_rel: _sha256(_before_b)},
                            after_hashes={_rel: _sha256(_after_b)},
                            duration_s=time.monotonic() - t_started,
                            error_reason=f"regenerated via producer script: {_gen_log}",
                        )
            # Compute-and-fill: when the concern needs an analysis-computed value,
            # surface the project's REAL execution-artifact values so the
            # implementer fills from DATA, never invention. comp_traceable is the
            # whitelist the post-apply guard checks introduced numbers against.
            comp_traceable: set[str] = set()
            computation_context = ""
            if _is_compute_required(item_text):
                comp_ctx, comp_traceable = _computation_context(
                    pdir, project_id=project_id, repo=repo_root,
                )
                if comp_ctx:
                    computation_context = (
                        "## Real computed values (from the analysis artifacts) — "
                        "fill ONLY from these\n\n"
                        f"{comp_ctx}\n\n"
                        "These are the project's actual harness-produced outputs. "
                        "Replace every placeholder / TBD the concern names with the "
                        "matching REAL number above. MAP each placeholder to its "
                        "most semantically-appropriate value, even when the names "
                        "differ — e.g. a `TOTAL` / `N` / 'dataset size' placeholder "
                        "= the cleaned dataset's data-row count; a 'missing' / "
                        "'uncomputable' / 'missing_invariant_flags' count = the "
                        "matching `missing_*` / `invalid_*` summary value; a VIF "
                        "field = the VIF cell for that variable. Prefer filling over "
                        "skipping: only leave a placeholder if NO value above could "
                        "plausibly correspond to it. NEVER write a number that is not "
                        "present above (or already in the target file) — every "
                        "figure you insert is checked against these artifacts and a "
                        "non-matching one is rolled back, so a value you cannot find "
                        "above must stay a placeholder (note it pending analysis).\n"
                    )
            edit_prompt = render_prompt(
                "agents/prompts/implementer_edit_research.md",
                {
                    "project_id": project_id,
                    "round_number": str(self._current_round_number),
                    "revision_spec_path": str(self._revision_spec_path),
                    "task_id": task_id,
                    "severity": severity,
                    "action_item_text": item_text,
                    "operation_hint": operation_hint,
                    "computation_context": computation_context,
                    "file_tree": _summarize_tree(pdir),
                    "target_window": _research_target_window(pdir, item_text),
                },
                repo_root=repo_root,
            )
        else:
            primary_tex = _find_primary_tex(source_dir)
            # Wider window than the old 60 lines: the LLM needs enough exact
            # surrounding text to produce a search string / diff that applies.
            manuscript_window = _windowed_view(source_dir / primary_tex, item_text, window=140)
            science_note = (
                "\n- **Science-class task**: this task may modify files under "
                "`projects/<id>/code/` or `projects/<id>/data/`. Any referenced "
                "analysis script will be exec'd after the edit; non-zero exit "
                "triggers rollback.\n"
                if severity == "science" else ""
            )
            edit_prompt = render_prompt(
                "agents/prompts/implementer_edit.md",
                {
                    "project_id": project_id,
                    "round_number": str(self._current_round_number),
                    "revision_spec_path": str(self._revision_spec_path),
                    "task_id": task_id,
                    "severity": severity,
                    "action_item_text": item_text,
                    "operation_hint": operation_hint,
                    "manuscript_window": manuscript_window,
                    "science_note": str(science_note) if science_note else "",
                    # The ACTUAL primary manuscript file — arXiv-intake papers
                    # use main-llmxive.tex, not main.tex (spec 023 defect #10:
                    # the hard-coded name sent every round-2 edit to a
                    # nonexistent file).
                    "primary_tex": str(primary_tex),
                },
                repo_root=repo_root,
            )

        # Single LLM call per task.
        try:
            response = chat_with_fallback(
                [
                    ChatMessage(role="system", content=system_prompt),
                    ChatMessage(role="user", content=edit_prompt),
                ],
                default_backend=self.entry.default_backend.value,
                fallback_backends=[b.value for b in self.entry.fallback_backends],
                model=self.entry.default_model,
            )
            response_text = response.text or ""
        except Exception as exc:
            return ImplementerLogEntry(
                task_id=task_id,
                status="skipped",
                action_item_severity=cast(Literal["writing", "science"], severity) if severity in {"writing", "science"} else None,
                action_item_text=item_text,
                duration_s=time.monotonic() - t_started,
                error_reason=f"LLM call failed: {type(exc).__name__}: {exc}",
            )

        edit = _parse_llm_edit(response_text)
        if edit is None:
            return ImplementerLogEntry(
                task_id=task_id,
                status="skipped",
                action_item_severity=cast(Literal["writing", "science"], severity) if severity in {"writing", "science"} else None,
                action_item_text=item_text,
                model_response_excerpt=response_text[:500],
                duration_s=time.monotonic() - t_started,
                error_reason="LLM did not emit a parseable JSON edit",
            )

        # Structural edits (move/delete a file) — for concerns that content edits
        # can't satisfy ("relocate logs/ -> docs/reproducibility/", "prune
        # redundant documents"). Handled separately from search/replace + diff.
        if edit["kind"] in ("move_file", "delete_file"):
            return self._apply_structural_edit(
                edit, project_id=project_id, repo_root=repo_root, track=track,
                severity=severity, item_text=item_text, task_id=task_id,
                response_text=response_text, t_started=t_started,
            )

        # Path validation (FR-019).
        target = _validate_edit_path(
            str(edit.get("file", "")), project_id=project_id, severity=severity,
            repo_root=repo_root, track=track,
        )
        if target is None:
            return ImplementerLogEntry(
                task_id=task_id,
                status="skipped",
                action_item_severity=cast(Literal["writing", "science"], severity) if severity in {"writing", "science"} else None,
                action_item_text=item_text,
                edit_kind=cast('Literal["search_and_replace", "unified_diff"] | None', edit.get("kind")),
                model_response_excerpt=response_text[:500],
                duration_s=time.monotonic() - t_started,
                error_reason=f"edit targets disallowed path: {edit.get('file')!r} (severity={severity})",
            )

        # Resolve a wrong/guessed filename to the REAL file for MODIFY edits
        # (the LLM often targets a venue-template name like neurips_2026.tex).
        # New-file (/dev/null) diffs are intentionally NOT resolved.
        diff_str = str(edit.get("diff", "")) if edit.get("kind") == "unified_diff" else ""
        is_new_file = bool(re.search(r"^---\s+(?:a/|b/)?/?dev/null", diff_str, re.M))
        if not is_new_file:
            target = _resolve_edit_target(
                target, project_id=project_id, repo_root=repo_root, track=track,
            )

        # Snapshot all paper-source files (any one might be touched) +
        # the target file specifically.
        snap = _snapshot([target])

        # Apply.
        if edit["kind"] == "search_and_replace":
            result = apply_search_and_replace(target, str(edit.get("search", "")), str(edit.get("replace", "")))
        elif edit["kind"] == "unified_diff":
            result = apply_unified_diff(target, str(edit.get("diff", "")))
        else:
            return ImplementerLogEntry(
                task_id=task_id,
                status="skipped",
                action_item_severity=cast(Literal["writing", "science"], severity) if severity in {"writing", "science"} else None,
                action_item_text=item_text,
                duration_s=time.monotonic() - t_started,
                error_reason=f"unknown edit kind: {edit.get('kind')!r}",
            )

        if not result.applied:
            return ImplementerLogEntry(
                task_id=task_id,
                status="skipped" if "file-not-found" not in (result.reject_reason or "") else "file-not-found",
                action_item_severity=cast(Literal["writing", "science"], severity) if severity in {"writing", "science"} else None,
                action_item_text=item_text,
                edit_kind=edit["kind"],
                model_response_excerpt=response_text[:500],
                duration_s=time.monotonic() - t_started,
                error_reason=result.reject_reason,
            )

        # Compile gate — PAPER track only. A research revision has no manuscript;
        # compiling a (non-existent) paper after every research edit would fail
        # ('no main.tex') and roll back every edit -> tasks_done=0. A research
        # edit to code/specs/docs stands once applied (science-class code edits
        # are still exec-verified below).
        if track == "paper":
            ok, log_tail = _compile_paper(source_dir)
            if not ok:
                _restore(snap)
                return ImplementerLogEntry(
                    task_id=task_id,
                    status="compile-failed",
                    action_item_severity=cast(Literal["writing", "science"], severity) if severity in {"writing", "science"} else None,
                    action_item_text=item_text,
                    edit_kind=edit["kind"],
                    files_modified=result.files_modified,
                    before_hashes=result.before_hashes,
                    after_hashes={},  # rolled back
                    model_response_excerpt=response_text[:500],
                    duration_s=time.monotonic() - t_started,
                    error_reason=f"lualatex failed: {log_tail[-200:]}",
                )

        # Research code edits must not leave broken Python (the paper track's
        # lualatex gate has no analogue here). py_compile every changed .py and
        # ROLL BACK on a syntax error, so a revision can never degrade the
        # analysis into an un-importable state.
        if track == "research":
            # Compute-and-fill guard: a "fill the computed value" edit may ONLY
            # introduce result-like numbers that trace to the real analysis
            # artifacts (or text the implementer was legitimately given). A
            # fabricated statistic (hallucinated VIF/coverage/count) is rolled
            # back — empirical values MUST trace to harness output, never the LLM.
            if _is_compute_required(item_text):
                before_map = {
                    str(p.resolve()): b.decode("utf-8", "replace")
                    for p, b in snap.items()
                }
                # NOTE: action-item numbers are deliberately NOT whitelisted — a
                # reviewer may cite an ILLUSTRATIVE example ("e.g., 342") that is
                # not a real computed value; copying it would launder a fabricated
                # figure. A real value is in ``comp_traceable`` (the artifacts);
                # anything else must come from the file's prior content.
                untraceable: set[str] = set()
                for fp in result.files_modified:
                    ap = Path(fp)
                    before = before_map.get(str(ap.resolve()), "")
                    try:
                        after = ap.read_text(encoding="utf-8", errors="replace")
                    except OSError:
                        continue
                    untraceable |= _untraceable_result_numbers(
                        before, after,
                        traceable=comp_traceable,
                        allow=_result_numbers(before),
                    )
                if untraceable:
                    _restore(snap)
                    return ImplementerLogEntry(
                        task_id=task_id,
                        status="skipped",
                        action_item_severity=cast(Literal["writing", "science"], severity) if severity in {"writing", "science"} else None,
                        action_item_text=item_text,
                        edit_kind=edit["kind"],
                        files_modified=result.files_modified,
                        model_response_excerpt=response_text[:500],
                        duration_s=time.monotonic() - t_started,
                        error_reason=(
                            "compute-and-fill guard: edit introduced result-like "
                            f"number(s) that trace to no analysis artifact: "
                            f"{sorted(untraceable)} — refusing to write invented "
                            "empirical values (rolled back)"
                        ),
                    )
            syn_err = _verify_changed_python(result.files_modified)
            if syn_err is not None:
                _restore(snap)
                return ImplementerLogEntry(
                    task_id=task_id,
                    status="compile-failed",
                    action_item_severity=cast(Literal["writing", "science"], severity) if severity in {"writing", "science"} else None,
                    action_item_text=item_text,
                    edit_kind=edit["kind"],
                    files_modified=result.files_modified,
                    before_hashes=result.before_hashes,
                    after_hashes={},  # rolled back
                    model_response_excerpt=response_text[:500],
                    duration_s=time.monotonic() - t_started,
                    error_reason=f"python syntax error after edit: {syn_err}",
                )

        # Science-class: best-effort analysis-script execution (FR-019).
        if severity == "science":
            needs_data = _run_referenced_analysis_scripts(target, repo_root=repo_root)
            if needs_data:
                return ImplementerLogEntry(
                    task_id=task_id,
                    status="needs-external-data",
                    action_item_severity="science",
                    action_item_text=item_text,
                    edit_kind=edit["kind"],
                    files_modified=result.files_modified,
                    before_hashes=result.before_hashes,
                    after_hashes=result.after_hashes,
                    model_response_excerpt=response_text[:500],
                    duration_s=time.monotonic() - t_started,
                    error_reason=needs_data,
                )

        return ImplementerLogEntry(
            task_id=task_id,
            status="done",
            action_item_severity=cast(Literal["writing", "science"], severity) if severity in {"writing", "science"} else None,
            action_item_text=item_text,
            edit_kind=edit["kind"],
            files_modified=result.files_modified,
            before_hashes=result.before_hashes,
            after_hashes=result.after_hashes,
            model_response_excerpt=response_text[:500],
            duration_s=time.monotonic() - t_started,
        )

    def _apply_structural_edit(
        self,
        edit: Mapping[str, object],
        *,
        project_id: str,
        repo_root: Path,
        track: str,
        severity: str,
        item_text: str,
        task_id: str,
        response_text: str,
        t_started: float,
    ) -> ImplementerLogEntry:
        """Apply a move_file / delete_file structural edit (validated to the
        track's allowed bases, with the same path guards as content edits)."""
        kind = str(edit["kind"])
        sev = cast(Literal["writing", "science"], severity) if severity in {"writing", "science"} else None

        def _skip(reason: str) -> ImplementerLogEntry:
            return ImplementerLogEntry(
                task_id=task_id, status="skipped", action_item_severity=sev,
                action_item_text=item_text, model_response_excerpt=response_text[:500],
                duration_s=time.monotonic() - t_started, error_reason=reason,
            )

        src_raw = str(edit.get("file") or edit.get("from") or edit.get("src") or "")
        src = _validate_edit_path(
            src_raw, project_id=project_id, severity=severity, repo_root=repo_root, track=track,
        )
        if src is None:
            return _skip(f"{kind}: disallowed/invalid source path: {src_raw!r}")
        if kind == "delete_file":
            result = apply_delete_file(src)
        else:  # move_file
            dst_raw = str(edit.get("to") or edit.get("dest") or edit.get("destination") or "")
            dst = _validate_edit_path(
                dst_raw, project_id=project_id, severity=severity, repo_root=repo_root, track=track,
            )
            if dst is None:
                return _skip(f"move_file: disallowed/invalid destination path: {dst_raw!r}")
            result = apply_move_file(src, dst)
        if not result.applied:
            return _skip(result.reject_reason or f"{kind} failed")
        return ImplementerLogEntry(
            task_id=task_id, status="done", action_item_severity=sev,
            action_item_text=item_text, files_modified=result.files_modified,
            before_hashes=result.before_hashes, after_hashes=result.after_hashes,
            model_response_excerpt=response_text[:500],
            duration_s=time.monotonic() - t_started,
        )

    @property
    def _current_round_number(self) -> int:
        return getattr(self, "_round_n_cached", 0)

    @property
    def _revision_spec_path(self) -> str:
        return getattr(self, "_revision_spec_path_cached", "")

    def _next_round_number(self, project_id: str, *, repo_root: Path) -> int:
        existing = rh_state.list_rounds(project_id, repo_root=repo_root)
        n = (max(existing) if existing else 0) + 1
        self._round_n_cached = n
        return n

    def _derive_round_number(self, revision_spec_path: str) -> int:
        """Parse the trailing `round-N` segment of the planner's
        revision_spec_path. Falls back to `_next_round_number` if the
        path doesn't end in `round-<int>`."""
        m = re.search(r"round-(\d+)/?$", revision_spec_path or "")
        if m:
            return int(m.group(1))
        # Defensive fallback — uses dir-count discovery.
        return 1

    def _emit_run_log(
        self,
        ctx: AgentContext,
        started: datetime,
        outcome: Outcome,
        failure_reason: str | None,
        outputs: list[str],
        backend_used: BackendName,
        model_used: str,
    ) -> RunLogEntry:
        ended = datetime.now(UTC)
        entry = RunLogEntry(
            run_id=ctx.run_id,
            entry_id=str(uuid4()),
            agent_name=self.name,
            project_id=ctx.project_id,
            task_id=ctx.task_id,
            inputs=ctx.inputs,
            outputs=outputs,
            backend=backend_used,
            model_name=model_used,
            prompt_version=self.entry.prompt_version,
            started_at=started,
            ended_at=ended,
            outcome=outcome,
            failure_reason=failure_reason,
            cost_estimate_usd=0.0,
        )
        runlog.append_entry(entry)
        return entry


# --- Module-level helpers --------------------------------------------------

def _find_primary_tex(source_dir: Path) -> str:
    """Return the relative name of the file containing `\\documentclass`.
    Defaults to `main.tex` if present and we can't determine; else the
    first `.tex` file alphabetically."""
    for tex in sorted(source_dir.rglob("*.tex")):
        try:
            head = tex.read_text(encoding="utf-8", errors="ignore")[:4000]
        except OSError:
            continue
        if "\\documentclass" in head:
            return tex.relative_to(source_dir).as_posix()
    main = source_dir / "main.tex"
    if main.is_file():
        return "main.tex"
    candidates = sorted(source_dir.glob("*.tex"))
    return candidates[0].name if candidates else "main.tex"


def _windowed_view(tex_path: Path, action_item_text: str, *, window: int = 60) -> str:
    """Return a windowed slice of `tex_path` centered on the line that
    most likely matches the action item. Heuristic: find the first
    keyword-overlap with the action-item text; fall back to the whole
    file (truncated) if no match."""
    if not tex_path.is_file():
        return "(file not found)"
    lines = tex_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    # Extract a few distinctive words from the action item.
    words = [
        w.lower() for w in re.findall(r"[a-zA-Z]{5,}", action_item_text)
        if w.lower() not in {"section", "appendix", "figure", "table", "should", "paper", "manuscript"}
    ][:4]
    target_idx = None
    for i, line in enumerate(lines):
        line_lower = line.lower()
        if all(w in line_lower for w in words) and words:
            target_idx = i
            break
    if target_idx is None:
        # Fall back: include the file head + tail.
        head = lines[: window // 2]
        return "\n".join(
            [f"{n+1:5d}: {ln}" for n, ln in enumerate(head)]
            + ["...", f"(file is {len(lines)} lines; full view truncated)"]
        )
    lo = max(0, target_idx - window // 2)
    hi = min(len(lines), target_idx + window // 2)
    return "\n".join(f"{n+1:5d}: {ln}" for n, ln in enumerate(lines[lo:hi], start=lo))


# A research action item often names the file it concerns (e.g.
# "code/data/validator.py should expose two flag columns"). Surface that file's
# content so the implementer can produce an exact-matching search_and_replace.
#: Any path/filename with a source-ish extension mentioned in an action item —
#: dir-prefixed ("code/x.py") OR bare ("checksums.json", "README.md").
_RESEARCH_FILE_RE = re.compile(
    r"`?([\w./+-]+\.(?:py|md|json|ya?ml|csv|tex|txt|toml|cfg|ini|sh|rst))`?"
)


def _research_target_window(
    project_dir: Path,
    action_item_text: str,
    *,
    max_files: int = 3,
    full_below: int = 260,
) -> str:
    """Show the EXACT current content of files the action item references.

    The #1 edit failure is the LLM emitting a search string / diff that doesn't
    match because it never saw the file's exact text. So for every file the action
    item names — dir-prefixed OR bare (resolved to a unique match anywhere under
    the project) — surface its FULL current content (line-numbered) when small,
    or a generous window when large, telling the model to copy search strings
    VERBATIM from it. Falls back to a directive when no existing file is named.
    """
    seen: set[Path] = set()
    blocks: list[str] = []
    skip = ("/.venv/", "/.git/", "__pycache__", "/site-packages/")
    for m in _RESEARCH_FILE_RE.finditer(action_item_text or ""):
        ref = m.group(1)
        cand: Path | None = project_dir / ref
        if not cand.is_file():
            base = Path(ref).name
            hits = [
                p for p in project_dir.rglob(base)
                if p.is_file() and not any(s in str(p) for s in skip)
            ]
            cand = hits[0] if len(hits) == 1 else None
        if cand is None or cand in seen:
            continue
        seen.add(cand)
        try:
            lines = cand.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        rel = cand.relative_to(project_dir).as_posix()
        if len(lines) <= full_below:
            body = "\n".join(f"{i + 1:5d}: {ln}" for i, ln in enumerate(lines))
            blocks.append(
                f"`{rel}` — FULL current content ({len(lines)} lines); copy any "
                f"`search` string VERBATIM from here (drop the NNN: prefix):\n{body}"
            )
        else:
            blocks.append(
                f"`{rel}` — {len(lines)} lines (windowed):\n"
                + _windowed_view(cand, action_item_text, window=140)
            )
        if len(blocks) >= max_files:
            break
    if blocks:
        return "\n\n".join(blocks)
    return (
        "(The action item does not name a specific existing file. Choose the most "
        "appropriate target from the file tree above — modify an existing file, or "
        "create a new one with a unified_diff against /dev/null.)"
    )


def _read_tasks_md(tasks_path: Path) -> list[dict[str, str]]:
    """Parse a revision spec's `tasks.md`. Returns a list of dicts with
    `id`, `severity`, `text` keys."""
    if not tasks_path.is_file():
        return []
    out: list[dict[str, str]] = []
    pat = re.compile(
        r"^- \[ \] T(\d+)\s*(?:\[P\])?\s*(?:\[([^\]]+)\])?\s+(.*)$", re.M
    )
    sev_in_text = re.compile(r"severity:\s*(writing|science|fatal)", re.IGNORECASE)
    text = tasks_path.read_text(encoding="utf-8")
    for m in pat.finditer(text):
        task_text = m.group(3).strip()
        # The bracket tag is a severity ONLY when it actually names one —
        # the revision adapter emits "[REV]" as a task-category tag with
        # the real severity inline as "(severity: writing)". Pre-023 the
        # tag was blindly taken as the severity ("REV"), which broke the
        # severity-dependent path rules for every adapter-written round.
        tag = (m.group(2) or "").strip().lower()
        if tag in {"writing", "science", "fatal"}:
            severity = tag
        else:
            sev_m = sev_in_text.search(task_text)
            severity = sev_m.group(1).lower() if sev_m else "writing"
        out.append({
            "id": m.group(1).strip(),
            "severity": severity,
            "text": task_text,
        })
    # Also accept the alternative `id: <hex>` markdown format the
    # revision_planner emits.
    alt_pat = re.compile(r"^\d+\.\s+\*\*\[([a-f0-9]+)\]\*\*\s*\(([^)]+)\)\s+(.*)$", re.M)
    for m in alt_pat.finditer(text):
        out.append({"id": m.group(1), "severity": m.group(2), "text": m.group(3).strip()})
    return out


def _read_action_items(round_dir: Path) -> dict[str, dict[str, str]]:
    """Read each action-item file (`<id>.md` or `action_<id>.md`) and
    return id → {severity, text, full_body}."""
    out: dict[str, dict[str, str]] = {}
    if not round_dir.is_dir():
        return out
    for md in round_dir.glob("*.md"):
        if md.name == "tasks.md":
            continue
        body = md.read_text(encoding="utf-8")
        m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", body, re.DOTALL)
        front: dict[str, object] = {}
        if m:
            try:
                front = yaml.safe_load(m.group(1)) or {}
            except yaml.YAMLError:
                front = {}
            text = m.group(2).strip()
        else:
            text = body
        item_id = str(front.get("id") or md.stem.replace("action_", ""))
        _sev2 = front.get("severity", "writing")
        _txt2 = front.get("text") or text
        out[item_id] = {
            "id": item_id,
            "severity": str(_sev2) if _sev2 else "writing",
            "text": (str(_txt2) if _txt2 else "")[:1000],
        }
    return out


def _inject_paperstatus(source_dir: Path, status: str) -> None:
    """Inject or update `\\paperstatus{...}` in the primary tex file
    (FR-022, US4)."""
    primary = source_dir / _find_primary_tex(source_dir)
    if not primary.is_file():
        return
    text = primary.read_text(encoding="utf-8")
    if "\\paperstatus" in text:
        text = re.sub(
            r"\\paperstatus\s*\{[^}]*\}", f"\\\\paperstatus{{{status}}}", text, count=1
        )
    else:
        text = text.replace(
            r"\begin{document}", f"\\paperstatus{{{status}}}\n\\begin{{document}}", 1,
        )
    primary.write_text(text, encoding="utf-8")


def _run_referenced_analysis_scripts(
    target: Path, *, repo_root: Path, budget_s: float = 300.0,
) -> str | None:
    """For science-class edits to `.py` files: exec the script with a
    budget. Returns None on success; a short error reason string on
    failure. Special-cases `FileNotFoundError`-style data-missing
    errors as `needs-external-data`."""
    if not target.suffix == ".py":
        return None  # nothing to run; the manuscript-only compile already passed
    try:
        proc = subprocess.run(
            ["python", str(target)],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=budget_s,
        )
    except subprocess.TimeoutExpired:
        return "analysis script timed out"
    if proc.returncode == 0:
        return None
    err = (proc.stderr or "").strip()
    if "FileNotFoundError" in err or "No such file or directory" in err:
        return f"needs-external-data: {err[-200:]}"
    return f"analysis script failed: {err[-200:]}"


def _bump_zero_round_counter(
    project_id: str, zero_round: bool, *, repo_root: Path,
) -> int:
    """Update the per-project consecutive-zero-success counter (FR-015).
    Returns the new value. Counter resets on any round with ≥1 success.
    Stored at `state/<id>.implementer.yaml`."""
    state_path = repo_root / "state" / f"{project_id}.implementer.yaml"
    state: dict[str, object] = {}
    if state_path.is_file():
        try:
            state = yaml.safe_load(state_path.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError:
            state = {}
    if zero_round:
        _czr = state.get("consecutive_zero_rounds", 0)
        state["consecutive_zero_rounds"] = (int(_czr) if isinstance(_czr, (int, float)) else 0) + 1
    else:
        state["consecutive_zero_rounds"] = 0
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(yaml.safe_dump(state, sort_keys=False), encoding="utf-8")
    _result = state["consecutive_zero_rounds"]
    return int(_result) if isinstance(_result, (int, float)) else 0
