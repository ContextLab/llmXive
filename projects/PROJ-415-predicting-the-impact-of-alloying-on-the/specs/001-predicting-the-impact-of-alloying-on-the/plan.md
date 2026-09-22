# Implementation Plan: Predicting the Impact of Alloying on the Diffusion Activation Energy in FCC Metals

**Branch**: `001-predict-alloy-diffusion` | **Date**: 2026-06-26 | **Spec**: `specs/001-predicting-the-impact-of-alloying-on-the/spec.md`
**Input**: Feature specification from `/specs/001-predicting-the-impact-of-alloying-on-the/spec.md`

## Summary

This project implements a predictive pipeline to quantify how alloying elements affect the diffusion activation energy in Face-Centered Cubic (FCC) metals. **Critical Scope Adjustment**: The original spec requested data from Materials Project/NIST, but no verified open URL for a complete FCC self-diffusion dataset exists in the input context. Therefore, this plan adopts a **"Real Data Hunt"** strategy:
1.  Attempt to download a real, open-access FCC diffusion dataset from verified sources (e.g., Zenodo, OpenKIM open subset, UCI).
2.  **If a real dataset is found**: Proceed with analysis, framing results as "Exploratory" if N < 50.
3.  **If NO real dataset is found**: The project halts at Phase 0 with a "Data Unavailable" report. **No synthetic data will be generated** to simulate results, as this would invalidate the scientific hypothesis.

The approach ingests raw diffusion data, filters for FCC self-diffusion, engineers atomic descriptors (specifically size mismatch), and trains Random Forest, Gradient Boosting, and Linear Regression models. The plan prioritizes statistical validity (p-values, bootstrap CIs) and robustness (threshold sensitivity) while strictly adhering to GitHub Actions CPU constraints and reproducibility principles.

**Traceability**:
- **US-1 (Data Ingestion)**: Addressed by Phase 0 (Data Acquisition & Curation), specifically Tasks T001, T001b, T051.
- **US-2 (Feature Engineering & Training)**: Addressed by Phase 1 (Feature Engineering & Model Training), specifically Tasks T002, T003, T004, T060.
- **US-3 (Statistical Validation)**: Addressed by Phase 2 (Validation & Sensitivity), specifically Tasks T005, T006, T007.
- **FR-001**: Addressed by T001 (Filtering logic).
- **FR-002**: Addressed by T002 (Feature calculation).
- **FR-003**: Addressed by T003 (RF/GB training).
- **FR-004**: Addressed by T003, T005 (CV and metrics).
- **FR-005**: Addressed by T004, T006 (Linear model and sensitivity).
- **FR-006**: Addressed by T030, T031 (Baseline retrieval).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `scikit-learn`, `numpy`, `periodictable`, `pytest`, `pyyaml`, `requests`  
**Storage**: Local CSV/JSON artifacts (`data/curated/`, `models/`, `results/`)  
**Testing**: `pytest` (unit tests for feature engineering, integration tests for pipeline)  
**Target Platform**: Linux (GitHub Actions free-tier runner)  
**Project Type**: Data Science / Computational Materials Science  
**Performance Goals**: Complete full pipeline (ingestion → validation) within 6 hours; model training < 2 CPU-hours.  
**Constraints**: Memory < 7 GB; No GPU required (CPU-tractable methods selected); No external API calls during runtime (data downloaded once).  
**Scale/Scope**: Dataset < 10 MB (curated open subsets); < 500 data points (typical for FCC self-diffusion open subsets).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Verification Method |
| :--- | :--- | :--- |
| **I. Reproducibility** | **CONDITIONAL PASS** | All random seeds pinned in `code/`. External data sources fixed to the **verified open subset found during the Data Hunt** (or project paused). `requirements.txt` pins versions. |
| **II. Verified Accuracy** | **CONDITIONAL PASS** | Citations in `research.md` reference the **actual verified URL found** (e.g., Zenodo ID). If no URL exists, the project is paused. No fabricated metrics. |
| **III. Data Hygiene** | **PASS** | Plan includes `data_provenance.json` generation (T051 fix). Raw data preserved; derivatives written to new files with checksums. |
| **IV. Single Source of Truth** | **PASS** | All figures/stats in `paper/` will be generated directly from `data/curated/` and `models/` artifacts. |
| **V. Versioning Discipline** | **PASS** | Artifacts will include content hashes in `state/` updates. |
| **VI. Computational Resource Compliance** | **PASS** | Methods (RF, GB, Linear) are CPU-tractable. Dataset size kept < 10 MB. Training time estimated < 2 CPU-hours. |
| **VII. Descriptor Consistency** | **PASS** | `periodictable` library (version pinned) used for atomic radii/electronegativity. Pauling scale enforced. |

## Phased Execution Plan

### Phase 0: Data Acquisition & Curation (US-1, FR-001)
- **T001**: **Data Hunt**: Attempt to download real FCC self-diffusion data from verified open sources (Zenodo, OpenKIM open subset, UCI).
- **T001b**: **Re-specify Source**: If the original NIST/Materials Project URLs are inaccessible, document the new source (e.g., Zenodo ID) in `data_provenance.json` and update traceability.
- **T030**: Calculate `baseline_shift` ($\Delta Q$) by retrieving $Q_{host}$ (pure metal) from the dataset or a standard reference file (`pure_metals_q.csv`).
- **T031**: **Baseline Retrieval**: If the dataset lacks 0 at.% rows, implement interpolation or lookup from `pure_metals_q.csv` to ensure FR-006 compliance.
- **T051**: Generate `data/curated/data_provenance.json` with checksums, source URLs, and row counts. Log excluded rows (e.g., missing concentration) with reason codes.
- **T052**: **Pause Check**: If no real data is found, generate a "Data Unavailable" report and halt.

### Phase 1: Feature Engineering & Model Training (US-2, FR-002, FR-003, FR-004)
- **T002**: Compute atomic descriptors (`size_mismatch`, `electronegativity_diff`) using `periodictable`.
- **T003**: Train Random Forest and Gradient Boosting models with Grid Search (5-fold CV) on CPU.
- **T004**: Train Linear Regression model for statistical inference (coefficients, p-values).
- **T060**: Implement and evaluate a **Mean Predictor** baseline model (mean of `delta_q_eV` in **training set**) for SC-001 comparison.

### Phase 2: Validation & Sensitivity (US-3, FR-005, FR-006, SC-002, SC-003)
- **T005**: Compute R², RMSE, MAE on held-out test set. Compare against Mean Predictor baseline.
- **T006**: Perform threshold sensitivity analysis (0.45–0.55 eV). **Logic**: Use real experimental error bars if available; otherwise, use model RMSE as a conservative estimate, explicitly labeled as such.
- **T007**: Generate final reports and plots. Include explicit "Exploratory" flag if N < 50.

## Project Structure

### Documentation (this feature)

```text
specs/001-predict-alloy-diffusion/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-415-predicting-the-impact-of-alloying-on-the/
├── code/
│   ├── __init__.py
│   ├── data/
│   │   ├── ingestion.py       # Loads real data from verified source, filters FCC/Self
│   │   ├── curation.py        # Handles missing values, writes provenance (T051), calculates baseline (T030)
│   │   └── baseline.py        # Implements Mean Predictor baseline (T060)
│   ├── features/
│   │   └── descriptors.py     # Computes size_mismatch, electronegativity
│   ├── models/
│   │   ├── train.py           # RF, GB, Linear training + GridSearch
│   │   └── evaluate.py        # Metrics, p-values, bootstrap
│   └── validation/
│       ├── baseline.py        # Implements Mean Predictor baseline (T060)
│       └── sensitivity.py     # Threshold sweep analysis
├── data/
│   ├── raw/                   # Downloaded real files
│   ├── curated/
│   │   ├── filtered.csv       # FCC/Self only
│   │   ├── enriched.csv       # With AtomicDescriptors
│   │   └── data_provenance.json # Hash log (T051)
│   └── reference/
│       └── pure_metals_q.csv  # Standard reference for Q_host (T031)
├── models/
│   ├── final_rf.pkl
│   ├── final_gb.pkl
│   └── linear_coef.json
├── results/
│   ├── metrics.json
│   └── sensitivity_plot.png
├── tests/
│   ├── unit/
│   └── integration/
├── requirements.txt
└── pyproject.toml
```

**Structure Decision**: Selected a modular `code/` layout separating data, features, models, and validation to ensure testability and alignment with the "Single Source of Truth" principle. This structure supports the independent testing of US-1 (Ingestion) and US-2 (Feature Engineering).

## Complexity Tracking

No violations detected. The linear flow (Ingest -> Feature -> Train -> Validate) is standard for this domain and fits within the specified resource constraints. The use of real data (if available) ensures scientific validity. If no real data is available, the project halts, avoiding fabrication.