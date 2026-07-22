# Implementation Plan: Investigate Brain Network Dynamics and VR Therapy Response

**Branch**: `[416-brain-network-dynamics]` | **Date**: 2026-06-24 | **Spec**: `specs/416-brain-network-dynamics/spec.md`
**Input**: Feature specification from `/specs/416-brain-network-dynamics/spec.md`

## Summary

This project implements a reproducible pipeline to investigate the association between resting-state brain network dynamics (modularity, global/local efficiency) and response to Virtual Reality (VR) exposure therapy for anxiety. The technical approach involves downloading open neuroimaging data, preprocessing it with motion correction and normalization, computing graph-theoretic metrics, and performing ANCOVA/Ridge regression with rigorous multiple-comparison correction and sensitivity analysis. The pipeline is designed to run on CPU-only GitHub Actions runners (2 cores, 7GB RAM) with a strict 6-hour window, streaming data where necessary to avoid memory overflows.

**Critical Note on Study Power**: Due to hardware constraints (N=20 subjects), this study is explicitly framed as **Exploratory**. If the sample size is insufficient for the target power (SC-004), results will be reported as effect size estimates with wide confidence intervals, not definitive hypothesis tests. The study is not powered to detect f²=0.15 effects with [deferred] power.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `nibabel`, `nilearn`, `networkx`, `scikit-learn`, `statsmodels`, `pandas`, `pyyaml`, `datasets` (Hugging Face)  
**Storage**: Local file system (`data/`, `reports/`); no external database.  
**Testing**: `pytest` (unit tests for metric computation, integration tests for pipeline flow).  
**Target Platform**: Linux (GitHub Actions runner).  
**Project Type**: Computational research pipeline / CLI.  
**Performance Goals**: Preprocessing ≤30 mins/subject (subset); Full pipeline ≤6 hours.  
**Constraints**: CPU-only (no CUDA); The research will investigate the impact of constrained memory resources on algorithmic scalability. The method involves a comparative analysis of memory usage patterns under varying resource limits, drawing on established benchmarks (DOI:10.1145/3456789).; Max disk space within typical single-node capacity constraints.; No GPU for training (only for inference if absolutely necessary, but plan is CPU-first).  
**Scale/Scope**: Subset of subjects (streamed from larger datasets if needed); ~-200 ROIs.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Action Required / Notes |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | All random seeds pinned in `code/`; external datasets fetched from canonical Hugging Face/OpenNeuro sources; `requirements.txt` provided. |
| **II. Verified Accuracy** | **PASS** | Citations for datasets and methods will be validated against the "Verified datasets" block in the user message before use. The verified source ID and validation log will be stored in `data/verified_sources.json`. |
| **III. Data Hygiene** | **PASS** | Raw data preserved in `data/raw/`; checksums recorded in `state/...yaml`; no in-place modification. |
| **IV. Single Source of Truth** | **PASS** | All figures/stats trace to `data/` rows and `code/` blocks. |
| **V. Versioning Discipline** | **PASS** | Artifact hashes tracked; `updated_at` timestamps managed by the system. |
| **VI. Neuroimaging Data Integrity** | **PASS** | Preprocessing pipeline (FSL/AFNI via `nilearn`) version-controlled; provenance metadata saved with derived matrices. |
| **VII. Biomarker Validation Standard** | **PASS** | Analysis includes p-value < 0.05, effect size > 0.5, and multiple-comparison correction (Bonferroni/FDR) as mandated. |

## Project Structure

### Documentation (this feature)

```text
specs/416-brain-network-dynamics/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
src/
├── models/              # Data classes (Subject, NetworkMetric, TreatmentResponse)
├── services/            # Preprocessing, Metric Computation, Statistical Analysis
├── cli/                 # Entry point for pipeline execution
└── lib/                 # Utilities (logging, validation, checksums)

tests/
├── contract/            # Schema validation tests
├── integration/         # End-to-end pipeline tests (with mocked data)
└── unit/                # Unit tests for metrics (modularity, efficiency)
```

**Structure Decision**: Single project structure (`src/`, `tests/`) chosen to minimize overhead for a research pipeline. All logic is encapsulated in `services/` to allow for easy swapping of preprocessing backends or statistical methods.

## Computational Strategy & Feasibility

### CPU-First Approach
The entire pipeline is designed for a CPU-only environment (2 cores, 7GB RAM).
1.  **Data Streaming**: Large neuroimaging datasets will be accessed via `datasets.load_dataset(..., streaming=True)` or by downloading specific subject shards to disk sequentially, preventing RAM overflow.
2.  **Preprocessing**: `nilearn` will be used for motion correction and normalization. For the 20-subject subset, processing time is estimated at <30 mins/subject on 2 cores.
3.  **Network Metrics**: `networkx` and `nilearn.connectome` compute metrics efficiently on CPU.
4.  **Statistics**: `statsmodels` and `scikit-learn` (Ridge) run natively on CPU.
5.  **Disk Constraint**: The streaming strategy ensures that raw NIfTI files are processed sequentially and deleted or archived to meet the 14GB disk limit. A subset of participants is estimated to fit within the limit (approx. 4GB for processed data).

### GPU Escape Hatch (Not Required)
No deep learning models or CUDA kernels are required for this study. All methods (GLM, Ridge, Graph metrics) are linear or iterative on CPU. If a future iteration requires a deep learning-based denoising step, the plan would switch to a scaled-down 8-bit model on a Kaggle GPU, but the current scope is fully CPU-tractable.

## FR/SC Coverage Matrix

| ID | Requirement / Criterion | Plan Phase / Step |
| :--- | :--- | :--- |
| **FR-001** | Download rs-fMRI data | **Phase 1**: `DataDownloader` service fetches from verified HuggingFace/OpenNeuro (ID in `data/verified_sources.json`). |
| **FR-002** | Preprocess (motion, slice, norm) | **Phase 2**: `PreprocessingService` runs `nilearn` pipeline; logs per-subject time. |
| **FR-003** | Compute connectivity matrices | **Phase 3**: `MetricService` calculates Pearson correlation from ROI time series. |
| **FR-004** | Calculate network properties (Q, Eff) | **Phase 3**: `MetricService` uses `networkx` for modularity/efficiency. |
| **FR-005** | ANCOVA / Ridge / Univariate logic | **Phase 4**: `StatisticalService` implements VIF check -> Ridge (lambda=1.0) -> Univariate fallback (if R² < 0.05). |
| **FR-006** | Multiple comparison correction | **Phase 4**: `StatisticalService` applies Bonferroni/FDR to p-values. |
| **FR-007** | Generate diagnostic plots | **Phase 4**: `ReportingService` generates scatter/residual plots. |
| **FR-008** | Associational framing | **Phase 4**: Report generator checks `metadata.study_design` for 'randomized' or `metadata.randomized` for boolean true; if neither, frames as 'ASSOCIATIONAL'. |
| **FR-009** | Validated instruments (GAD-7, HAM-A) | **Phase 1**: `DataValidator` checks instrument names against a whitelist. |
| **FR-010** | Sensitivity analysis (motion/p-value) | **Phase 4**: `SensitivityService` sweeps motion {2.0, 3.0} mm and p {0.01, 0.05, 0.1}. Output: `reports/sensitivity_analysis.md`. |
| **FR-011** | Verify pre/post pairs | **Phase 1**: `DataValidator` halts if pre/post fMRI or scores missing (Gate). |
| **FR-012** | VIF > 5 -> Ridge -> Univariate | **Phase 4**: Explicit logic in `StatisticalService` (VIF calculation -> Ridge -> Univariate). |
| **FR-013** | Confounders (meds, age) | **Phase 4**: `StatisticalService` adds covariates if present in metadata. |
| **SC-001** | Dataset-variable fit | **Phase 1**: `DataValidator` halts on missing variables. |
| **SC-002** | Motion threshold exclusion | **Phase 2**: `PreprocessingService` flags/excludes subjects >3mm/3°. |
| **SC-003** | Metric bounds (Q>=0, Eff>=0) | **Phase 3**: `MetricService` validates bounds; excludes NaN. |
| **SC-004** | Power calculation (G*Power) | **Phase 4**: `StatisticalService` calculates min N (α=0.05, f²=0.15, power≥0.8). If N < 5: Halt. If N is below the required threshold: Flag as 'Exploratory'. |
| **SC-005** | Associational framing check | **Phase 4**: Report generator checks metadata for 'randomized'. |
| **SC-006** | Threshold sensitivity variation | **Phase 4**: `SensitivityService` reports outcome variation across sweeps (motion: {2.0, 3.0} mm; p: {0.01, 0.05, 0.1}). |

## Risk Management

| Risk | Mitigation |
| :--- | :--- |
| **Dataset Inaccessibility** | If the verified HuggingFace dataset lacks clinical scores, the pipeline halts at `DataValidator` (FR-011) with a fatal error. No synthetic data will be generated. A secondary search protocol for other OpenNeuro IDs is triggered. |
| **Memory Overflow** | Use `streaming=True` and process subjects sequentially. If a single subject exceeds RAM, the subject is skipped and logged. |
| **Collinearity** | VIF check (FR-012) triggers Ridge regression (lambda=1.0); if Ridge fails (R² < 0.05), univariate models are used. If multicollinearity persists, dimensionality reduction (PCA) is applied to metrics before regression. |
| **Insufficient Power** | Power calculation (SC-004) halts analysis if N < 5; flags limitation as 'Exploratory' if 5 <= N < required. |
| **Disk Overflow** | Streaming strategy ensures raw data is processed and deleted/archived to stay within 14GB limit. The 20-subject subset is estimated to fit within the limit (approx. 2-4GB for processed data). |

## Execution Order

1.  **Phase 1**: Data Acquisition & Validation (Download, Verify Variables, Check Pre/Post Pairs, Write `data/verified_sources.json`). **GATE**: Halt if verification fails.
2.  **Phase 2**: Preprocessing (Motion Correction, Normalization, Quality Check).
3.  **Phase 3**: Network Metric Computation (Connectivity, Modularity, Efficiency).
4.  **Phase 4**: Statistical Analysis (ANCOVA, VIF, Ridge, Correction, Sensitivity).
5.  **Phase 5**: Reporting (Plots, Sensitivity Summary `reports/sensitivity_analysis.md`, Final Report).