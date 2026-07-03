# Implementation Plan: Network Module Dynamics in Predicting Working Memory

**Branch**: `001-network-module-dynamics-wm` | **Date**: 2024-05-21 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-the-role-of-network-module-dynamics-in-p/spec.md`

## Summary

This project implements an exploratory analysis to investigate the association between the temporal flexibility of resting-state functional network modules and individual differences in working memory capacity. Using a subset of subjects from the Human Connectome Project (HCP, OpenNeuro ds001734), the pipeline will preprocess fMRI time series, compute dynamic community detection metrics via **Multilayer Modularity Optimization (MMO)** to ensure computational feasibility, and perform partial Spearman correlation analysis controlling for non-linear motion residuals. The implementation is constrained to CPU-only execution on GitHub Actions free-tier runners (≤7 GB RAM, ≤6 h runtime), necessitating careful memory management, data sampling, and efficient algorithmic choices.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `numpy`, `pandas`, `scikit-learn`, `networkx`, `leidenalg` (for MMO), `nilearn` (CPU-only), `psutil`, `openneuro-py`, `scipy`  
**Storage**: Local file system (`data/raw_fmri`, `data/processed`, `data/results`), Parquet/CSV formats  
**Testing**: `pytest`  
**Target Platform**: Linux (GitHub Actions free-tier runner)  
**Project Type**: computational-research-pipeline  
**Performance Goals**: Process 100 subjects within 6 hours; peak RAM ≤ 7 GB  
**Constraints**: No GPU, no CUDA, no 8-bit/4-bit quantization, no large-LLM inference. Data must be subset to fit memory.  
**Scale/Scope**: A sample of subjects, A typical duration of HCP rs-fMRI data per subject, as established in prior literature (e.g., Van Essen et al., 2013; Glasser et al., 2013)., Multiple sliding window lengths for sensitivity analysis.  
**Dataset**: Primary source is **OpenNeuro ds001734** (verified public, no-auth, contains rs-fMRI + 2-back). If this dataset is not available in the verified list, the script aborts with a "Dataset Mismatch Error".

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Action |
| :--- | :--- | :--- |
| **I. Reproducibility** | PASS | All random seeds (numpy, random, networkx, leidenalg) pinned in `code/`. `requirements.txt` pins exact versions. Data fetched from canonical HCP source (ds001734). |
| **II. Verified Accuracy** | PASS | Citations for HCP dataset (ds001734) and MMO algorithm will be validated against primary sources. **Blocking Gate**: Ingestion script aborts if dataset URL is not in the verified list. |
| **III. Data Hygiene** | PASS | Raw data stored in `data/raw_fmri` (checksummed). Derivations (cleaned time series, flexibility scores) written to new files in `data/processed`. PII scan enabled. |
| **IV. Single Source of Truth** | PASS | All statistics in `paper/` will be auto-generated from `data/results` via scripts in `code/`. No hand-typed numbers. |
| **V. Versioning Discipline** | PASS | Content hashes for all artifacts recorded in `state/...yaml`. Timestamps updated on change. |
| **VI. Neuroimaging Data Integrity** | PASS | Preprocessing pipeline configuration (`code/preprocessing/fmriprep.conf`) is version-controlled and committed. Its content hash is recorded in `state/...yaml`. |
| **VII. Behavioral Measure Consistency** | PASS | Raw response logs retained under `data/raw_behavior/`. Scoring algorithm version documented in `code/behavioral_scoring/scoring_algo_version.txt`. |

## Project Structure

### Documentation (this feature)

```text
specs/001-the-role-of-network-module-dynamics-in-p/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Pre-defined schemas (Phase 0 inputs)
│   ├── dataset.schema.yaml
│   └── output.schema.yaml
└── tasks.md             # Phase 2 output (not created by /speckit-plan)
```

### Source Code (repository root)

```text
code/
├── ingestion/
│   ├── download_hcp.py          # Fetches data from HCP/OpenNeuro (ds001734)
│   └── preprocess.py            # Motion scrubbing, OLS regression, FD calculation
├── analysis/
│   ├── dynamic_connectivity.py  # Multilayer Modularity Optimization (MMO)
│   └── statistics.py            # Partial Spearman, Permutation test, Sensitivity
├── utils/
│   ├── memory_monitor.py        # psutil peak RSS tracking
│   └── config.py                # Seeding, window lengths, thresholds
├── results/
│   └── generate_report.py       # Generates final statistics and plots
└── requirements.txt

data/
├── raw_fmri/                    # Original NIfTI/Parquet (checksummed)
├── raw_behavior/                # 2-back logs
├── processed/                   # Cleaned time series, flexibility scores
└── results/                     # Correlation stats, p-values, plots

tests/
├── unit/
├── integration/
└── contract/
```

**Structure Decision**: Single-project structure (`code/`, `data/`, `tests/`) chosen for simplicity and direct alignment with the computational pipeline nature of the research. No separate backend/frontend.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Multilayer Modularity Optimization (MMO)** | Required by FR-003 to capture dynamic reconfiguration and stabilize community detection while fitting CPU constraints. MMO constructs a supra-graph and optimizes globally, reducing complexity from O(N_windows * N_iterations) to O(N_subjects * N_layers). | Sliding-window Louvain with per-window consensus is computationally prohibitive for large-scale datasets involving numerous iterations, windows, and subjects. and may artificially suppress dynamics. |
| **Motion-Stratified Sensitivity Analysis** | Required by FR-008 to control for non-linear motion confounds. Stratifying by motion level and checking robustness ensures the association is not driven by residual motion artifacts. | Simple linear regression of mean FD is insufficient to remove non-linear motion effects in fMRI. |
| **Bonferroni Correction for Window Length** | Required by FR-009 to correct for multiple testing inherent in the sensitivity analysis (window lengths). | Uncorrected p-values in sensitivity analysis increase the risk of false discovery. |
| **Memory Monitoring** | Required by FR-010 and SC-004 to ensure feasibility on GitHub Actions free tier. | No monitoring would risk silent OOM crashes and failed CI jobs. |
| **Permutations** | Required for robust p-value estimation (min p=0.0002) in a small sample (N=100). | 1,000 permutations (min p=0.001) may be insufficient for reliable inference in exploratory neuroscience. |
