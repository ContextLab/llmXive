# Project-ID numbering race fix + duplicate cleanup

**Date**: 2026-05-06
**Triggered by**: user observation that two PROJ-261s and two PROJ-262s existed with different topics
**Tracked in**: spec 004 / PR #109

## Root cause

`src/llmxive/cli.py:_cmd_brainstorm` computed `next_num` once at the
top of the function from an in-memory snapshot of `state/projects/`,
then claimed IDs sequentially. The inner allocation loop only re-checked
against the local `existing_ids` set, never against disk. Two
concurrent invocations (e.g., two cron-driven `python -m llmxive
brainstorm` calls firing at the same time) would each compute the
same `next_num` from independent disk snapshots, then both write
`PROJ-NNN-<slug-A>.yaml` / `PROJ-NNN-<slug-B>.yaml` — duplicate
project numbers with different slugs.

This had already manifested on `main`:

| Duplicate group | Slug A | Slug B |
|-|-|-|
| PROJ-261 | `evaluating-the-impact-of-code-duplicatio` (carry-forward, computer science) | `investigating-the-correlation-between-gu` (biology) |
| PROJ-262 | `predicting-molecular-dipole-moments-with` (carry-forward, chemistry) | `quantifying-the-impact-of-magnetic-field` (physics) |

## Fix (Q1B from user dialog)

New module `src/llmxive/state/project_id_lock.py` with two helpers:

- `project_id_lock(repo_root)` — context manager that takes an
  exclusive `fcntl.flock` on `state/.brainstorm.lock` for the duration
  of the with-block. Lock is microseconds-long (covers only the
  read-disk + write-state-YAML window), not the LLM call.
- `next_available_proj_num(*, repo_root, starting_num=1)` — scans
  `state/projects/` AND `projects/` directories from disk and returns
  the smallest free `n`. Works correctly with `-iterN` suffixes
  (treats them as occupying the canonical slot).

`cli._cmd_brainstorm` now wraps the per-seed allocation in the lock,
and writes the state YAML eagerly inside the lock (acting as the ID
claim) before releasing.

Regression test at `tests/phase1/test_project_id_lock.py` — 8 tests,
including a `os.fork()`-based concurrent-allocation test that
confirms two children racing for the lock produce DISTINCT project
numbers.

## Cleanup (Q3A from user dialog)

Renamed the two non-carry-forward duplicates to next-available IDs
(331 + 332) so each PROJ-NNN is unique on the branch:

| Old ID | New ID |
|-|-|
| `PROJ-261-investigating-the-correlation-between-gu` | `PROJ-331-investigating-the-correlation-between-gu` |
| `PROJ-262-quantifying-the-impact-of-magnetic-field` | `PROJ-332-quantifying-the-impact-of-magnetic-field` |

The carry-forward projects (`PROJ-261-evaluating-...` and
`PROJ-262-predicting-...`) keep their numbers, since spec 003 + spec
004 reports + carry-forward manifests + the parent issue/tracker all
reference them.

Files updated:
- Project directories renamed under `projects/`.
- State YAMLs renamed under `state/projects/`; internal `id:` field
  updated.
- `.history.jsonl` files renamed.
- `web/data/projects.json` IDs replaced.
- Run-log JSONL entries (2 files) updated to use the new IDs.

## Verification

- `grep -rn "PROJ-261-investigating\|PROJ-262-quantifying" --include="*.md" --include="*.yaml" --include="*.json" --include="*.jsonl"` → 0 matches (clean).
- `pytest tests/phase1/test_project_id_lock.py -v` → 8/8 PASS.
- `pytest tests/phase1/` (full regression) → all PASS.
- `ls projects/` shows each PROJ-NNN unique.

## Forward-looking note

This fix is a defensive narrow patch on the brainstorm allocation
path. A future spec (likely the librarian-agent spec) should consider
whether other places that allocate project-ID-shaped strings
(`paper_initializer`, `task_atomizer`, etc.) also need the lock.

The lock pattern (`project_id_lock` + `next_available_proj_num`) is
reusable — any agent that needs to claim a fresh PROJ-NNN should
import these helpers rather than implementing its own allocation.
