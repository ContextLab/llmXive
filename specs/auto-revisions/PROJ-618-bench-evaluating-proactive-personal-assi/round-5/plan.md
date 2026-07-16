# Implementation Plan

**Kind**: paper_writing
**Action item severity counts**: writing=3, science=0

## Approach

For each `writing`-severity action item: edit the manuscript LaTeX
source (under `paper/source/`) to address the concern. Re-compile
after each batch of edits.

For each `science`-severity action item: assess whether the underlying
research artifact (data, analysis, experiments) requires modification.
If yes: edit code under the project's research spec; re-run; integrate
results into the manuscript.

## Constraints

- All citations remain verified.
- LaTeX must compile cleanly after the revision (proofreader flags empty).
- The action items list is the authoritative scope — do NOT pull in
  refactors / cleanups beyond what each item demands.
