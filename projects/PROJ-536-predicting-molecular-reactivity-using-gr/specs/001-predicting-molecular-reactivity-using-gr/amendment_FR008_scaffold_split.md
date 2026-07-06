# Spec Amendment Request: FR-008 Data Splitting Strategy

**Date**: 2023-10-27
**Author**: llmXive Automated Science Pipeline
**Related Task**: T009
**Target Document**: `specs/001-predicting-molecular-reactivity-using-gr/spec.md`
**Section**: Functional Requirements (FR-008)

## 1. Current State

The current specification for **FR-008** (Data Splitting Strategy) mandates:
> "The dataset must be split into training, validation, and test sets using **reaction class stratification** to ensure that each split contains a representative distribution of reaction classes."

This approach assumes that reaction classes are well-defined, non-overlapping, and that the primary source of variance is the reaction class itself. It does not explicitly account for molecular scaffold bias, where similar molecules (sharing a Murcko scaffold) might appear in both training and test sets, leading to overly optimistic performance estimates (data leakage).

## 2. Problem Statement

Recent analysis and the project's implementation plan (`plan.md`) indicate that **Scaffold Split** is the industry standard for molecular machine learning to prevent data leakage. Reaction class stratification alone is insufficient because:
1. **Scaffold Leakage**: Molecules with the same core scaffold but different substituents may be assigned to different reaction classes, allowing the model to "memorize" the scaffold rather than learning generalizable reactivity rules.
2. **Generalization Goal**: The goal is to predict reactivity for *novel* chemical spaces. A scaffold split ensures the model is tested on entirely new core structures, providing a more rigorous evaluation of true generalization capability.
3. **Plan Alignment**: The project implementation plan explicitly requires a "Scaffold Split" methodology to satisfy SC-005 (Data Validity) and ensure robust model evaluation.

## 3. Proposed Change

Update **FR-008** to replace "reaction class stratification" with "Scaffold Split based on Murcko Scaffolds".

### New Requirement Text (FR-008)
> "The dataset must be split into training, validation, and test sets using a **Scaffold Split** strategy based on Bemis-Murcko scaffolds.
>
> - **Method**: Generate the Bemis-Murcko scaffold for every unique molecule in the dataset. Group reactions by the scaffolds of their reactants.
> - **Distribution**: Ensure that the distribution of reaction classes is approximately balanced across splits, but prioritize the separation of scaffolds. No scaffold present in the training set may appear in the validation or test sets.
> - **Ratio**: Maintain a standard split ratio (e.g., 80% train, 10% validation, 10% test) unless statistical power dictates otherwise.
> - **Leakage Prevention**: This split must strictly prevent data leakage of molecular cores between training and evaluation sets."

## 4. Impact Analysis

- **Data Pipeline**: The `src/data/preprocess.py` module (Task T016a) must implement scaffold generation (via RDKit) and grouping logic instead of simple class-based stratification.
- **Evaluation**: Metrics may initially appear lower compared to random/class-based splits, as the model faces a harder generalization task. This is the correct and expected behavior for a rigorous scientific study.
- **Documentation**: The `spec.md` and `plan.md` must be synchronized to reflect this change.
- **No Breaking Changes**: This change improves the scientific validity of the project without altering the core architecture or input/output contracts.

## 5. Acceptance Criteria

1. `spec.md` is updated to reflect the new FR-008 text.
2. `src/data/preprocess.py` implements the scaffold split logic using `rdkit.Chem.Scaffolds.MurckoScaffold`.
3. Unit tests confirm that no scaffold ID appears in both training and test sets.
4. The implementation log explicitly reports the number of unique scaffolds in each split.

## 6. Approval Status

[ ] Approved
[ ] Pending Review
[ ] Rejected (with comments)

*Note: This amendment is required before the implementation of T016a (Scaffold Split logic) to ensure the code aligns with the approved specification.*
