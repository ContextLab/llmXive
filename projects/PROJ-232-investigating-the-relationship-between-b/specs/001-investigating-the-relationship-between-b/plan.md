# Implementation Plan: Investigating the Relationship Between Brain Network Dynamics and Individual Differences in Musical Emotion Perception

**Branch**: `001-brain-music-emotion` | **Date**: 2026-10-26 | **Spec**: `specs/001-investigating-the-relationship-between-b/spec.md`  
**Input**: Feature specification from `/specs/001-investigating-the-relationship-between-b/spec.md`

## Summary
The pipeline must (1) attempt to download open datasets, (2) validate that required variables are present, (3) if validation fails, generate a **Data‑Gap Report** and **run a simulated‑data validation** to demonstrate the full methodological workflow, (4) otherwise run the full neuro‑behavioral analysis: fMRIPrep preprocessing, Schaefer‑200 time‑series extraction, Pearson functional connectivity, graph‑theoretic metrics, PCA‑reduced edge features, partial correlations controlling for age/sex/FD, regularized regression with k‑fold cross‑validation, FDR correction, power analysis, and resource‑usage reporting. All steps are CPU‑first and fit within the GitHub Actions free‑tier limits.

## Technical Context
- **Language/Version**: Python 3.10  
- **Primary Dependencies**: `datasets==2.19.0`, `pandas==2.2.2`, `numpy==1.26.4`, `scikit-learn==1.5.0`, `networkx==3.3`, `bctpy==0.5.0`, `statsmodels==0.14.2`, `matplotlib==3.9.0`, `pydantic==2.7.1`  
- **Storage**: `data/` (raw downloads + checksums), `results/` (CSV/JSON outputs), `reports/` (validation & resource logs)  
- **Testing**: `pytest` suite covering schema contracts, matrix integrity, VIF screening, PCA variance, and FDR logic  
- **Target Platform**: Linux GitHub Actions free tier (2 CPU cores, ≤ 7 GB RAM, ≤ 6 h wall‑clock) – **CPU‑first**; no GPU required.  
- **Constraints**: No fabricated data; any missing required variable triggers a Data‑Gap Report and aborts downstream analysis **unless** the simulated‑data validation step is invoked.

## Constitution Check
| Principle | Reference in Plan | Outcome |
|-----------|-------------------|---------|
| I. Reproducibility | Deterministic URLs, pinned random seeds, full scripted pipeline (`src/main.py`) | ✅ |
| II. Verified Accuracy | Only URLs from the **Verified Datasets** block are used | ✅ |
| III. Data Hygiene | SHA‑256 checksums recorded; raw files immutable; no PII | ✅ |
| IV. Single Source of Truth | All figures/tables derived from files under `results/` and `reports/` | ✅ |
| V. Versioning Discipline | Content hashes tracked in `state/projects/...yaml`; any artifact change updates timestamp | ✅ |
| VI. Neuro‑Imaging Preprocessing Standardization | fMRIPrep step (Task 0.3) defined (executed only if raw NIfTI present) | ✅ (conditional) |
| VII. Behavioral‑Neural Data Alignment and Confound Control | Partial correlation and regression include age, sex, FD; merge requires complete rows; FDR applied (q < 0.05) | ✅ |

## Project Structure
```
specs/001-investigating-the-relationship-between-b/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── dataset.schema.yaml
    ├── output.schema.yaml
    └── data_gap_report.schema.yaml

code/
├── src/
│   ├── config.py
│   ├── data/
│   │   ├── download.py          # download & checksum
│   │   ├── validate.py          # validation gate & Data‑Gap Report
│   │   └── preprocess.py        # fMRIPrep wrapper (runs only if raw NIfTI present)
│   ├── analysis/
│   │   ├── graph_metrics.py     # time‑series extraction, FC, graph metrics
│   │   ├── stats.py             # power, partial corr, regression, FDR, simulation
│   │   └── visualize.py         # figures
│   └── main.py                  # orchestrator
├── assets/
│   └── schaefer200_labels.csv
└── tests/
    ├── contract/
    ├── integration/
    └── unit/
```

## Complexity Tracking
| Violation | Why Needed | Simpler Alternative Rejected |
|-----------|------------|------------------------------|
| Data‑gap handling | No open dataset supplies required paired fMRI + MER; must stop rather than fabricate | Ignoring the gap would breach Constitution I & III |
| Under‑powered sample | Detecting `r ≥ 0.20` at `α = 0.05` requires ≈ 194 subjects; matched subset may be smaller | Proceeding without power check would violate SC‑005 |
| High‑dimensional edge predictors | `p ≫ N` makes ordinary regression unstable | Dropping edges entirely would lose critical information; PCA retains variance while limiting dimensionality |
| Computational overload | All steps are CPU‑first and comfortably fit within free‑tier limits | — |
| Scope drift | Every new task is explicitly tied to an FR/SC; any deviation requires a spec amendment. | — |

## Implementation Phases

### Phase 0 – Data Acquisition, Validation, and Scope Alignment
| Task | Description | FR/SC Covered |
|------|-------------|---------------|
| **0.0 – Download & Subject Matching (FR‑001)** | `download.py` fetches each verified URL via `datasets.load_dataset` or `requests`, computes SHA‑256 checksums, logs per‑file success/failure, and attempts deterministic matching of HCP IDs to MER records (or via age + sex). | FR‑001 |
| **0.1 – Validation Gate (FR‑001)** | `validate.py` inspects downloaded files for required columns (`subject_id`, `age`, `sex`, `fd_mean`, `mer_score`, `fc_upper_tri`). If any are missing, populates `reports/data_gap_report.json` (using `data_gap_report.schema.yaml`) and exits with status 1, halting later phases. | FR‑001 |
| **0.2 – Schema Validation (FR‑001)** | Validates the merged subject table against `contracts/dataset.schema.yaml`. Failure triggers the same Data‑Gap Report. | FR‑001 |
| **0.3 – fMRIPrep Execution (FR‑002)** | When raw NIfTI files are present, runs fMRIPrep in CPU‑only mode with motion correction and band‑pass filtering (0.01–0.1 Hz). Documented command; execution is skipped if raw data are absent. | FR‑002 (conditional) |
| **0.4 – MER Instrument Reliability Check (FR‑009, FR‑007)** | Looks up the Barcelona Music Reward Questionnaire validation paper, records reported Cronbach’s α (≥ 0.80) and citation, writes `reports/mer_reliability.json`. If α < 0.80 the pipeline flags a failure but continues to the validation gate. | FR‑009, FR‑007 |
| **0.5 – Subject‑Matching Reliability (FR‑010)** | Computes a match‑confidence score for each paired subject (age + sex agreement). Summarizes proportion of confident matches; writes `reports/match_confidence.json`. | FR‑010 |
| **0.5‑b – Matched‑Subject Proportion (SC‑006)** | Calculates `matched_proportion = N_matched / N_total_HCP`. Recorded in `reports/match_summary.json`. | SC‑006 |
| **0.5‑c – Metric‑Completion Proportion (SC‑007)** | After graph‑metric extraction (Phase 1), computes proportion of subjects with all required metrics; stored in `reports/metric_completion.json`. Evaluated **only if** a compliant dataset is available. | SC‑007 (conditional) |
| **0.6 – Simulated‑Data Validation (Methodology fallback)** | Generates synthetic connectivity matrices (random SPD) and synthetic MER scores, runs the full pipeline (Phases 1‑2) on a small sample (n=10) to confirm code path works. Results are written to `reports/simulated_validation.json`. This step runs automatically **when the validation gate fails** due to missing variables. | Provides a runnable methodology when real data are absent. |
| **0.7 – Independent Test (US‑1) & N‑Distribution (US‑2)** | *Removed* – replaced by the simulated‑data validation step. |

### Phase 1 – Feature Extraction (executed only if Phase 0 passes)
| Task | Description | FR/SC Covered |
|------|-------------|---------------|
| **1.0 – Time‑Series Extraction & Pearson FC (FR‑003)** | Uses fMRIPrep‑processed NIfTI + Schaefer‑200 atlas to extract region‑wise time series and compute Pearson correlation matrices for each subject. If only `fc_upper_tri` is provided, reconstructs the full matrix. | FR‑003 |
| **1.1 – Matrix Reconstruction** | Reconstructs full 200 × 200 symmetric matrix; validates diagonal = 1.0 and values ∈ [−1, 1]. | — |
| **1.2 – Edge‑Weight Transformation** | Takes absolute values, retains top [deferred] strongest positive edges, produces a binary‑weighted matrix. | — |
| **1.3 – Graph‑Metric Computation (FR‑004)** | Computes global efficiency, Louvain modularity, participation coefficient, within‑network efficiency for DMN, Salience, Visual, Reward (NAcc + VS) using `bctpy`. Stores results in `results/network_metrics.csv`. | FR‑004 |
| **1.4 – VIF Screening** | Calculates variance‑inflation factors for scalar metrics; drops any predictor with VIF > 5, logs to `results/vif_report.json`. | — |
| **1.5 – Metric‑Completion Reporting (SC‑007 – conditional)** | After metrics are computed, calculates the proportion of subjects with *all* required metrics (excluding excluded subjects) and writes to `reports/metric_completion.json`. This proportion is only required when a compliant dataset is present. | SC‑007 (conditional) |

### Phase 2 – Statistical Modeling (executed only if Phase 1 succeeds)
| Task | Description | FR/SC Covered |
|------|-------------|---------------|
| **2.1 – Power Check & Conditional Modeling (FR‑005, SC‑001, SC‑005)** | Performs partial correlation between each retained metric and `mer_score`, controlling for age, sex, `fd_mean`. Uses `statsmodels.stats.power` to compute required N for detecting `r = 0.20` at `α = 0.05`. If actual `N < required_N` (≈ 194), aborts further modeling, writes an exploratory flag in `results/run_summary.json`, and **records both `required_N` and `actual_N`**. | FR‑005, SC‑001, SC‑005 |
| **2.2 – Dimensionality Reduction & Ridge Regression (FR‑005, SC‑002)** | Applies PCA to the edge‑strength vectors, retains enough components to explain ≥ 80 % variance (typically ≤ 10 PCs). Combines these PCs with VIF‑screened scalar metrics as predictors. Fits a Ridge regression with 5‑fold CV (seed = 42). Outputs cross‑validated R² and compares to intercept‑only baseline in `results/analysis_results.csv`. | FR‑005, SC‑002 |
| **2.3 – Multiple‑Comparison Correction (FR‑006, SC‑003)** | Applies Benjamini–Hochberg FDR (q < 0.05) to all partial‑correlation p‑values; stores adjusted p‑values alongside raw values. | FR‑006, SC‑003 |
| **2.4 – Reporting & Summary (SC‑004)** | `visualize.py` generates (a) scatter plot of predicted vs. actual MER scores with regression line and R² annotation, (b) bar chart of metrics that survive FDR. `main.py` writes `results/run_summary.json` summarizing N, RAM/CPU usage, power status, validation‑gate outcome, matched proportion, metric‑completion proportion, and simulated‑validation flag. | SC‑004 |

### Phase 3 – Verification
| Task | Description |
|------|-------------|
| **3.1 – Schema Contract Tests** | Validate `results/network_metrics.csv` against `contracts/dataset.schema.yaml` **if present**, `results/analysis_results.csv` against `contracts/output.schema.yaml`, and `reports/data_gap_report.json` against `contracts/data_gap_report.schema.yaml`. |
| **3.2 – Unit Tests** | Test matrix symmetry, edge‑weight transformation, VIF calculation, PCA variance capture, and FDR adjustment on synthetic but schema‑conformant fixtures. |
| **3.3 – Integration Test** | Confirm that with the current verified sources the pipeline stops after Task 0.1/0.2 and produces a correctly‑structured Data‑Gap Report (FR‑001). Also verify that the simulated‑data validation runs successfully when invoked. |

## FR/SC Coverage Map
| ID | Covered by |
|----|-------------|
| FR‑001 | Tasks 0.0, 0.1, 0.2 |
| FR‑002 | Task 0.3 (conditional) |
| FR‑003 | Task 1.0 |
| FR‑004 | Task 1.3 |
| FR‑005 | Tasks 2.1, 2.2 |
| FR‑006 | Task 2.3 |
| FR‑007 | Task 0.4 |
| FR‑008 | Task 2.1 (required N reporting) |
| FR‑009 | Task 0.4 |
| FR‑010 | Task 0.5 |
| SC‑001 | Task 2.1 (correlation vs. null) |
| SC‑002 | Task 2.2 (R² vs. intercept‑only) |
| SC‑003 | Task 2.3 (FDR < 0.05) |
| SC‑004 | Task 2.4 (resource‑usage log) |
| SC‑005 | Task 2.1 (power calculation) |
| SC‑006 | Task 0.5‑b (matched proportion) |
| SC‑007 | Task 1.5 (metric‑completion proportion) – evaluated only if data are available |
| SC‑008 | Task 0.4 (MER reliability) |
| US‑1 | Simulated‑data validation (Task 0.6) |
| US‑2 | Task 0.5‑b (N and MER distribution) |
| US‑4 | Task 2.4 (resource‑usage report) |
| US‑5 | Task 2.1 (power analysis) |

## Risk Mitigation
| Risk | Mitigation |
|------|------------|
| No open dataset with required variables | Validation gate halts execution and emits Data‑Gap Report; simulated‑data step demonstrates full workflow. |
| Under‑powered sample | Minimum‑N check aborts primary modeling and flags exploratory status, reporting required vs. actual N. |
| High‑dimensional edge predictors | PCA reduces dimensionality; VIF screening removes collinear scalar predictors. |
| Computational overload | All steps are CPU‑first and comfortably fit within free‑tier limits. |
| Scope drift | Every new task is explicitly tied to an FR/SC; any deviation requires a spec amendment. |

---



