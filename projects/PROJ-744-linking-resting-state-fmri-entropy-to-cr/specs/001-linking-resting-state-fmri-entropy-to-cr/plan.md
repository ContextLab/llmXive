# Implementation Plan: Linking Resting‑State fMRI Entropy to Creative Problem Solving

**Branch**: `001-linking-resting-state-fmri-entropy-to-creative-problem-solving` | **Date**: 2026-06-25 | **Spec**: `spec.md`
**Input**: Feature specification from `specs/001-linking-resting-state-fmri-entropy-to-creative-problem-solving/spec.md`

## Summary

This feature implements a computational neuroscience pipeline to test the association between resting-state fMRI entropy (Multiscale Sample Entropy) and creative problem-solving ability (NIH Toolbox Creativity Composite). The approach involves ingesting pre-processed HCP data from the OpenNeuro S bucket, parcellating time series using the HCP 360-parcel atlas, computing entropy metrics, and performing robust linear regression with Benjamini-Hochberg FDR correction. The entire pipeline is optimized to run on a CPU-only GitHub Actions runner (2 cores, 7 GB RAM) within 45 minutes.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `numpy`, `pandas`, `scikit-learn`, `statsmodels`, `nibabel`, `requests`, `tqdm`, `h5py`  
**Storage**: Local filesystem (`data/`, `results/`); CSV/Parquet for intermediate artifacts.  
**Testing**: `pytest` (unit tests for entropy logic, integration tests for pipeline flow).  
**Target Platform**: Linux (GitHub Actions Free Tier: 2 CPU, 7 GB RAM, no GPU).  
**Project Type**: Computational Research Pipeline / CLI  
**Performance Goals**: ≤45 minutes wall-clock time for N=1000 subjects; memory usage <6 GB peak.  
**Constraints**: No GPU/CUDA; no external API calls during runtime (data pre-fetched); strict adherence to spec-defined parameters (m=2, r=0.2, scales 1-20).  
**Scale/Scope**: N=1000 subjects, 360 parcels, Benjamini-Hochberg FDR for network-level tests.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Reproducibility**: Plan mandates pinned `requirements.txt`, random seed initialization in `code/`, and checksum verification of downloaded data (FR-001).
- **II. Verified Accuracy**: All dataset references in `research.md` are restricted to the verified URLs provided in the project context (OpenNeuro/HCP S3). No external URLs (e.g., UK Biobank) are cited.
- **III. Data Hygiene**: Plan includes explicit steps for checksumming raw downloads and creating derivative files with new names (no in-place modification).
- **IV. Single Source of Truth**: Output schemas (`contracts/`) define the exact structure of `AssociationResult` and `EntropyMetric` to ensure paper figures trace back to `data/`.
- **V. Versioning Discipline**: Plan requires content hashing of artifacts; the pipeline explicitly writes these hashes to `state/projects/PROJ-744-linking-resting-state-fmri-entropy-to-cr.yaml` to ensure full compliance with the Constitution. Every artifact (e.g., `data/results/association_results.csv`) is hashed and recorded in this state file.
- **VI. Neuroimaging Data Integrity**: Plan explicitly retrieves data from OpenNeuro/HCP S (ds000114) and preserves raw 4-D volumes. No HuggingFace parquet files are used for raw fMRI data.
- **VII. Statistical Modeling Transparency**: 
  - *Amendment Note*: The Constitution Principle VII grounds methodology in "linear mixed-effects models" and "Benjamini-Hochberg FDR". 
  - *Deviation*: This study uses **Robust Linear Regression (RLM)** instead of LMM because the data is cross-sectional (no repeated measures) and low-dimensional (6 networks), making LMMs over-parameterized and statistically unstable. 
  - *Deviation*: The plan replaces "Permutation-based cluster correction" (which was methodologically invalid for 6 data points) with **Benjamini-Hochberg FDR**, which is the standard and appropriate correction for this low-dimensional multiple comparison problem. 
  - *Action*: This deviation is flagged for Constitution amendment ratification to align the governing document with the scientifically valid methodology required for this specific study design.

## Project Structure

### Documentation (this feature)

```text
specs/001-linking-resting-state-fmri-entropy-to-creative-problem-solving/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   ├── entropy_output.schema.yaml
│   └── association_result.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── ingestion/
│   ├── download_hcp.py       # FR-001: Download & checksum (OpenNeuro S3)
│   └── parcellate.py         # FR-002: Apply atlas (nibabel)
├── entropy/
│   ├── mse.py                # FR-003: Vectorized MSE
│   └── aggregate.py          # FR-004: Global/Network averages + CV (SC-006)
├── modeling/
│   ├── robust_regression.py  # FR-005: RLM + HC3
│   ├── fdr_correction.py     # FR-006: BH-FDR correction
│   └── sensitivity.py        # FR-007: R-sweep (SC-003)
├── utils/
│   ├── logging.py
│   └── motion_check.py       # Edge case: motion flagging
├── benchmark/
│   └── benchmark.sh          # FR-008: Performance verification
└── main.py                   # Pipeline orchestration

tests/
├── unit/
│   ├── test_mse.py           # US-2 Test 1
│   └── test_aggregation.py   # US-2 Test 2
└── integration/
    └── test_pipeline.py      # US-1, US-3 acceptance
```

**Structure Decision**: Single `code/` directory with modular sub-packages (`ingestion`, `entropy`, `modeling`) to maintain a linear data flow and facilitate isolated unit testing of computationally intensive steps (entropy) vs. statistical steps (modeling).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Benjamini-Hochberg FDR | Required by FR-006 (revised) to control FDR across 6 network tests. Cluster correction is invalid for N=6. | Permutation cluster correction is statistically undefined for 6 data points; BH-FDR is the gold standard for low-dimensional multiple comparisons. |
| Vectorized MSE Implementation | Required by FR-008 to meet 45-min runtime on 2-core CPU. | Naive Python loops for Sample Entropy are too slow for large-scale datasets involving many subjects, numerous parcels, and multiple scales. |
| Robust Regression (RLM) | Required by FR-005 to handle heteroscedasticity in behavioral data. | OLS would produce biased standard errors if variance is non-constant; LMM is inappropriate for cross-sectional data. |
| Symmetry Check (Reverse Causality) | Required by FR-009 to test association symmetry. | Swapping X/Y in cross-sectional data does not prove causality; it only tests correlation symmetry. Explicitly disclaimed as non-causal. |

## Performance Verification (FR-008)

To ensure compliance with the 45-minute wall-clock time constraint on the target hardware:
1. **Benchmark Script**: A dedicated `benchmark.sh` script will be executed in the CI pipeline.
2. **Full Cohort Run**: The benchmark runs the **full N=1000 cohort** (not an extrapolation) on the GitHub Actions runner.
3. **Measurement**: The script measures total wall-clock time and peak memory usage.
4. **Pass/Fail**: If time > 45 minutes or memory > 7 GB, the build fails with a detailed error log.
5. **Optimization**: If the benchmark fails, the pipeline must be optimized (e.g., increased batch size, more aggressive streaming) until it passes.

This mandatory verification ensures that the performance claim is not theoretical but empirically validated on the target infrastructure.

## Data Completeness & Reporting

- **Completeness Metric**: A `Data Completeness Report` will be generated after entropy computation, calculating the percentage of subjects with valid entropy for all 360 parcels.
- **Threshold**: The report must confirm ≥95% completeness (SC-005).
- **Output**: The report includes `valid_parcel_count` and `completeness_pct` fields in the `dataset.schema.yaml` output.
- **CV Metric**: The `aggregate.py` script calculates the Coefficient of Variation (CV) of parcel-wise entropies for every subject to satisfy SC-006.

## Sensitivity Analysis Reporting

- **Metric**: The sensitivity analysis (FR-007) will report `sensitivity_delta_p` (change in p-value across r-sweep) and a `stability_score` (variance of p-values).
- **Output**: These metrics are added to the `association_result.schema.yaml` to ensure the variation in association rates is explicitly captured.

## Computational Task Ordering

1. **Data Ingestion**: Download raw 4-D volumes from OpenNeuro S3 (FR-001).
2. **Parcellation**: Extract time series using `nibabel` (FR-002).
3. **Entropy Computation**: Compute MSE and aggregate metrics (FR-003, FR-004).
4. **Completeness Check**: Verify ≥95% valid parcels (SC-005).
5. **Modeling**: Fit RLM models and apply BH-FDR correction (FR-005, FR-006).
6. **Sensitivity**: Run r-sweep and calculate stability scores (FR-007).
7. **Symmetry Check**: Run reverse-causality check (FR-009).
8. **Benchmark**: Verify runtime constraints (FR-008).
9. **Reporting**: Generate final CSVs and JSON reports.