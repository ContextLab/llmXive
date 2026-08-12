# Implementation Plan: Evaluating the Correlation Between Compositional Features and Predicted Formation Energy in Inorganic Materials

**Branch**: `001-evaluating-compositional-correlation` | **Date**: 2026-06-24 | **Spec**: [link]
**Input**: Feature specification from `/specs/001-evaluating-the-correlation-between-compo/spec.md`

## Summary

This plan implements a CPU-first computational pipeline to evaluate the correlation between compositional descriptors (mean/variance of electronegativity, atomic radius, valence electrons, melting point, ionization energy) and predicted formation energy in inorganic materials. The approach involves downloading a verified subset of the Materials Project MP-2020 dataset via the MPDS API (with fallback to a checksummed local cache), computing descriptors using `pymatgen`/`matminer`, training Random Forest and Gradient Boosting regressors via `scikit-learn` on an 80/20 stratified split (by Chemical Family), and performing feature importance analysis including Conditional Permutation Importance, SHAP interactions, and Accumulated Local Effects (ALE) plots. The pipeline is designed to run within the GitHub Actions free-tier constraints (2 CPU, ~7 GB RAM, ≤6h) and strictly adheres to the project constitution regarding reproducibility and data hygiene.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pymatgen`, `matminer`, `scikit-learn`, `pandas`, `numpy`, `eli5`, `shap`, `pytest`  
**Storage**: Local file system (`data/`), JSON/YAML artifacts  
**Testing**: `pytest` with contract validation  
**Target Platform**: Linux (GitHub Actions Runner)  
**Project Type**: Computational Research Pipeline  
**Performance Goals**: Complete pipeline ≤ 6 hours; Memory usage < 6 GB; R² > 0.0 (baseline)  
**Constraints**: CPU-only (no GPU); No external API calls during runtime (except dataset download); Strict reproducibility (fixed seeds); No synthetic data substitution.  
**Scale/Scope**: ~12,500 inorganic compounds (verified subset); 10 descriptors per compound.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Strategy | Status |
|-----------|---------------------|--------|
| **I. Reproducibility** | All random seeds pinned in `code/`. Dataset fetched from canonical source (MP-2020 via MPDS API) every run. `requirements.txt` pins versions. Fallback to checksummed local cache if API fails. | ✅ Pass |
| **II. Verified Accuracy** | Citations in `research.md` and `data-model.md` restricted to verified sources (MP-2020). No fabricated URLs. | ✅ Pass |
| **III. Data Hygiene** | Raw data checksummed on download. Derived descriptors written to new files with versioned names. No in-place modification. | ✅ Pass |
| **IV. Single Source of Truth** | All statistics in `data/evaluation/*.json` trace to specific code blocks. No hand-typed numbers in plan. | ✅ Pass |
| **V. Versioning Discipline** | Content hashes tracked in `state/`. Artifacts updated only via pipeline execution. | ✅ Pass |
| **VI. Deterministic Feature Engineering** | Descriptors computed via pure functions in `code/utils/descriptors.py` using a version-controlled elemental property table in `data/elemental_properties/`. Pipeline fails if table version/hash does not match expected value. | ✅ Pass |
| **VII. Statistical Evaluation Rigor** | 80/20 stratified split, Conditional Permutation Importance, SHAP interactions, VIF logging (with warning, not removal), ALE plots, and permutation-based significance tests implemented as specified. Paired t-tests for model comparison (RF vs GB) with BH correction. | ✅ Pass |

## Project Structure

### Documentation (this feature)

```text
specs/001-evaluating-the-correlation-between-compo/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
code/
├── __init__.py
├── ingest.py            # Data download, filtering, checksumming (FR-001)
├── features.py          # Descriptor computation (FR-002, VI)
├── train.py             # Model training, splitting, saving (FR-003, FR-003a)
├── evaluate.py          # Metrics calculation, overfitting check (FR-004, T025)
├── importance.py        # Feature ranking, permutation, ALE, VIF (FR-005, FR-006, T038-T047)
├── utils/
│   ├── __init__.py
│   ├── descriptors.py   # Pure functions for mean/variance (VI)
│   ├── chemical_families.py # Logic for deriving Chemical Family
│   └── io.py            # JSON/CSV loading and saving
└── main.py              # Pipeline orchestrator (FR-007, FR-009)

data/
├── raw/                 # Downloaded raw MP-2020 subset
├── processed/           # Cleaned CSVs with descriptors
├── elemental_properties/ # Versioned elemental tables
└── evaluation/          # Models, metrics, plots, rankings

tests/
├── contract/            # Schema validation tests
├── integration/         # Pipeline end-to-end tests
└── unit/                # Descriptor logic tests
```

**Structure Decision**: Single project structure selected for simplicity and tight coupling of data processing and modeling. `code/utils/` created to satisfy T049 (cleanup) and ensure deterministic feature engineering (Principle VI).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | No violations detected. | N/A |

## Implementation Phases

### Phase 0: Data Ingestion & Verification (FR-001, SC-006)
1.  **Download**: Fetch MP-2020 dataset via `matminer` MPDS loader (requires `MPDS_API_KEY` in CI).
2.  **Fallback**: If API fails, load from `data/raw/mp-2020.csv` (checksummed, versioned).
3.  **Verify**: Check file size (expected to contain a substantial number of rows) and SHA-256 checksum. Log result to `data/evaluation/dataset_verification.json`. Fail if mismatch.
4.  **Filter**: Select inorganic compounds, exclude missing formation energy or composition.
5.  **Version Pin**: Verify `data/elemental_properties/` matches expected version hash. Fail if mismatch.

### Phase 1: Feature Engineering (FR-002, VI)
1.  **Chemical Family Derivation**: Use `code/utils/chemical_families.py` to assign a `chemical_family` to each compound.
    *   *Algorithm*: Identify the dominant element (highest stoichiometric coefficient). Map its group/block (e.g., Group 1 -> Alkali, d-block -> Transition, O-containing -> Oxide) to a fixed set of families.
2.  **Descriptor Computation**: Compute mean/variance for 5 elemental properties using `code/utils/descriptors.py`.
3.  **Output**: Write `data/processed/with_descriptors.csv`.

### Phase 2: Model Training & Evaluation (FR-003, FR-004, FR-004a, FR-004b)
1.  **Split**: 80/20 stratified split by `chemical_family`.
2.  **Train**: Random Forest (max_depth=20, 200 trees), Gradient Boosting (a set of estimators).
3.  **Evaluate**: Calculate R², MAE, RMSE. Allow negative R².
4.  **Overfitting Check**: Compute `overfitting_ratio = train_r2 - val_r2`. Log to `data/evaluation/model_metrics.json`. Flag if > 0.1.
5.  **Statistical Test**: Perform paired t-test comparing RF vs. GB validation scores. Apply Benjamini-Hochberg correction if multiple metrics tested. Save p-values/CIs to `data/evaluation/statistical_tests.json`.

### Phase 3: Feature Importance & Sensitivity (FR-005, FR-006, SC-002, SC-003)
1.  **Importance**: Extract tree-based importance.
2.  **Validation**: Compute Conditional Permutation Importance (using `eli5` or custom) to handle collinearity.
3.  **Ranking**: Rank top features. Validate stability (correlation r ≥ 0.8).
4.  **SHAP**: Compute SHAP interaction values to assess joint effects of correlated descriptors.
5.  **ALE Plots**: Generate ALE plots for top features.
6.  **Write ALE**: Write PNG images to `data/evaluation/ale_*.png`. Verify file existence and non-zero size (FR-008).
7.  **Non-linearity Score**: Calculate `|R²_quad - R²_lin|` for the ALE curve of each top feature. Log to `data/evaluation/ale_metrics.json`. Require > 0.5 for SC-003.
8.  **VIF**: Calculate VIF scores. Log warning if > 10, but do not remove features.
