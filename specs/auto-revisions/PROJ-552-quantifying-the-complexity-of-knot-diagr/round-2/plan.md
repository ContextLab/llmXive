# Implementation Plan

**Kind**: research_writing
**Action item severity counts**: writing=21, science=0

## Approach

For each `writing`-severity action item: edit the project's research
artifacts (reproducibility docs under `docs/`, specs under `specs/`,
data descriptors under `data/`) to address the concern.

For each `science`-severity action item: modify the analysis code
under `code/` (and `tests/`), re-run it, and record the corrected
results in the relevant `docs/` / `data/` artifact.

## Constraints

- All citations / external references remain verified.
- Changed Python must import and `py_compile` cleanly after the edit.
- The action items list is the authoritative scope — do NOT pull in
  refactors / cleanups beyond what each item demands.
