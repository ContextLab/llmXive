# Implementation Plan: The Impact of Network Efficiency on Age-Related Changes in Resting-State EEG

**Branch**: `429-network-efficiency-eeg` | **Date**: 2026-07-08 | **Spec**: `spec.md`
**Input**: Feature specification from `spec.md`

## Summary

This project implements a reproducible neuroinformatics pipeline to quantify the relationship between age-related cognitive decline and resting-state EEG functional network efficiency. The technical approach involves downloading the Temple University Hospital (TUH) EEG Corpus, preprocessing it with MNE-Python (10s epochs, ICA artifact removal), computing graph-theoretical metrics (Global/Local Efficiency, Path Length, etc.) via NetworkX, and performing statistical analysis (Multivariate Regression with covariates) on CPU-only infrastructure. The plan acknowledges the fixed nature of the TUH dataset and prioritizes calculating Minimum Detectable Effect Size (MDES) over forcing a power target that may be unachievable.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: MNE-Python, NetworkX, SciPy, Pandas, Statsmodels, Matplotlib, Seaborn, PyWavelets
**Storage**: Local filesystem (`data/`), HDF5/NumPy for intermediate matrices, CSV for results.
**Testing**: `pytest` with `pytest-cov` for coverage; `ruff` for linting; `black` for formatting.
**Target Platform**: Linux (GitHub Actions Free Tier: 2 CPU, 7GB RAM, 14GB Disk).
**Project Type**: Data Science / Computational Neuroscience Pipeline.
**Performance Goals**: Complete full pipeline (download -> preprocess -> analyze) within 6 hours on CPU.
**Constraints**: CPU-only execution (SC-001); No GPU usage; Memory < 7GB (requires streaming or chunked processing); Strict adherence to 10s epoch length (FR-002).
**Scale/Scope**: Processing of a subset of the TUH EEG Corpus (Adults, ~-80yo) sufficient for MDES calculation.

> **Note on Data Scale**: The full TUH corpus is large. The plan utilizes streaming or a fixed-seed random sample to fit within the 7GB RAM / 14GB disk constraint, ensuring the *real* data is used rather than synthetic stand-ins.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Implementation Strategy |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | `requirements.txt` pinned; `random_seed` variable defined in `code/utils/config.py`; Data fetched from canonical PhysioNet/TUH URL; `trace_id` injected into all outputs. |
| **II. Verified Accuracy** | **PASS** | All citations (TUH, MNE, NetworkX) will be validated against the primary source URLs in `research.md`. Title overlap check enforced by validator. |
| **III. Data Hygiene** | **PASS** | Raw data stored in `data/raw/` with SHA-256 checksums recorded in `state/`. No in-place modification; derived data in `data/processed/`. PII scan via `git-secrets` or similar in CI. |
| **IV. Single Source of Truth** | **PASS** | All figures/stats in `paper/` generated via scripts in `code/` reading from `data/results/`. No manual entry. |
| **V. Versioning Discipline** | **PASS** | `state/projects/PROJ-429-...yaml` updated on artifact change; Content hashes stored in `state/`. |
| **VI. Signal Integrity** | **PASS** | Preprocessing pipeline (low-frequency, ICA) designed to minimize spectral leakage; Epoching (appropriate duration) selected to balance resolution and stationarity. |
| **VII. Non-Circularity** | **PASS** | Predictors (EEG metrics) derived strictly from signal; Outcomes (Age, Cognitive Score) from metadata. No overlap in data sources. |

## Project Structure

### Documentation (this feature)

```text
specs/429-network-efficiency-eeg/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── network_metrics.schema.yaml
│   └── correlation_results.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── __init__.py
├── config.py            # Global config, seeds, paths
├── main.py              # Orchestration entry point
├── data/
│   ├── __init__.py
│   ├── download.py      # TUH fetch logic (streaming/chunked)
│   ├── preprocess.py    # MNE pipeline (filter, ICA, epoch)
│   └── validate.py      # Schema checks, PII scan
├── analysis/
│   ├── __init__.py
│   ├── connectivity.py  # Coherence calculation
│   ├── graph_metrics.py # NetworkX metrics (Global/Local Eff)
│   ├── stats.py         # Regression, FDR, MDES
│   └── sensitivity.py   # Threshold variation analysis
├── viz/
│   ├── __init__.py
│   └── plots.py         # Age-stratified bar plots, topology maps
├── utils/
│   ├── __init__.py
│   ├── io.py            # CSV/JSON helpers, trace_id injection
│   └── logging.py
└── tests/
    ├── test_download.py
    ├── test_preprocess.py
    ├── test_graph_metrics.py
    └── test_schema_validation.py

data/
├── raw/                 # Downloaded EDF files (streamed or subset)
├── processed/
│   ├── epochs/          # MNE Epochs objects (.fif)
│   └── connectivity/    # NumPy arrays (.npy)
├── results/
│   ├── network_metrics.csv
│   ├── correlation_results.csv
│   └── regression_results.csv
└── quality/
    ├── download_report.json
    ├── exclusion_log.csv
    └── efficiency_check.json

docs/
├── decisions/
│   └── epoch_length.md  # Rationale for 10s vs 2s
└── constitution.md      # Project constitution
```

**Structure Decision**: Single project structure (`code/`, `data/`, `docs/`) as per standard Python data science conventions. Separation of `analysis` (metrics) and `viz` (plotting) ensures modularity.

**Configuration Artifacts**:
- `code/requirements.txt`: Pinned dependencies.
- `code/.ruff.toml`: Linting configuration.
- `code/pyproject.toml`: Black formatting configuration.

## Complexity Tracking

No violations of the Constitution found. The complexity is driven by the need to process large EEG data on limited RAM (7GB).
- **Strategy**: Use MNE's `streaming` capabilities or process subjects in batches to keep memory usage low.
- **Rejection of Alternatives**: Pre-loading the entire dataset into RAM is rejected due to the 7GB constraint. Synthetic data generation is rejected due to the "Data Hygiene" and "Single Source of Truth" principles.

## Phase Breakdown

### Phase 0: Data Acquisition & Validation (FR-001, FR-007)
- **Goal**: Download TUH EEG subset, validate metadata (Age, Cognitive Scores).
- **Steps**:
  1. Implement `code/data/download.py` to fetch from PhysioNet/TUH.
  2. Filter for adults (Age >= 18).
  3. Validate cognitive instruments (MMSE, MoCA). **If structured scores are missing**, flag records with `exclusion_reason: "Missing_Cognitive_Score"` in `data/quality/exclusion_log.csv`. Use "Diagnosis" as a proxy if available.
  4. Generate `data/quality/download_report.json` and `data/quality/exclusion_log.csv`.
- **Output**: Validated raw data subset, exclusion log.

### Phase 1: Preprocessing & Epoching (FR-002)
- **Goal**: Clean signal, create 10s epochs.
- **Steps**:
  1. Bandpass filter low-frequency components below 40 Hz.
  2. Run ICA for artifact removal.
  3. Epoch into 10s segments.
  4. Reject epochs with >50% artifacts; **calculate SNR per epoch and set `snr_flag` boolean (True if SNR < 10dB)**.
  5. Save `data/processed/epochs/*.fif`.
- **Output**: Cleaned, epoched data.

### Phase 2: Connectivity & Graph Metrics (FR-003)
- **Goal**: Compute adjacency matrices and graph metrics.
- **Steps**:
  1. Calculate Coherence (Welch) **per frequency band (Alpha, Beta, Theta)** on epochs of appropriate duration.
  2. Construct adjacency matrices (variable-sized system).
  3. Compute Global Efficiency, Local Efficiency (**average of local efficiencies of each node, where local efficiency of a node is the global efficiency of its neighborhood subgraph**), Path Length, Clustering, Modularity.
  4. **Verify formulas via Unit Test against a synthetic graph with known efficiency values** (not tautological check).
  5. Generate `data/results/efficiency_check.json`.
- **Output**: `data/results/network_metrics.csv`.

### Phase 3: Statistical Analysis (FR-004, SC-002, SC-004)
- **Goal**: Correlate metrics with Age/Cognition; Control FWER; Assess Feasibility.
- **Steps**:
  1. Perform **Sensitivity Analysis (MDES calculation)** for the available N to determine the minimum detectable effect size. **Record feasibility in `data/quality/download_report.json`**.
  2. Perform **Multivariate Linear Regression** (with covariates Sex, Education) to control for confounds. Use Partial Correlation as a sensitivity check.
  3. Apply Bonferroni/FDR correction.
  4. Generate `data/results/correlation_results.csv` and `data/results/regression_results.csv`.
- **Output**: Statistical results, MDES report.

### Phase 4: Sensitivity & Visualization (FR-005, FR-008, SC-003)
- **Goal**: Robustness checks and plots.
- **Steps**:
  1. Vary network density thresholds and artifact thresholds.
  2. Generate age-stratified bar plots with CIs. **Visualize network topology changes using MNE's `plot_connectome` and `plot_topomap`**.
  3. Generate `data/results/sensitivity_report.md` **documenting specific variations (density, artifact thresholds)**.
- **Output**: Figures, sensitivity report.

### Phase 5: Reproducibility & Finalization (FR-006)
- **Goal**: Hashing, tracing, final assembly.
- **Steps**:
  1. Calculate SHA-256 hashes for all artifacts. **Generate `version_map.json` aggregating all hashes**.
  2. Inject `trace_id` into all CSVs. **Trace ID is SHA-256 of concatenation of input data and code**.
  3. Update `state/` with artifact hashes.
  4. **Run validation script to check for `trace_id` column and required data types (handling missing file case)**.
- **Output**: Final `data/results/` with trace IDs, updated `state/`, `version_map.json`.