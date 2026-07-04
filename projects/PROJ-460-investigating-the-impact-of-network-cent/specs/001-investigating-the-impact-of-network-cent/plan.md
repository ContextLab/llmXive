# Implementation Plan: Investigating Network Centrality in ASD Resting-State fMRI

**Branch**: `001-investigate-asd-centrality` | **Date**: 2026-06-24 | **Spec**: `specs/001-investigating-asd-centrality/spec.md`
**Input**: Feature specification from `/specs/001-investigating-asd-centrality/spec.md`

## Summary

This feature implements a neuroimaging analysis pipeline to investigate the impact of network centrality on resting-state functional connectivity in Autism Spectrum Disorder (ASD). The system downloads ABIDE fMRI data from the verified fcon_1000 repository, preprocesses it with fMRIPrep (including motion scrubbing and global signal regression), constructs functional connectivity graphs using the Schaefer atlas, computes centrality metrics (degree, betweenness, eigenvector), and performs statistical group comparisons using Network-Based Statistic (NBS) and FDR correction. The analysis is strictly observational, CPU-tractable, and designed to run within GitHub Actions free-tier constraints (2 CPU, 7GB RAM). All results are computed at runtime from real data; no simulated or hardcoded metrics are used.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: 
- `nilearn` (fMRI preprocessing/visualization)
- `networkx` (graph centrality metrics)
- `nbs` (Network-Based Statistic) or `nibabel` + custom permutation testing
- `scikit-learn` (classification, statistics)
- `pandas`, `numpy` (data manipulation)
- `docker` (fMRIPrep execution)
- `abide` (verified HuggingFace loader for ABIDE metadata and NIfTI paths)
**Storage**: Local filesystem (`data/raw`, `data/processed`); no external DB.
**Testing**: `pytest` (unit/integration), `pytest-cov` (coverage).
**Target Platform**: Linux (GitHub Actions free-tier runner).
**Project Type**: Computational neuroscience pipeline / CLI.
**Performance Goals**: 
- Preprocessing: < 4 hours for sample batch (due to 6h job limit, full run requires sampling).
- Centrality computation: < 30 minutes for N=200 participants.
- Memory: < 6GB peak RAM (via chunked processing).
**Constraints**: 
- No GPU/CUDA.
- **Strict fMRIPrep requirement**: The pipeline MUST use the fMRIPrep Docker container with a specific version tag. No fallback to pre-processed data or alternative pipelines is permitted to ensure reproducibility (Constitution I & VI). If fMRIPrep cannot be executed, the pipeline halts with an error.
- Dataset size limited to a manageable disk footprint; full ABIDE is too large, so strict sampling or verified subset usage is required.
**Scale/Scope**: N ≥ 100 ASD, N ≥ 100 Control (if data available in verified subset); 400 ROIs.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. All metrics are computed dynamically at runtime.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
| :--- | :--- | :--- |
| **I. Reproducibility** | PASS | Plan mandates pinned seeds, Docker versioning, and `requirements.txt`. No fallbacks to non-reproducible data. |
| **II. Verified Accuracy** | PASS | Plan restricts dataset sources to the verified fcon_1000/ABIDE official repository and `abide` package. No fabricated URLs. |
| **III. Data Hygiene** | PASS | Raw data preserved in `data/raw`; checksums recorded; no in-place modification. |
| **IV. Single Source of Truth** | PASS | All figures/stats trace to `data/` and `code/`; no hand-typed numbers in paper. |
| **V. Versioning Discipline** | PASS | Artifacts carry content hashes; state file updated on change. |
| **VI. Neuroimaging Data Integrity** | PASS | Raw scans stored unchanged; fMRIPrep version/params logged; derived data new files. |
| **VII. Statistical Rigor** | PASS | Plan mandates NBS/permutation testing, FDR correction, effect sizes, and collinearity diagnostics. |

**Action Required**: The "FABRICATED-RESULT" concern is addressed by ensuring **no hardcoded metrics** are used. All results (accuracy, centrality values) must be computed at runtime from real data. The plan explicitly defers specific numeric thresholds to the `research.md` phase where real data verification occurs.

## Project Structure

### Documentation (this feature)

```text
specs/001-investigating-asd-centrality/
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
├── 01_download.py           # ABIDE data fetch & checksum (uses `abide` package)
├── 02_preprocess.py         # fMRIPrep wrapper / execution (strict Docker)
├── 03_connectivity.py       # Time-series extraction, Correlation matrix, Scrubbing
├── 04_centrality.py         # Graph construction, Centrality metrics
├── 05_analysis.py           # NBS, FDR, Sensitivity analysis
├── 06_classification.py     # Logistic Regression, Nested CV
├── 07_visualize.py          # Nilearn brain plots
├── config.py                # Paths, seeds, thresholds (no hardcoded results)
└── requirements.txt         # Pinned dependencies

data/
├── raw/                     # Unmodified ABIDE data (or verified subset)
├── processed/               # fMRIPrep outputs, Time-series, Matrices
└── results/                 # Statistical outputs, Plots, Classifiers

tests/
├── unit/                    # Logic tests (e.g., centrality calc)
├── integration/             # Pipeline flow tests
└── contract/                # Schema validation tests
```

**Structure Decision**: Single `code/` directory with modular scripts ordered by pipeline dependency. This ensures data flows linearly from download -> preprocess -> analysis, satisfying the "Data before Task" ordering rule.

## Contract Mapping

To ensure internal coherence, each pipeline step is mapped to its corresponding contract schema:

| Pipeline Script | Output Artifact | Contract Schema |
| :--- | :--- | :--- |
| `01_download.py` | `data/raw/metadata.parquet` | `contracts/dataset_schema.schema.yaml` |
| `02_preprocess.py` | `data/processed/preprocessed/*.nii.gz` | `contracts/participant.schema.yaml` (QC logs) |
| `03_connectivity.py` | `data/processed/timeseries/*.csv` | `contracts/statistical_results_schema.schema.yaml` (intermediate) |
| `04_centrality.py` | `data/processed/centrality/*.csv` | `contracts/centrality_metrics_schema.schema.yaml` |
| `05_analysis.py` | `data/processed/results/*.csv` | `contracts/stats_schema.schema.yaml` |
| `06_classification.py` | `data/processed/classification/*.json` | `contracts/classification_results.schema.yaml` |
| `05_analysis.py` (Sensitivity) | `data/processed/results/sensitivity/*.json` | `contracts/centrality_sensitivity.schema.yaml` |

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **fMRIPrep Docker** | Required for standardized, reproducible neuroimaging preprocessing (Constitution VI). | Manual preprocessing (fsl/fslmaths) is error-prone and violates reproducibility standards. |
| **Motion Scrubbing & GSR** | Required to mitigate motion artifacts (methodology concern). | Ignoring motion leads to spurious correlations and invalid centrality claims. |
| **Network-Based Statistic (NBS)** | Required to account for spatial autocorrelation and metric collinearity (methodology concern). | Simple t-tests are underpowered and prone to false positives in network data. |
| **Nested Cross-Validation** | Required to prevent double-dipping in classification (scientific soundness concern). | Simple CV on selected features inflates accuracy and invalidates diagnostic claims. |
| **Sensitivity Analysis** | Required by FR-009 to validate threshold robustness. | Single-threshold analysis is scientifically insufficient for network topology studies. |
| **Collinearity Diagnostics** | Required by FR-010 (centrality metrics are mathematically correlated). | Ignoring collinearity would lead to false claims of "independent" effects. |