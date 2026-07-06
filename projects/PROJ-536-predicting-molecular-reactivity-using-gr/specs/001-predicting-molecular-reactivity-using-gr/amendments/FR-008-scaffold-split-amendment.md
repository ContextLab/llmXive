# Amendment Request: FR-008 Data Splitting Strategy

**Date**: 2023-10-27
**Author**: Automated Science Pipeline (llmXive)
**Related Tasks**: T009, T016a
**Status**: Draft for Review

## Summary

This amendment proposes updating **Functional Requirement FR-008** in `spec.md` to explicitly mandate a **Scaffold Split** methodology for data partitioning, replacing the previously implied "reaction class stratification" approach. This change aligns the specification with the implementation plan (`plan.md`) and the critical need to prevent data leakage in molecular property prediction tasks.

## Context

In molecular machine learning, standard random splits often lead to over-optimistic performance estimates because structurally similar molecules (sharing the same Murcko scaffold) frequently appear in both training and test sets. If the model simply memorizes the scaffold's properties, it will appear to generalize well even when it has learned no reaction chemistry.

The current `spec.md` mentions "reaction class stratification," which does not guarantee structural separation between splits. The implementation plan (`plan.md`) and the scaffold split logic implemented in `T016a` (`src/data/preprocess.py`) require a strict structural separation.

## Proposed Change

Replace the text of **FR-008** in `spec.md` with the following:

> **FR-008: Data Splitting Strategy**
> The dataset must be partitioned into training, validation, and test sets using a **Scaffold Split** based on the Bemis-Murcko scaffold of the product molecule.
>
> **Requirements**:
> 1. **Scaffold Definition**: The scaffold is defined as the union of all rings and linkers in the product molecule's graph, excluding terminal side chains.
> 2. **Split Integrity**: No molecule sharing the same Murcko scaffold may appear in more than one split (train/val/test).
> 3. **Stratification**: If possible, the split should maintain the distribution of reaction classes across the three sets, but structural integrity (scaffold uniqueness) takes precedence over class balance.
> 4. **Ratio**: The default split ratio is 80% training, 10% validation, and 10% test.
> 5. **Leakage Prevention**: Any molecule in the test set that shares a scaffold with the training set is considered a data leakage error and must be excluded.

## Rationale

1. **Scientific Validity**: A scaffold split provides a more rigorous test of a model's ability to generalize to *new* chemical spaces, which is the true goal of reactivity prediction.
2. **Consistency**: Aligns the specification with the actual implementation in `src/data/preprocess.py` (Task T016a).
3. **Industry Standard**: This is the standard evaluation protocol for molecular property prediction (e.g., in MoleculeNet benchmarks) to ensure fair comparison with state-of-the-art methods.

## Impact Analysis

- **Spec.md**: Requires text replacement in the Functional Requirements section.
- **Data Pipeline**: No code changes required; `src/data/preprocess.py` already implements this logic.
- **Metrics**: Expected MAE/RMSE may increase compared to a random split, but this reflects a more realistic assessment of model performance.

## Acceptance Criteria

- [ ] `spec.md` is updated with the new FR-008 text.
- [ ] The `src/data/preprocess.py` module is verified to enforce the scaffold split constraint.
- [ ] A validation script confirms 0% scaffold overlap between train and test sets.

## Approval

*Pending approval from the project lead to merge into `spec.md`.*
