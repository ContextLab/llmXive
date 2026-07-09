# Implementation Plan: Reconstructing Solar Irradiance from Historical Sunspot Records

**Branch**: `001-reconstruct-solar-irradiance` | **Date**: 2026-07-02 | **Spec**: `specs/001-reconstructing-solar-irradiance-from-his/spec.md`
**Input**: Feature specification from `/specs/001-reconstructing-solar-irradiance-from-his/spec.md`

## Summary

This project implements a cycle‑specific non‑linear regression pipeline to reconstruct Total Solar Irradiance (TSI) from historical Group Sunspot Number (GSN) records spanning the telescopic era to the present. The core technical approach involves a **Two-Stage Calibration** with **Proxy Anchoring**:
1.  **Stage 1 (Satellite Training)**: Train a Random Forest (or Gaussian Process) on satellite‑era data (2003–2015) using GSN, a **cycle_phase** feature (derived via Hilbert‑Huang Transform), and a facular proxy (Ca II K or Mg II). The model is validated using **Leave-One-Cycle-Out (LOCO) Cross-Validation** to ensure generalization to unseen cycle dynamics, not just unseen time points.
2.  **Stage 2 (Isotope Anchoring)**: Adjust the model's uncertainty scaling and bias using a loss term derived from cosmogenic isotope proxies (14C, 10Be) in pre‑satellite periods. This anchors the reconstruction to physical reality before generating the final time series.

Model performance is evaluated on a held‑out validation set (2016–present) **and** via **LOCO-CV**. The final reconstruction for the early modern period through the early 21st century includes uncertainty bands derived from both CV error and isotope agreement. External validation uses the fixed 2007 baseline (Lean et al.) as a reference, treating it as a static benchmark (no re-tuning). Statistical significance of variance differences is tested by comparing the reconstruction's variance against the *empirical variance* of the isotope proxies, not just internal consistency.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `scikit-learn`, `numpy`, `matplotlib`, `seaborn`, `requests`, `pyyaml`, `scipy`, `pyhht` (CPU‑only HHT implementation)  
**Storage**: Local `data/` directory (raw CSV/Parquet, processed Parquet); no external database.  
**Testing**: `pytest` for unit tests on data preprocessing, model logic, and contract validation.  
**Target Platform**: Linux (GitHub Actions free‑tier runner: 2 CPU, ~7 GB RAM, no GPU).  
**Performance Goals**: Total runtime ≤ 6 h; memory ≤ 6 GB; model training ≤ 30 min on CPU.  
**Constraints**: No GPU, no large‑scale deep learning, all libraries CPU‑only.  
**Scale/Scope**: ~12 years of satellite data for training, ~400 years of GSN for reconstruction, 1 000 bootstrap iterations (parallelized over 2 cores).

## Constitution Check

| Principle | Status | Verification Method |
|-----------|--------|---------------------|
| I. Reproducibility | PASS | Random seeds pinned; datasets fetched from canonical URLs (manual download); `requirements.txt` pins versions. |
| II. Verified Accuracy | PASS | All datasets sourced from primary canonical portals (SILSO, NASA SORCE, ESGF, NOAA). Specific URLs provided in `research.md` and `quickstart.md`. `download.py` computes SHA-256 checksums to verify integrity. |
| III. Data Hygiene | PASS | Raw data checksummed; transformations produce new files; no PII. |
| IV. Single Source of Truth | PASS | All figures/statistics trace to single rows in `data/` and code blocks. |
| V. Versioning Discipline | PASS | SHA‑256 hashes computed on file content after each artifact write; `updated_at` timestamp updated atomically in `state` YAML. |
| VI. Cycle‑Specific Calibration Integrity | PASS | `cycle_phase` (derived from HHT) used as continuous feature; LOCO-CV ensures non-overfitting to specific cycles. |
| VII. Historical Gap Handling and Uncertainty Quantification | PASS | Linear interpolation for missing GSN; HHT mandatory for cycle detection; uncertainty bands derived from CV + isotope alignment; 1 000 block‑bootstrap iterations comparing reconstruction to proxy variance. |

## Project Structure

### Documentation (this feature)

```text
specs/001-reconstructing-solar-irradiance-from-his/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   └── output.schema.yaml
└── tasks.md             # Phase 2 output (NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
projects/PROJ-381-reconstructing-solar-irradiance-from-his/
├── code/
│   ├── __init__.py
│   ├── config.py              # Paths, seeds, hyperparams
│   ├── data/
│   │   ├── __init__.py
│   │   ├── download.py        # Manual‑download helper scripts for GSN, SORCE/TIM, CMIP6, isotopes
│   │   ├── preprocess.py      # Interpolation, HHT cycle detection, cycle_phase engineering
│   │   └── loaders.py         # Parquet/CSV loaders
│   ├── models/
│   │   ├── __init__.py
│   │   ├── train.py           # RF/GP training with LOCO‑CV and hyperparameter tuning
│   │   ├── evaluate.py        # RMSE, R², baseline re‑run, correlation with CMIP6
│   │   └── reconstruct.py     # Apply calibrated model to pre‑satellite GSN
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── bootstrap.py       # Proxy‑augmented block‑bootstrap for variance tests
│   │   └── plots.py           # Variance CI, difference plots, baseline comparison
│   └── main.py                # Orchestration script
├── data/
│   ├── raw/                   # Manually downloaded files (checksummed)
│   ├── processed/             # Interpolated, HHT‑derived, feature‑engineered Parquet
│   └── results/               # Reconstructions, uncertainty bands, bootstrap stats, plots
├── tests/
│   ├── contract/              # Schema validation tests
│   ├── unit/                  # Preprocessing, model logic tests
│   └── integration/           # End‑to‑end pipeline tests
├── docs/
│   └── paper/                 # Draft manuscript (generated from results)
└── requirements.txt
```

**Structure Decision**: Single‑project layout with modular `code/` sub‑packages. All data flows through `data/` with explicit raw → processed → results stages, matching the Constitution’s single source of truth requirement.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | Constitution Check passed. The Two-Stage Calibration, LOCO-CV, and Proxy Anchoring are necessary for scientific validity, not optional complexity. | N/A |

## Detailed Phase Breakdown

### Phase 0 – Research & Design (completed)

- Dataset strategy (see `research.md`).
- Methodology selection, statistical rigor plan, and risk assessment (see `research.md`).

### Phase 1 – Implementation Design

1.  **Data Acquisition & Verification**  
    - Run `code/data/download.py`. The script prints manual download URLs (SILSO, NASA SORCE, ESGF, NOAA) and verifies checksums after the user places files in `data/raw/`.  
    - Compute SHA‑256 of each raw file content and store in `state/...yaml`. This enforces Principle II (Verified Accuracy).

2.  **Preprocessing** (`code/data/preprocess.py`)  
    - Linear interpolation of missing GSN values.  
    - **Mandatory**: Apply Hilbert‑Huang Transform (via `pyhht`) to derive instantaneous frequency; detect cycle boundaries and compute **cycle_phase** (0‑1 within each cycle). *No fallback to peak detection*.  
    - One‑hot encode `cycle_phase` bins (e.g., 10 bins) for model input.  
    - Normalise numerical features (zero mean, unit variance).  
    - Store processed Parquet in `data/processed/` and record hash.

3.  **Model Development** (`code/models/train.py`)  
    - Perform 5‑fold CV on the 2003‑2015 training set to tune Random Forest hyper‑parameters (`n_estimators≤100`, `max_depth≤10`).  
    - Conduct **Leave-One-Cycle-Out (LOCO) CV**: iteratively hold out each solar cycle within the training period, train on the remaining cycles, and evaluate on the held‑out cycle. Report LOCO‑CV RMSE and R².  
    - **Isotope-Calibrated Adjustment**: If isotope data is available, apply a post-hoc bias correction to the model's predictions for the pre-satellite era, minimizing the difference between reconstructed variance and isotope proxy variance.  
    - Train final model on the full training set with selected hyper‑parameters.  
    - Compute OOB error as an additional over‑fit guard.  
    - Save model (`.pkl`) and record hash.

4.  **Baseline Comparison** (`code/models/evaluate.py`)  
    - Load the **fixed** 2007 baseline reconstruction (Lean et al.) as an external reference. **Do not re-tune** or re-run the baseline on the 2003-2015 split.  
    - Compute baseline RMSE, R², and correlation with CMIP6 for the overlapping period.  
    - Store baseline metrics for fair comparison.

5.  **Reconstruction** (`code/models/reconstruct.py`)  
    - Apply the calibrated model to the full pre‑satellite GSN (1610‑2002).  
    - Propagate CV‑derived prediction intervals and isotope-adjusted uncertainty to form uncertainty bands (`tsi_lower`, `tsi_upper`).  
    - Save reconstruction Parquet and record hash.

6.  **External Proxy Validation & Statistical Significance** (`code/analysis/bootstrap.py`)  
    - Load cosmogenic isotope series (14C, 10Be).  
    - Compute variance of reconstruction and variance of each isotope proxy for the Maunder, Dalton, and Modern minima.  
    - Perform 1 000 block‑bootstrap iterations on **both** the reconstruction and the proxy variance (block length = autocorrelation‑derived).  
    - Test if the reconstruction's variance distribution significantly differs from the proxy's variance distribution.  
    - Apply Bonferroni correction for the three pairwise comparisons (α = 0.05/3).  
    - Output p‑values, 95 % CI, and a table indicating statistical significance.

7.  **Versioning Discipline Implementation**  
    - After each step (download, preprocess, train, reconstruct, bootstrap) compute SHA‑256 of the **file content** of the output artifact.  
    - Write the hash to `state/projects/PROJ-381-reconstructing-solar-irradiance-from-his.yaml` under `artifact_hashes`.  
    - Atomically update `updated_at` to the current ISO timestamp.

### Phase 2 – Execution & CI

- GitHub Actions workflow executes the above steps in order, ensuring data is downloaded before any processing, models are trained before evaluation, and figures are generated before manuscript assembly.

## Compute Feasibility

- All heavy operations (HHT, Random Forest, bootstrap) are CPU‑only and bounded to ≤ 2 CPU cores.  
- Memory usage stays < 6 GB by streaming large pre‑satellite GSN in chunks.  
- Total runtime on the free‑tier runner is estimated to be within a practical range for iterative development.

## Risks and Mitigations (updated)

| Risk | Mitigation |
|------|------------|
| Non-Stationarity of GSN-TSI relationship | **Non-Stationarity Check**: Compare model residuals against isotope trends. If drift detected, flag reconstruction as high uncertainty. |
| Manual download complexity | Scripted checksum verification ensures data integrity; specific canonical URLs provided. |
| HHT computational cost | Use `pyhht` with minimal mode; process one year at a time to stay within RAM limits. No fallback to peak detection. |
| Model over‑fit to short satellite window | 5‑fold CV + LOCO‑CV + OOB error; Isotope-Calibrated Adjustment anchors to physical reality. |
| Distribution‑shift validation | External proxy validation with isotopes; bootstrap compares reconstruction variance to independent proxies. |
| Multicollinearity between Sunspot and Cycle | Use continuous `cycle_phase` (time-based) instead of categorical `cycle_id`; report descriptive relationships only. |
| Bootstrap circularity | Bootstrap compares reconstruction variance to **independent isotope proxy variance**, not internal consistency. |
| Versioning gaps | Explicit SHA‑256 hashing on file content and atomic timestamp update after every major artifact. |
| Baseline comparison bias | Strictly treat 2007 baseline as fixed; no re-tuning allowed. |

### Success Criteria Mapping

| Success Criteria | Plan Element Addressing It |
|------------------|----------------------------|
| SC-001 (RMSE reduction ≥15%) | Phase 1 Step 4 (Baseline Comparison) on held-out validation set. |
| SC-002 (R² score comparable) | Phase 1 Step 3 (Model Development) on held-out validation set. |
| SC-003 (Variance significance) | Phase 1 Step 6 (External Proxy Validation) using proxy-augmented bootstrap. |
| SC-004 (CMIP6 correlation) | Phase 1 Step 4 (Baseline Comparison) correlation check. |