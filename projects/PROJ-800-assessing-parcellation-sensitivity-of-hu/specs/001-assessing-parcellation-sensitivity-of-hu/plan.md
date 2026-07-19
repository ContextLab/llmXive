# Implementation Plan: Assessing Parcellation Sensitivity of Hub Resilience in Healthy Connectomes

**Branch**: `001-assessing-parcellation-sensitivity` | **Date**: 2026-07-09 | **Spec**: `specs/001-assessing-parcellation-sensitivity/spec.md`

## Summary

This project implements a reproducible pipeline to assess the sensitivity of "hub resilience" (stability of hub identification) across three distinct parcellation resolutions (AAL-90, Schaefer-200, Schaefer-400) using healthy adult fMRI data. The technical approach involves downloading raw fMRI time-series from an open repository (OpenNeuro ds000177), generating three adjacency matrices per subject via distinct parcellation pipelines, computing degree and betweenness centrality, defining hubs via a top-10% threshold, and quantifying overlap using **Voxel-Wise Hub Mask Overlap** and **Excess Overlap** (cardinality-normalized Jaccard). A **Spatial Spin Test** validates statistical significance. The implementation is strictly CPU-first, targeting GitHub Actions free-tier constraints (limited cores and memory, 6h limit), utilizing streaming for data ingestion and efficient graph libraries (NetworkX, NumPy).

**Methodological Note**: The Functional Requirements (FR-005, FR-009) in the spec mandate "majority-vote spatial overlap" and "Spearman rank correlation" between mapped nodes. However, the Convergence Panel identified these as methodologically flawed (construct validity, undefined vector lengths, cardinality bias). This Plan **supersedes** those specific FRs for the primary analysis, adopting the scientifically valid **Voxel-Wise Hub Mask Overlap** and **Excess Overlap** metrics. The node-mapping approach is retained only as a secondary, descriptive analysis with explicit warnings about its limitations and a weighted aggregation scheme to mitigate spatial bias.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `nibabel` (NIfTI I/O), `nilearn` (atlas loading, signal extraction), `networkx` (graph metrics), `numpy`, `pandas`, `scipy` (stats), `matplotlib`, `seaborn`, `datasets` (HuggingFace streaming), `tqdm`, `nibabel` (for voxel-wise masking).  
**Storage**: Local file system (`data/raw`, `data/processed`, `data/results`). No external database.  
**Testing**: `pytest` with `pytest-cov`. Unit tests for centrality logic, overlap functions, and spatial mapping. Integration tests for the full pipeline on a single subject.  
**Target Platform**: Linux (GitHub Actions Runner).  
**Performance Goals**: Process N=100 subjects within 6 hours; peak RAM < 7 GB.  
**Constraints**: No GPU usage for graph metrics; strict adherence to open, downloadable datasets; no synthetic data generation.  
**Scale/Scope**: A number of subjects, 3 resolutions (90, 200, 400 nodes), 3 centrality metrics, 1 permutation test (1000 iters).

> **Deferred Values**: The specific dataset ID (ds000177) is confirmed. The exact hub threshold percentage is fixed at [deferred] per spec, but the sensitivity analysis (FR-008) sweeps this.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Action Required |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Plan mandates `random_seed` pinning in `code/`, streaming from canonical sources, and `requirements.txt` pinning. |
| **II. Verified Accuracy** | **PASS** | Plan requires citations in `research.md` to be verified against primary sources before artifact write. **Blocking Mechanism**: The `Reference-Validator` agent runs as a CI pre-commit hook or `pre-build` step. If any citation is unverified, the hook exits with a non-zero status code, **blocking** the build and preventing artifact write. |
| **III. Data Hygiene** | **PASS** | Plan includes checksumming steps for `data/raw` and `data/processed` artifacts; no in-place modification. |
| **IV. Single Source of Truth** | **PASS** | Plan defines `data/results` as the sole source for statistics; figures generated directly from these results. |
| **V. Versioning Discipline** | **PASS** | **Task T030** (see below) implements `code/utils/update_state.py` to update the project state YAML with content hashes and timestamps for every artifact change. |
| **VI. Parcellation Resolution Invariance** | **PASS** | Plan explicitly tracks resolution (AAL/Schaefer) in all output filenames and metadata; comparisons only via overlap stats. |
| **VII. Set-Theoretic Hub Validation** | **PASS** | Plan defines hubs strictly as top [deferred] sets; validation via Voxel-Wise Overlap and Excess Overlap, not mathematical derivation. |

## Project Structure

### Documentation (this feature)

```text
projects/PROJ-800-assessing-parcellation-sensitivity-of-hu/specs/001-assessing-parcellation-sensitivity/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── adjacency_matrix.schema.yaml
│   ├── hub_set.schema.yaml
│   ├── overlap_result.schema.yaml
│   └── hub_analysis_output.schema.yaml
└── tasks.md             # Phase 2 output (generated by /speckit-tasks)
```

### Source Code (repository root)

```text
projects/PROJ-800-assessing-parcellation-sensitivity-of-hu/
├── data/
│   ├── raw/                 # Downloaded NIfTI files (streamed/chunked)
│   ├── processed/           # Adjacency matrices (.npy), centrality scores (.csv), spatial maps (.npy)
│   └── results/             # Overlap stats, p-values, plots, validation_report.json
├── code/
│   ├── __init__.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── adjacency_matrix.py    # Class for matrix handling [Pending: T007]
│   │   ├── hub_set.py             # Class for hub definition [Pending: T007]
│   │   └── centrality_score.py    # Class for centrality metrics [Pending: T007]
│   ├── pipelines/
│   │   ├── __init__.py
│   │   ├── download.py            # Data acquisition (streaming)
│   │   ├── parcellate.py          # Atlas application
│   │   ├── centrality.py          # Graph metric computation
│   │   └── overlap.py             # Jaccard/Dice, Excess Overlap, Spatial Spin Test
│   ├── utils/
│   │   ├── spatial_mapping.py     # Voxel-wise mask generation logic
│   │   ├── checksums.py           # Hygiene utilities
│   │   └── update_state.py        # [Pending: T030] Implements Constitution Principle V
│   └── main.py                    # Orchestration script
├── tests/
│   ├── unit/
│   │   ├── test_centrality.py     # [Pending: T020]
│   │   ├── test_overlap.py        # [Pending: T029]
│   │   └── test_spatial.py
│   └── integration/
│       └── test_pipeline_single_subject.py
├── requirements.txt
├── pyproject.toml                 # Includes black, ruff, pytest config [Pending: T003]
├── .pre-commit-config.yaml        # Includes reference-validator hook [Pending: T003]
└── README.md
```

**Structure Decision**: Single-project structure (`code/`, `data/`, `tests/`) selected to simplify dependency management for a computational pipeline. No web frontend required.

## Complexity Tracking

No violations. The complexity is inherent to the multi-resolution comparison and statistical validation, which is required by the spec.

## Resolving Unresolved Panel Concerns

The following specific concerns from the previous iteration are addressed in the plan and will be implemented in `tasks.md` and code:

1.  **Task T020 (Unit test for hub threshold logic)**: The test cases will explicitly verify `floor(90 * 0.10) == 9`, `floor(200 * 0.10) == 20`, and `floor(400 * 0.10) == 40`. Inputs will be `N=90`, `N=200`, `N=400`; expected outputs are the integer counts. **Deliverable**: `tests/unit/test_centrality.py`.
2.  **Task T029 (Jaccard/Dice function signature)**: The implementation in `code/pipelines/overlap.py` will define `def compute_overlap(set_a: set, set_b: set) -> dict: {"jaccard": float, "dice": float}`. **Deliverable**: `code/pipelines/overlap.py`.
3.  **Task T001/T004 (Directory Structure)**: The plan explicitly defines the `data/raw`, `data/processed`, `data/results`, `code/`, `tests/` hierarchy. The implementation phase will create these directories.
4.  **Task T007 (Model Classes)**: The plan includes `code/models/adjacency_matrix.py`, `hub_set.py`, and `centrality_score.py` as **Pending Implementation** files. The implementation phase will create these files with class definitions.
5.  **Task T024 (Spatial Mapping)**: The plan includes `code/utils/spatial_mapping.py` to generate `data/processed/mapping_schaefer_to_aal.npy` via **Voxel-Wise Hub Mask Overlap** (not simple index swap).
6.  **Task T017 (Validation Report)**: The plan includes a step to generate `data/results/validation_report.json` containing checksums and status of all artifacts.
7.  **Task T030 (State Update Script)**: A new task to implement `code/utils/update_state.py` which updates `state/projects/PROJ-800-assessing-parcellation-sensitivity-of-hu.yaml` with content hashes and timestamps, satisfying Constitution Principle V.
8.  **Methodological Flaws (FR-005/FR-009)**: The plan explicitly replaces the flawed "majority-vote spatial overlap" and "Spearman correlation" with **Voxel-Wise Hub Mask Overlap** and **Excess Overlap** for the primary analysis, as mandated by the Convergence Panel. The node-mapping approach is retained only as a secondary, descriptive analysis with weighted aggregation to mitigate spatial bias.
9.  **Dataset Variable Fit**: The plan confirms OpenNeuro ds000177 contains sufficient rs-fMRI data. If the dataset lacks specific edge types, the analysis will be limited to available modalities (Assumption 2).
10. **Statistical Rigor**: The plan explicitly includes Bonferroni/FDR correction for multiple comparisons and the **Spatial Spin Test** (Alexander-Bloch et al.) for permutation, addressing the spatial autocorrelation flaw.
11. **Compute Feasibility**: The plan prioritizes CPU-tractable methods (NetworkX, streaming) and explicitly avoids GPU for graph metrics. If a predefined time threshold is breached, the pipeline will automatically reduce N to a lower, safe operational limit and log a 'Power Limitation' warning.
12. **Cardinality Mismatch**: The plan introduces **Excess Overlap** (Observed Jaccard - Expected Jaccard) to normalize for set size differences.
13. **Versioning Discipline**: Task T030 explicitly implements the state update script.
14. **Verified Accuracy Gating**: The plan specifies the CI blocking mechanism (non-zero exit code) for unverified citations.

## Unresolved Panel Concerns (Addressed in Plan)

- **Dataset Variable Fit**: The plan confirms OpenNeuro ds000177 contains sufficient rs-fMRI data. If the dataset lacks specific edge types, the analysis will be limited to available modalities (Assumption 2).
- **Statistical Rigor**: The plan explicitly includes Bonferroni/FDR correction for multiple comparisons and the **Spatial Spin Test** (Alexander-Bloch et al.) for permutation, addressing the spatial autocorrelation flaw.
- **Compute Feasibility**: The plan prioritizes CPU-tractable methods (NetworkX, streaming) and explicitly avoids GPU for graph metrics. If a predefined time threshold is breached, the pipeline will automatically reduce N to a lower, safe operational limit and log a 'Power Limitation' warning.
- **Cardinality Mismatch**: The plan introduces **Excess Overlap** (Observed Jaccard - Expected Jaccard) to normalize for set size differences.
- **Versioning Discipline**: Task T030 explicitly implements the state update script.
- **Verified Accuracy Gating**: The plan specifies the CI blocking mechanism (non-zero exit code) for unverified citations.

## Pending Artifacts

The following artifacts are listed in the structure but are **not yet created**; they are deliverables for the implementation phase:
- `code/models/adjacency_matrix.py`
- `code/models/hub_set.py`
- `code/models/centrality_score.py`
- `code/utils/update_state.py`
- `tests/unit/test_centrality.py` (specifically T020)
- `code/pipelines/overlap.py` (specifically T029)
- `data/processed/mapping_schaefer_to_aal.npy` (generated by T024)
- `data/results/validation_report.json` (generated by T017)
- `pyproject.toml`, `.pre-commit-config.yaml` (T003)
- `data/raw/`, `data/processed/`, `data/results/`, `code/`, `tests/` directories (T001, T004)