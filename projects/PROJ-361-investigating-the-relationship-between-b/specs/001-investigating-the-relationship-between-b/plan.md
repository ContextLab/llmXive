# Implementation Plan: Investigating the Relationship Between Brain Network Topology and Susceptibility to Visual Illusions

**Branch**: `001-investigating-relationship-between-brain-network` | **Date**: 2026-06-27  
**Spec**: `specs/001-investigating-the-relationship-between-b/spec.md`

## Summary

This project implements an observational correlational study linking resting-state functional brain network topology to susceptibility for visual illusions (Müller-Lyer and Ponzo). The technical approach involves: (1) downloading and preprocessing resting-state fMRI data from the **OpenNeuro ds004285** dataset using fMRIPrep, (2) extracting BOLD time series from Schaefer 200 ROIs, (3) computing five graph-theoretic topology metrics, (4) reducing these metrics via PCA to orthogonal components (Integration, Segregation) to address collinearity, and (5) performing FDR-corrected correlation analysis against psychophysically measured illusion scores available in the same dataset. The study relies entirely on real biological data from OpenNeuro; synthetic data is NOT used for hypothesis validation.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `nipype` (fMRIPrep interface), `nibabel`, `numpy`, `pandas`, `networkx`, `bctpy` (Brain Connectivity Toolbox), `scikit-learn`, `matplotlib`, `seaborn`, `openneuro-py`, `pytest`.  
**Storage**: Local file system (`data/raw/` -> `RawFMRI` entity, `data/processed/` -> `PreprocessedFMRI`/`TimeSeries` entities), SQLite for session tracking.  
**Testing**: `pytest` (unit/integration), `pandas.testing` for data schema validation.  
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 CPU, 7GB RAM).  
**Project Type**: Computational Neuroscience / Data Analysis Pipeline.  
**Performance Goals**: Pipeline must complete preprocessing and analysis for a **subset of 5 subjects** within 6 hours on CPU-only hardware for CI validation. Full cohort processing (n=50) is designed to be streamable but requires external compute (local/cloud) for full batch execution due to fMRIPrep runtime.  
**Constraints**: No GPU; no deep learning model training; data subset to fit 7GB RAM; strict adherence to fMRIPrep containerized preprocessing (pinned version `poldracklab/fmriprep:23.1.0`).  
**Scale/Scope**: 50 subjects (OpenNeuro ds004285), 200 ROIs, 5 topology metrics reduced to 2-3 PCA components, 2 behavioral measures.

> Note: As per reviewer `eric-kandel-simulated`, this study operates at the **systems/network level** of explanation. It explicitly frames findings as associational correlations between network topology and perceptual bias. It does not claim to trace mechanisms to the synaptic level, acknowledging this as a limitation of the current scope and a direction for future mechanistic modeling.

## Constitution Check

This plan adheres to the following principles from `projects/PROJ-361-investigating-the-relationship-between-b/.specify/memory/constitution.md`:

- **I. Reproducibility**: All random seeds (Louvain, PCA, data splits) are pinned. fMRIPrep is containerized with a **pinned tag** (`poldracklab/fmriprep:23.1.0`). `requirements.txt` is pinned. External datasets (OpenNeuro ds004285) are fetched from the canonical source on every run.
- **II. Verified Accuracy**: All dataset citations refer to the `# Verified datasets` block. The primary data source is **OpenNeuro ds004285**, which has a verified URL and contains both the required fMRI and behavioral data.
- **III. Data Hygiene**: Raw data is checksummed upon download. Preprocessed outputs are new files. No PII is stored; only anonymized Study IDs.
- **IV. Single Source of Truth**: All statistics in the final report are generated from `data/processed/` via `code/` scripts; no manual entry.
- **V. Versioning**: Artifacts carry content hashes. The `state/` file is updated by the `code/utils/update_state.py` script, triggered automatically by a `git_hooks/pre-commit` hook. The plan explicitly describes this mechanism: every research-stage artifact change updates the project's `state/...yaml` `updated_at` timestamp and records the new hash.
- **VI. Neuroimaging Preprocessing Rigor**: fMRIPrep (pinned version) is mandated for all fMRI data. Motion correction and nuisance regression are standard.
- **VII. Statistical Correction Discipline**: Benjamini-Hochberg FDR is applied to all correlation tests. Uncorrected p-values are not reported as significant.

## Project Structure

### Documentation (this feature)
```text
specs/001-investigating-the-relationship-between-b/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
```

### Source Code (repository root)
```text
projects/PROJ-361-investigating-the-relationship-between-b/
├── data/
│   ├── raw/             # Downloaded fMRI NIfTI files (RawFMRI entity)
│   ├── processed/       # Preprocessed NIfTI, time-series matrices, metrics (PreprocessedFMRI, TimeSeries entities)
│   └── behavioral/      # CSV exports from psychophysical task (IllusionScore entity)
├── code/
│   ├── preprocessing/
│   │   ├── download_openneuro.py
│   │   ├── run_fmriprep.sh
│   │   └── extract_timeseries.py
│   ├── topology/
│   │   ├── compute_connectivity.py
│   │   ├── compute_metrics.py
│   │   └── reduce_dimensions.py  # PCA for collinearity
│   ├── analysis/
│   │   ├── correlation_analysis.py
│   │   └── generate_plots.py
│   ├── behavioral/
│   │   ├── export_scores.py      # Extract from OpenNeuro
│   │   └── validate_schema.py
│   ├── utils/
│   │   ├── config.py
│   │   └── update_state.py       # Versioning mechanism (Constitution Principle V)
│   └── main.py           # Pipeline orchestrator
├── git_hooks/
│   └── pre-commit        # Hook to trigger update_state.py
├── tests/
│   ├── unit/             # Uses synthetic data for arithmetic validation ONLY
│   ├── integration/
│   └── contract/
├── requirements.txt
└── README.md
```

**Structure Decision**: A modular, single-repo structure is chosen to facilitate the end-to-end pipeline execution on CI. The separation into `preprocessing`, `topology`, `analysis`, and `behavioral` directories ensures clear ownership of the distinct phases required by the user stories (US-1 to US-4). The `git_hooks` directory contains the mechanism to satisfy Constitution Principle V.

## Complexity Tracking

No complexity violations found. The project scope is contained within the computational limits of a free-tier runner by limiting CI validation to 5 subjects and using CPU-tractable methods (fMRIPrep, BCT, Pearson correlation). The full 50-subject analysis is designed to be streamable but acknowledged as requiring external compute for full batch execution.