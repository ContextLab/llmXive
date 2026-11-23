# PR: Align FR-008 with Scaffold Split methodology (AMENDMENT-001)

## Description

This PR resolves the documented contradiction between `spec.md` FR-008 (which
mandated reaction class stratification for data splits) and `plan.md` (which
implements a Murcko Scaffold Split to prevent data leakage). It updates
`spec.md` FR-008 to mandate the Scaffold Split and records the formal amendment
request (AMENDMENT-001) under
`specs/001-predicting-molecular-reactivity-using-gr/amendments/`.

## Motivation

Reaction class stratification balances class frequencies but does not prevent
molecules with shared scaffolds from appearing in both train and test sets,
which inflates test performance and undermines the GNN-vs-baseline comparison
(FR-005, SC-001, SC-006). A scaffold split evaluates generalization to novel
molecular scaffolds, which is the claim the research question actually makes.

## Changes

- **spec.md — FR-008**: replaced "stratified by reaction class" with "grouped by
 molecular scaffold (Murcko Scaffold Split)"; `reaction_class` is retained as a
 reporting dimension only, not a split key.
- **Added** `amendments/AMENDMENT-001-FR-008-scaffold-split.md`: the formal
 amendment request with rationale and impact analysis.
- **Added** this PR description for workflow traceability (task T009).

## New FR-008 Text

> **FR-008**: System MUST ensure all models (GNN and baselines) are trained and
> evaluated on data splits grouped by molecular scaffold (Murcko Scaffold Split)
> to prevent data leakage between train, validation, and test sets. The
> `reaction_class` field remains available as a reporting/analysis dimension
> (e.g., per-class error breakdown), but MUST NOT be used as the primary split
> key. (See US-2)

## Impact

- Unblocks T016a (Scaffold Split implementation in `src/data/preprocess.py`).
- US-2 comparison (T024–T027) uses identical scaffold folds across GNN, RF, and
 LR, keeping the paired statistical tests valid.
- No changes to data-model, contracts, or success criteria values.

## Verification

- [x] Amendment document exists with rationale and impact analysis.
- [x] `spec.md` FR-008 text updated to the new wording.
- [x] `reaction_class` retained in the data model for per-class reporting.
