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


def _parse_llm_edit(response_text: str) -> dict[str, object] | None:
    """Parse an LLM response into a structured edit dict. Returns None
    if no valid JSON-edit block is found. We extract the first valid
    JSON object that has a `kind` field matching `search_and_replace`
    or `unified_diff`."""
    # First try the whole response as JSON.
    text = response_text.strip()
    if text.startswith("```"):
        # Strip markdown fences if the model misbehaved.
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```\s*$", "", text)
    try:
        data = json.loads(text)
        if isinstance(data, dict) and data.get("kind") in {"search_and_replace", "unified_diff"}:
            return data
    except json.JSONDecodeError:
        pass
    # Fallback: scan for a JSON-shaped substring.
    for m in _JSON_BLOCK_RE.finditer(text):
        try:
            data = json.loads(m.group(0))
            if isinstance(data, dict) and data.get("kind") in {"search_and_replace", "unified_diff"}:
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
            (proj / sub).resolve() for sub in ("code", "data", "specs", "docs")
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
        bases = [proj / s for s in ("code", "data", "specs", "docs")]
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
                # Final recompile (FR-010).
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
                final_compile_attempted=success_count > 0,
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
                last_command = "lualatex"  # the round's compile gate
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

        # Build the LLM prompt (track-aware).
        system_prompt = load_prompt("agents/prompts/implementer.md", repo_root=repo_root)
        if track == "research":
            # A RESEARCH revision edits the project's OWN artifacts (code / specs
            # / docs / data) — there is no manuscript. Show the authored file tree
            # plus, when the action item names a file, a window over it.
            from llmxive.agents.research_reviewer import _summarize_tree

            pdir = project_dir if project_dir is not None else source_dir.parent.parent
            edit_prompt = render_prompt(
                "agents/prompts/implementer_edit_research.md",
                {
                    "project_id": project_id,
                    "round_number": str(self._current_round_number),
                    "revision_spec_path": str(self._revision_spec_path),
                    "task_id": task_id,
                    "severity": severity,
                    "action_item_text": item_text,
                    "file_tree": _summarize_tree(pdir),
                    "target_window": _research_target_window(pdir, item_text),
                },
                repo_root=repo_root,
            )
        else:
            primary_tex = _find_primary_tex(source_dir)
            manuscript_window = _windowed_view(source_dir / primary_tex, item_text)
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
_RESEARCH_PATH_RE = re.compile(r"((?:code|specs|docs|data)/[\w./+-]+\.[A-Za-z0-9]+)")


def _research_target_window(
    project_dir: Path, action_item_text: str, *, window: int = 80
) -> str:
    """Window the project file named in the action item (if any), else a directive."""
    for m in _RESEARCH_PATH_RE.finditer(action_item_text or ""):
        target = project_dir / m.group(1)
        if target.is_file():
            return f"`{m.group(1)}` (numbered):\n" + _windowed_view(
                target, action_item_text, window=window
            )
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
