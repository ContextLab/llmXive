# Implementation Plan: Investigating the Relationship Between Brain Network Dynamics and Subjective Time Perception

**Branch**: `001-gene-regulation` | **Date**: 2026-06-24 | **Spec**: [link]
**Input**: Feature specification from `/specs/001-investigating-the-relationship-between-b/spec.md`

## Summary

This project implements a computational neuroscience pipeline to investigate the relationship between dynamic brain network reconfigurability (derived from resting-state fMRI) and cognitive processing speed (Digit Symbol Substitution Test, DSST). The system attempts to download HCP data, preprocess it via fMRIPrep (where resources allow), compute sliding-window community transitions using the Louvain algorithm, and perform Spearman correlations with Bonferroni correction and permutation validation.

**Critical Constraint**: The implementation is constrained to run on free-tier GitHub Actions with limited CPU and RAM resources. Full fMRIPrep preprocessing of 100 subjects is **not feasible** on this hardware. Furthermore, **no verified source** for the required fMRI time-series is currently available in the provided dataset list. Therefore:
1.  **CI/Test Mode**: The pipeline runs on a 1-2 subject subset **ONLY IF** real fMRI data is successfully downloaded and verified. If real fMRI data is unavailable (which is the current state), the pipeline **fails gracefully** with a clear "Data Gap: fMRI time-series not found" error.
2.  **No Simulation for Hypothesis**: Synthetic data is **strictly prohibited** for the primary hypothesis test or correlation analysis. Synthetic data is used **only** in unit tests (`tests/unit/`) to verify code logic (e.g., that the Louvain algorithm runs, that the correlation function executes).
3.  **Full Study Mode**: The plan assumes the full study will be executed on a cluster with sufficient resources (adequate RAM, multiple CPUs) to run fMRIPrep on the full cohort. The CI run serves as a **reproducibility check** of the code logic and statistical pipeline, not a full data processing run.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: nilearn (CPU), networkx, scikit-learn, pandas, matplotlib, nibabel, scipy, pytest.
**Storage**: Local file system (`data/raw`, `data/processed`, `data/results`).
**Testing**: pytest (unit tests for metrics, integration tests for pipeline flow).
**Target Platform**: Linux (GitHub Actions runner).
**Project Type**: Computational Research Pipeline (CLI).
**Performance Goals**: 
- CI/Test: Process 1-2 subject subset (or fail with "Data Gap" if real data missing) in ≤ 6 hours.
- Full Study: Process 100 subjects on a cluster in ≤ 6 hours.
**Constraints**: 
- No GPU; no CUDA.
- fMRIPrep is **required** for real data (Constitution Principle VI). Simulation of preprocessing is **prohibited** for the main analysis.
- Louvain algorithm must be deterministic with seeded RNG.
- If verified URLs do not contain real fMRI time-series, the analysis step is skipped, and a "Data Gap" is reported.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*Gates determined based on constitution file*

| Principle | Compliance Status | Notes |
|-----------|---|---|
| I. Reproducibility | **PASS** | Plan mandates pinned `requirements.txt`, seeded RNGs (Louvain, Permutation), and checksummed data. |
| II. Verified Accuracy | **PASS** | Plan restricts dataset citations to the "Verified datasets" block. If verified sources lack required data types (fMRI), the pipeline fails with "Data Gap" rather than using unverified or synthetic data. |
| III. Data Hygiene | **PASS** | Plan enforces read-only raw data, checksums in `state/`, and PII-free outputs. |
| IV. Single Source of Truth | **PASS** | All statistics trace to `data/analysis_results.tsv`; no hand-typed values in paper. |
| V. Versioning Discipline | **PASS** | Content hashes for artifacts; `updated_at` timestamp updates on change. |
| VI. Neuroimaging Reproducibility | **PASS** | Plan specifies fMRIPrep version and flags; logs stored in `data/preprocess_log.txt`. **Note**: If real data is missing, preprocessing is skipped, and this step is marked "N/A". No simulation allowed. |
| VII. Statistical Transparency | **PASS** | Plan mandates single `code/analysis.py` recording Spearman, Bonferroni, and permutation details. |

## Project Structure

### Documentation (this feature)

```text
specs/001-investigating-the-relationship-between-b/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── dataset.schema.yaml
    ├── metric.schema.yaml
    └── result.schema.yaml
```

### Source Code (repository root)

```text
projects/PROJ-433-investigating-the-relationship-between-b/
├── data/
│   ├── raw/               # Downloaded HCP data (checksummed)
│   ├── processed/         # fMRIPrep outputs, connectivity matrices
│   └── results/           # TSVs, plots, permutation outputs
├── code/
│   ├── __init__.py
│   ├── download.py        # HCP download logic with content verification
│   ├── preprocess.py      # fMRIPrep invocation wrapper (requires real data)
│   ├── metrics.py         # Sliding window & Louvain reconfigurability
│   ├── analysis.py        # Correlation, Bonferroni, Permutation
│   ├── viz.py             # Scatter plots
│   └── utils.py           # QC, logging, seeding
├── tests/
│   ├── unit/              # Includes synthetic data tests for logic only
│   └── integration/
├── requirements.txt       # Pinned dependencies
└── README.md
```

**Structure Decision**: Single-project structure selected to minimize overhead for a research pipeline. All logic resides in `code/`, data in `data/`. This aligns with the "Single Source of Truth" and reproducibility requirements.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Distributed fMRIPrep | Full multi-subject processing requires distributed compute to meet 6h SLA. | Single-node processing of a substantial cohort exceeds 6h on free-tier hardware. |
| Sliding Window + Louvain | Required to capture dynamic reconfigurability (not static connectivity). | Static connectivity ignores the "dynamics" aspect of the hypothesis. |
| Permutation Testing | Necessary to validate significance against non-normal distributions. | Standard parametric tests may be invalid for small sample sizes or non-normal data. |
| **Data Gap Handling** | Verified URLs may lack fMRI time-series. | Simulating data would violate scientific validity and Constitution Principle II. |

## FR/SC Coverage Map

- **FR-001 (Download)**: Implemented in `code/download.py`. **Constraint**: If verified URLs do not contain fMRI time-series, the system logs "Data Gap: fMRI missing" and fails the FR-001 check for this run. No simulation.
- **FR-002 (Preprocess)**: Implemented in `code/preprocess.py` using fMRIPrep. **Constraint**: Requires real NIfTI input. If missing, step is skipped and marked "N/A". Simulation is prohibited.
- **FR-003 (Sliding Window)**: Implemented in `code/metrics.py`. Requires preprocessed time-series.
- **FR-004 (Louvain)**: Implemented in `code/metrics.py`. Seeded RNG.
- **FR-005 (Correlation)**: Implemented in `code/analysis.py`. Excludes subjects with missing data.
- **FR-006 (Bonferroni)**: Implemented in `code/analysis.py`.
- **FR-007 (Visualization)**: Implemented in `code/viz.py`.
- **FR-008 (Permutation)**: Implemented in `code/analysis.py`.
- **SC-001 (fMRIPrep Success)**: Measured only if real data is processed. If data is missing, reported as "N/A - Data Unavailable".
- **SC-002 (Reproducibility)**: Verified by re-running with same seed on CI (if data available).
- **SC-003 (CSV Output)**: Output is `data/analysis_results.tsv` (TSV per Constitution VII).
- **SC-004 (Effect Size)**: Reported in results.
- **SC-005 (Plots)**: Generated if analysis runs.

## Computational Feasibility Note

The plan acknowledges that running full fMRIPrep on 2 CPU/7GB RAM is **infeasible**. The CI pipeline will:
1.  Attempt to download verified data.
2.  If real fMRI is found: Run a **strictly limited** subset (e.g., 1-2 subjects) or fail with "Resource Limit" if memory is exceeded.
3.  If real fMRI is **not** found: Log "Data Gap: fMRI time-series not found in verified sources" and skip preprocessing/analysis.
4.  Run **unit tests** on synthetic data to verify code logic (not hypothesis).

The full scientific result (a substantial cohort of subjects) is expected to be generated on a cluster, not the CI runner.

## Category Error Prevention

The plan explicitly prevents the following invalid scenarios:
- **Synthetic Metrics + Real Behavior**: The pipeline will not correlate synthetic reconfigurability metrics with real DSST scores. If fMRI is missing, the analysis step is skipped entirely.
- **Synthetic Data for Hypothesis**: Synthetic data is used **only** in `tests/unit/` to verify that the code runs. It is never used to generate results for the research question.
- **Simulation of fMRIPrep**: The plan does not simulate fMRIPrep outputs. If real data is missing, the preprocessing step is marked as failed/skipped.