"""LLMReviewer — live Reviewer-Protocol implementation backed by a chat LLM.

Wraps a backend + a per-lens panel prompt (under
``agents/prompts/panels/panel_<stage>_<lens>.md``) + the SSoT
``_shared/panel_review_block.md`` output contract into a class that
satisfies :class:`llmxive.convergence.types.Reviewer`.

The class is what unblocks the spec-015 end-to-end real-call calibration
runs (T068 prerequisite) — the registry's ``_TodoReviewer`` placeholders
fail loud when invoked; this class provides the actual implementation
each lens needs.

The reviewer:

1. Loads its lens-specific prompt + the shared output contract from
   disk (the prompt files were authored in T049-T053).
2. On ``identify``: composes a system+user message pair (system = lens
   prompt + shared block; user = the artifacts dict serialized as
   labeled sections), calls the backend, parses the YAML-frontmatter
   response, and returns the structured concerns.
3. On ``rereview``: prepends the prior concerns to the user message
   so the LLM does the diff-check the shared block describes (no
   fresh independent critique), then parses the verdict per concern.

Honest failure modes: missing prompt file → RuntimeError; unparseable
YAML frontmatter → RuntimeError; concerns missing required fields →
RuntimeError. The engine treats RuntimeError as a non-convergence
signal — no silent acceptance of a malformed review.
"""

from __future__ import annotations

import hashlib
import logging
import re
import uuid
from pathlib import Path
from typing import Any

import yaml

from llmxive.backends.base import ChatMessage
from llmxive.backends.router import chat_with_model_fallback

from . import review_cache
from .types import Concern, Verdict, coerce_severity

logger = logging.getLogger(__name__)


# Last-resort line-scan extractors: when a lens's frontmatter fails ALL YAML
# repairs (the temp=0 reviewers are deterministic, so a single malformed review
# would otherwise hard-stall the project — the live PROJ-492 tasks-panel
# "[ordering]: frontmatter is not valid YAML: while scanning a simple key").
_SALVAGE_VERDICT_RE = re.compile(r"(?mi)^[ \t]*verdict:[ \t]*([a-z_]+)")
_SALVAGE_SEV_RE = re.compile(r"^[ \t]*-?[ \t]*severity:[ \t]*([A-Za-z_]+)")
_SALVAGE_TEXT_RE = re.compile(r"^[ \t]*-?[ \t]*text:[ \t]*(\S.*?)[ \t]*$")


def _salvage_review(frontmatter: str) -> dict | None:
    """Best-effort extraction of verdict + concern (severity, text) pairs by
    line-scan when YAML parsing fails entirely. ONLY rescues a NON-accept review
    (>=1 concern with text): it never manufactures a clean accept from
    unparseable YAML, so it cannot cause a false convergence. Returns None when
    no concern can be recovered (the caller then raises honestly)."""
    vm = _SALVAGE_VERDICT_RE.search(frontmatter)
    verdict = vm.group(1).strip().lower() if vm else None
    concerns: list[dict] = []
    cur: dict | None = None
    for raw in frontmatter.splitlines():
        sm = _SALVAGE_SEV_RE.match(raw)
        tm = _SALVAGE_TEXT_RE.match(raw)
        if sm:
            if cur and cur.get("text"):
                concerns.append(cur)
            cur = {"severity": sm.group(1)}
        elif tm:
            val = tm.group(1).strip().strip("\"'")
            if cur is None:
                cur = {"severity": "requirement", "text": val}
            elif not cur.get("text"):
                cur["text"] = val
    if cur and cur.get("text"):
        concerns.append(cur)
    concerns = [c for c in concerns if c.get("text")]
    if concerns:
        return {"verdict": verdict or "minor_revision", "concerns": concerns}
    return None

# --- prompt loading -------------------------------------------------------


_SHARED_PROMPT_REL = "agents/prompts/_shared/panel_review_block.md"
_PANEL_DIR_REL = "agents/prompts/panels"

# File-naming overrides (mirrors tests/contract/test_panel_prompts.py):
# the inner "plan_" / "paper_plan_" prefix is dropped when the lens
# would double-prefix.
_FILENAME_OVERRIDES: dict[tuple[str, str], str] = {
    ("planned", "plan_consistency"): "panel_plan_consistency.md",
    ("paper_planned", "plan_constitution_consistency"): (
        "panel_paper_plan_constitution_consistency.md"
    ),
}

_STAGE_PREFIX: dict[str, str] = {
    "flesh_out_complete": "idea",
    "clarified": "spec",
    "planned": "plan",
    "tasked": "tasks",
    "paper_clarified": "paper_spec",
    "paper_planned": "paper_plan",
    "paper_tasked": "paper_tasks",
}

# Some stages reuse PRE-EXISTING per-lens prompt files that live at the
# ``agents/prompts/`` root rather than under ``panels/`` — specifically
# the spec-015 ``paper_review`` (12-panel) and ``research_review``
# (8-panel) stages, which were established before the panels/ directory
# convention. Mapping is ``stage → (relative_root, basename_pattern)``;
# ``basename_pattern`` is formatted with the ``lens`` name. Lookup
# falls through to ``_STAGE_PREFIX`` if a stage isn't here.
_EXTERNAL_PROMPT_ROOTS: dict[str, tuple[str, str]] = {
    "paper_review": ("agents/prompts", "paper_reviewer_{lens}.md"),
    "research_review": ("agents/prompts", "research_reviewer_{lens}.md"),
}

# Per-(stage, lens) basename overrides for the external (reused 8-/12-panel)
# prompts whose lens name doesn't match the established filename: the
# code/data lenses carry a ``_research``/``_paper`` suffix, and the generic
# ``research_reviewer``/``paper_reviewer`` lens uses the un-suffixed base
# prompt. Resolved under the stage's _EXTERNAL_PROMPT_ROOTS root.
_EXTERNAL_FILENAME_OVERRIDES: dict[tuple[str, str], str] = {
    ("research_review", "code_quality"): "research_reviewer_code_quality_research.md",
    ("research_review", "data_quality"): "research_reviewer_data_quality_research.md",
    ("research_review", "research_reviewer"): "research_reviewer.md",
    ("paper_review", "paper_reviewer"): "paper_reviewer.md",
    ("paper_review", "code_quality"): "paper_reviewer_code_quality_paper.md",
    ("paper_review", "data_quality"): "paper_reviewer_data_quality_paper.md",
}


def _prompt_path_for(*, stage: str, lens: str, repo_root: Path) -> Path:
    override = _FILENAME_OVERRIDES.get((stage, lens))
    if override is not None:
        return repo_root / _PANEL_DIR_REL / override
    external = _EXTERNAL_PROMPT_ROOTS.get(stage)
    if external is not None:
        root_rel, pattern = external
        basename = _EXTERNAL_FILENAME_OVERRIDES.get((stage, lens), pattern.format(lens=lens))
        return repo_root / root_rel / basename
    prefix = _STAGE_PREFIX.get(stage)
    if prefix is None:
        raise ValueError(
            f"unknown stage {stage!r}; no panel-prompt prefix mapping. "
            f"Known: {sorted({*_STAGE_PREFIX, *_EXTERNAL_PROMPT_ROOTS})!r}"
        )
    return repo_root / _PANEL_DIR_REL / f"panel_{prefix}_{lens}.md"


def _load_system_prompt(*, stage: str, lens: str, repo_root: Path) -> str:
    """Concatenate the per-lens prompt + the SSoT panel-review block."""
    lens_path = _prompt_path_for(stage=stage, lens=lens, repo_root=repo_root)
    if not lens_path.exists():
        raise RuntimeError(
            f"panel prompt not found: {lens_path}. Expected at this path "
            f"per the panel-prompt convention; check T049-T053 authoring."
        )
    shared_path = repo_root / _SHARED_PROMPT_REL
    if not shared_path.exists():
        raise RuntimeError(
            f"SSoT shared panel block not found: {shared_path}. Spec-015 "
            "T048 should have authored this."
        )
    return lens_path.read_text() + "\n\n---\n\n" + shared_path.read_text()


# --- response parsing -----------------------------------------------------


_YAML_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---", re.DOTALL)

# Code-fence stripper: many models wrap the YAML in ```yaml ... ``` or
# bare ``` ... ``` fences. We accept either + look for the frontmatter
# inside.
_CODE_FENCE_RE = re.compile(
    r"```(?:yaml|yml)?\s*\n(.*?)\n```", re.DOTALL | re.IGNORECASE,
)

# LLM-emitted YAML often has un-quoted ``text:`` / ``location:`` values
# containing apostrophes / parens / colons that crash ``yaml.safe_load``,
# OR multi-line free-form text where the continuation line isn't properly
# indented as a YAML continuation. We re-format such lines as block
# scalars (``key: |\n  value``) before re-parsing as a last-resort
# fallback. See ``_safe_yaml_load`` and ``_reformat_unquoted_scalars``.
_PROBLEMATIC_CHARS_RE = re.compile(r"['\"]")


_FREE_TEXT_KEYS = (
    "text", "location", "response", "what_changed",
    # Specialist-reviewer frontmatter free-text fields. These hold prose that
    # routinely contains a colon ("Critical gap: no report exists"), which makes
    # the raw YAML invalid ("mapping values are not allowed here"). Without these
    # in the free-text set the recovery cascade skipped them and the whole review
    # was rejected -> the specialist produced NO verdict -> review coverage stayed
    # incomplete (7/7 never reached) -> the project could never advance. Treat them
    # as free text so the recovery quotes / block-scalars them.
    "feedback", "summary", "rationale", "justification", "comment", "comments",
    "notes", "explanation",
)
# Matches a YAML key line OR a list-item-key line:
#   "    text: value"
#   "    - text: value"
# The optional ``listmarker`` group captures the ``- `` prefix when it
# applies, so the block-scalar wrapper can preserve it during repair.
_KEY_LINE_RE = re.compile(
    r"^(?P<indent>[ \t]*)(?P<listmarker>-\s+)?(?P<key>[A-Za-z_][\w-]*)"
    r"\s*:(?:\s+(?P<value>.*))?$"
)
_LIST_ITEM_RE = re.compile(r"^[ \t]*-(?:\s|$)")
_DOC_BOUNDARY_RE = re.compile(r"^(?:---|\.\.\.)\s*$")


def _reformat_unquoted_scalars(yaml_text: str) -> str:
    """Best-effort: rewrite ``text:`` / ``location:`` / ``response:`` /
    ``what_changed:`` scalar values that contain apostrophes / quotes OR
    that span multiple lines (LLMs frequently emit free-form text after
    one of these keys without continuation indentation) as YAML block
    scalars (``key: |\\n  value\\n  continuation``).

    The transformation is conservative: it only touches lines whose key
    is in ``_FREE_TEXT_KEYS``; everything else is preserved verbatim.

    The repair walks line-by-line so it can greedily absorb continuation
    lines that don't match a structural pattern (next key, list item,
    document boundary). This handles the real production failure mode
    where the LLM emits ``text: foo`` followed by an unindented next
    line that YAML interprets as a new top-level scalar.
    """
    lines = yaml_text.splitlines()
    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        m = _KEY_LINE_RE.match(line)
        if (
            m is not None
            and m.group("key") in _FREE_TEXT_KEYS
            and m.group("value")
        ):
            key = m.group("key")
            indent = m.group("indent")
            listmarker = m.group("listmarker") or ""
            value = m.group("value").rstrip()
            # The "effective" indent for block-scalar continuation is
            # ``indent + listmarker`` (when the key was preceded by a
            # ``- ``, the YAML continuation indent must align past the
            # marker, not just past the leading whitespace). Inner indent
            # for the scalar's content is +2 from there.
            effective_indent = indent + listmarker
            inner_indent = effective_indent + "  "
            # If the value already starts with a YAML scalar/flow
            # marker (``'``, ``"``, ``[``, ``{``, ``|``, ``>``), the LLM
            # already produced valid YAML — don't touch it. This
            # preserves the well-formed-input invariant.
            already_proper_scalar = value.startswith(
                ("'", '"', "[", "{", "|", ">")
            )
            # Detect whether repair is needed: problematic chars in
            # value OR a continuation line that's not properly
            # indented as a YAML continuation of this scalar.
            needs_repair = (
                not already_proper_scalar
                and bool(_PROBLEMATIC_CHARS_RE.search(value))
            )
            block_lines = [value]
            j = i + 1
            while j < len(lines):
                nxt = lines[j]
                if not nxt.strip():
                    break
                if _DOC_BOUNDARY_RE.match(nxt):
                    break
                if _LIST_ITEM_RE.match(nxt) and (
                    len(nxt) - len(nxt.lstrip())
                ) <= len(indent):
                    break
                nxt_m = _KEY_LINE_RE.match(nxt)
                if nxt_m is not None and (
                    len(nxt_m.group("indent")) <= len(indent)
                ):
                    break
                # Lower-indent continuation → YAML structural breakage,
                # absorb into block scalar.
                if len(nxt) - len(nxt.lstrip()) < len(inner_indent):
                    needs_repair = True
                block_lines.append(nxt.strip())
                j += 1
            if needs_repair:
                # Preserve the list-marker (``- ``) prefix when the key
                # was at a list-item position; otherwise just emit the
                # key + block-scalar indicator.
                out.append(f"{indent}{listmarker}{key}: |")
                for b in block_lines:
                    out.append(f"{inner_indent}{b}")
                i = j
                continue
        out.append(line)
        i += 1
    return "\n".join(out) + ("\n" if yaml_text.endswith("\n") else "")


def _force_block_scalar_all_freetext_keys(yaml_text: str) -> str:
    """Last-resort recovery — force EVERY ``text:`` / ``location:`` /
    ``response:`` / ``what_changed:`` line to a block scalar regardless
    of what its current value looks like.

    More aggressive than ``_reformat_unquoted_scalars``: it doesn't
    check for problematic chars or already-proper scalar markers —
    every free-text key becomes a block scalar that absorbs its
    continuation up to the next structural line. This is the safety
    net for LLM outputs whose strings have unbalanced double-quotes
    (``while scanning a double-quoted scalar``) or other quoting
    pathologies the conservative pass can't reliably detect.
    """
    lines = yaml_text.splitlines()
    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        m = _KEY_LINE_RE.match(line)
        if m is not None and m.group("key") in _FREE_TEXT_KEYS and m.group("value"):
            indent = m.group("indent")
            listmarker = m.group("listmarker") or ""
            key = m.group("key")
            value = m.group("value").rstrip()
            # Preserve the list-marker (``- ``) prefix; YAML block-
            # scalar continuation indent must align past the marker.
            effective_indent = indent + listmarker
            inner_indent = effective_indent + "  "
            # Strip leading/trailing quote chars from the value so a
            # block scalar doesn't start with " or '.
            cleaned = value.strip("\"'")
            block_lines = [cleaned]
            j = i + 1
            while j < len(lines):
                nxt = lines[j]
                if not nxt.strip():
                    break
                if _DOC_BOUNDARY_RE.match(nxt):
                    break
                if _LIST_ITEM_RE.match(nxt) and (
                    len(nxt) - len(nxt.lstrip())
                ) <= len(indent):
                    break
                nxt_m = _KEY_LINE_RE.match(nxt)
                if nxt_m is not None and (
                    len(nxt_m.group("indent")) <= len(indent)
                ):
                    break
                block_lines.append(nxt.strip().strip("\"'"))
                j += 1
            out.append(f"{indent}{listmarker}{key}: |")
            for b in block_lines:
                out.append(f"{inner_indent}{b}")
            i = j
            continue
        out.append(line)
        i += 1
    return "\n".join(out) + ("\n" if yaml_text.endswith("\n") else "")


def _fold_wrapped_metadata_scalars(yaml_text: str) -> str:
    """Re-join a NON-free-text scalar value the model wrapped across physical
    lines (the live PROJ-492 tasks-panel ``[ordering]`` + ``[scope]`` "while
    scanning a simple key" crash: a long ``artifact_path:`` value broken mid-path
    into ``artifact_path: projects/PROJ-492-evaluating-the-statistical-`` /
    ``validity-of-p/tasks.md``).

    YAML reads the orphan continuation line as a fresh key candidate with no
    colon and raises "while scanning a simple key", aborting the WHOLE panel —
    and the line-scan ``_salvage_review`` only rescues a NON-accept review, so a
    clean ACCEPT whose ``artifact_path:`` wraps would still hard-crash the panel.

    This repair folds each orphan continuation line (a non-blank line that is NOT
    a doc boundary, NOT a list item, and does NOT itself introduce a ``key:``)
    back into the preceding scalar value. It deliberately EXCLUDES the
    ``_FREE_TEXT_KEYS`` (``text``/``location``/``response``/``what_changed``) —
    those wrapped-prose values are owned by the block-scalar repairs, which join
    with a space; wrapped metadata (paths / hashes / ids) is contiguous, so it is
    rejoined with NO separator. The repair is purely STRUCTURAL — it reconstructs
    the value the model line-wrapped; it never invents a ``verdict:`` or a
    concern, so it cannot cause a false convergence.
    """
    lines = yaml_text.splitlines()
    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        m = _KEY_LINE_RE.match(line)
        value = m.group("value").rstrip() if (m and m.group("value")) else None
        # Only fold a non-free-text key whose value is a PLAIN scalar (not a
        # block/flow/quoted/comment marker the existing repairs already own).
        if (
            m is not None
            and m.group("key") not in _FREE_TEXT_KEYS
            and value
            and not value.startswith(("|", ">", "[", "{", "'", '"', "#", "&", "*"))
        ):
            indent = m.group("indent")
            listmarker = m.group("listmarker") or ""
            absorbed: list[str] = []
            j = i + 1
            while j < len(lines):
                nxt = lines[j]
                if not nxt.strip():
                    break
                if _DOC_BOUNDARY_RE.match(nxt):
                    break
                if _LIST_ITEM_RE.match(nxt):
                    break
                if _KEY_LINE_RE.match(nxt) is not None:
                    break
                absorbed.append(nxt.strip())
                j += 1
            if absorbed:
                folded = value + "".join(absorbed)
                out.append(f"{indent}{listmarker}{m.group('key')}: {folded}")
                i = j
                continue
        out.append(line)
        i += 1
    return "\n".join(out) + ("\n" if yaml_text.endswith("\n") else "")


# Characters that may legally follow a backslash inside a YAML double-quoted
# scalar (YAML 1.1 escape set + whitespace/line-continuation). Anything else —
# notably a LaTeX command like ``\cite`` / ``\ref`` / ``\section`` (``\c``,
# ``\r``→ wait, ``\r`` is valid; ``\c``/``\s`` are not) — is an INVALID escape
# that makes ``yaml.safe_load`` reject the whole frontmatter. Paper reviewers
# quote LaTeX constantly, so this is the #1 paper-review parse failure.
_VALID_DQ_ESCAPE = set('0abtnvfre"\\/N_LPxuU \t\r\n')
_DQ_SPAN_RE = re.compile(r'"(?:[^"\\]|\\.)*"', re.S)


def _fix_invalid_dq_escapes(yaml_text: str) -> str:
    """Double any INVALID backslash escape inside a double-quoted scalar so the
    backslash survives as a literal (``\\cite`` -> ``\\\\cite`` -> parses to the
    literal ``\\cite``). Content-preserving — unlike the block-scalar repair it
    keeps the scalar's text intact, so a LaTeX-quoting reviewer's action items
    are not lost."""
    def _fix(m: re.Match[str]) -> str:
        inner = m.group(0)[1:-1]
        out: list[str] = []
        i = 0
        while i < len(inner):
            ch = inner[i]
            if ch == "\\":
                nxt = inner[i + 1] if i + 1 < len(inner) else ""
                if nxt and nxt in _VALID_DQ_ESCAPE:
                    out.append(ch + nxt)
                    i += 2
                    continue
                out.append("\\\\")  # lone/invalid backslash -> literal backslash
                i += 1
                continue
            out.append(ch)
            i += 1
        return '"' + "".join(out) + '"'

    return _DQ_SPAN_RE.sub(_fix, yaml_text)


def _safe_yaml_load(yaml_text: str) -> object:
    """Robust YAML loader for LLM frontmatter.

    Recovery cascade (most content-preserving first):

    1. Try the standard ``yaml.safe_load``.
    2. Double INVALID backslash escapes in double-quoted scalars
       (``_fix_invalid_dq_escapes``) — fixes LaTeX (``\\cite``) quoting
       WITHOUT mangling the scalar. Try again.
    3. FOLD a wrapped NON-free-text scalar (``_fold_wrapped_metadata_scalars``) —
       fixes a long ``artifact_path:`` the model line-wrapped (the "while
       scanning a simple key" crash) by rejoining the orphan continuation.
    4. CONSERVATIVE repair ``_reformat_unquoted_scalars``. Try again.
    5. AGGRESSIVE repair ``_force_block_scalar_all_freetext_keys`` (rewrites
       free-text keys as block scalars). Final attempt.
    6. If all fail, raise the ORIGINAL ``YAMLError`` so the caller's message
       points at the LLM's actual output, not the repaired version.
    """
    try:
        return yaml.safe_load(yaml_text)
    except yaml.YAMLError as orig_err:
        # Stage 2: fix invalid double-quoted backslash escapes (LaTeX).
        deescaped = _fix_invalid_dq_escapes(yaml_text)
        if deescaped != yaml_text:
            try:
                return yaml.safe_load(deescaped)
            except yaml.YAMLError:
                pass
        # Stage 3: fold a wrapped non-free-text scalar (e.g. a line-broken
        # artifact_path). Runs on the ORIGINAL text — it targets metadata
        # keys the free-text repairs deliberately skip, so it composes with
        # them rather than conflicting. Also retried after the conservative
        # pass below for inputs that need both.
        folded = _fold_wrapped_metadata_scalars(yaml_text)
        if folded != yaml_text:
            try:
                return yaml.safe_load(folded)
            except yaml.YAMLError:
                pass
        # Stage 4: conservative repair (also re-run on the de-escaped text).
        conservative = _reformat_unquoted_scalars(yaml_text)
        if conservative != yaml_text:
            try:
                return yaml.safe_load(conservative)
            except yaml.YAMLError:
                pass
        # Stage 4b: conservative repair ON TOP of the metadata fold, for a
        # response that wraps BOTH a metadata scalar AND a free-text value.
        if folded != yaml_text:
            folded_conservative = _reformat_unquoted_scalars(folded)
            if folded_conservative != folded:
                try:
                    return yaml.safe_load(folded_conservative)
                except yaml.YAMLError:
                    pass
        # Stage 3: aggressive repair (force ALL free-text keys to block
        # scalars). Run on the ORIGINAL text (not the conservative
        # output) so the two repairs don't compound into broken output.
        aggressive = _force_block_scalar_all_freetext_keys(yaml_text)
        if aggressive != yaml_text:
            try:
                return yaml.safe_load(aggressive)
            except yaml.YAMLError:
                pass
        raise orig_err from None


# Matches just the OPENING frontmatter delimiter (a leading ``---`` line).
_OPEN_DELIM_RE = re.compile(r"^---[ \t]*\r?\n")
# A YAML document-boundary line (``---`` or ``...``) on its own line.
_DOC_BOUNDARY_LINE_RE = re.compile(r"(?m)^(?:---|\.\.\.)[ \t]*$")


def _extract_frontmatter(candidate: str) -> str | None:
    """Return the YAML-frontmatter text from a stripped reviewer response.

    Reviewers are contracted to emit ``---\\n<yaml>\\n---\\n<prose>``. Real
    reasoning-model output sometimes drops (or is truncated before) the CLOSING
    ``---`` — the model ends right after ``concerns:``, or the endpoint hangs
    mid-response. The strict both-delimiters regex then matches nothing and a
    single such reviewer crashes the ENTIRE panel/run. This recovers the
    frontmatter in three shapes, most-specific first:

    1. Proper ``---\\n<yaml>\\n---`` — strict regex (fast path).
    2. Opening ``---`` + a later doc-boundary line (``---``/``...``) — cut there.
    3. Opening ``---`` with NO closing delimiter — take the longest leading
       line-block that still parses to a non-empty YAML mapping (so the
       structured verdict/concerns survive; any trailing prose is dropped).

    Returns ``None`` only when there is no opening ``---`` at all.
    """
    m = _YAML_FRONTMATTER_RE.search(candidate)
    if m is not None:
        return m.group(1)
    open_m = _OPEN_DELIM_RE.match(candidate)
    if open_m is None:
        return None
    body = candidate[open_m.end():]
    # Shape 2: a closing doc-boundary somewhere later.
    boundary = _DOC_BOUNDARY_LINE_RE.search(body)
    if boundary is not None:
        return body[: boundary.start()]
    # Shape 3: no closing delimiter — maximal leading block that yaml-loads to a
    # non-empty mapping. Trims any unfenced prose the model appended.
    lines = body.splitlines()
    for end in range(len(lines), 0, -1):
        chunk = "\n".join(lines[:end]).rstrip()
        if not chunk:
            continue
        try:
            loaded = _safe_yaml_load(chunk)
        except Exception:
            continue
        if isinstance(loaded, dict) and loaded:
            return chunk
    return body  # nothing parsed cleanly — let downstream raise a precise error


_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*(\{.*\})\s*```", re.S)


def _try_json_review_object(text: str) -> dict | None:
    """A model that emits the review as a JSON object (fenced ```json {...} or a
    bare leading object) rather than YAML frontmatter. Returns the parsed dict
    IFF it carries a ``verdict`` key — the verdict gate avoids misreading a
    stray JSON snippet in the prose body as the review. None otherwise."""
    import json as _json

    m = _JSON_FENCE_RE.search(text)
    blob = m.group(1) if m else None
    if blob is None:
        s, e = text.find("{"), text.rfind("}")
        if s == -1 or e <= s:
            return None
        blob = text[s:e + 1]
    for loader in (_json.loads, _safe_yaml_load):
        try:
            obj = loader(blob)
        except Exception:
            continue
        return obj if isinstance(obj, dict) and "verdict" in obj else None
    return None


def _parse_response(
    response_text: str, *, lens: str, stage: str, default_artifact: str,
) -> tuple[str, list[Concern]]:
    """Parse the LLM's YAML-frontmatter response into (verdict, concerns).

    The output contract (defined in ``_shared/panel_review_block.md``):

    ```yaml
    ---
    reviewer_name: <lens>
    reviewer_kind: llm
    stage: <stage>
    artifact_path: <path>
    artifact_hash: <hash>
    verdict: accept | minor_revision | major_revision | reject
    concerns:
      - severity: trivial | code | ...
        location: "..."
        text: "..."
    ---
    <prose body>
    ```

    Raises ``RuntimeError`` on missing frontmatter / invalid YAML /
    missing required fields — engine treats as non-convergence.
    """
    candidate = response_text.strip()
    # A model (notably qwen3.5, the default) wraps the WHOLE review in a
    # ```yaml ... ``` fence — and as a reasoning model it frequently TRUNCATES
    # before the closing ```, so `_CODE_FENCE_RE` (which needs the close) never
    # matches and the leading ```yaml line hides the `---` frontmatter from
    # `_extract_frontmatter`, crashing the panel ("no YAML frontmatter"; the live
    # PROJ-492 plan-panel scientific_soundness engine failure on the qwen switch).
    # A fence at POSITION 0 wraps the whole document — it can NEVER be a prose
    # example (prose never starts the response) — so stripping the opening fence
    # line (and a matching trailing close, if any) here is safe, unlike the
    # search-anywhere fence strip below which stays a guarded fallback.
    _lead_fence = re.match(r"```(?:yaml|yml)?[ \t]*\r?\n", candidate, re.IGNORECASE)
    if _lead_fence is not None:
        candidate = candidate[_lead_fence.end():]
        candidate = re.sub(r"\r?\n```[ \t]*$", "", candidate).strip()
    # Frontmatter extraction takes PRIORITY over fence-stripping. A reviewer's
    # prose body frequently contains a ```yaml ... ``` example (or quotes a
    # fenced block from the artifact); stripping that fence FIRST would hijack
    # `candidate` to the example's contents and drop the real frontmatter — the
    # Part-7 PROJ-552 crash (`scope_fidelity` review: opening `---`, no closing
    # `---`, and a fenced block in the prose). Only when the raw response has no
    # recoverable frontmatter do we treat it as a wholly fence-wrapped document
    # (many LLMs wrap the whole YAML in ```yaml ... ``` despite the prompt) and
    # retry on the unwrapped fence contents.
    frontmatter = _extract_frontmatter(candidate)
    if frontmatter is None:
        fence_m = _CODE_FENCE_RE.search(candidate)
        if fence_m is not None:
            frontmatter = _extract_frontmatter(fence_m.group(1).strip())
    meta: object | None = None
    if frontmatter is None:
        # JSON fallback. Some models emit the review as a JSON object
        # (```json {"verdict": ..., "concerns": [...]}) instead of YAML
        # frontmatter. temperature=0 (deterministic reviewers) makes such a
        # mis-formatted reply RECUR identically on every retry, so the parser —
        # not a re-prompt — must absorb it, or the panel fails PERMANENTLY
        # (observed live: PROJ-018 spec panel, requirements_coverage R3).
        meta = _try_json_review_object(candidate)
        if meta is None:
            raise RuntimeError(
                f"LLMReviewer[{lens}]: response has no YAML frontmatter "
                f"(missing `---` delimiters) and no JSON review object. "
                f"First 200 chars: {response_text[:200]!r}"
            )
    if meta is None:
        try:
            meta = _safe_yaml_load(frontmatter) or {}
        except yaml.YAMLError as exc:
            # All YAML repairs failed. Before crashing the whole panel on ONE
            # lens's malformed output (deterministic at temp=0 → hard-stall),
            # line-scan for verdict + concerns. Salvage rescues only a NON-accept
            # review, so it cannot rubber-stamp garbage as a clean accept.
            salvaged = _salvage_review(frontmatter)
            if salvaged is not None:
                logger.warning(
                    "LLMReviewer[%s]: frontmatter YAML invalid (%s); salvaged "
                    "%d concern(s) by line-scan (treated as non-accept)",
                    lens, str(exc).splitlines()[0], len(salvaged["concerns"]),
                )
                meta = salvaged
            else:
                raise RuntimeError(
                    f"LLMReviewer[{lens}]: frontmatter is not valid YAML: {exc}"
                ) from exc
    if not isinstance(meta, dict):
        raise RuntimeError(
            f"LLMReviewer[{lens}]: frontmatter must be a YAML mapping; "
            f"got {type(meta).__name__}"
        )
    # False-convergence guard (spec-015 honesty; same "absence of evidence MUST
    # NOT pass" family as the reviser `<missing>` guard `a3e9d824` and the
    # spec-019 fill gate). A contentless or truncated review — frontmatter with
    # NEITHER a `verdict:` NOR a `concerns:`/`action_items:` key — carries no
    # evidence that a review actually happened (e.g. `---\n---`, or the model
    # hung after emitting only `notes:`). Defaulting such a review to `accept`
    # with zero concerns silently rubber-stamps it as a clean pass. A GENUINE
    # clean accept always states `verdict:` (spec-015 SSoT) or an explicit
    # `action_items:`/`concerns:` (legacy panels). Raise so the engine treats it
    # as non-convergence (retry) rather than false convergence.
    if not ({"verdict", "concerns", "action_items"} & set(meta)):
        raise RuntimeError(
            f"LLMReviewer[{lens}]: review frontmatter has neither `verdict:` nor "
            f"`concerns:`/`action_items:` — a contentless/truncated review MUST "
            f"NOT count as acceptance (false-convergence guard). First 200 chars: "
            f"{response_text[:200]!r}"
        )
    verdict = str(meta.get("verdict", "")).strip().lower() or "accept"
    # Spec-015 SSoT schema uses ``concerns:``; the legacy 12-panel +
    # 8-panel prompts (paper_reviewer_*.md / research_reviewer_*.md)
    # emit ``action_items:`` per the pre-spec-015 v1.1.0 reviewer
    # contract. Accept either key as the source of structured
    # findings — when BOTH are present, ``concerns`` wins (the LLM
    # explicitly produced the SSoT shape). Same fields (text +
    # severity); the legacy ``writing|science|fatal`` severity
    # values are a strict subset of the spec-015 Severity enum so
    # no mapping is needed.
    raw_concerns = meta.get("concerns")
    if not raw_concerns:
        raw_concerns = meta.get("action_items") or []
    if not isinstance(raw_concerns, list):
        raise RuntimeError(
            f"LLMReviewer[{lens}]: `concerns:`/`action_items:` must be "
            f"a list; got {type(raw_concerns).__name__}"
        )
    concerns: list[Concern] = []
    for i, c in enumerate(raw_concerns):
        if not isinstance(c, dict):
            continue
        # Robust parse: panels routinely emit a generic severity word
        # (low/medium/high/minor/critical) instead of llmXive's domain classes.
        # ``coerce_severity`` maps those onto the canonical enum (generic words
        # stay inside the safe in-place-revision band) and defaults a genuinely
        # unknown token to ``writing`` with a warning — a single odd severity must
        # not crash the whole stage panel (the PROJ-492 tasks-gate engine failure
        # on severity 'low' that blocked every project here).
        sev_raw = str(c.get("severity", "writing")).strip().lower()
        sev = coerce_severity(sev_raw, lens=lens)
        # Reject empty / whitespace-only / non-string `text` BEFORE we
        # construct the Concern. The model-layer validator (Concern.text:
        # min_length=1) catches it too, but raising RuntimeError here
        # produces the engine-recognised non-convergence signal (matches
        # the surrounding severity-rejection style) instead of a
        # pydantic ValidationError. ``location`` is intentionally NOT
        # required (see Concern docstring).
        text_raw = c.get("text", "")
        if not isinstance(text_raw, str) or not text_raw.strip():
            raise RuntimeError(
                f"LLMReviewer[{lens}]: concern {i} has empty/missing text; "
                f"the LLM produced a concern with severity {sev_raw!r} but "
                f"no description. This is a structurally invalid concern."
            )
        concerns.append(Concern(
            id=str(c.get("id") or f"{lens}-{uuid.uuid4().hex[:8]}"),
            reviewer=lens,
            severity=sev,
            artifact=str(c.get("artifact") or default_artifact),
            location=str(c.get("location") or ""),
            text=text_raw.strip(),
        ))
    return verdict, concerns


# --- LLMReviewer ---------------------------------------------------------


def _serialize_artifacts(artifacts: dict[str, str]) -> str:
    """Render the artifacts dict into a human-readable user message."""
    parts: list[str] = []
    for path, content in artifacts.items():
        # Special keys (those starting with __) become labeled context
        # blocks rather than file-headed sections.
        if path.startswith("__") and path.endswith("__"):
            label = path.strip("_").replace("_", " ").title()
            parts.append(f"# {label}\n\n{content}")
        else:
            parts.append(f"## {path}\n\n{content}")
    return "\n\n".join(parts)


def _serialize_concerns(concerns: list[Concern]) -> str:
    """Format a concern list for the re-review path."""
    return "\n".join(
        f"- id: {c.id}\n  severity: {c.severity.value}\n  "
        f"location: {c.location!r}\n  text: {c.text!r}"
        for c in concerns
    )


class LLMReviewer:
    """Live Reviewer for one panel lens.

    Conforms structurally to :class:`llmxive.convergence.types.Reviewer`.
    """

    def __init__(
        self,
        *,
        lens: str,
        stage: str,
        backend: Any,
        repo_root: Path,
        model: str | None = None,
        # Reasoning-safe but BOUNDED: a measured full-spec review used ~9.7K
        # completion tokens; 32_768 is ~3x headroom. 128K invites the reasoning
        # model to keep thinking past the wall-clock deadline (→ hang/thrash).
        max_tokens: int | None = 32_768,
        # DETERMINISTIC by default (temperature 0). A non-zero temperature makes
        # the panel emit a DIFFERENT crop of concerns every round — the spec/plan
        # convergence then oscillates (24→10→3→5→4→1→11 instead of converging)
        # and the in-place reviser can never satisfy a moving target, so the
        # stage burns its whole round + kickback cap re-flagging (often FALSE)
        # concerns — e.g. "FR-003 not anchored to a User Story" when the spec
        # plainly says "See US-5". The research/paper reviewers already pin
        # temperature=0; the convergence panels must too.
        temperature: float = 0.0,
    ) -> None:
        self.name = lens
        self._lens = lens
        self._stage = stage
        self._backend = backend
        self._repo_root = Path(repo_root)
        self._model = model
        self._temperature = temperature
        # Spec 015: qwen3.5-122b is a *reasoning* model — its hidden
        # chain-of-thought tokens count against the response budget. The
        # 512-default of OpenAI-shaped APIs is far too small (reasoning
        # consumes it all → empty content + finish_reason=length). 32_768 is
        # a reasoning-safe but BOUNDED budget (~3x the ~9.7K measured for a
        # full-spec review): big enough that a complex lens never exhausts it
        # before emitting its verdict, small enough that reasoning finishes
        # inside the wall-clock deadline (128K invited past-deadline thinking).
        self._max_tokens = max_tokens
        # Eager-load the system prompt — fail fast if missing.
        self._system_prompt = _load_system_prompt(
            stage=stage, lens=lens, repo_root=self._repo_root,
        )

    # --- public Protocol methods --------------------------------------

    # A verdict that REQUESTS revision. The R1 action-items gate fires only when
    # the reviewer explicitly asked for changes yet enumerated NO concerns — a
    # self-contradictory review. (An unparsed/empty verdict with no concerns is
    # treated as an accept, not re-prompted.)
    _NONACCEPT_VERDICTS = frozenset({
        "minor_revision", "major_revision", "reject", "rejected", "revise",
        "needs_revision", "changes_requested", "request_changes",
    })

    def identify(
        self,
        artifacts: dict[str, str],
        *,
        constitution: str | None,
        advisory: list[str],
    ) -> list[Concern]:
        user = self._compose_identify_user(
            artifacts=artifacts, constitution=constitution, advisory=advisory,
        )
        # Resumable cache (spec: make qwen-outage recovery cheap). The key
        # hashes EVERY review-determining input (composed user message +
        # system prompt + lens + stage + model); a HIT is byte-for-byte
        # equivalent to a fresh call's INPUTS, so reusing it cannot change
        # the review. On MISS we call the model and STORE before returning.
        # All cache ops are best-effort — never crash / change a review.
        cache_key = review_cache.compose_key(
            user=user,
            system=self._system_prompt,
            lens=self._lens,
            stage=self._stage,
            model=self._model,
        )
        cached = review_cache.load(self._repo_root, cache_key)
        if cached is not None:
            return cached
        messages = [
            ChatMessage(role="system", content=self._system_prompt),
            ChatMessage(role="user", content=user),
        ]
        response_text = self._call_backend(messages)
        default_artifact = self._pick_default_artifact(artifacts)
        verdict, concerns = _parse_response(
            response_text,
            lens=self._lens,
            stage=self._stage,
            default_artifact=default_artifact,
        )
        # R1 ACTION-ITEMS GATE (the single shared review protocol): a reviewer that
        # requests revision but enumerates ZERO concerns is self-contradictory —
        # it says "change this" with nothing to act on. Such a review is REJECTED
        # and RESUBMITTED ONCE with an explicit instruction; if it still produces
        # no actionable items it is taken as an accept (the reviewer had nothing
        # concrete to say). This guarantees every round-1 non-accept carries the
        # action items round 2 will address and round 3 will sign off on.
        if not concerns and (verdict or "").strip().lower() in self._NONACCEPT_VERDICTS:
            resubmit = [
                *messages,
                ChatMessage(role="assistant", content=response_text),
                ChatMessage(role="user", content=(
                    "Your verdict requests revision but you listed NO concerns / "
                    "action items. A review that asks for changes MUST enumerate "
                    "specific, actionable items — one concern per item, each naming "
                    "the artifact + location and the concrete change required. "
                    "Re-issue the review now with those explicit action items; OR, "
                    "if you have nothing actionable, return `verdict: accept`. "
                    "Output ONLY the review document."
                )),
            ]
            response_text = self._call_backend(resubmit)
            _, concerns = _parse_response(
                response_text,
                lens=self._lens,
                stage=self._stage,
                default_artifact=default_artifact,
            )
        review_cache.store(self._repo_root, cache_key, concerns)
        return concerns

    def rereview(
        self,
        artifacts: dict[str, str],
        own_concerns: list[Concern],
        responses: list[Any],
        *,
        constitution: str | None,
        advisory: list[str],
    ) -> list[Verdict]:
        user = self._compose_rereview_user(
            artifacts=artifacts,
            own_concerns=own_concerns,
            responses=responses,
            constitution=constitution,
            advisory=advisory,
        )
        messages = [
            ChatMessage(role="system", content=self._system_prompt),
            ChatMessage(role="user", content=user),
        ]
        response_text = self._call_backend(messages)
        default_artifact = self._pick_default_artifact(artifacts)
        _, new_concerns = _parse_response(
            response_text,
            lens=self._lens,
            stage=self._stage,
            default_artifact=default_artifact,
        )
        # Build verdicts: for each PRIOR concern, fail if it appears in
        # new_concerns (by id) else pass. New concerns (no matching id)
        # are surfaced via the Verdict.new_concerns field on a synthetic
        # first verdict so the engine sees them — same shape the engine
        # already expects.
        new_by_id = {c.id: c for c in new_concerns}
        verdicts: list[Verdict] = []
        for prior in own_concerns:
            still_open = prior.id in new_by_id
            verdicts.append(Verdict(
                concern_id=prior.id,
                reviewer=self._lens,
                status="fail" if still_open else "pass",
            ))
        # Any new concerns the reviewer surfaced with NO matching prior
        # id are surfaced via a Verdict's `new_concerns` field so the
        # engine sees them.
        truly_new = [c for c in new_concerns if c.id not in {p.id for p in own_concerns}]
        if truly_new:
            if verdicts:
                verdicts[0] = Verdict(
                    concern_id=verdicts[0].concern_id,
                    reviewer=verdicts[0].reviewer,
                    status=verdicts[0].status,
                    new_concerns=truly_new,
                )
            else:
                # FR-012 accepter re-review: this lens raised NO prior
                # concerns (R1-accepter) but the R2 revision broke its
                # lens, so it surfaces NEW breakage here. There is no
                # prior verdict to attach them to — emit a synthetic
                # FAIL verdict carrying the new concerns so the engine
                # does NOT converge over silent breakage. (Dropping
                # these was the bug: the engine could report `converged`
                # while an accepter's lens was freshly violated.)
                verdicts.append(Verdict(
                    concern_id=truly_new[0].id,
                    reviewer=self._lens,
                    status="fail",
                    new_concerns=truly_new,
                ))
        return verdicts

    # --- internal helpers ----------------------------------------------

    def _compose_identify_user(
        self,
        *,
        artifacts: dict[str, str],
        constitution: str | None,
        advisory: list[str],
    ) -> str:
        sections: list[str] = []
        sections.append("# Stage")
        sections.append(self._stage)
        sections.append("# Artifacts under review")
        sections.append(_serialize_artifacts(artifacts))
        if constitution:
            sections.append("# Constitution (FR-030)")
            sections.append(constitution)
        if advisory:
            sections.append("# Advisory inputs (human / personality triage)")
            sections.append("\n\n".join(advisory))
        sections.append("# Task")
        sections.append(
            "Apply YOUR lens only. Return the YAML-frontmatter response "
            "per the shared output contract. Use the lens name "
            f"{self._lens!r} in `reviewer_name`."
        )
        return "\n\n".join(sections)

    def _compose_rereview_user(
        self,
        *,
        artifacts: dict[str, str],
        own_concerns: list[Concern],
        responses: list[Any],
        constitution: str | None,
        advisory: list[str],
    ) -> str:
        sections: list[str] = []
        sections.append("# Stage")
        sections.append(self._stage)
        sections.append("# Artifacts (revised — what you are RE-reviewing)")
        sections.append(_serialize_artifacts(artifacts))
        sections.append("# Your prior concerns (with their `id`s)")
        sections.append(_serialize_concerns(own_concerns))
        if responses:
            sections.append("# Reviser's responses to those concerns")
            sections.append("\n".join(
                f"- concern_id: {r.concern_id}\n"
                f"  response: {getattr(r, 'response', '')!r}\n"
                f"  what_changed: {getattr(r, 'what_changed', '')!r}"
                for r in responses
            ))
        if constitution:
            sections.append("# Constitution (FR-030)")
            sections.append(constitution)
        if advisory:
            sections.append("# Advisory inputs")
            sections.append("\n\n".join(advisory))
        sections.append("# Task")
        sections.append(
            "RE-REVIEW: per the shared output contract's R3 rules. For "
            "each prior concern decide whether it has been ADEQUATELY "
            "ADDRESSED. Return concerns with the ORIGINAL `id`s preserved "
            "for any still unresolved + new concerns with fresh ids. Do "
            "NOT generate a fresh independent critique."
        )
        return "\n\n".join(sections)

    def _pick_default_artifact(self, artifacts: dict[str, str]) -> str:
        """Return the first non-context artifact key as the default
        `artifact` for concerns that don't specify one."""
        for key in artifacts:
            if not (key.startswith("__") and key.endswith("__")):
                return key
        return "(unknown)"

    def _call_backend(self, messages: list[ChatMessage]) -> str:
        # Route through the SAME-BACKEND peer-model fallback chain
        # (:func:`chat_with_model_fallback`): a transient outage/hang on the
        # primary model (e.g. a qwen3.5-122b vLLM stall) walks to gpt-oss-120b /
        # gemma on the same injected backend instead of retrying the dead model
        # and stalling the whole panel. The reasoning-safe ``max_tokens`` is
        # carried to every peer (they're also reasoning models). The helper owns
        # the kwarg-degradation for backends/test fakes whose ``chat`` signature
        # omits ``max_tokens``/``temperature``.
        response = chat_with_model_fallback(
            self._backend,
            messages,
            model=self._model,
            max_tokens=self._max_tokens,
            temperature=self._temperature,
        )
        return getattr(response, "text", "") or ""


# --- convenience: bulk panel construction --------------------------------


def build_panel(
    *,
    stage: str,
    lenses: list[str],
    backend: Any,
    repo_root: Path,
    model: str | None = None,
) -> list[LLMReviewer]:
    """Build a full LLMReviewer panel for one stage. Drivers (T068
    calibration, T073 traversal) call this to wire the registry's
    placeholder reviewers with live implementations."""
    return [
        LLMReviewer(
            lens=lens, stage=stage, backend=backend,
            repo_root=repo_root, model=model,
        )
        for lens in lenses
    ]


# Stable artifact hash helper (used by drivers that want to populate
# `artifact_hash` in their YAML before passing to the LLM).


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


__all__ = ["LLMReviewer", "build_panel", "sha256_hex"]
