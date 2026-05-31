"""FR-031 deterministic pre-filter guards for tasker writebacks (T027 cutover).

Single source of truth (Constitution Principle I) for the four refusal
guards that BOTH paths — the legacy Mode-A/Mode-B loop in ``tasks_cmd.py``
AND the spec-015 convergence-engine bridge in ``_tasker_engine_bridge.py``
— MUST run before persisting an LLM-produced spec.md / plan.md / tasks.md
rewrite. The guards were inlined in ``tasks_cmd.py`` at lines ~322, ~330,
~348, ~361 before this extraction; the engine bridge previously skipped
them entirely, which violated FR-031. T027 production cutover requires
both code paths to use the same guards.

Guard catalog:

* ``_tasks_task_id_count`` — a tasks.md rewrite must contain at least 5
  ``T###`` ids (otherwise the LLM has replaced the file with prose like
  "all tasks completed"; observed regression).
* ``_has_markdown_header`` — a spec.md / plan.md rewrite must have at
  least one ``# `` header line (otherwise the LLM has replaced the file
  with raw prose).
* ``_constraint_preservation`` — a spec.md rewrite MUST NOT shrink the
  set of distinct ``FR-###`` / ``SC-###`` identifiers vs. the prior
  on-disk content (FR-012; observed: 12 FR + 5 SC → 0 FR + 2 SC across
  rounds on PROJ-262 — the constitution-forbidden "weaken the test"
  failure mode).
* ``looks_like_diff`` (from ``_diff_guard``) — a writeback must not be
  a unified or context diff.

Public API:

* :func:`check_legacy_guards` — given a target filename and the
  proposed new content + the existing on-disk content, return the list
  of refusal messages (empty list = guards pass).
"""

from __future__ import annotations

import re

from ._diff_guard import looks_like_diff

_TASK_ID_RE = re.compile(r"^- \[[ Xx]\] T\d+[a-z]?\b", re.MULTILINE)
_MD_HEADER_RE = re.compile(r"^# ", re.MULTILINE)
_FR_SC_RE = re.compile(r"\b(?:FR|SC)-\d+")


def _tasks_task_id_count(content: str) -> int:
    """Return the number of ``- [ ] T###`` / ``- [X] T###`` lines."""
    return len(_TASK_ID_RE.findall(content))


def _has_markdown_header(content: str) -> bool:
    return bool(_MD_HEADER_RE.search(content))


def _constraint_id_set(content: str) -> set[str]:
    return set(_FR_SC_RE.findall(content))


def check_legacy_guards(
    *,
    filename: str,
    new_content: str,
    original_content: str,
) -> list[str]:
    """Run the FR-031 pre-filter guards on a proposed writeback.

    Args:
        filename: bare filename — one of ``"tasks.md"``, ``"spec.md"``,
            ``"plan.md"``. The guard set is filename-specific.
        new_content: the LLM's proposed full-file rewrite.
        original_content: the on-disk content the rewrite would replace
            (used for the FR-012 constraint-preservation check on
            spec.md).

    Returns:
        A list of human-readable refusal messages. An empty list means
        every guard passed and the caller MAY persist ``new_content``.
        A non-empty list means the caller MUST reject the writeback;
        each message names the violated invariant so it can be surfaced
        back through the engine as a Concern (or logged by the legacy
        loop).
    """
    refusals: list[str] = []

    # Universal guard: never write a unified or context diff.
    is_diff, reason = looks_like_diff(new_content)
    if is_diff:
        refusals.append(
            f"refusing {filename} writeback: looks like a diff ({reason})"
        )
        # If it's a diff we don't run the structural guards; the content
        # is fundamentally the wrong shape.
        return refusals

    if filename == "tasks.md":
        n_ids = _tasks_task_id_count(new_content)
        if n_ids < 5:
            refusals.append(
                f"refusing tasks.md writeback: only {n_ids} task IDs "
                f"(need >=5). The LLM likely replaced the file with prose."
            )
        return refusals

    if filename in ("spec.md", "plan.md"):
        if not _has_markdown_header(new_content):
            refusals.append(
                f"refusing {filename} writeback: no markdown headers."
            )

    if filename == "spec.md":
        # FR-012: the set of distinct FR-/SC- ids must NOT shrink. The
        # legacy loop observed a regression on PROJ-262 where the LLM
        # "resolved" analyze findings by gutting the spec (12 FR / 5 SC
        # -> 0 FR / 2 SC).
        cur_ids = _constraint_id_set(original_content)
        new_ids = _constraint_id_set(new_content)
        if len(new_ids) < len(cur_ids):
            refusals.append(
                f"refusing spec.md writeback: it drops requirements "
                f"({len(cur_ids)} -> {len(new_ids)} FR/SC ids); a "
                f"constraint would be deleted."
            )

    return refusals


__all__ = ["check_legacy_guards"]
