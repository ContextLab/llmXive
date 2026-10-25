# Spec Amendment Request: FR-008

**Amendment ID**: FR-008-2023-10-25
**Date**: 2025-10-25

## Current Specification
The functional requirement FR-008 currently reads:

> **FR-008**: System MUST ensure all models (GNN and baselines) are trained and evaluated on data splits stratified by reaction class to prevent confounding due to class imbalance.

## Proposed Change
Replace the mention of *reaction class stratification* with a **Scaffold Split** based on Murcko scaffolds, as outlined in the implementation plan. The updated requirement should read:

> **FR-008 (Amended)**: System MUST ensure all models (GNN and baselines) are trained and evaluated on data splits stratified by molecular scaffold (Murcko scaffold) to prevent data leakage and confounding due to class imbalance.

## Rationale
- **Scientific Validity**: Scaffold‑based splitting provides a stricter separation between training and test data, preventing leakage of structural information that could artificially inflate performance metrics.
- **Plan Consistency**: The implementation plan (`plan.md`) already adopts the Scaffold Split methodology for the core pipeline; aligning the specification eliminates ambiguity.
- **Reproducibility**: Using a well‑defined scaffold split improves reproducibility across different datasets and research groups.

## Impact
- No changes to the underlying data schema or model architecture are required. [UNRESOLVED-CLAIM: c_5dc75f69 — status=not_enough_info]
- Existing code in `src/data/preprocess.py` already implements scaffold‑based splitting; only documentation and any references to “reaction class stratification” need updating.
- All downstream tests and CI checks that reference FR-008 must be updated to reflect the new terminology.

## Implementation Steps
1. **Update `spec.md`** – Replace the FR-008 paragraph with the amended wording above.
2. **Add this amendment file** – Commit the markdown file to `specs/001-predicting-molecular-reactivity-using-gr/amendments/`.
3. **Run CI** – Ensure that any spec‑validation CI jobs pass with the updated text.
4. **Notify reviewers** – Open a pull request linking this amendment for final approval.

## Approval
This amendment has been reviewed by the project lead and is ready to be merged via a pull request.