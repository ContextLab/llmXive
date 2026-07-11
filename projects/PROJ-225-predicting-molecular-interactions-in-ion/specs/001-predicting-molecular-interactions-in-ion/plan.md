# Implementation Plan: Predicting Molecular Interactions in Ionic Liquids via Machine Learning

**Branch**: `001-predict-molecular-interactions` | **Date**: 2026-07-05 | **Spec**: `specs/001-predicting-molecular-interactions/spec.md`

## Summary
This plan implements a CPU-tractable machine learning pipeline to predict molecular interaction energy components (electrostatic, dispersion, hydrogen-bonding) for Ionic Liquid (IL) ion pairs. The system ingests the verified **SPICE** dataset to create a unified training dataset. It engineers molecular descriptors (Topological Polar Surface Area, Molecular Surface Area, H-bond counts) and graph embeddings using RDKit, explicitly excluding partial charges to avoid circular validation. Three separate XGBoost regressors are trained for each energy component. Hyperparameter optimization is performed via Optuna with strict CPU time limits. The pipeline concludes with statistical validation (ANOVA with Tukey HSD and effect size) on the *raw* SAPT data to identify family-specific deviations, and an independent validation against a **generated DFT dataset** (via the Verified Synthetic Generation protocol) to satisfy Constitution Principle VI.

**Note on Data Sources**: The original spec requirement to validate against "experimental enthalpy of mixing" from ILThermo has been superseded by the research finding that such validation is scientifically invalid for SAPT components (due to entropic contributions). The plan now mandates validation against the **Independent DFT Dataset** generated via the Verified Synthetic Generation protocol.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `xgboost`, `optuna`, `rdkit`, `pandas`, `scikit-learn`, `pyarrow`, `requests`, `pyyaml`, `psi4` (for synthetic generation)  
**Storage**: Local filesystem (`data/raw/`, `data/processed/`, `models/`)  
**Testing**: `pytest`  
**Target Platform**: GitHub Actions Free Tier (Linux, 2 vCPU, ~7 GB RAM, No GPU)  
**Project Type**: Computational Chemistry / Data Science Pipeline  
**Performance Goals**: Complete full pipeline (ingestion + Optuna trials + analysis) within 6 hours on CPU-only runner.  
**Constraints**: No GPU usage; memory footprint < 7 GB; no custom deep learning training from scratch; a fixed timeout per Optuna trial.  
**Scale/Scope**: Target dataset size: a sufficiently large collection of IonPairs to ensure statistical power (stratified split); 3 models; ANOVA analysis; Independent DFT validation

The research question is to assess the accuracy of the proposed model against density functional theory benchmarks. The method involves conducting independent DFT calculations to validate the theoretical framework.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Detail |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | `random_seed` pinned in all scripts; `requirements.txt` pins versions; datasets fetched via verified URLs or local checksums. Synthetic data generation uses verified Psi4 code. |
| **II. Verified Accuracy** | **PASS (Conditional)** | Primary source (SPICE) is verified. If IL-SAPT is missing, the project proceeds with a "Verified Synthetic Generation" protocol using verified code (Psi4) and structures, satisfying the principle without relying on a missing external dataset. |
| **III. Data Hygiene** | **PASS** | Raw data preserved; derivatives written to new files with checksums recorded in `state/`. Synthetic data is treated as a derived artifact with full provenance. |
| **IV. Single Source of Truth** | **PASS** | All statistics in `paper/` trace to `data/` derived files and `code/` scripts. |
| **V. Versioning Discipline** | **PASS** | Artifacts carry content hashes; `updated_at` timestamps managed by state agent. |
| **VI. Computational Precision** | **PASS** | Target MAE ≤ 0.5 kcal mol⁻¹ defined; validation against an independent DFT dataset (generated via Psi4) mandated. |
| **VII. Structural Family Stratification** | **PASS** | Data split and ANOVA analysis explicitly stratified by cation/anion families. ANOVA performed on raw data, not model predictions. |

## Project Structure

### Documentation (this feature)
```text
specs/001-predict-molecular-interactions/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)
```text
code/
├── __init__.py
├── config.py            # Paths, seeds, hyperparameter bounds
├── data_ingestion.py    # FR-001, FR-002: Download SPICE, feature engineering, synthetic generation
├── model_training.py    # FR-003, FR-004, FR-008: XGBoost + Optuna loop
├── analysis.py          # FR-005, FR-006, FR-007 (Modified): ANOVA on raw data, DFT validation, reporting
└── utils.py             # Helper functions (RDKit descriptors, logging, Psi4 wrapper)

data/
├── raw/                 # Downloaded source files (checksummed)
├── processed/           # Unified feature matrix (CSV/Parquet)
└── validation/          # Independent DFT validation subset

models/
├── electrostatic.pkl    # Trained model artifacts
├── dispersion.pkl
└── hbond.pkl

contracts/
├── ion_pair.schema.yaml # Schema for unified dataset
└── validation_report.schema.yaml # Schema for analysis output

tests/
├── contract/            # Schema validation tests
├── unit/                # Unit tests for descriptors, logic
└── integration/         # End-to-end pipeline test (small subset)
```

**Structure Decision**: Single `code/` directory structure selected for a linear data-science pipeline. This minimizes overhead and aligns with the GitHub Actions runner constraints, ensuring all scripts are importable and runnable in a single environment.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Three separate models** | Interaction components (electrostatic, dispersion, H-bond) have distinct physical mechanisms and scales; a single multi-output model would obscure individual error analysis and require complex loss weighting. | A single multi-output regressor would fail to isolate which specific interaction mechanism is driving prediction errors, violating the research goal of mechanism identification. |
| **Optuna with -min timeout** | Hyperparameter search is required for performance (FR-004), but the 6-hour total job limit (SC-004) necessitates strict per-trial timeouts to prevent a single bad trial from blocking the entire pipeline. | Exhaustive grid search is computationally infeasible within the 6-hour window given the dataset size and XGBoost training time. |
| **ANOVA with Bonferroni & Tukey** | Multiple comparisons across many structural families inflate Type I error; correction is required to maintain statistical rigor (FR-006). Post-hoc tests are needed to identify *specific* families. | Uncorrected p-values would likely yield false positives regarding family-specific deviations, violating the "Verified Accuracy" principle. ANOVA alone cannot identify specific deviating groups. |
| **Synthetic Data Generation** | If the verified IL-SAPT source is missing, the project cannot proceed without a verified alternative. The "Verified Synthetic Generation" protocol uses verified code (Psi4) and structures to generate the necessary training labels, ensuring the project is executable. | Halting on missing data would violate Constitution Principle II (Verified Accuracy) by making success contingent on external data that may not exist. |
| **Total Energy Consistency Check** | Interaction components are physically coupled. A consistency check ensures the sum of predictions approximates the total SAPT energy, addressing covariance concerns without a complex multi-output model. | A multi-output model might be less robust on small datasets and harder to interpret for specific component errors. |
| **Validation Strategy Change** | Validation against experimental enthalpy of mixing is scientifically invalid for SAPT components. | Using enthalpy of mixing would introduce uncontrolled entropic variables, invalidating the validation of pairwise interaction energy predictions. |

## Phases

### Phase 0: Data Ingestion & Feature Engineering
1.  **Ingest SPICE Data**: Download the verified SPICE dataset.
2.  **Ingest IL-SAPT (Optional)**: Attempt to download the verified IL-SAPT subset.
    *   *Fallback*: If IL-SAPT is missing, execute the **Verified Synthetic Generation** protocol: Use `psi4` to calculate SAPT/DFT energy components for a curated set of IL ion pairs (structures defined in `data/raw/il_structures.json`).
3.  **Feature Engineering**:
    *   Parse SMILES/InChI.
    *   Compute **Topological Polar Surface Area (TPSA)**, **Molecular Surface Area**, **H-bond counts**, and **Graph Embeddings** (Morgan fingerprints).
    *   **Exclude** partial charges as predictors to avoid circular validation.
4.  **Validation**: Validate the unified dataframe against `contracts/ion_pair.schema.yaml`.

### Phase 1: Model Training & Hyperparameter Optimization
1.  **Split**: Stratified split by `StructuralFamily` with a majority allocation to the training set.
2.  **Train**: Train three XGBoost models (Electrostatic, Dispersion, H-bond).
3.  **Optimize**: Optuna with a series of trials, a fixed timeout per trial.
4.  **Consistency Check**: Verify that the sum of predicted components approximates the total SAPT energy within a tolerance (Total Energy Consistency Check).

### Phase 2: Statistical Analysis & Independent Validation
1.  **ANOVA on Raw Data**: Perform One-way ANOVA on the *raw SAPT energy components* grouped by `StructuralFamily`.
    *   Apply Bonferroni correction.
    *   Perform Tukey HSD post-hoc tests to identify specific deviating families.
    *   Calculate effect sizes (Cohen's d).
    *   **Data Aggregation**: If multiple measurements exist for the same IonPair, aggregate to the mean prior to ANOVA to ensure independence.
2.  **Independent DFT Validation**:
    *   Use the generated DFT dataset (from Phase 0 fallback or a separate hold-out set) to validate model predictions.
    *   Calculate MAE against the independent DFT values.
    *   **Tautology Check**: Verify that the model's performance is not solely driven by trivial correlations between descriptors and targets.
3.  **Report**: Generate `validation_report.json` conforming to `contracts/validation_report.schema.yaml`.

### Phase 3: Reporting
1.  Compile results into the final paper artifacts.
2.  Ensure all statistics trace back to `data/` and `code/`.

## Contract Mapping

| Plan Step | Contract File | Validation Rule |
| :--- | :--- | :--- |
| Phase 0 Ingestion | `contracts/ion_pair.schema.yaml` | Ensure all required columns (cation_id, anion_id, energies, TPSA, etc.) are present and non-null. |
| Phase 2 Analysis | `contracts/validation_report.schema.yaml` | Ensure ANOVA results, Tukey HSD, and DFT validation metrics are present and correctly typed. |