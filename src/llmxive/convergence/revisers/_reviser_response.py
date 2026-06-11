"""Shared reviser response contract — delimited, path-keyed artifact bodies.

WHY THIS EXISTS (the bug it fixes)
----------------------------------
Every reviser used to instruct the LLM to return a single JSON object that
EMBEDDED the whole revised document(s) as JSON STRING value(s)
(``{"new_spec_md": "<~19K chars of escaped spec.md>", "responses": [...]}``)
and then parsed it with a bare ``json.loads``. For a large Markdown / LaTeX
document full of quotes, ``$``, backslashes and newlines the model frequently
emits INVALID JSON — a single unescaped ``"`` inside the body ends the string
early, so ``json.loads`` blows up ("Expecting ',' delimiter ... char 19455").
This crashed R2 of the convergence loop on EVERY reviewable stage.

THE FIX
-------
Separate the document bodies from the structured change-log:

* The per-concern change-log is a SMALL fenced ```json``` block — small,
  quote-light, and parsed leniently (it reliably round-trips).
* Each full revised artifact is emitted VERBATIM (exactly as it should land on
  disk — NO escaping, NO JSON) between line-markers::

      ===BEGIN_ARTIFACT <repo-relative-path>===
      <entire file content>
      ===END_ARTIFACT===

  A regex extracts ``{path: body}`` with zero unescaping, so quotes / ``$`` /
  backslashes / newlines in the body can never break the parse.

BACKWARD COMPATIBILITY
----------------------
If a reply carries NO ``===BEGIN_ARTIFACT`` markers we fall back to the LEGACY
JSON parse (``new_spec_md`` / ``new_tasks_md`` / ``new_idea_md`` /
``updated_artifacts`` ...). That keeps the existing fake-backend tests — which
feed the old JSON shape — green, and tolerates a model that still answers in
the old format. The legacy decode applies the proven lenient repairs
(``_escape_newlines_in_json_strings`` then a YAML fallback) before giving up.
"""

from __future__ import annotations

import json
import re
from typing import Any

from llmxive.speckit.clarify_cmd import _escape_newlines_in_json_strings
from llmxive.speckit.yaml_extract import parse_yaml_lenient

from ..types import Concern, ConcernResponse

# --- the canonical instruction injected into every reviser prompt ----------

RESPONSE_FORMAT_BLOCK = (
    "# Response format (MANDATORY — read carefully)\n\n"
    "Return your answer in TWO parts, in this exact order.\n\n"
    "## Part 1 — the per-concern change-log\n\n"
    "A SMALL fenced ```json block (and nothing else inside the fence) with "
    "this exact shape:\n\n"
    "```json\n"
    "{\n"
    '  "responses": [\n'
    "    {\n"
    '      "concern_id": "<id of a panel concern>",\n'
    '      "response": "<how you addressed this concern>",\n'
    '      "what_changed": "<concrete diff summary>",\n'
    '      "artifacts_changed": ["<repo-relative path you edited>"]\n'
    "    }\n"
    "  ]\n"
    "}\n"
    "```\n\n"
    "Keep this JSON SMALL: it is only the change-log, never the documents "
    "themselves. Every panel concern MUST have exactly one entry.\n\n"
    "## Part 2 — each full revised artifact, VERBATIM\n\n"
    "After the json fence, emit EACH artifact you changed as raw text "
    "(exactly the bytes that should be written to disk — do NOT escape it, do "
    "NOT wrap it in JSON, do NOT fence it), framed by these EXACT line "
    "markers, one block per artifact:\n\n"
    "===BEGIN_ARTIFACT <repo-relative-path>===\n"
    "<the entire file content, verbatim>\n"
    "===END_ARTIFACT===\n\n"
    "Rules for Part 2:\n"
    "- Emit the COMPLETE file each time (not a patch / diff).\n"
    "- The path on the BEGIN line MUST be one of the editable paths named in "
    "the task above, copied EXACTLY.\n"
    "- The body between the markers is taken literally; quotes, $, backslashes "
    "and blank lines are fine and need NO escaping.\n"
    "- Emit ONE block per artifact you change; omit artifacts you did not "
    "change.\n"
)


# --- delimited-artifact extraction -----------------------------------------

# Matches one ``===BEGIN_ARTIFACT <path>=== ... ===END_ARTIFACT===`` block.
# The path captures everything up to the trailing ``===`` on the BEGIN line;
# the body is non-greedy up to the next END marker. DOTALL so the body may
# span newlines.
#
# Equals-count TOLERANCE (``={2,}``): the prompt asks for exactly three ``=``,
# but reasoning models emit the run NON-DETERMINISTICALLY as two, three, or more
# ``=`` from one sample to the next. The strict 3-``=`` form silently extracted
# ZERO artifacts whenever a sample used two — so the reviser's whole revision was
# discarded, every concern padded ``<missing>``, and the panel kicked back (the
# PROJ-552 plan-stage loop: round-1 happened to emit ``==`` → 0 artifacts →
# kickback, while rounds that emitted ``===`` converged). The keywords
# ``BEGIN_ARTIFACT`` / ``END_ARTIFACT`` anchor the match, so a looser delimiter
# never over-matches ordinary ``==`` prose.
_ARTIFACT_BLOCK_RE = re.compile(
    r"^={2,}BEGIN_ARTIFACT[ \t]+(?P<path>.+?)[ \t]*={2,}[ \t]*\r?\n"
    r"(?P<body>.*?)"
    r"\r?\n?^={2,}END_ARTIFACT={2,}[ \t]*\r?$",
    re.DOTALL | re.MULTILINE,
)


def _extract_delimited_artifacts(text: str) -> dict[str, str]:
    """Pull every ``===BEGIN_ARTIFACT <path>=== ... ===END_ARTIFACT===`` block.

    Returns ``{path: body}`` with the body taken raw (NO unescaping). Only a
    single trailing newline before the END marker is stripped (the regex
    consumes it) — the body is otherwise byte-for-byte what the model emitted.
    """
    out: dict[str, str] = {}
    for m in _ARTIFACT_BLOCK_RE.finditer(text or ""):
        path = m.group("path").strip()
        body = m.group("body")
        if path:
            out[path] = body
    return out


# --- responses (change-log) extraction -------------------------------------


def _strip_response_fence(text: str) -> str:
    """Return the FIRST ```json fenced block, else the first balanced {...}.

    The change-log lives in a small fenced json block that precedes the
    artifact markers. If no fence is present, fall back to the first
    balanced object so a model that forgot the fence still parses.
    """
    raw = text or ""
    fence = re.search(
        r"```(?:json|yaml|yml)?\s*\n(.*?)\n```", raw, re.DOTALL | re.IGNORECASE
    )
    if fence:
        return fence.group(1)
    # First balanced {...}: scan for the first '{' then match braces, ignoring
    # braces inside double-quoted strings.
    start = raw.find("{")
    if start == -1:
        return raw
    depth = 0
    in_str = False
    escape = False
    for i in range(start, len(raw)):
        ch = raw[i]
        if escape:
            escape = False
            continue
        if ch == "\\":
            escape = True
            continue
        if ch == '"':
            in_str = not in_str
            continue
        if in_str:
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return raw[start : i + 1]
    return raw[start:]


def _loads_lenient(payload: str) -> Any:
    """``json.loads`` with the proven lenient repairs, then a YAML fallback.

    Reuses the clarify/tasks-command helpers so the change-log parse matches
    the rest of the codebase. Returns the parsed object, or raises the final
    ``json.JSONDecodeError`` / ``yaml.YAMLError`` if nothing parses.
    """
    try:
        return json.loads(payload)
    except json.JSONDecodeError:
        pass
    try:
        return json.loads(_escape_newlines_in_json_strings(payload))
    except json.JSONDecodeError:
        pass
    # YAML is a JSON superset and tolerates many LLM quirks; let its error
    # propagate if even this fails.
    return parse_yaml_lenient(payload)


def _extract_responses(text: str) -> list[dict[str, Any]]:
    """Parse the change-log's ``responses`` list from the reply (leniently).

    Returns the raw list of response dicts (empty list if none / unparseable
    — the caller pads to one-per-concern, so an empty list is honest, not a
    crash). Artifact extraction is what gates total failure, not this.
    """
    fenced = _strip_response_fence(text)
    try:
        obj = _loads_lenient(fenced)
    except Exception:  # any parse failure → no responses
        return []
    if not isinstance(obj, dict):
        return []
    raw = obj.get("responses")
    if not isinstance(raw, list):
        return []
    return [r for r in raw if isinstance(r, dict)]


# --- legacy fallback --------------------------------------------------------

# The single-doc legacy keys. Each maps the old JSON ``new_*_md`` field onto
# the reviser's expected artifact path. A reviser's expected artifact path
# SUFFIX selects which key it owns (so a reply that — wrongly — carries BOTH
# ``new_tasks_md`` and ``new_spec_md`` still routes the right body to a
# tasks-side reviser; the engine's downstream guards reject the cross-write).
_LEGACY_KEY_FOR_SUFFIX: tuple[tuple[str, str], ...] = (
    ("tasks.md", "new_tasks_md"),
    ("spec.md", "new_spec_md"),
)
# Fallback probe order when the expected path matches no known suffix.
_LEGACY_SINGLE_DOC_KEYS = ("new_spec_md", "new_tasks_md", "new_idea_md")


def _legacy_key_for_target(target: str | None) -> tuple[str, ...]:
    """Return the legacy single-doc key(s) to probe for ``target``, most
    specific first, then the generic fallbacks."""
    preferred: list[str] = []
    if target:
        for suffix, key in _LEGACY_KEY_FOR_SUFFIX:
            if target.endswith(suffix):
                preferred.append(key)
                break
    # Idea artifacts have no distinctive 'spec.md'/'tasks.md' suffix; the
    # generic probe order (which includes ``new_idea_md``) covers them.
    rest = [k for k in _LEGACY_SINGLE_DOC_KEYS if k not in preferred]
    return tuple(preferred + rest)


def _legacy_parse(
    text: str, expected_artifacts: list[str]
) -> tuple[dict[str, str], list[dict[str, Any]]] | None:
    """LEGACY JSON parse for replies with NO ``===BEGIN_ARTIFACT`` markers.

    Handles both legacy shapes:

    * ``{"new_spec_md"/"new_tasks_md"/"new_idea_md": "<doc>", "responses": [...]}``
      → single-doc; keyed to ``expected_artifacts[0]``.
    * ``{"updated_artifacts": {path: text, ...}, "responses": [...]}``
      → multi-doc; paths kept as-is (caller validates against its set).

    Returns ``(artifacts_by_path, responses)`` or ``None`` when the reply is
    not parseable JSON/YAML at all (so the caller raises its own honest
    ``parseable JSON`` error with its own message). When the reply parses but
    carries no usable doc field, returns ``({}, responses)`` so the caller can
    raise its own ``no usable '<field>'`` error.
    """
    fenced = _strip_response_fence(text)
    try:
        obj = _loads_lenient(fenced)
    except Exception:  # not parseable at all
        return None
    if not isinstance(obj, dict):
        return None

    responses_raw = obj.get("responses")
    responses = (
        [r for r in responses_raw if isinstance(r, dict)]
        if isinstance(responses_raw, list)
        else []
    )

    # Multi-doc legacy shape.
    raw_updates = obj.get("updated_artifacts")
    if isinstance(raw_updates, dict):
        arts = {
            str(p): t for p, t in raw_updates.items() if isinstance(t, str)
        }
        return arts, responses

    # Single-doc legacy shape. Probe the key that matches the reviser's
    # expected artifact FIRST (so a tasks reviser picks ``new_tasks_md`` even
    # when the reply also — wrongly — carries ``new_spec_md``).
    target = expected_artifacts[0] if expected_artifacts else None
    for key in _legacy_key_for_target(target):
        val = obj.get(key)
        if isinstance(val, str) and val.strip():
            return {target or key: val}, responses

    # Parsed, but no usable doc field — let the caller raise its own message.
    return {}, responses


# --- public API -------------------------------------------------------------


def parse_reviser_response(
    text: str, *, expected_artifacts: list[str]
) -> tuple[dict[str, str], list[dict[str, Any]]]:
    """Parse a reviser reply into ``(new_artifacts_by_path, responses)``.

    Strategy:

    1. Extract every ``===BEGIN_ARTIFACT <path>=== ... ===END_ARTIFACT===``
       block (the robust delimited contract — bodies need no unescaping). If
       ANY block is present, that is the authoritative artifact set; the
       change-log ``responses`` are parsed leniently from the small fenced
       json block.
    2. BACKWARD-COMPAT: if NO delimited markers are present, fall back to the
       LEGACY JSON parse (``new_*_md`` / ``updated_artifacts``).
    3. Total failure (no artifacts extracted by EITHER path AND the legacy
       parse could not even parse the reply): raise ``RuntimeError`` so the
       engine treats it as non-convergence (preserves fail-loud behaviour).

    ``responses`` is returned RAW (list of dicts as the model emitted them);
    the caller maps each onto a ``ConcernResponse`` and pads missing concerns.
    """
    delimited = _extract_delimited_artifacts(text)
    if delimited:
        return delimited, _extract_responses(text)

    legacy = _legacy_parse(text, expected_artifacts)
    if legacy is None:
        raise RuntimeError(
            "reviser response carried neither '===BEGIN_ARTIFACT' markers nor "
            "parseable legacy JSON; first 200 chars: "
            f"{(text or '')[:200]!r}"
        )
    # legacy may be ({}, responses) — the caller decides whether an empty
    # artifact map is an error for its contract (single-doc revisers raise a
    # 'no usable <field>' message; multi-doc revisers raise on their own map).
    return legacy


def build_concern_responses(
    responses_raw: list[dict[str, Any]],
    concerns: list[Concern],
    *,
    default_artifacts: list[str] | None = None,
) -> list[ConcernResponse]:
    """Map raw response dicts onto one ``ConcernResponse`` per concern.

    Preserves the existing per-concern padding behaviour shared by every
    reviser: a concern with no matching response gets an explicit
    ``response="<missing>"`` entry (so R3 sees it and fails the concern); an
    empty field becomes ``"<empty>"``. ``default_artifacts`` seeds
    ``artifacts_changed`` when the model omits it (single-doc revisers pass
    ``[the_doc_path]``; multi-doc revisers pass ``None`` → empty list).
    """
    by_id: dict[str, dict[str, Any]] = {}
    for raw in responses_raw:
        cid = raw.get("concern_id")
        if isinstance(cid, str):
            by_id[cid] = raw

    # Observability (notes/spec-015 follow-up): when concerns get padded
    # ``<missing>``, record WHY in ``what_changed`` so the convergence trail
    # distinguishes "the whole reply parsed to zero per-concern responses"
    # (format drift / truncation — the PROJ-552 plan-009 R2 shape) from "the
    # model answered other concerns but skipped this one". A total parse
    # failure raises upstream and never reaches this padding path.
    if not by_id:
        missing_reason = (
            "reviser reply parsed to ZERO per-concern responses "
            f"({len(responses_raw)} raw entries, none with a concern_id) — "
            "likely response-format drift or truncation; no response for "
            "this concern"
        )
    else:
        answered_preview = ", ".join(sorted(by_id)[:5])
        missing_reason = (
            "reviser produced no response for this concern (it DID respond "
            f"to {len(by_id)} other concern(s): {answered_preview}"
            f"{', …' if len(by_id) > 5 else ''})"
        )

    out: list[ConcernResponse] = []
    for c in concerns:
        r = by_id.get(c.id)
        if r is None:
            out.append(
                ConcernResponse(
                    concern_id=c.id,
                    response="<missing>",
                    what_changed=missing_reason,
                    artifacts_changed=[],
                )
            )
            continue
        out.append(
            ConcernResponse(
                concern_id=c.id,
                response=str(r.get("response", "")).strip() or "<empty>",
                what_changed=str(r.get("what_changed", "")).strip() or "<empty>",
                artifacts_changed=[
                    str(x)
                    for x in (r.get("artifacts_changed") or (default_artifacts or []))
                ],
            )
        )
    return out



#: Corrective re-prompt for the load-dependent failure observed live on
#: PROJ-552's plan panel (spec 023 defect #13): under a heavy concern load
#: the model spends its output on a long change-log and emits ZERO complete
#: ``===BEGIN_ARTIFACT`` blocks — the reply parses but the revision is
#: unusable. One explicit re-pass recovers it.
MISSING_ARTIFACTS_REPROMPT = (
    "\n\nIMPORTANT — your previous reply contained the per-concern "
    "change-log but ZERO complete ===BEGIN_ARTIFACT blocks, so the entire "
    "revision was unusable. Re-emit your answer with BOTH parts: keep each "
    "change-log entry to ONE short sentence, then emit EVERY artifact you "
    "changed as a complete ===BEGIN_ARTIFACT <path>=== ... "
    "===END_ARTIFACT=== block. Budget your output for the artifact blocks "
    "first; never end the reply without them."
)


def run_pass_with_artifact_retry(run_pass, *, reviser_name: str):
    """Call ``run_pass()``; on the zero-artifact RuntimeError, make ONE
    corrective re-pass with :data:`MISSING_ARTIFACTS_REPROMPT` appended to
    the prompt (every doc reviser exposes the ``extra_instructions`` hook).
    Anything other than the zero-artifact/unparseable shape propagates
    unchanged (backend outages are not retried here)."""
    import logging

    from llmxive.backends.base import BackendError

    try:
        return run_pass()
    except BackendError:
        raise
    except RuntimeError as exc:
        if "no usable" not in str(exc) and "parseable" not in str(exc):
            raise
        logging.getLogger(__name__).warning(
            "%s: reply unusable (%s) — corrective re-pass", reviser_name,
            str(exc)[:120],
        )
        return run_pass(MISSING_ARTIFACTS_REPROMPT)

__all__ = [
    "MISSING_ARTIFACTS_REPROMPT",
    "RESPONSE_FORMAT_BLOCK",
    "build_concern_responses",
    "parse_reviser_response",
    "run_pass_with_artifact_retry",
]
