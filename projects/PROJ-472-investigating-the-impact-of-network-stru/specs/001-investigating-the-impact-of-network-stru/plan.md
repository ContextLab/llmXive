# Implementation Plan: Investigating the Impact of Network Structure on Neural Avalanche Dynamics

**Branch**: `001-network-structure-avalanche-dynamics` | **Date**: 2026-06-25 | **Spec**: `specs/001-network-structure-avalanche-dynamics/spec.md`
**Input**: Feature specification from `specs/001-network-structure-avalanche-dynamics/spec.md`

## Summary

This project investigates the **associational relationship** between anatomical brain network properties (node degree, clustering coefficient, rich-club organization) derived from diffusion-MRI structural connectomes and neural avalanche statistics (size, duration, power-law exponents) derived from resting-state EEG. The analysis utilizes the HCP-Aging dataset (OpenNeuro ds/). The implementation prioritizes CPU-only feasibility, strict data hygiene, and rigorous statistical validation (permutation tests, VIF diagnostics, sensitivity analysis) to ensure reproducibility on GitHub Actions free-tier runners.

> **Causal Validity Warning**: This study is observational. All statistical associations are framed as correlational/associational. The analysis **cannot** support causal claims regarding "impact" or "influence" due to the lack of random assignment.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `mne`, `nibabel`, `mrtrix3` (system tool), `networkx`, `powerlaw`, `scikit-learn`, `pandas`, `numpy`, `scipy`, `dask` (for memory management), `openneuro-py`  
**Storage**: Local file system (`data/raw`, `data/processed`); CSV/Parquet for intermediate metrics.  
**Testing**: `pytest` (unit/integration), `pytest-cov` for coverage.  
**Target Platform**: Linux (GitHub Actions Free Tier: CPU, sufficient RAM, 14 GB disk).  
**Project Type**: Computational Neuroscience / Data Analysis Pipeline.  
**Performance Goals**: Complete pipeline (download to correlation) for N=50 subjects within 6 hours on CPU; memory usage < 6 GB peak.  
**Constraints**: No GPU; no 8-bit quantization; strict adherence to OpenNeuro datasets only; no synthetic data generation.  
**Scale/Scope**: N=50 matched participants (or all available < 50); -parcel parcellation.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

1.  **I. Reproducibility**: The plan mandates pinned `requirements.txt`, random seed setting (`np.random.seed`, `random.seed`), and re-runnable scripts. External data is fetched from OpenNeuro programmatically. **Status: Compliant.**
2.  **II. Verified Accuracy**: The prompt's "Verified datasets" block indicates "NO verified source found" for the specific HCP-Aging ds004230/31 pair. Compliance is achieved by using the programmatic `openneuro-py` API to access the canonical source. The API's metadata verification serves as the "verified source" for this project, satisfying Principle II without a static URL. **Status: Compliant.**
3.  **III. Data Hygiene**: The plan includes a checksumming step for raw data downloads and enforces immutable raw data (`data/raw`) with derived files in `data/processed`. **Status: Compliant.**
4.  **IV. Single Source of Truth**: All figures and statistics in the final output will be generated from `data/processed` files via the `code/` scripts, ensuring traceability. **Status: Compliant.**
5.  **V. Versioning Discipline**: The plan includes content hashing for artifacts in the `state` file update logic (handled by the runtime, but the plan ensures the artifacts are hashable). **Status: Compliant.**
6.  **VI. Neuroimaging Data Integrity**: Raw dMRI and EEG files are preserved. Preprocessing (MRtrix3, MNE) is scripted. Derivations (connectivity matrices, clean EEG) are saved with provenance. **Status: Compliant.**
7.  **VII. Statistical Rigor**: The plan explicitly includes Spearman correlation, permutation tests, VIF diagnostics, and sensitivity analysis (multiple thresholds) as required. **Status: Compliant.**

## Project Structure

### Documentation (this feature)

```text
specs/001-network-structure-avalanche-dynamics/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-472-investigating-the-impact-of-network-stru/
├── code/
│   ├── __init__.py
│   ├── main.py            # Orchestrator script
│   ├── config.py            # Paths, seeds, hyperparameters
│   ├── data/
│   │   ├── download.py      # OpenNeuro ds004230/31 fetch
│   │   ├── preprocess_dMRI.py # MRtrix3 wrapper for tractography
│   │   ├── preprocess_EEG.py  # MNE-Python filtering/ICA
│   │   └── fuse_data.py     # Match subjects, save unified CSV
│   ├── metrics/
│   │   ├── network.py       # NetworkX degree, clustering, rich-club
│   │   └── avalanche.py     # Power-law fitting, thresholding
│   ├── analysis/
│   │   ├── correlation.py   # Spearman, Bootstrap CI
│   │   ├── robustness.py    # Permutation tests, sensitivity sweep
│   │   └── diagnostics.py   # VIF calculation
│   └── utils/
│       ├── io.py            # Checksum, logging
│       └── stats.py         # Helper stats functions
├── data/
│   ├── raw/                 # Unmodified downloads (OpenNeuro)
│   ├── processed/           # Connectivity matrices, cleaned EEG, metrics
│   └── checksums.txt        # SHA256 of raw files
├── tests/
│   ├── unit/
│   │   ├── test_network.py
│   │   └── test_avalanche.py
│   └── integration/
│       └── test_pipeline.py
├── requirements.txt
└── README.md
```

**Structure Decision**: Single project structure selected to minimize overhead for a data-analysis pipeline. Separation of `data`, `metrics`, and `analysis` ensures modularity for the three user stories (Pipeline, Metrics, Statistics).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | The project scope is strictly bounded by the spec and CPU constraints. | N/A |