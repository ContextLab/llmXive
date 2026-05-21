"""Per-invocation inspection record writer for Phase 3 validation.

Spec 011 (Phase 3 — Specify → Clarify validation) needs verbatim per-agent
I/O capture: system prompt + user prompt + raw LLM response + parsed output
+ file diffs persisted to disk so a maintainer (or a later auditor) can
reconstruct exactly what an agent was asked and exactly what it produced
without re-invoking the LLM.

This module exposes a single public function, :func:`capture`, plus two
helpers (:func:`_redact`, :func:`_atomic_write`) factored out for testing.

The writer is OPT-IN. Production code paths only call into it when the
environment variable ``LLMXIVE_INSPECTION_DIR`` is set, which the spec-011
validation harness (:mod:`scripts.validate_phase3`) toggles for the
duration of each agent invocation. Production cron jobs never set the env
var, so this module is a no-op in production.

See ``specs/011-phase3-specify-clarify-testing/contracts/inspection-record.md``
for the formal JSON schema this writer emits.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

# Secrets that must NEVER appear verbatim in an inspection record.
# Each entry is read via ``os.environ.get`` at write time; any non-empty
# value found is replaced with the literal string ``<redacted>``. The
# deny-list is intentionally explicit — pattern-matching arbitrary
# "looks like a secret" strings is error-prone, while resolving via
# os.environ catches every real secret that the running process knew
# about. If a new credential gets introduced, append it here.
_SECRETS_ENV_VARS = (
    "DARTMOUTH_CHAT_API_KEY",
    "GITHUB_TOKEN",
    "GH_TOKEN",
    "ANTHROPIC_API_KEY",
    "HF_TOKEN",
    "OPENAI_API_KEY",
)

# Accepted outcome values — matches the per-agent base-class vocabulary
# used elsewhere in the pipeline. ``escalated`` (spec 014 / FR-014) covers
# the Tasker's analyze-loop cap-hit hand-off to human_input_needed.
_VALID_OUTCOMES = frozenset(
    {"committed", "abstained", "failed", "held", "no-op", "escalated"}
)

# Required schema keys (top-level). See contracts/inspection-record.md.
# ``rounds`` (spec 014 / FR-004) is appended; spec-011 records that predate it
# remain readable because the loader tolerates a missing key — but every
# record this writer EMITS includes it (default ``[]``).
_REQUIRED_KEYS = frozenset({
    "project_id", "agent_name", "agent_version", "model", "backend",
    "started_at", "ended_at", "duration_s", "outcome",
    "reset_artifacts", "prompts", "raw_response", "parsed_output",
    "file_diffs", "error", "rounds",
})


def _redact(text: str) -> str:
    """Replace any known-secret value found in ``text`` with ``<redacted>``.

    Reads each name in :data:`_SECRETS_ENV_VARS` via ``os.environ.get``;
    if the env var is set to a non-empty value, every occurrence of that
    value in ``text`` is substituted (string-equality, case-sensitive —
    not a regex, since a partial-match would be wrong for short keys).
    """
    if not text:
        return text
    out = text
    for name in _SECRETS_ENV_VARS:
        val = os.environ.get(name)
        if val and len(val) >= 8:  # don't redact 2-char "values" — too false-positive-prone
            out = out.replace(val, "<redacted>")
    return out


def _atomic_write(path: Path, data: str) -> None:
    """Write ``data`` to ``path`` atomically via a ``.tmp`` + ``os.replace`` swap.

    A concurrent reader never sees a half-written file: either the old
    full content (if the swap hasn't happened) or the new full content
    (if it has). Mode is 0o644; encoding is UTF-8.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(data, encoding="utf-8")
    os.chmod(tmp, 0o644)
    os.replace(tmp, path)


def capture(
    *,
    project_id: str,
    agent_name: str,
    agent_version: str,
    model: str,
    backend: str,
    started_at: datetime,
    ended_at: datetime,
    outcome: str,
    prompts: dict[str, str],
    raw_response: str,
    parsed_output: dict[str, Any],
    file_diffs: list[dict[str, str]],
    reset_artifacts: list[str],
    error: str | None,
    spec_root: Path,
    rounds: list[dict[str, Any]] | None = None,
) -> Path:
    """Write one inspection record JSON file and return its path.

    The schema follows ``contracts/inspection-record.md`` (v1). Writes
    are atomic. Secret env-var values are redacted from ``prompts.system``,
    ``prompts.user``, and ``raw_response`` before serialization.

    Args:
        project_id: ``PROJ-NNN-<slug>``.
        agent_name: ``"specifier"`` or ``"clarifier"`` (Phase 3 set).
        agent_version: prompt_version from agents/registry.yaml.
        model: resolved model id from chat_with_fallback.
        backend: e.g., ``"dartmouth"``.
        started_at, ended_at: tz-aware datetimes; ``ended_at >= started_at``.
        outcome: one of :data:`_VALID_OUTCOMES`.
        prompts: ``{"system": "...", "user": "..."}``. Either may be empty
            string only when outcome == "no-op".
        raw_response: verbatim LLM response text. Empty only when
            outcome == "no-op".
        parsed_output: agent's parsed interpretation. Empty dict allowed
            when outcome in {"failed", "no-op"}.
        file_diffs: ``[{path, before, after}, ...]``. Empty list when
            outcome in {"failed", "abstained", "no-op"}.
        reset_artifacts: paths the FR-015 reset removed before this
            invocation. Empty list when nothing was wiped.
        error: non-None iff outcome == "failed".
        spec_root: the spec directory under which to write
            ``inspections/<project_id>/<agent_name>.json``.
        rounds: spec 014 / FR-004 — one dict per Tasker analyze round
            (``round_index``, ``analyze_report``, ``mode_b_patch``,
            ``verdict``, ``files_rewritten``, ``diffs``). ``None``/empty for
            the Planner and every non-looping agent; persisted as ``[]``.

    Returns:
        Absolute path to the written JSON file.

    Raises:
        ValueError: if any required key is missing or outcome is invalid.
        TypeError: if started_at / ended_at aren't datetimes.
    """
    if outcome not in _VALID_OUTCOMES:
        raise ValueError(
            f"invalid outcome {outcome!r}; expected one of {sorted(_VALID_OUTCOMES)}"
        )
    if not isinstance(started_at, datetime) or not isinstance(ended_at, datetime):
        raise TypeError("started_at and ended_at must be datetime instances")
    if ended_at < started_at:
        raise ValueError(
            f"ended_at ({ended_at}) is before started_at ({started_at})"
        )
    # Cross-field outcome ↔ payload consistency.
    if outcome == "failed" and not error:
        raise ValueError("outcome=failed requires a non-empty error message")
    if outcome != "failed" and error:
        raise ValueError(
            f"outcome={outcome!r} forbids a non-null error (got {error!r})"
        )

    duration_s = (ended_at - started_at).total_seconds()
    record: dict[str, Any] = {
        "project_id": project_id,
        "agent_name": agent_name,
        "agent_version": agent_version,
        "model": model,
        "backend": backend,
        "started_at": started_at.isoformat(),
        "ended_at": ended_at.isoformat(),
        "duration_s": duration_s,
        "outcome": outcome,
        "reset_artifacts": list(reset_artifacts),
        "prompts": {
            "system": _redact(prompts.get("system", "")),
            "user": _redact(prompts.get("user", "")),
        },
        "raw_response": _redact(raw_response),
        "parsed_output": parsed_output,
        "file_diffs": [
            {"path": d["path"], "before": d.get("before", ""), "after": d.get("after", "")}
            for d in file_diffs
        ],
        "error": error,
        # spec 014 / FR-004: one sub-record per Tasker analyze round; ``[]``
        # for the Planner (and every spec-011-era agent).
        "rounds": list(rounds) if rounds else [],
    }

    # Schema sanity — every required key present at this point.
    missing = _REQUIRED_KEYS - record.keys()
    if missing:
        raise ValueError(f"missing required keys in record: {sorted(missing)}")

    out_path = Path(spec_root) / "inspections" / project_id / f"{agent_name}.json"
    payload = json.dumps(record, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    _atomic_write(out_path, payload)
    return out_path


__all__ = ["capture"]
