# Implementation Plan: Investigating the Impact of Network Structure on Neural Avalanche Dynamics

**Branch**: `001-network-structure-avalanche-dynamics` | **Date**: 2026-06-24 | **Spec**: `specs/001-network-structure-avalanche-dynamics/spec.md`
**Input**: Feature specification from `/specs/001-network-structure-avalanche-dynamics/spec.md`

## Summary

This project investigates the associational relationship between anatomical brain network properties (degree, clustering, rich-club) derived from diffusion-MRI and *simulated* neural avalanche statistics (size, duration, power-law exponents). Due to the unavailability of verified public datasets containing matched dMRI and resting-state EEG for the same participants, the study adopts a **simulation-based approach**. Structural connectomes from verified dMRI data (OpenNeuro) will be used to generate synthetic EEG time-series via a linear neural mass model, from which avalanche statistics are computed. The implementation will build a CPU-tractable pipeline to process dMRI, simulate avalanches, and perform rigorous statistical testing (Spearman correlation, permutation tests, VIF diagnostics) to validate structure-simulation coupling hypotheses.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `mne`, `networkx`, `powerlaw`, `scipy`, `pandas`, `numpy`, `scikit-learn`, `huggingface_hub`, `openneuro-py`, `bctpy`  
**Storage**: Local filesystem (`data/raw`, `data/processed`, `data/results`) with CSV/Parquet/JSON formats.  
**Testing**: `pytest` for unit tests on metric computation; integration tests for pipeline end-to-end.  
**Target Platform**: GitHub Actions `ubuntu-latest` (2 vCPU, ~7 GB RAM, CPU-only).  
**Project Type**: Computational Research Pipeline / CLI.  
**Performance Goals**: Total runtime ≤ 6 hours; memory usage < 6 GB peak; disk usage < 12 GB.  
**Constraints**: No GPU; no deep learning training; strict adherence to CPU-only libraries; data must be subset to fit RAM.  
**Scale/Scope**: Processing of a verified subset of participants (target: a representative cohort) from OpenNeuro ds003813 for structural connectomes.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Constitution Principle | Compliance Status | Action / Note |
| :--- | :--- | :--- |
| **I. Reproducibility** | **Pass** | All scripts will pin random seeds (`np.random.seed`, `random.seed`). Dependencies pinned in `requirements.txt`. Simulation parameters are deterministic. |
| **II. Verified Accuracy** | **Pass** | Dataset URLs restricted to verified sources (OpenNeuro ds003813). No fabricated URLs. Simulation logic is documented. |
| **III. Data Hygiene** | **Pass** | Raw data stored in `data/raw` with checksums. Derived data in `data/processed` with provenance metadata. No in-place edits. |
| **IV. Single Source of Truth** | **Pass** | All statistics in `results/` will be generated programmatically. No manual entry in reports. |
| **V. Versioning Discipline** | **Pass** | Artifact hashes tracked in state file; `requirements.txt` ensures version lock. |
| **VI. Neuroimaging Data Integrity** | **Pass** | MRtrix/MNE versions pinned. Raw files preserved; derived matrices/epochs saved as new files. |
| **VII. Statistical Rigor** | **Pass** | Plan includes Spearman correlation, a shuffle permutation test with a sufficient number of iterations, VIF diagnostics, and sensitivity sweeps as mandated. |

## Project Structure

### Documentation (this feature)

```text
specs/001-network-structure-avalanche-dynamics/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   └── output.schema.yaml
└── tasks.md             # Phase 2 output (generated later)
```

### Source Code (repository root)

```text
code/
├── __init__.py
├── config.py            # Paths, seeds, hyperparameters
├── data/
│   ├── __init__.py
│   ├── download.py      # Fetch from verified OpenNeuro sources
│   ├── preprocess_dMRI.py # MRtrix3 workflow: HCP 360-parcel parcellation (FR-001)
│   └── simulate_EEG.py  # Neural mass model simulation from structural graphs
├── analysis/
│   ├── __init__.py
│   ├── metrics.py       # Network metrics (degree, clustering, rich-club)
│   ├── avalanches.py    # Power-law fitting, z-score thresholding (FR-004, FR-011)
│   └── stats.py         # Correlation, permutation (FR-007), VIF (FR-009), sensitivity
├── main.py              # Orchestration script
└── requirements.txt

tests/
├── test_metrics.py
├── test_avalanches.py
└── test_stats.py
```

**Structure Decision**: Single `code/` directory with modular sub-packages (`data`, `analysis`) to maintain simplicity for a research pipeline. No separate frontend/backend.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Simulation Pipeline** | Required because matched empirical dMRI+EEG data is unavailable. | A single-modality study cannot answer the research question. |
| **Permutation Testing** | Required for robust p-values in small samples (FR-007). | Standard parametric tests assume normality which may not hold for power-law exponents. |
| **Sensitivity Sweep** | Required to validate threshold robustness (FR-008). | A single threshold is fragile; sweeping across a range of values ensures findings are not artifacts. |
| **MRtrix3 Workflow** | Required for HCP 360-parcel parcellation (FR-001). | Default parcellations do not meet spec requirements. |

## Data Transformation Logic

- **Input**: Parquet/CSV from OpenNeuro (dMRI tractography results).
- **Process**: `preprocess_dMRI.py` converts raw tractography to 360-parcel adjacency matrices using MRtrix3.
- **Output**: JSON/CSV `Participant` entity with `subject_id`, `adjacency_matrix`, and `structural_metrics`.
- **Simulation**: `simulate_EEG.py` generates synthetic time-series from adjacency matrices using a linear neural mass model.

## Null Result Protocol

If the verified dMRI dataset (OpenNeuro) contains fewer than 10 usable subjects after preprocessing:
1. The pipeline halts the correlation analysis.
2. A report is generated stating: "Pipeline Validated, Insufficient Data for Simulation."
3. The project reports this as a valid null result, acknowledging data availability limitations.

This protocol ensures reproducibility and transparency even when the primary hypothesis cannot be tested due to data absence.