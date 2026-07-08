# Implementation Plan: Predicting Molecular Properties from Open Babel Fingerprints with Random Forests

**Branch**: `001-predicting-molecular-properties` | **Date**: 2026-07-08 | **Spec**: `specs/001-predicting-molecular-properties/spec.md`

## Summary

This feature implements a comparative analysis to quantify the error in standard additive fragment models (Crippen's method) for predicting logP, solubility, and boiling point, and to map the specific molecular contexts (substructure interactions) where non-linear Random Forest models outperform these baselines. The approach utilizes Open Babel fingerprints (ECFP4, MACCS, FP2) on a diverse dataset of ≥5,000 molecules, adhering strictly to CPU-only execution constraints (≤6h runtime, ≤7GB RAM) and reproducible data hygiene standards. The study is explicitly framed as quantifying "model capacity gaps" (statistical corrections) rather than discovering independent physical mechanisms, acknowledging the circularity of using the same data for training and explanation.

## Technical Context

**Language/Version**: Python 3.10+  
**Primary Dependencies**: `rdkit`, `scikit-learn`, `shap`, `pandas`, `numpy`, `datasets` (HuggingFace), `requests`  
**Storage**: Local filesystem (`data/raw`, `data/processed`, `data/derived`); CSV/Parquet formats  
**Testing**: `pytest` (contract tests for schema validation, unit tests for data preprocessing)  
**Target Platform**: GitHub Actions Free Runner (Linux, 2 CPU, 7GB RAM, No GPU)  
**Project Type**: Computational Chemistry / Data Science Pipeline  
**Performance Goals**: Complete full pipeline (download → baseline → RF training → SHAP analysis) within 6 hours; Memory usage < 6GB peak.  
**Constraints**: No GPU acceleration; no deep learning; dataset sampling required if >5,000 molecules; strict deterministic seeds.  
**Scale/Scope**: [deferred] molecules; target properties; fingerprint types.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Implementation Detail |
| :--- | :--- | :--- |
| **I. Reproducibility** | **Compliant** | All random seeds pinned in `code/`. External datasets fetched via verified HuggingFace URLs only. `requirements.txt` pins versions. |
| **II. Verified Accuracy** | **Compliant** | Citations in `research.md` restricted to the `# Verified datasets` block. No invented URLs. |
| **III. Data Hygiene** | **Compliant** | Raw data preserved; checksums recorded in state file. Derivations written to new files. PII scan passed (chemical data). |
| **IV. Single Source of Truth** | **Compliant** | All figures/stats in `paper/` will trace to `data/` rows and `code/` blocks. No hand-typed numbers. |
| **V. Versioning Discipline** | **Compliant** | Artifacts carry content hashes. The `state.yaml` file is updated with the `updated_at` timestamp upon any artifact change, as required by the constitution. |
| **VI. Non-Additivity Interaction Mapping** | **Compliant** | Plan explicitly includes Phase 1 (Baseline) and Phase 2 (RF) comparison, with Phase 3 dedicated to SHAP interaction mapping to isolate "interaction zones" (framed as statistical corrections). |
| **VII. Computational Efficiency and Determinism** | **Compliant** | Plan mandates dataset sampling (≤5k), `max_depth` limits, and priority-based fingerprint generation (ECFP4 > MACCS > FP2) to ensure ≤6h runtime. |

## Project Structure

### Documentation (this feature)

```text
specs/001-predicting-molecular-properties/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (Design Artifacts)
│   ├── molecule.schema.yaml
│   ├── prediction.schema.yaml
│   └── interaction_context.schema.yaml
└── tasks.md             # Phase 2 output (NOT created by /speckit-plan)
```

**Schema Timing Note**: The `contracts/` directory contains **design artifacts** (schemas) defined in Phase 1 to establish the data contract. The actual **data instances** (e.g., `InteractionContext` rows) are generated in Phase 2/3 (Analysis). The schema exists before the data it describes, which is a standard design pattern, not a sequencing conflict. The `InteractionContext` schema defines the *structure* of the output (e.g., bit pairs, interaction strength), while the *values* are derived from the analysis pipeline.

### Source Code (repository root)

```text
projects/PROJ-324-predicting-molecular-properties-from-ope/
├── code/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── data/
│   │   ├── download.py          # Fetches from verified HF URLs
│   │   ├── preprocess.py        # Filters, cleans, computes Crippen
│   │   └── fingerprints.py      # Generates MACCS, ECFP4, FP2 (using rdkit.Chem)
│   ├── models/
│   │   ├── baseline.py          # Crippen implementation
│   │   └── random_forest.py     # RF training & CV
│   ├── analysis/
│   │   ├── stats.py             # Wilcoxon test, MAE calc, permutation test
│   │   └── explainability.py    # SHAP values & mapping
│   └── main.py                  # Pipeline orchestration
├── data/
│   ├── raw/                     # Downloaded datasets (checksummed)
│   ├── processed/               # Cleaned CSVs, fingerprints
│   └── derived/                 # Predictions, SHAP outputs
└── tests/
    ├── unit/
    ├── integration/
    └── contract/                # Schema validation tests
```

**Structure Decision**: Single-project structure selected. The workflow is a linear pipeline (Download → Process → Model → Analyze) rather than a service or multi-component app. This minimizes overhead and fits the 6-hour CI constraint.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **SHAP Interaction Values** | Required by FR-006/US-3 to map specific bit-pair interactions, not just feature importance. | Standard feature importance (Gini) only ranks single bits; it cannot capture the *interaction* (non-linearity) required to identify "interaction zones" where additivity fails. |
| **Priority-Based Fingerprint Strategy** | Required by FR-009 to handle runtime constraints. | Generating all three fingerprints for all molecules simultaneously risks exceeding 6h runtime on the 2-core runner. The priority strategy ensures core results (ECFP4) are delivered even if time runs out. |
| **Dataset Sampling (≤5k)** | Required by FR-001/Assumptions to fit 7GB RAM. | Processing full PubChem/ChEMBL subsets (millions of rows) is computationally infeasible on the free-tier runner; sampling preserves diversity (Tanimoto < 0.7) while ensuring feasibility. |
| **Nested Cross-Validation** | Required to address methodological concerns about paired error comparison. | A simple Wilcoxon test on a single split introduces confounding variance. Nested CV ensures the baseline and RF are evaluated on the exact same test folds. |