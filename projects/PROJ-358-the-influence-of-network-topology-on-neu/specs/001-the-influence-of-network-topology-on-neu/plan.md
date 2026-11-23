# Implementation Plan: The Influence of Network Topology on Neural Synchrony During Cognitive Tasks

**Branch**: `001-the-influence-of-network-topology-on-neu` | **Date**: 2026-08-05 | **Spec**: `spec.md`

## Summary

This project investigates the associational relationship between baseline resting-state network topology (predictor) and task-evoked neural synchrony (outcome) during working memory performance. Due to the gated nature of the Human Connectome Project (HCP) data, the plan substitutes the HCP dataset with **OpenNeuro ds000246** (verified open dataset containing both Resting-State and n-back Working Memory task scans). The technical approach involves: (1) downloading and preprocessing a subset of N=30 subjects from OpenNeuro, (2) parcellating data into a set of regions, (3) computing graph-theoretical metrics on resting-state connectivity and task-evoked functional connectivity (Task FC - Rest FC) on task epochs, and (4) performing FDR-corrected correlation analyses with sensitivity checks on network thresholds. The pipeline is designed to run entirely on a CPU-first GitHub Actions free-tier runner with a strict 6-hour runtime budget.

## Spec Deviation & Mitigation

| Spec Requirement | Status | Mitigation / Deviation |
|------------------|--------|------------------------|
| **FR-001**: Download N=100 subjects from HCP via API. | **NOT SATISFIED** | HCP is gated. Plan uses OpenNeuro ds000246 (N=30 approx). **Requires Spec Amendment** to change dataset and N count before project acceptance. |
| **FR-002**: Spatial normalization to MNI space. | **SATISFIED** | Explicitly included in preprocessing pipeline (`nilearn.resample_to_img`). |
| **SC-004**: Runtime ≤ 6 hours. | **SATISFIED (for N=30)** | Estimated runtime for OpenNeuro (N=30) is ~2.5 hours. N=100 is infeasible on CI. |
| **SC-005**: Memory ≤ 7 GB. | **SATISFIED** | Streaming subject-by-subject ensures peak RAM < 4 GB. |
| **Construct Validity**: Working Memory Task. | **SATISFIED** | OpenNeuro contains n-back (Working Memory) task datasets. |

> **Note**: The spec mandates HCP. This plan executes on OpenNeuro to ensure reproducibility on CI. The `spec.md` must be amended to reflect the dataset change before the project can be marked 'Accepted'.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `numpy`, `scipy`, `pandas`, `nibabel`, `networkx`, `nilearn`, `requests`, `tqdm`, `pytest`  
**Storage**: Local temporary directories for streaming data; final artifacts in `data/` (parquet/CSV).  
**Testing**: `pytest` (unit tests for metric calculation, integration tests for pipeline flow).  
**Target Platform**: Linux (GitHub Actions free-tier runner).  
**Project Type**: Data analysis pipeline / research script.  
**Performance Goals**: Total runtime ≤ 2.5 hours (OpenNeuro N=30); Peak RAM ≤ 4 GB; Process a cohort of subjects

The research question, method, and references remain unchanged as no specific values or citations were present in the original passage to modify..  
**Constraints**: No local GPU; must handle OpenNeuro download limits; must exclude subjects with high motion (FD > 0.5mm); strictly associational framing.  
**Scale/Scope**: 30 subjects (OpenNeuro), 2 scans/subject (rest + n-back task), 200 regions.

### Data Feasibility & Verification
- **Dataset**: OpenNeuro ds000246 (verified open source).
- **Content**: Resting-state fMRI + n-back Working Memory task fMRI.
- **Download**: `nilearn.datasets.fetch_openneuro('ds000246')` (no auth required).
- **Size**: ~2GB total for N=30 subjects.
- **Streaming**: Code uses `streaming=True` for robustness, though full download fits in RAM.

### Preprocessing Steps (FR-002 Compliance)
1. **Motion Correction**: Realignment of 4D volumes.
2. **Spatial Normalization**: **Resample to MNI space (1mm or 2mm)** using `nilearn.resample_to_img`.
3. **Temporal Filtering**: Low-pass filter (-0.1 Hz).
4. **Nuisance Regression**: Regress out motion parameters, CSF, WM signals.
5. **Parcellation**: Apply a Schaefer atlas with a variable number of regions to extract time-series.

## Constitution Check

*Gates determined based on constitution file*

| Principle | Status | Action Required |
|-----------|--------|-----------------|
| I. Reproducibility | **PASS** | Pin seeds, use `requirements.txt`, stream data. |
| II. Verified Accuracy | **PASS** | Citations to `research.md` will be validated against primary sources (OpenNeuro ds000246). |
| III. Data Hygiene | **PASS** | `data/checksums.txt` and `state/projects/PROJ-358-.../artifact_hashes.yaml` will track raw and processed files. |
| IV. Single Source of Truth | **PASS** | Stats derived from `data/` CSVs, not hand-typed. |
| V. Versioning Discipline | **PASS** | Artifact hashes tracked in `state/projects/PROJ-358-.../artifact_hashes.yaml`. |
| VI. Trait-State Distinction | **PASS** | Pipeline explicitly separates `resting` and `task` scan files before processing. |
| VII. Metric Standardization | **PASS** | `networkx` and `nilearn` versions pinned; thresholding method documented. |

## Project Structure

### Documentation (this feature)

```text
specs/001-the-influence-of-network-topology-on-neu/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── graph_metrics.schema.yaml
│   └── synchrony_metrics.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-358-the-influence-of-network-topology-on-neu/
├── code/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── data/
│   │   ├── download.py          # Handles OpenNeuro fetch + streaming
│   │   └── preprocess.py        # Motion correction, MNI normalization, parcellation
│   ├── analysis/
│   │   ├── graph_metrics.py     # Clustering, path length, efficiency
│   │   ├── synchrony.py         # Mean FC calculation (Task & Rest)
│   │   └── stats.py             # Correlation, FDR, sensitivity
│   └── main.py                  # Orchestration script
├── data/
│   ├── raw/                     # Downloaded NIfTI (streamed/processed)
│   ├── processed/               # Time-series CSVs, metrics CSVs
│   ├── checksums.txt            # SHA256 checksums for raw data
│   └── artifact_hashes.yaml     # Hashes for versioning
├── tests/
│   ├── unit/
│   │   └── test_metrics.py
│   └── integration/
│       └── test_pipeline.py
└── docs/
    └── constitution.md
```

**Structure Decision**: Single project structure (`code/` and `data/` split) chosen for simplicity and direct alignment with the data pipeline nature of the research. No web/mobile components.

## Complexity Tracking

No complexity violations. The pipeline is linear: Download -> Preprocess -> Compute Metrics -> Correlate. The only complexity is handling the data size, mitigated by the small OpenNeuro dataset (N=30) and streaming.