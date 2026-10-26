# Implementation Plan: Investigating the Relationship Between Brain Network Dynamics and Individual Differences in Musical Emotion Perception

**Branch**: `001-brain-music-emotion` | **Date**: 2026-10-26 | **Spec**: `specs/001-investigating-the-relationship-between-b/spec.md`  
**Input**: Feature specification from `/specs/001-investigating-the-relationship-between-b/spec.md`

## Summary
The project must (1) acquire paired resting‑state fMRI and Music Emotion Rating (MER) data, (2) preprocess the fMRI with fMRIPrep (CPU‑only), (3) extract Schaefer regional time series (using an appropriate parcellation resolution) and compute Pearson functional connectivity matrices, (4) derive global and network‑specific graph metrics plus edge‑level strengths, (5) merge these metrics with MER scores, (6) run partial correlations (controlling for age, sex, FD) and a regularized regression model with 5‑fold CV, (7) apply FDR correction, (8) report resource usage and power analysis, and (9) generate reproducible figures. The pipeline includes a **validation gate** that halts execution when required paired data are unavailable, preserving reproducibility and avoiding fabrication.

## Technical Context
- **Language/Version**: Python 3.10  
- **Primary Dependencies**: `datasets==2.19.0`, `pandas==2.2.2`, `numpy==1.26.4`, `scikit-learn==1.5.0`, `networkx==3.3`, `bctpy==0.5.0`, `statsmodels==0.14.2`, `matplotlib==3.9.0`, `pydantic==2.7.1`  
- **Storage**: `data/` (raw downloads + checksums), `results/` (CSV/JSON outputs), `reports/` (validation & resource logs)  
- **Testing**: `pytest` suite covering schema contracts, matrix integrity, VIF screening, PCA variance, and FDR logic  
- **Target Platform**: Linux GitHub Actions free tier (2 CPU cores, ≤ 7 GB RAM, ≤ 6 h wall‑clock) – **CPU‑first**; no GPU required.  
- **Constraints**: No fabricated data; any missing required variable triggers a Data‑Gap Report and aborts further analysis.

## Constitution Check
| Principle | Reference in Plan | Outcome |
|-----------|-------------------|---------|
| I. Reproducibility | Pinning of seeds (`RANDOM_SEED=42`), deterministic URLs, full pipeline scripted in `src/main.py` | ✅ |
| II. Verified Accuracy | Only URLs from the **Verified Datasets** block are used; no unverified citations | ✅ |
| III. Data Hygiene | SHA‑256 checksums recorded (`data/checksums.json`); raw files immutable; no PII | ✅ |
| IV. Single Source of Truth | All figures/tables derived from files under `results/` and `reports/` | ✅ |
| V. Versioning Discipline | Content hashes tracked in `state/projects/...yaml`; any artifact change updates timestamp | ✅ |
| VI. Neuro‑Imaging Preprocessing Standardization | fMRIPrep step (Task 0.3) will be executed when raw fMRI becomes available, satisfying the non‑negotiable requirement. | ✅ (fulfilled when data present) |
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
    ├── data_gap_report.schema.yaml
    └── network_metrics.schema.yaml

code/
├── src/
│   ├── config.py
│   ├── data/
│   │   ├── download.py
│   │   ├── validate.py
│   │   └── preprocess.py   # fMRIPrep execution (runs when raw fMRI is present)
│   ├── analysis/
│   │   ├── graph_metrics.py
│   │   ├── stats.py
│   │   └── visualize.py
│   └── main.py
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
| Data‑gap handling | No open dataset provides required paired fMRI + MER; must stop rather than fabricate | Ignoring the gap would breach Constitution I & III |
| Under‑powered sample | Detecting `r ≥ 0.20` with `α = 0.05` needs `N ≈ 194`; current matched subsets are smaller | Proceeding without a power check would violate SC‑005 |
| High‑dimensional edge predictors | `p ≫ N` makes ordinary regression unstable | Dropping edges entirely would lose critical information; PCA retains variance while limiting dimensionality |
| Computational overload | All steps are CPU‑first and fit within 2 CPU cores, < 2 GB RAM, < 30 min runtime. No GPU needed. |
| Scope drift | Every new task is explicitly tied to an FR/SC; any deviation requires a spec amendment. |

## Implementation Phases

### Phase 0 – Data Acquisition, Validation, and Scope Alignment
| Task | Description | FR/SC Covered |
|------|-------------|---------------|
| **0.0 – Download & Subject Matching (FR‑001)** | `download.py` fetches each URL from the Verified Datasets block via `datasets.load_dataset` or `requests`, computes SHA‑256 checksums, logs per‑file success/failure, and attempts deterministic matching of HCP Subject IDs to MER records (or via demographic keys). | FR‑001 |
| **0.1 – Validation Gate (FR‑001)** | `validate.py` inspects downloaded files for required columns (`subject_id`, `age`, `sex`, `fd_mean`, `mer_score`, `fc_upper_tri`). If any are missing, populates `reports/data_gap_report.json` (using `data_gap_report.schema.yaml`) and exits with status 1, halting later phases. | FR‑001 |
| **0.2 – Schema Validation (FR‑001)** | Validates the merged subject table against `contracts/dataset.schema.yaml`. Failure triggers the same Data‑Gap Report. | FR‑001 |
| **0.3 – fMRIPrep Execution (FR‑002)** | When raw NIfTI files are present, runs fMRIPrep in CPU‑only mode with motion correction and band‑pass filtering (0.01–0.1 Hz): <br>`fmriprep /path/to/raw /path/to/derivatives participant --ignore slicetiming --output-spaces MNI152NLin2009cAsym --use-syn-sdc --fd-spike-threshold 0.5 --nthreads 2 --omp-nthreads 2 --mem_mb 6000 --fs-license-file $FREESURFER_LICENSE` <br>Generates motion‑corrected, band‑passed time series and mean FD. Placeholder documented until raw fMRI becomes available. | FR‑002 (conditional) |
| **0.4 – Independent Test (US‑1) & N‑Distribution (US‑2)** | If validation passes, runs the pipeline on a random 5‑subject subset, verifies matrix symmetry, range, diagonal = 1.0, and writes `reports/independent_test_summary.json`. | US‑1, US‑2 |
| **0.5 – Data‑Gap Report Generation** | Writes `reports/data_gap_report.json` summarizing missing variables, per‑file columns, and timestamp. | FR‑001 |

### Phase 1 – Feature Extraction (executed only if Phase 0 passes)
| Task | Description | FR/SC Covered |
|------|-------------|---------------|
| **1.0 – Time‑Series Extraction & Pearson FC (FR‑003)** | Uses fMRIPrep‑processed NIfTI + Schaefer‑200 atlas to extract region‑wise time series and compute Pearson correlation matrices for each subject. If only `fc_upper_tri` is provided, reconstructs the full matrix. | FR‑003 |
| **1.1 – Matrix Reconstruction** | Reconstructs full 200 × 200 symmetric matrix from `fc_upper_tri`; validates diagonal = 1.0 and value range. | – |
| **1.2 – Edge‑Weight Transformation** | Takes absolute values of correlations, retains top [deferred] strongest positive edges, produces a binary‑weighted matrix. | – |
| **1.3 – Graph‑Metric Computation** | Computes: global efficiency, Louvain modularity, participation coefficient, within‑network efficiency for DMN, Salience, Visual, Reward (NAcc + VS) using `bctpy`. Stores results in `results/network_metrics.csv`. | FR‑004 |
| **1.4 – VIF Screening** | Calculates variance‑inflation factors for scalar metrics; drops any predictor with VIF > 5, logs to `results/vif_report.json`. | – |

### Phase 2 – Statistical Modeling (executed only if Phase 1 succeeds)
| Task | Description | FR/SC Covered |
|------|-------------|---------------|
| **2.1 – Power Check & Conditional Modeling (FR‑005, SC‑001, SC‑005)** | Performs partial correlation between each retained metric and `mer_score`, controlling for age, sex, `fd_mean`. Uses `statsmodels.stats.power` to compute required N for detecting `r = 0.20` at `α = 0.05`. **If** actual `N < required_N` (≈ 194), the pipeline aborts further modeling, writes an exploratory flag in `results/run_summary.json`, and skips Tasks 2.2‑2.4. Otherwise proceeds. | FR‑005, SC‑001, SC‑005 |
| **2.2 – Dimensionality Reduction & Ridge Regression** | Applies PCA to the edge‑strength vectors, retains enough components to explain ≥ 80 % variance (typically ≤ 10 PCs). Combines these PCs with VIF‑screened scalar metrics as predictors. Fits a Ridge regression with 5‑fold CV (seed = 42). Outputs cross‑validated R² and compares to intercept‑only baseline in `results/analysis_results.csv`. | FR‑005, SC‑002 |
| **2.3 – Multiple‑Comparison Correction** | Applies Benjamini–Hochberg FDR (q < 0.05) to all partial‑correlation p‑values; stores adjusted p‑values alongside raw values. | FR‑006, SC‑003 |
| **2.4 – Reporting & Summary** | `visualize.py` generates (a) scatter plot of predicted vs. actual MER scores with regression line and R² annotation, (b) bar chart of metrics that survive FDR. `main.py` writes `results/run_summary.json` summarizing N, RAM/CPU usage, power status, and validation‑gate outcome. | SC‑004 |

### Phase 3 – Verification
| Task | Description |
|------|-------------|
| **3.1 – Schema Contract Tests** | Validates `results/network_metrics.csv` against `contracts/network_metrics.schema.yaml`, `results/analysis_results.csv` against `contracts/output.schema.yaml`, and `reports/data_gap_report.json` against `contracts/data_gap_report.schema.yaml`. |
| **3.2 – Unit Tests** | Tests matrix symmetry, edge‑weight transformation, VIF calculation, PCA variance capture, and FDR adjustment on synthetic but schema‑conformant fixtures. |
| **3.3 – Integration Test** | Confirms that with the current verified sources the pipeline stops after Task 0.1/0.2 and produces a correctly‑structured Data‑Gap Report (FR‑001). |

## FR/SC Coverage Map
| ID | Covered by |
|----|-------------|
| FR‑001 | **Tasks 0.0, 0.1, 0.2** – download, validation gate, and schema validation of paired data |
| FR‑002 | **Task 0.3** – fMRIPrep execution (runs when raw fMRI is available) |
| FR‑003 | **Task 1.0** – time‑series extraction & Pearson FC (runs when raw fMRI is available) |
| FR‑004 | **Task 1.3** – graph‑metric computation |
| FR‑005 | **Task 2.1** (partial correlation) & **Task 2.2** (Ridge regression) |
| FR‑006 | **Task 2.3** – FDR correction |
| SC‑001 | **Task 2.1** – correlation vs. null |
| SC‑002 | **Task 2.2** – R² vs. intercept‑only |
| SC‑003 | **Task 2.3** – FDR‑adjusted q < 0.05 |
| SC‑004 | **Task 2.4** – RAM/CPU usage log |
| SC‑005 | **Task 2.1** – power calculation; exploratory flag if under‑powered |
| US‑1 | **Task 0.4** – independent 5‑subject test (when data present) |
| US‑2 | **Task 0.4** – N and MER distribution reporting |
| US‑4 | **Task 2.4** – resource‑usage report |
| US‑5 | **Task 2.1** – power analysis |

## Risk Mitigation
| Risk | Mitigation |
|------|------------|
| No open dataset with required variables | Validation gate halts execution and emits a Data‑Gap Report; no fabrication. |
| Under‑powered sample | Minimum‑N check (Task 2.1) aborts primary modeling and flags exploratory status. |
| High‑dimensional edge predictors | PCA reduces dimensionality before regression; VIF screening removes collinear scalar predictors. |
| Computational overload | All steps are CPU‑first and fit well within 2 CPU cores, < 2 GB RAM, < 30 min runtime. No GPU needed. |
| Scope drift | Every new task is explicitly tied to an FR/SC; any deviation requires a spec amendment. |

---



