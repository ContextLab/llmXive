# Implementation Plan: Predicting the Stability of Perovskite Structures Using Machine Learning

**Branch**: `001-gene-regulation` | **Date**: 2026-06-25 | **Spec**: `specs/001-gene-regulation/spec.md`
**Input**: Feature specification from `specs/001-gene-regulation/spec.md`

## Summary

This project implements a machine learning pipeline to predict the thermodynamic stability (decomposition energy) of ABX₃ perovskite structures. The approach involves ingesting data from the Materials Project and OQMD, calculating physical descriptors (Goldschmidt tolerance factor, octahedral factor, ionic radius mismatch, electronegativity differences), training a RandomForestRegressor with nested cross-validation (outer /20 split, inner -fold CV), and performing virtual screening on a combinatorial library of hypothetical compositions. The pipeline is strictly constrained to CPU-only execution on GitHub Actions free-tier runners.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pymatgen` (for structure analysis and descriptor calculation), `scikit-learn` (for modeling), `pandas`, `numpy`, `requests` (for API ingestion), `pyyaml`.  
**Storage**: Local CSV/Parquet files for intermediate data; `.pkl` for model artifacts.  
**Testing**: `pytest` with contract tests against YAML schemas.  
**Target Platform**: Linux (GitHub Actions runner).  
**Project Type**: Data science pipeline / CLI.  
**Performance Goals**: Complete full pipeline (ingestion, training, screening) in ≤ 6 hours; memory usage ≤ 7 GB.  
**Constraints**: No GPU/CUDA; no external API keys that expire during CI; strict adherence to `pymatgen` definitions for descriptors.  
**Scale/Scope**: Up to 10,000 training entries; combinatorial library size determined by element sets {K,Rb,Cs,Ba,Sr} × {Ti,Zr,Hf,Sn,Ge} × {F,Cl,Br,I}.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

1.  **Reproducibility**: The plan mandates pinned random seeds, explicit `requirements.txt` versioning, and deterministic data ingestion from canonical sources (Materials Project/OQMD verified URLs).
2.  **Verified Accuracy**: All dataset references in `research.md` are restricted to the verified URLs provided in the input block. No invented URLs.
3.  **Data Hygiene**: The plan includes checksumming steps for downloaded data and treats raw data as immutable, writing derivatives to new files.
4.  **Single Source of Truth**: All figures and metrics are generated programmatically from the `data/` artifacts; no hand-typed numbers in the plan or future reports.
5.  **Versioning Discipline**: Artifacts (data, models, plots) will carry content hashes recorded in the project state.
6.  **Numerical Stability**: The plan explicitly requires `pymatgen` for all descriptor calculations (t, μ, etc.) and defines the regression target as decomposition energy (eV/atom), ensuring consistency with the spec.
7.  **Combinatorial Screening Validity**: The screening phase strictly adheres to the defined element sets (A={K,Rb,Cs,Ba,Sr}, B={Ti,Zr,Hf,Sn,Ge}, X={F,Cl,Br,I}) and the negative energy threshold per atom.

## Project Structure

### Documentation (this feature)

```text
specs/001-gene-regulation/
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
├── data/
│   ├── download.py          # API ingestion (FR-001)
│   ├── descriptors.py       # Feature calculation (FR-002)
│   └── preprocess.py        # Cleaning and splitting
├── models/
│   ├── train.py             # Model training and CV (FR-003)
│   └── predict.py           # Screening logic (FR-004)
├── viz/
│   └── plot.py              # Visualization generation (FR-005)
├── utils/
│   ├── api_client.py        # Rate limiting and retry logic
│   └── config.py            # Hyperparameters and constants
└── main.py                  # Orchestration script
tests/
├── unit/
│   ├── test_descriptors.py
│   └── test_api_client.py
├── contract/
│   └── test_schemas.py      # Validates against contracts/*.schema.yaml
└── integration/
    └── test_pipeline.py     # End-to-end run with sample data
```

**Structure Decision**: A modular Python package structure (`code/`) is selected to separate data ingestion, modeling, and visualization concerns. This supports the independent testing requirements (US-1, US-2, US-3) and ensures the pipeline can be executed step-by-step or end-to-end. The `contracts/` directory in `specs/` will hold the YAML schemas for data validation.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | The scope is well-bounded by the spec and compute constraints. | N/A |

## Detailed Implementation Phases

### Phase 0: Data Strategy & Feasibility (Research)
- **FR-001**: Verify access to verified OQMD dataset URLs. Implement a fallback strategy if Materials Project API fails (retry logic).
- **Dataset Fit Check**: Confirm that the verified OQMD dataset contains `decomposition_energy` and structural data (Space Group, Lattice Parameters) required to filter for Cubic/Rhombohedral phases.
- **Schema Validation**: If using Parquet source, validate that columns `space_group`, `lattice_parameters`, and `decomposition_energy` exist. If missing, switch to CSV source.
- **Constraint Validation**: Ensure the `pymatgen` library can handle the specific elements in the hypothetical library (K, Rb, Cs, Ba, Sr, Ti, Zr, Hf, Sn, Ge, F, Cl, Br, I) without missing ionic radii.

### Phase 1: Data Ingestion & Descriptor Generation
- **FR-001**: Implement `download.py` to fetch up to 10,000 entries.
  - **Min-Count Enforcement**: If Materials Project yields < 5,000 valid entries, automatically trigger OQMD ingestion until total count >= 5,000.
  - Filter strictly for Space Groups in the Cubic or Rhombohedral systems..
- **FR-002**: Implement `descriptors.py` using `pymatgen` to calculate:
  - Goldschmidt tolerance factor ($t$)
  - Octahedral factor ($\mu$)
  - **Ionic radius mismatch** (explicitly implemented)
  - **Electronegativity difference** (explicitly implemented)
- **FR-001/US-1**: Handle missing values (flag/exclude) and log exclusion reasons.
- **FR-001**: Implement retry mechanism with exponential backoff for API rate limits.
- **Output**: `data/processed/features.csv` with zero nulls in the target column.

### Phase 2: Model Training & Validation
- **Data Split**: Perform an **/20 stratified split** of the dataset into `train_set` and `test_set` (held out).
- **FR-003**: Implement `train.py` using `scikit-learn`'s `RandomForestRegressor`.
- **Nested CV**:
  - **Inner Loop**: Perform k-fold cross-validation grid search over `max_depth` {10, 15, 20} and `min_samples_leaf` {1, 2, 4} **ONLY on the `train_set`**.
  - **Selection**: Select best hyperparameters based on lowest inner CV error.
  - **Outer Loop**: Retrain the model with best parameters on the full `train_set`.
- **Evaluation**: Evaluate the final model on the **held-out `test_set`**.
  - **SC-001**: Log test-set RMSE. If > 0.15 eV/atom, flag as "low confidence" (previously a small effect size).
- **SC-002**: Implement **permutation-based sensitivity analysis** (`sklearn.inspection.permutation_importance`) on the test set to validate feature importance hypotheses.
- **FR-005**: Generate `predicted-vs-true.png` (test set) and `feature-importance.png` (permutation importance).
- **Output**: `results/model.pkl`, `results/metrics.json` (including test RMSE and permutation scores).

### Phase 3: Virtual Screening
- **FR-004**: Generate combinatorial library of hypothetical ABX₃:
  - **A-site**: {K, Rb, Cs, Ba, Sr} (Alkali + Alkaline-Earth)
  - **B-site**: {Ti, Zr, Hf, Sn, Ge} (Transition + Sn/Ge)
  - **X-site**: {F, Cl, Br, I}
- **FR-004**: Filter for geometric feasibility (0.8 ≤ t ≤ 1.1).
- **OOD Check**: Verify that the hypothetical library contains compositions with descriptor values outside the training distribution range (to ensure extrapolation testing).
- **FR-004**: Predict decomposition energy using the trained model.
- **FR-004**: Rank candidates and flag those with predicted energy below a defined stability threshold.
- **Output**:
  - `results/screening_full.csv`: The **full** ranked list of >= 200 feasible candidates.
  - `results/screening_candidates.md`: Top candidates extracted from the full list.

### Phase 4: Integration & Verification
- **SC-004**: Measure total runtime; ensure ≤ 6 hours.
- **SC-005**: Monitor memory usage; ensure ≤ 7 GB.
- **Constitution Check**: Verify all artifacts are checksummed and reproducible.
- **Functional Consistency**: Verify that all training data and model metadata explicitly state the DFT functional used (PBE).
