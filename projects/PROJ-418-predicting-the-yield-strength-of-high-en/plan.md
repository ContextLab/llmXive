# Project Plan: Predicting the Yield Strength of High‑Entropy Alloys

**Project ID:** PROJ-418-predicting-the-yield-strength-of-high-en
**Document version:** 1.1 (updated to reflect FR‑006)
**Last updated:** 2026‑07‑30

## Table of Contents

1. [Project Scope](#project-scope)
2. [Data Acquisition & Descriptor Engineering](#data-acquisition--descriptor-engineering)
3. [Model Training & Evaluation](#model-training--evaluation)
4. [Statistical Validation & Significance Testing](#statistical-validation--significance-testing)
5. [Reporting & Disclaimers](#reporting--disclaimers)
6. [Cross‑Cutting Concerns & Infrastructure](#cross‑cutting-concerns--infrastructure)
7. [Change Log](#change-log)

## Project Scope

The goal of this project is to predict the **yield strength** of high‑entropy alloys (HEAs) from compositional descriptors. The pipeline proceeds through the following high‑level stages:

1. **Data acquisition** – download verified HEA composition datasets.
2. **Descriptor calculation** – compute δ, Δχ, VEC, mixing entropy, and melting‑temperature variance.
3. **Model training** – train Linear Regression, Random Forest, and Gradient Boosting models with 5‑fold cross‑validation.
4. **Statistical validation** – permutation importance, multiple‑comparison correction, bootstrap confidence intervals, VIF diagnostics, and sensitivity analysis.
5. **Reporting** – generate a comprehensive markdown report with mandatory disclaimer text.

All steps are fully automated and produce artefacts under the `data/`, `output/`, and `figures/` directories as described in the task specifications.

## Data Acquisition & Descriptor Engineering

*Refer to tasks T008‑T015 for detailed implementation.*

## Model Training & Evaluation

*Refer to tasks T016‑T022 for detailed implementation.*

## Statistical Validation & Significance Testing

### Permutation Importance Testing

**FR‑006 Requirement:** A large, fixed number of permutations must be performed for all permutation‑importance tests.

**Implementation change:**
- The previously contemplated *adaptive permutation‑count logic* (which varied the number of permutations based on dataset size) has been **removed**.
- All permutation‑importance evaluations will now use a **fixed count of 1,000 permutations** regardless of the number of samples.
- This fixed count is enforced in `code/models/evaluate.py` via the constant `NUM_PERMUTATIONS = 1000`.
- The change is reflected in the plan and the corresponding code (task T044 ensures a warning is logged only if the dataset is extremely small, but the permutation loop always runs 1,000 iterations).

This approach guarantees statistical robustness and compliance with FR‑006.

### Multiple‑Comparison Correction

*Implemented in tasks T024‑T025.*

### Bootstrap Resampling

*Implemented in task T026.*

### Sensitivity Analysis

*Implemented in task T027.*

## Reporting & Disclaimers

- All generated figures will have the disclaimer “**Associational analysis only; no causal inference**” injected via `utils.plot_utils.inject_disclaimer`.
- The final markdown report (`output/report.md`) will include the same disclaimer through `utils.report_utils.inject_disclaimer`.
- If `data_status.json` indicates a low sample count (`count_warning == true`), a “Data Limitation Warning” section is added automatically.

## Cross‑Cutting Concerns & Infrastructure

- Deterministic logging, random‑seed management, and configuration handling are provided by the `utils` package (tasks T004‑T007).
- Runtime tracking, provenance, and artifact hashing are covered by tasks T022, T060‑T063.

## Change Log

| Date | Task | Description |
|------------|------|-------------|
| 2026‑07‑30 | T048 | Updated `spec.md` to replace “disjoint elemental sets” with “Stratified by Elemental Ratios”. |
| 2026‑07‑30 | T049 | **Removed adaptive permutation‑count logic** from `plan.md`; added explicit statement that **1,000 permutations** will be used for all permutation‑importance tests (FR‑006). |
| 2026‑07‑30 | T050 | Added clarification in `spec.md` Assumptions that the permutation count is fixed at 1,000. |

---

*End of document.*