# Implementation Plan: Predicting Battery Electrolyte Decomposition Products via DFT and Machine Learning

**Branch**: `001-gene-regulation` | **Date**: 2026-07-10 | **Spec**: `specs/001-gene-regulation/spec.md`
**Input**: Feature specification from `/specs/001-gene-regulation/spec.md`

## Summary

This feature implements a CPU-constrained pipeline to predict battery electrolyte **thermodynamic stability** (decomposition energy) using DFT-derived ground-state descriptors (HOMO, LUMO, bond lengths). The system ingests a **manually curated, literature-sourced dataset** of real electrolyte species (EC, DMC, LiPF6). It calculates synthetic labels ($E_{decomp}$) using the formula $E_{decomp} = E_{products} - E_{reactants} - nF\phi$ and performs rigorous **Leakage Detection** to ensure features are NOT mathematically identical to the target.

**Critical Data Constraint**: The pipeline **MUST** halt immediately if the specific literature-sourced dataset (containing both DFT descriptors and experimental onset potentials for the same molecules) cannot be verified and loaded. **No synthetic data generation is permitted.**

The model is a Random Forest Regressor trained on non-identity features (HOMO, LUMO, bond lengths). Validation is performed against a held-out literature subset to assess **correlation** between thermodynamic predictions and experimental kinetic onsets, explicitly acknowledging the physics gap. **No bias correction is applied.**

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `scikit-learn`, `numpy`, `pyyaml`, `scipy` (CPU-only wheels)  
**Storage**: Local CSV/JSON artifacts in `data/` and `data/derived/`  
**Testing**: `pytest` (unit tests for data ingestion, VIF, partial correlation, and model constraints)  
**Target Platform**: Linux (GitHub Actions free-tier: 2 CPU, 7 GB RAM, no GPU)  
**Project Type**: Computational Science Pipeline / CLI  
**Performance Goals**: Complete training and validation within 6 hours; RAM usage < 7 GB  
**Constraints**: No GPU/CUDA; no deep learning; strict VIF < 10 and Partial Correlation < 0.9 for independent predictors; deterministic synthetic labels; **No Identity Features in Input**.  
**Scale/Scope**: Small-scale feasibility study (~20-50 unique electrolyte molecules from literature).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Strategy |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PENDING** | Random seeds pinned in `code/`; external datasets replaced by a specific, checksummed literature CSV (SHA-256 recorded in `state/`) with a verified DOI. **Status remains PENDING until DOI and checksum are confirmed.** |
| **II. Verified Accuracy** | **PENDING** | All dataset sources are static, cited literature papers (verified DOIs in `research.md`); no synthetic data generation. **Status remains PENDING until specific DOI and content are verified.** |
| **III. Data Hygiene** | **PASS** | Raw data preserved in `data/raw/` (static CSV); derived data in `data/derived/` with checksums; no in-place modification. |
| **IV. Single Source of Truth** | **PASS** | All figures/stats in final report trace to `data/derived/` and `code/`; no hand-typed numbers. |
| **V. Versioning Discipline** | **PASS** | Content hashes tracked in `state/`; artifact changes update timestamps. |
| **VI. Computational Stability** | **PASS** | Pipeline designed for moderate RAM/CPU-only constraints; synthetic labels calculated deterministically via formula $E_{decomp} = E_{products} - E_{reactants} - nF\phi$. |
| **VII. Mechanistic Interpretability** | **PASS** | Random Forest with permutation importance used; validation on literature subset; no black-box claims; explicit rejection of identity features. |

## Project Structure

### Documentation (this feature)

```text
specs/001-gene-regulation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   └── model_output.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── __init__.py
├── config.py            # Paths, seeds, constants
├── data_ingestion.py    # Load static literature CSV, validate schema, check intersection
├── feature_engineering.py # Calculate E_decomp, Drop Identity, VIF, Partial Correlation
├── model_training.py    # RF training (non-identity features only), CV, permutation importance
├── validation.py        # Literature subset validation, sensitivity analysis
└── utils.py             # Logging, checksums

data/
├── raw/                 # Static literature CSV (checksummed, DOI recorded)
├── derived/             # Processed CSVs, model artifacts, validation reports
└── external/            # N/A

tests/
├── contract/            # Schema validation tests
├── integration/         # Pipeline end-to-end tests
└── unit/                # VIF, Partial Correlation, and rejection logic tests
```

**Structure Decision**: Single project structure selected to minimize overhead and ensure tight coupling between data processing and modeling steps, adhering to the "Single Source of Truth" principle.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **None** | The plan adheres strictly to the spec and constitution. | N/A |

## Phased Implementation Plan

### Phase 0: Data Curation & Contract Validation
**Goal**: Ingest real data and validate schema.
1.  **0.1 Verified Source Identification**: Identify specific peer-reviewed papers (with DOIs) containing DFT descriptors (HOMO, LUMO, bond lengths, total energies) AND experimental onset potentials for EC, DMC, or LiPF6. **HALT** if no such verified source exists.
2.  **0.2 Literature Curation**: Manually extract data from the verified source(s) for ~20-50 molecules. Save as `data/raw/literature_subset.csv`. Record the DOI in `state/`.
3.  **0.3 Contract Validation Execution**: Run `code/data_ingestion.py` to load the CSV and validate against `contracts/dataset.schema.yaml`. **HALT** if validation fails. This step explicitly executes the contract validator as a distinct gate.
4.  **0.4 Checksum**: Calculate SHA-256 of `literature_subset.csv` and record in `state/`.

### Phase 1: Feature Engineering & Leakage Detection
**Goal**: Calculate targets and remove identity features.
1.  **1.1 Target Calculation**: Calculate `decomp_energy` for each `Molecule` instance (as defined in `data-model.md`) using $E_{decomp} = E_{products} - E_{reactants} - nF\phi$.
2.  **1.2 Identity Feature Exclusion**: **Explicitly drop** `reactant_energy` and `product_energy` from the feature matrix *before* any model training or leakage check. These fields are used *only* for target calculation.
3.  **1.3 Collinearity Check**: Calculate VIF on the remaining features. Flag features with VIF ≥ 10.
4.  **1.4 Leakage Detection (FR-010)**: Calculate **Partial Correlation** between each remaining feature and `decomp_energy`, controlling for other features.
    -   **Rejection Rule**: If Partial Correlation > 0.9, **REJECT** the feature.
    -   **Action**: Remove rejected features from the feature set.
5.  **1.5 Residual Correlation Check**: Calculate partial correlation of the *remaining* feature set against `decomp_energy`.
    -   **HALT Rule**: If the remaining set still shows Partial Correlation > 0.9, **HALT** with "Residual Identity Detected" error.
6.  **1.6 Final Feature Set**: Output `data/derived/features_cleaned.csv` containing only non-identity features (e.g., HOMO, LUMO, bond lengths).

### Phase 2: Model Training
**Goal**: Train Random Forest on valid features.
1.  **2.1 Training**: Train Random Forest Regressor on `features_cleaned.csv` using 5-fold CV stratified by potential level.
2.  **2.2 Constraints Check**: Ensure RAM < 7 GB, no GPU usage, runtime < 6h.
3.  **2.3 Importance Extraction**: Calculate permutation importance.

### Phase 3: Theoretical Limit Check & Sensitivity Analysis
**Goal**: Validate against literature subset and assess threshold robustness.
1.  **3.1 Data Intersection Check**: Verify that the molecules in the training set have corresponding experimental onset potentials in the curated dataset. **HALT** if the intersection is empty (Validation Impossible).
2.  **3.2 Proxy Validation**: Compare model predictions for the held-out literature subset against experimental onset potentials.
    -   **Metric**: Calculate R² (correlation) and report the "Physics Gap" (thermodynamic vs. kinetic).
    -   **Bias Correction**: **None**. Report raw correlation.
3.  **3.3 Sensitivity Analysis (SC-003)**: Sweep stability threshold (e.g., -0.05, 0.0, +0.05 eV).
    -   **Metric**: Calculate False Positive/Negative rates relative to the *theoretical* stability boundary (E_decomp < 0).
    -   **Output**: Sensitivity report (`data/derived/sensitivity_analysis.csv`).
4.  **3.4 Associational Framing**: Ensure all reports state findings are "associational" and not causal.

## Requirements Traceability

| Requirement | Phase/Step | Implementation Detail |
| :--- | :--- | :--- |
| **FR-001** | Phase 0.2 | Ingest DFT data from literature (real data, not synthetic). |
| **FR-002** | Phase 1.1 | Calculate `decomp_energy` using the formula. |
| **FR-003** | Phase 2.1 | Train Random Forest (CPU-only, Scikit-learn). |
| **FR-004** | Phase 2.1 | 5-fold CV stratified by potential. |
| **FR-005** | Phase 2.3 | Permutation importance extraction. |
| **FR-006** | Phase 3.2 | Validation against literature subset (proxy correlation). |
| **FR-007** | Phase 3.3 | Sensitivity analysis on thresholds. |
| **FR-008** | Phase 3.4 | Explicit associational framing in reports. |
| **FR-009** | N/A | **Not Implemented** (Bias correction removed due to physics gap). |
| **FR-010** | Phase 1.4 | Partial correlation analysis; reject features > 0.9. |
| **FR-011** | Phase 3.2 | Explicit statement of "Thermodynamic Stability" vs "Kinetic Onset". |
| **SC-001** | Phase 3.2 | R² score calculated as correlation metric. |
| **SC-002** | Phase 2.3 | Feature importance shift analysis. |
| **SC-003** | Phase 3.3 | False-positive/negative rates at swept thresholds. |
| **SC-004** | Phase 2.2 | Resource constraints checked. |
| **SC-005** | Phase 1.3 | VIF < 10 check. |

## Risk Assessment

1.  **Data Scarcity**: The literature subset may be too small (< 20 molecules) or lack experimental onset data for the same molecules.
    -   *Mitigation*: If data is insufficient, the study concludes with a "Data Scarcity" finding rather than a failed model.
2.  **Feature Rejection**: Partial correlation may reject all features, or residual correlation may remain high.
    -   *Mitigation*: The plan explicitly handles this by halting with a "No viable features" or "Residual Identity" report, which is a valid scientific result.
3.  **Physics Gap**: The correlation between thermodynamic and kinetic stability may be weak.
    -   *Mitigation*: The plan explicitly reports this as a limitation and does not attempt to "fix" it with invalid bias correction.
4.  **Validation Impossible**: If the intersection of training molecules and experimental data is empty.
    -   *Mitigation*: Phase 3.1 halts the pipeline with a "Validation Impossible" report, satisfying the requirement to not fake validation.