# Spec Amendment Request: AMENDMENT-001 — FR-008 Split Methodology

**Feature Branch**: `001-predicting-molecular-reactivity`
**Amendment ID**: AMENDMENT-001
**Date**: 2023-10-27
**Status**: Approved (this amendment tracks the workflow; spec.md has been updated in this revision)
**Affected Requirement**: FR-008
**Affected Success Criteria**: SC-001, SC-006
**Requested By**: Implementation Plan (`plan.md`, "Critical Methodology Update")

## 1. Summary of Change

Replace the mandated **reaction class stratification** split in FR-008 with a
**Scaffold Split** (grouped by Murcko scaffold) for all train/validation/test and
cross-validation splits of the GNN and baseline models.

## 2. Current (Old) FR-008 Text

> **FR-008**: System MUST ensure all models (GNN and baselines) are trained and
> evaluated on data splits stratified by reaction class to prevent confounding due
> to class imbalance. (See US-2)

## 3. Proposed (New) FR-008 Text

> **FR-008**: System MUST ensure all models (GNN and baselines) are trained and
> evaluated on data splits grouped by molecular scaffold (Murcko Scaffold Split)
> to prevent data leakage between train, validation, and test sets. The
> `reaction_class` field remains available as a reporting/analysis dimension
> (e.g., per-class error breakdown), but MUST NOT be used as the primary split
> key. (See US-2)

## 4. Rationale

1. **Data leakage prevention (construct validity).** Reaction class stratification
 only balances class frequencies; it does not prevent molecules sharing the same
 chemical scaffold from appearing in both training and test sets. Molecules with
 identical scaffolds are near-duplicates from a learning perspective, so a
 random/class-stratified split inflates test performance and invalidates the
 comparison between the GNN and descriptor-based baselines (FR-005, SC-001).
2. **Alignment with the research question.** The research question asks whether
 graph topology generalizes to unseen structures. A scaffold split directly
 evaluates generalization to novel scaffolds, which is the scientifically
 meaningful claim.
3. **Consistency with the implementation plan.** `plan.md` Phase 0, step 5 already
 implements the Scaffold Split via MurckoScaffold grouping and flags this spec
 contradiction. This amendment resolves the spec/plan contradiction so that
 T016a (Scaffold Split implementation) can proceed without violating the spec.
4. **Edge-case handling preserved.** The spec's edge case for reaction classes
 with <10 examples is retained through per-class reporting: classes with
 insufficient test-set representation are flagged as "insufficient data for
 stratified evaluation" in the evaluation report rather than dropped.

## 5. Impact Analysis

| Item | Impact |
| --- | --- |
| FR-008 | Rewritten (this amendment). |
| SC-001, SC-006 | Unchanged in wording; the "same stratified test set" is now the same scaffold-split test set. |
| plan.md | No change needed — plan already specifies Scaffold Split. |
| tasks.md | T016a implements the split; T016b tracks this amendment. |
| data-model.md | No change — `reaction_class` field is retained for reporting. |
| Test plans | Baseline comparison (US-2) uses identical scaffold folds for GNN, RF, and LR, preserving paired statistical tests. |

## 6. Approval

The plan proceeds with the Scaffold Split as the scientifically correct approach
(per `plan.md` "Critical Methodology Update"). `spec.md` has been updated in this
revision to incorporate the new FR-008 text; this document formally records the
amendment request and its rationale for traceability.
