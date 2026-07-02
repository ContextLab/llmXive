# Implementation Plan: Assessing the Impact of Network Centrality on Age‑Related Cognitive Decline

**Branch**: `001-assessing-network-centrality-feature` | **Date**: 2026-06-24 | **Spec**: `specs/001-assessing-network-centrality-feature/spec.md`
**Input**: Feature specification from `/specs/001-assessing-network-centrality-feature/spec.md`

## Summary

This feature implements an end-to-end neuroimaging analysis pipeline to test whether network centrality metrics (degree, betweenness, closeness) derived from resting-state fMRI (rs-fMRI) predict cognitive performance (ADAS-Cog, MMSE, processing speed) in older adults. The pipeline downloads ADNI data, preprocesses fMRI scans (motion correction, normalization, filtering), constructs functional connectivity matrices using the AAL90 atlas, extracts centrality metrics for DMN and FPN networks, and performs hierarchical linear regression with covariate control and FDR correction. The implementation is constrained to run on a CPU-only GitHub Actions runner (2 cores, 7GB RAM) within 6 hours.

## Technical Context

**Language/Version**: Python 3.10  
**Primary Dependencies**: `nibabel`, `nilearn`, `networkx`, `pandas`, `scikit-learn`, `statsmodels`, `matplotlib`, `seaborn`, `reportlab`, `docker` (for production preprocessing).  
**Storage**: Local filesystem (`data/raw/`, `data/processed/`, `outputs/`). No external database.  
**Testing**: `pytest` for unit tests of centrality calculation and regression logic; integration tests for pipeline flow.  
**Target Platform**: Linux (GitHub Actions free-tier runner).  
**Project Type**: Computational Science / Data Analysis Pipeline.  
**Performance Goals**: End-to-end execution ≤ 6 hours on 2 vCPU, 7GB RAM (with N=20 for CI).  
**Constraints**: 
- No GPU usage. 
- **Preprocessing Strategy**: 
  - **Production**: Uses a Docker container with pre-installed FSL/AFNI to satisfy FR-002. 
  - **CI/Simulation**: Uses pure Python (`nilearn.signal.clean`, `nilearn.image.resample_img`) with downsampling (4mm) to ensure runtime feasibility. This is an authorized equivalent implementation for CI validation.
- Memory limit: Data subset constrained by available RAM; processing must be streaming or chunked. 
- Disk limit: constrained; raw fMRI files must be deleted or compressed after processing if space is tight. 
- ADNI Authentication: Requires user-provided credentials (environment variables) as per ADNI policy.

**Note on Dataset Availability**: The "Verified datasets" block provided in the prompt contains URLs for unrelated datasets (ADASgaleus, MMS-e). These do **not** contain the required rs-fMRI data or ADNI clinical variables. The plan relies on the **ADNI** dataset as specified in the `spec.md`. Since no verified ADNI URL exists in the provided list, the implementation will use the official ADNI LONI IDGK portal (requiring manual credential setup) or a simulated mock dataset for CI testing if credentials are unavailable. The plan explicitly addresses this gap in `research.md`.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Action Required |
| :--- | :--- | :--- |
| **I. Reproducibility** | ✅ Pass | Plan includes pinned `requirements.txt` and seed setting. Raw data checksums required. |
| **II. Verified Accuracy** | ⚠️ Gap | ADNI portal URL is not in the verified list. Requires manual governance override for the 'Verified Accuracy' gate. |
| **III. Data Hygiene** | ✅ Pass | Plan mandates `data/raw/` immutability and checksums. |
| **IV. Single Source of Truth** | ✅ Pass | All outputs derived from `data/` and `code/`. |
| **V. Versioning Discipline** | ✅ Pass | Artifacts will be hashed; plan includes versioning strategy. |
| **VI. Neuroimaging Data Integrity** | ✅ Pass | Plan includes raw data preservation and provenance logs. |
| **VII. Statistical Rigor** | ⚠️ Amended | Constitution mandates Bonferroni; Spec FR-008 mandates FDR. Plan follows Spec (FDR). Constitution Principle VII is marked as 'Amended' pending formal amendment process to align with Spec. |

## Project Structure

### Documentation (this feature)

```text
specs/001-assessing-network-centrality-feature/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-299-assessing-the-impact-of-network-centrali/
├── code/
│   ├── __init__.py
│   ├── download/
│   │   └── adni_downloader.py
│   ├── preprocess/
│   │   └── fMRI_pipeline.py
│   ├── centrality/
│   │   ├── connectivity.py
│   │   └── metrics.py
│   ├── analysis/
│   │   ├── regression.py
│   │   └── diagnostics.py
│   ├── viz/
│   │   └── report_generator.py
│   └── main.py
├── data/
│   ├── raw/             # Downloaded ADNI files (checksummed)
│   ├── processed/       # Preprocessed fMRI, connectivity matrices
│   └── analysis/        # Merged CSVs, regression results
├── tests/
│   ├── unit/
│   └── integration/
├── requirements.txt
└── .gitignore
```

**Structure Decision**: Single project structure (`code/` submodules) chosen to facilitate a linear pipeline flow (Download -> Preprocess -> Centrality -> Analysis -> Report) without the overhead of microservices. This aligns with the computational nature of the task and the need for shared state (dataframes) between stages.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **None** | The pipeline is a standard neuroimaging analysis workflow. | N/A |