# Implementation Plan: Investigating the Relationship Between Brain Network Dynamics and Individual Differences in Sensorimotor Performance

**Branch**: `001-brain-proprioception-correlation` | **Date**: 2024-05-21 | **Spec**: `specs/001-brain-proprioception-correlation/spec.md`
**Input**: Feature specification from `specs/001-brain-proprioception-correlation/spec.md`

## Summary

**Scope Correction**: The original research question mentioned "proprioceptive acuity." However, the HCP S1200 dataset does not contain direct joint position sense tests. Therefore, this study explicitly investigates **motor execution performance** (finger tapping + grip force) as the behavioral outcome. The study does **not** claim to measure proprioceptive sense. All reports will explicitly state this limitation and frame findings as "associational relationships" between network topology and motor performance.

This project implements a computational neuroscience pipeline to investigate the correlational relationship between resting-state functional connectivity network metrics (modularity, participation coefficient, within-module degree, global efficiency) and **sensorimotor performance** (using Motor Task Performance as a measure of motor execution) in the Human Connectome Project (HCP) S1200 dataset. 

The approach involves downloading **Minimal Preprocessed** (MNI normalized, ICA-FIX denoised) resting-state fMRI data and behavioral metrics from verified official sources (OpenNeuro ds000117 and HCP ConnectomeDB). The pipeline computes graph-theoretic metrics via the Schaefer 400-parcel atlas, performs Spearman correlations (controlling for FD), and applies FDR correction. The pipeline is optimized for execution on a CPU-limited GitHub Actions runner (multi-core, 7GB RAM) using batch processing and streaming, with a fallback to a scaled-down GPU run on Kaggle if fMRI volume loading exceeds memory limits.

**Preprocessing Note**: The spec's generic requirement for "motion correction, slice-time correction, normalization" is satisfied by the **Minimal Preprocessed** release of HCP data (OpenNeuro ds000117), which is already MNI normalized and ICA-FIX denoised. Re-running these steps is unnecessary and computationally prohibitive on the target runner. The plan utilizes the pre-denoised data directly, performing only QC (tSNR/FD calculation) as defined in FR-002.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `nibabel`, `numpy`, `pandas`, `scikit-learn`, `networkx`, `bctpy` (Brain Connectivity Toolbox), `matplotlib`, `seaborn`, `requests`, `tqdm`, `pyyaml`, `openneuro-py`, `hcp`.  
**Storage**: Local filesystem (`data/raw`, `data/processed`, `data/analysis`) with checksums recorded in `state`.  
**Testing**: `pytest` with contract tests against YAML schemas.  
**Target Platform**: GitHub Actions `ubuntu-latest` (CPU-first), with a specific escape hatch script for Kaggle GPU if `MemoryError` occurs during fMRI volume loading.  
**Project Type**: Research Pipeline / CLI  
**Performance Goals**: Complete analysis of up to 50 subjects within 6 hours on CPU (or extended runtime if batch-size reduction is triggered); memory usage < 7GB.  
**Constraints**: No local GPU on CI; strict data hygiene (checksums); no fabrication of results; explicit handling of missing data; FDR correction mandatory; **no partial correlation for FD** (relying on ICA-FIX).  
**Scale/Scope**: A cohort of human subjects will evaluate graphs of moderate complexity., generating a substantial volume of raw data. (streamed).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence / Implementation Plan |
| :--- | :--- | :--- |
| **I. Reproducibility** | ✅ | `requirements.txt` pins versions; random seeds set in `code/analysis/` (specifically for Louvain); HCP data fetched via verified API/URLs; pipeline scripts are idempotent. **Output `metrics_summary.csv` includes `random_seed` field.** |
| **II. Verified Accuracy** | ✅ | All citations (Schaefer atlas, OpenNeuro ds000117, HCP S1200) will be validated against the "Verified datasets" block in `research.md` before use. No hallucinated URLs. |
| **III. Data Hygiene** | ✅ | `data/` files will be checksummed (SHA-256) upon download; raw data preserved; derived data written to new files; PII scan configured. |
| **IV. Single Source of Truth** | ✅ | All figures/statistics in the report generated programmatically from `data/analysis/` CSVs; no hand-typed numbers. |
| **V. Versioning Discipline** | ✅ | Content hashes for artifacts stored in `state/...yaml`; `updated_at` timestamps managed by the advancement agent. |
| **VI. Neuroimaging Data Provenance** | ✅ | OpenNeuro ds000117 version and dataset tag recorded; preprocessing steps (ICA-FIX, GSR) verified in metadata; tSNR calculated on pre-denoised data. |
| **VII. Statistical Correlation Integrity** | ✅ | Analysis script uses `scipy.stats.spearmanr` with **fixed seed**; **r > 0.3 threshold** and **p < 0.05 threshold** logged in `analysis.log` and `power_analysis.json`; FDR (Benjamini-Hochberg) applied; parameters version-controlled. |

## Project Structure

### Documentation (this feature)

```text
specs/001-brain-proprioception-correlation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-284-investigating-the-relationship-between-b/
├── data/
│   ├── raw/               # Downloaded OpenNeuro/HCP NIfTIs and behavioral CSVs (checksummed)
│   ├── processed/         # QC-passed NIfTIs (no re-preprocessing)
│   └── analysis/          # Connectivity matrices, metrics, correlation results, PCA outputs
│       ├── pca_loadings.csv       # (T023a) Output of PCA: loadings for 2 components
│       ├── factor_scores.csv      # (T023a) Output of PCA: 2 factor scores per subject
│       └── full_metrics.csv       # (T023b) Merged metrics + PCA scores
├── code/
│   ├── download/
│   │   ├── fetch_openneuro.py
│   │   └── fetch_hcp_behavioral.py
│   ├── preprocess/
│   │   └── run_qc_only.py       # Calculates tSNR/FD, no motion correction
│   ├── analysis/
│   │   ├── compute_connectivity.py
│   │   ├── extract_metrics.py   # Includes Louvain with fixed seed
│   │   ├── run_pca_on_metrics.py # (T023a) Runs PCA, writes 2-component outputs
│   │   ├── correlations.py      # (T023b) Merges metrics + PCA, runs Spearman, FDR
│   │   └── power_analysis.py    # Post-hoc power analysis
│   ├── viz/
│   │   ├── plot_scatter.py
│   │   └── plot_network.py      # Generates network diagrams
│   ├── utils/
│   │   ├── config.py
│   │   └── checksums.py
│   └── main_pipeline.py
├── tests/
│   ├── contract/
│   │   └── test_schemas.py
│   └── integration/
│       └── test_pipeline_flow.py
├── reports/
│   └── summary.md         # Final generated report (includes limitation statements)
├── requirements.txt
└── .specify/
    └── memory/
        └── constitution.md
```

**Structure Decision**: A linear pipeline structure is chosen (`download` → `QC` → `analysis` → `viz`) to ensure strict data provenance and reproducibility. This aligns with the "Single Source of Truth" principle and simplifies the batch-processing logic required for the CPU constraint.

## Methodology Phases

### Phase 0: Data Acquisition (Download)
- **Source**: OpenNeuro `ds000117` (Minimal Preprocessed, ICA-FIX) for fMRI; HCP ConnectomeDB for behavioral data.
- **Strategy**: Use `openneuro-py` to stream/download NIfTI files; use `hcp` library or verified CSV export for behavioral data.
- **Filtering**: Select up to 50 subjects with complete data (fMRI + behavioral + FD). If <50 available, proceed with max N (min 30).
- **Motion Control**: Exclude subjects with mean FD > 0.5mm (strict threshold). **No partial correlation for FD**.

### Phase 1: Preprocessing (QC Only)
- **Input**: Minimal Preprocessed NIfTIs (already ICA-FIX, MNI normalized).
- **Steps**:
  - Verify file integrity (checksums).
  - Calculate tSNR: `mean(signal) / std(signal)` (excluding the initial volumes).
  - Calculate mean FD (from provided motion parameters).
- **QC Threshold**: tSNR ≥ 50 for ≥ 90% of voxels; mean FD < 0.5mm.
- **Output**: `data/processed/subjects_included.csv` (list of valid subjects).
- **Note**: No custom motion correction/normalization is performed; the data is used as provided by the HCP Minimal Preprocessed pipeline. This satisfies the spec's requirement for a "standard preprocessing pipeline" by utilizing the pre-processed gold-standard release.

### Phase 2: Connectivity & Metrics
- **Atlas**: Schaefer high-resolution parcel (100 networks).
- **Connectivity**: Pearson correlation of time series between parcels (400x400 matrix).
- **Metrics**:
  - **Modularity**: Global scalar (Louvain algorithm, **fixed random seed**).
  - **Participation Coefficient**: Mean across all nodes.
  - **Within-Module Degree**: Mean across all nodes.
  - **Global Efficiency**: Mean across all nodes (FR-003).
- **Implementation**: `bctpy` library for graph metrics.
- **Reproducibility**: Log `random_seed` and `algorithm_version` for Louvain in `metrics_summary.csv`.

### Phase 3: PCA & Correlation (Addressing T023a, T023b)
- **PCA**:
  - **Input**: `metrics_summary.csv`.
  - **Logic**: Compute PCA on network metrics. **Must output exactly two components.**
  - **Output**: `data/analysis/pca_loadings.csv` (loadings for 2 components) and `data/analysis/factor_scores.csv` (2 factor scores per subject).
- **Merge**: Merge raw metrics with PCA factor scores into `data/analysis/full_metrics.csv`.
- **Correlation**:
  - **Test**: Spearman correlation between each metric (and PCA factors) and Motor Task Performance.
  - **Logging**: Log test type (Spearman), `r > 0.3` threshold, `p < 0.05` threshold in `analysis.log`.
  - **Correction**: Benjamini-Hochberg FDR (q < 0.05).
  - **Limitation**: Explicitly state that results are "associational" and acknowledge residual motion confound despite ICA-FIX. Explicitly state that Motor Task Performance is a measure of motor execution, not proprioceptive acuity.

### Phase 4: Visualization
- **Scatter Plots**: Generate for all tested correlations (significant or not) with annotated statistics.
- **Network Diagrams**: Generate for significant findings (q < 0.05) using `networkx`, highlighting sensorimotor regions.
- **Output**: `reports/plots/*.png`.

### Phase 5: Reporting
- **Input**: All analysis results.
- **Logic**: Generate `reports/summary.md`.
- **Requirement**: Programmatically insert **Limitation Statement** regarding:
  1. Motor Task Performance as a measure of motor execution (not proprioception).
  2. Residual motion confound despite ICA-FIX.
- **Power Analysis**: Include post-hoc power analysis (detectable effect size r for N subjects at 80% power, α=0.05, FDR corrected) in `power_analysis.json` and the report.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Batch Processing Logic** | Required to fit 400x400 matrix computations for 50 subjects within 7GB RAM. | Processing all subjects in memory would exceed the 7GB limit, causing OOM crashes on the GitHub Actions runner. |
| **FDR Correction** | Mandatory for statistical validity when testing 4+ metrics. | Bonferroni is too conservative for exploratory neuroscience; FDR is the standard for this number of tests. |
| **No Partial Correlation for FD** | Partial correlation cannot remove non-linear, spatially structured bias from motion. | Relying on ICA-FIX is the standard approach for HCP Minimal Preprocessed data; partial correlation is scientifically unsound here. |
| **Louvain Fixed Seed** | Required for reproducibility of stochastic modularity metric. | Without fixed seed, modularity values vary across runs, violating Constitution Principle I. |
| **Minimal Preprocessed Data** | Re-running full preprocessing on CI is computationally infeasible. | The HCP Minimal Preprocessed pipeline is the gold standard; re-running it would duplicate effort and exceed time limits. |
| **PCA 2-Component Constraint** | Required to reduce dimensionality to a manageable set of factors for correlation. | Using all components leads to overfitting; 2 components are specified to capture major variance axes. |

## Compute Feasibility & Escape Hatch

### CPU-First Strategy
The primary implementation runs on a GitHub Actions runner with a multi-core CPU and sufficient memory for the workload.
- **Optimization**:
  - Stream data; never load all 50 subjects' fMRI into RAM.
  - Process subjects in batches (e.g., a small group of subjects per batch).
  - Use `float32` precision.
  - Release memory explicitly (`del` + `gc.collect()`) after each batch.
- **Runtime**: Expected to exceed 6 hours if batch size is reduced dynamically due to memory pressure. The pipeline is designed to **not fail** but to continue with reduced throughput.

### GPU Escape Hatch
If the **fMRI volume loading** (not matrix computation) exceeds CPU memory limits:
- **Trigger**: `MemoryError` during `nibabel.load` or volume streaming of a single subject's 4D NIfTI.
- **Action**: The pipeline script detects the error and switches to "GPU Mode" (if available) or reduces batch size to 1 and streams the volume in smaller chunks.
- **Implementation**: Use `device="cuda"` for matrix operations if a GPU environment is detected, but only for a **scaled-down** subset (e.g., 5 subjects) to fit the ~16GB VRAM of a free Kaggle GPU.
- **Constraint**: Do **not** fabricate a CPU approximation for a GPU task. If the method requires GPU, plan the real scaled GPU run.
