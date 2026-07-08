# Implementation Plan: Predicting Material Degradation Pathways from Compositional Data

**Branch**: `001-predict-degradation-pathways` | **Date**: 2024-05-21 | **Spec**: `specs/001-predicting-material-degradation-pathways/spec.md`
**Input**: Feature specification from `/specs/001-predicting-material-degradation-pathways/spec.md`

## Summary

This project implements a multi-label classification pipeline to predict material degradation pathways (e.g., pitting, stress corrosion cracking) from elemental composition data. The approach ingests raw corrosion datasets from public Zenodo repositories, filters for metallic alloys, encodes elemental weight percentages into feature vectors, and trains a CPU-tractable Random Forest classifier. The plan explicitly addresses the spec's requirement for an Out-of-Distribution (OOD) test set based on alloy class, a literature-derived Reference Importance Vector for validation, and rigorous statistical checks (permutation tests, threshold sensitivity) to ensure robustness and associational framing.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `pandas`, `scikit-learn`, `shap`, `numpy`, `requests`, `pyyaml`, `tqdm`
**Storage**: Local file system (`data/`, `results/`)
**Testing**: `pytest`
**Target Platform**: GitHub Actions Free Tier (Linux, 2 CPU, 7GB RAM, No GPU)
**Project Type**: Computational Research Pipeline
**Performance Goals**: Full pipeline execution ≤ 6 hours; Memory usage < 6 GB peak.
**Constraints**: No GPU/CUDA; No deep learning; CPU-only Random Forest; Strict adherence to free-tier resource limits.
**Scale/Scope**: Processing of public corrosion datasets (target: ≥200 valid records, ≥70% retention).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

**Status**: PASS (With explicit mitigation strategies for known gaps)

1. **I. Reproducibility**: Random seeds will be pinned in `code/`. External datasets will be fetched from Zenodo via checksummed links.
2. **II. Verified Accuracy**: All citations in `research.md` and `data-model.md` will be validated against primary sources before review.
3. **III. Data Hygiene**: Raw data will be checksummed. Derivations saved as new files. No PII.
4. **IV. Single Source of Truth**: All figures/stats trace to `data/` and `code/`.
5. **V. Versioning**: Artifacts carry content hashes; state file updated on change.
6. **VI. Corrosion Dataset Integrity**:
 * *Mitigation*: The spec mandates Zenodo data. The plan will attempt to fetch the specific Zenodo DOI cited in the spec (e.g., ``). The 'Verified datasets' block is a secondary check. If the specific DOI is unreachable, the pipeline halts with a clear 'Dataset Unreachable' error. The plan does *not* assume the 'Verified datasets' block is the sole source of truth.
7. **VII. Model Evaluation and Explainability**:
 * OOD split by **alloy class** (not source) implemented as per FR-007 (Task T022).
 * Reference Importance Vector constructed via literature review (as per SC-003) using a rule-based extraction protocol (Task T037).
 * Macro-F1 > 0.6 threshold and SHAP analysis included.
 * Confidence interval widening (20% fallback) implemented as per FR-009. The plan applies a default 20% widening factor to confidence intervals and explicitly annotates the specific factor value as `[deferred]` in the output artifact to indicate it is a placeholder for context-specific refinement (Task T039).

## Project Structure

### Documentation (this feature)

```text
specs/001-predicting-material-degradation-pathways/
├── plan.md # This file
├── research.md # Phase 0 output
├── data-model.md # Phase 1 output
├── quickstart.md # Phase 1 output
└── contracts/ # Phase 1 output
 ├── dataset.schema.yaml
 └── output.schema.yaml
```

### Source Code (repository root)

```text
projects/PROJ-532-predicting-material-degradation-pathways/
├── code/
│ ├── __init__.py
│ ├── ingestion.py # FR-001, FR-002: Data fetch, filter, impute
│ ├── preprocessing.py # FR-002: Feature encoding, atomic properties, OOD Split
│ ├── training.py # FR-003: RF training, OOD split (FR-007)
│ ├── evaluation.py # FR-004, SC-001: Macro-F1, Permutation test
│ ├── explainability.py # FR-005, SC-003: SHAP, Threshold sweep
│ ├── literature_review.py # SC-003: Build Reference Importance Vector
│ └── utils.py
├── data/
│ ├── raw/ # Downloaded Zenodo files (checksummed)
│ ├── processed/ # Cleaned CSV, feature matrices
│ └── contracts/ # Literature vector, retention audit
├── results/
│ ├── metrics/ # F1 scores, confusion matrices
│ ├── plots/ # SHAP plots, sensitivity curves
│ └── report.md # Final summary
├── tests/
│ ├── unit/
│ ├── integration/
│ └── contract/
└── requirements.txt
```

**Structure Decision**: Single project structure selected. Separation of `code/` (logic), `data/` (artifacts), and `results/` (outputs) ensures reproducibility and clear provenance. The `literature_review.py` script is explicitly added to produce the `literature_vector.json` artifact required by the evaluation phase, resolving the producer-consumer gap.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Literature Review Task | SC-003 requires validation against a vector derived from 5 specific papers. | Using a hardcoded vector would violate "Verified Accuracy" and "Reproducibility" as the vector must be derived from the actual literature. |
| OOD Class-Based Split | FR-007 mandates holding out specific alloy classes (e.g., HEAs) to test generalization. | A random split or source-based split (by Zenodo study) fails to test the model's ability to generalize to *new material classes*, which is the core scientific question. |
| Threshold Sensitivity Sweep | FR-005 requires robustness checks across decision boundaries. | A single threshold (0.5) assumes optimal operating conditions which may not exist; sensitivity analysis is required to prove robustness. |
| Permutation Test Baseline | SC-001 requires statistical distinguishability from random chance. | A simple random baseline (shuffling labels) does not preserve the multi-label correlation structure required for valid significance testing in this domain. |

## Methodology

### Phase 1: Data Ingestion & Preparation

1. **Task T017: Calculate Retention Audit**
 * **Input**: Raw Zenodo dataset.
 * **Action**: Filter for metallic alloys, impute missing values (<5% median, ≥5% exclude).
 * **Output**: `data/processed/cleaned_alloys.csv` and `data/processed/retention_audit.json` (containing **calculated** retention % and valid record count to verify SC-005).
 * **Success Criteria**: ≥70% retention and ≥200 valid records.

2. **Task T022: Class-Based OOD Split**
 * **Input**: `cleaned_alloys.csv`.
 * **Action**: Identify unique `material_class` values. If sufficient diversity exists (≥2 classes), hold out one or more classes (e.g., High-Entropy Alloys) as the OOD test set. If insufficient diversity, fall back to stratified random split and flag in report.
 * **Output**: `data/processed/train_set.parquet`, `data/processed/test_ood_set.parquet`.
 * **Note**: This explicitly implements the **alloy class** holdout required by FR-007, replacing any source-based split logic.

3. **Task T037: Construct Reference Importance Vector**
 * **Input**: 5 review papers (from Assumptions).
 * **Action**: Perform systematic review. Extract qualitative rankings (e.g., "Cr increases resistance" -> +1). Aggregate into a quantitative vector. Ensure independence from training data.
 * **Output**: `data/contracts/literature_vector.json`.
 * **Note**: This task explicitly produces the artifact consumed by T038, resolving the producer-consumer gap.

### Phase 2: Model Training & Evaluation

4. **Task T023: Train Random Forest**
 * **Input**: `train_set.parquet`.
 * **Action**: Train CPU-only Random Forest.
 * **Output**: `results/model_artifact.pkl`.

5. **Task T024: Generate Stratified Random Baseline**
 * **Input**: `test_ood_set.parquet`.
 * **Action**: Shuffle labels *relative to features* while **preserving the marginal distribution and multi-label correlation structure** of each label (to maintain the null baseline integrity as required by SC-001).
 * **Output**: Baseline F1 score.

6. **Task T025: Permutation Test**
 * **Input**: Model predictions, Baseline.
 * **Action**: Run multiple iterations. Calculate p-value.
 * **Output**: `results/metrics/permutation_test.json`.

7. **Task T038: Validate SHAP vs Reference Vector**
 * **Input**: `model_artifact.pkl`, `literature_vector.json` (from T037).
 * **Action**: Calculate SHAP values. Compute Spearman rank correlation.
 * **Output**: `results/metrics/shap_correlation.json`.

8. **Task T039: Apply Limitation Flags and CI Widening**
 * **Input**: Evaluation results.
 * **Action**: If environmental variables missing, **apply a default [deferred] widening factor** to confidence intervals. **Annotate the specific factor value as `[deferred]`** in the output artifact to indicate it is a placeholder for context-specific refinement.
 * **Output**: `results/metrics/final_report.json` (with `[deferred]` annotation).

### Phase 3: Sensitivity & Reporting

9. **Task T040: Threshold Sensitivity Sweep**
 * **Input**: Model predictions.
 * **Action**: Sweep threshold (± {, 0.05, 0.1}).
 * **Output**: `results/plots/sensitivity_curve.png`.

10. **Task T041: Final Report Generation**
 * **Input**: All metrics, plots.
 * **Action**: Compile `results/report.md`.
 * **Output**: Final report.