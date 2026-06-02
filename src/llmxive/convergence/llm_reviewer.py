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
import re
import uuid
from pathlib import Path
from typing import Any

import yaml

from llmxive.backends.base import ChatMessage
from llmxive.backends.router import chat_with_model_fallback

from . import review_cache
from .types import Concern, Severity, Verdict

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


_FREE_TEXT_KEYS = ("text", "location", "response", "what_changed")
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


def _safe_yaml_load(yaml_text: str) -> object:
    """Robust YAML loader for LLM frontmatter.

    Three-stage recovery cascade:

    1. Try the standard ``yaml.safe_load``.
    2. If that fails, run the CONSERVATIVE repair
       ``_reformat_unquoted_scalars`` (only re-quotes scalars that
       contain problematic chars or are followed by mis-indented
       continuation). Try ``yaml.safe_load`` again.
    3. If that ALSO fails, run the AGGRESSIVE repair
       ``_force_block_scalar_all_freetext_keys`` (rewrites EVERY
       ``text``/``location``/``response``/``what_changed`` line as a
       block scalar regardless of what it looks like). Final attempt.
    4. If all three attempts fail, raise the ORIGINAL ``YAMLError``
       so the caller's error message points at the LLM's actual
       output, not at the repaired version.
    """
    try:
        return yaml.safe_load(yaml_text)
    except yaml.YAMLError as orig_err:
        # Stage 2: conservative repair.
        conservative = _reformat_unquoted_scalars(yaml_text)
        if conservative != yaml_text:
            try:
                return yaml.safe_load(conservative)
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
    if frontmatter is None:
        raise RuntimeError(
            f"LLMReviewer[{lens}]: response has no YAML frontmatter "
            f"(missing `---` delimiters). First 200 chars: "
            f"{response_text[:200]!r}"
        )
    try:
        meta = _safe_yaml_load(frontmatter) or {}
    except yaml.YAMLError as exc:
        raise RuntimeError(
            f"LLMReviewer[{lens}]: frontmatter is not valid YAML: {exc}"
        ) from exc
    if not isinstance(meta, dict):
        raise RuntimeError(
            f"LLMReviewer[{lens}]: frontmatter must be a YAML mapping; "
            f"got {type(meta).__name__}"
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
        sev_raw = str(c.get("severity", "writing")).strip().lower()
        try:
            sev = Severity(sev_raw)
        except ValueError as exc:
            raise RuntimeError(
                f"LLMReviewer[{lens}]: concern {i} has unknown severity "
                f"{sev_raw!r}; expected one of {[s.value for s in Severity]!r}"
            ) from exc
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
    ) -> None:
        self.name = lens
        self._lens = lens
        self._stage = stage
        self._backend = backend
        self._repo_root = Path(repo_root)
        self._model = model
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
