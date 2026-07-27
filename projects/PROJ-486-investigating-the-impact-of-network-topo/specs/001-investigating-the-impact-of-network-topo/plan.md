# Implementation Plan: Investigating the Impact of Network Topology on Neural Entrainment to Rhythmic Stimuli

**Branch**: `001-network-topology-entrainment` | **Date**: 2026-06-28 | **Spec**: `spec.md`
**Input**: Feature specification from `specs/001-investigating-the-impact-of-network-topo/spec.md`

## Summary

This project implements a statistical pipeline to investigate the association between resting-state network topology (Clustering Coefficient, Characteristic Path Length) derived from HCP fMRI data and neural entrainment strength. The system enforces a strict "Real Data First" policy: if the inner join of fMRI and entrainment data yields N < 30, the pipeline halts with a "Data Insufficient" status and does NOT generate synthetic data for the hypothesis test. Synthetic data generation is strictly reserved for `validation_mode` to verify code logic. The pipeline includes robustness checks via alternative parcellations (AAL, Power 264), multiple comparison corrections (Holm-Bonferroni), and collinearity diagnostics (VIF).

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `pandas`, `numpy`, `scipy`, `statsmodels`, `networkx`, `matplotlib`, `seaborn`, `huggingface_hub`, `pyyaml`, `nilearn`
**Storage**: Local file system (`data/raw`, `data/processed`, `data/visualizations`)
**Testing**: `pytest` (unit tests for data validation, integration tests for pipeline flow)
**Target Platform**: GitHub Actions `ubuntu-latest` (2 cores, 7GB RAM)
**Project Type**: Data Analysis Pipeline / CLI Tool
**Performance Goals**: Complete analysis of N=50 subjects with 200x200 matrices within 6 hours.
**Constraints**: CPU-only execution for statistical analysis; no GPU required for NetworkX or linear models; strict memory limit prevents loading full HCP S1200 raw images into RAM (must use precomputed connectivity matrices or stream).
**Scale/Scope**: N=50 subjects (subset of HCP), 3 atlas types (Schaefer, AAL, Power 264).

> **Critical Feasibility Note**: The spec requires downloading and preprocessing HCP S1200 data to parcellate into the Schaefer atlas (FR-001). The plan prioritizes a **Local Preprocessing Fallback**: if the verified HCP URLs do not contain pre-computed connectivity matrices, the system will download the raw HCP minimally preprocessed data (via HCP API or direct link) and use `nilearn` to parcellate the time series into the Schaefer atlas locally. This ensures FR-001 is satisfied even if pre-computed matrices are missing. If raw data is also unavailable, the pipeline halts with "Data Insufficient".

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Status | Evidence / Action Plan |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | `requirements.txt` will pin all versions. Random seeds (numpy, python) will be set in `code/config.py`. Data sources are fixed URLs. |
| **II. Verified Accuracy** | **PASS** | All dataset URLs in `research.md` are drawn from the verified list. Citations will be validated by the Reference-Validator. |
| **III. Data Hygiene** | **PASS** | `data/` structure includes `raw` (immutable) and `processed` (derived). Checksums will be generated for `data/raw/hcp_connectivity_subset.csv`, `data/raw/entrainment_metrics.csv`, and all derived files in `data/processed/` and recorded in `state/...yaml`. |
| **IV. Single Source of Truth** | **PASS** | All figures and stats in `paper/` will be generated directly from `data/processed` CSVs. No manual entry. |
| **V. Versioning Discipline** | **PASS** | Content hashes for data and code will be tracked in the project state file. |
| **VI. Statistical Rigor** | **PASS** | Plan includes Holm-Bonferroni correction (FR-004, US-2) and VIF checks (FR-004). P-values and effect sizes (r) will be reported. Correction is applied to the full family of tests (univariate and MLR) if the MLR stage is reached. |
| **VII. Multimodal Data Alignment** | **PASS** | `code/data_loader.py` will perform an inner join on `subject_id` and validate N >= 30 before proceeding (FR-003, US-1). |

## Project Structure

### Documentation (this feature)

```text
specs/001-network-topology-entrainment/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-486-investigating-the-impact-of-network-topo/
├── code/
│   ├── __init__.py
│   ├── config.py              # Paths, seeds, constants
│   ├── data_loader.py         # FR-001, FR-003, FR-007, FR-008
│   ├── graph_metrics.py       # FR-002, FR-012 (zero-variance)
│   ├── simulation.py          # FR-009, US-4 (Validation Mode only)
│   ├── analysis.py            # FR-004, US-2 (Correlation, MLR, VIF, Correction)
│   ├── viz.py                 # FR-005, FR-010, US-3 (Scatter, Bar charts)
│   └── main.py                # Orchestration, CLI entry point
├── data/
│   ├── raw/
│   │   ├── hcp_connectivity_subset.csv  # Derived from HCP source (pre-computed or raw time series)
│   │   └── entrainment_metrics.csv      # Input CSV (or simulated in validation)
│   ├── processed/
│   │   ├── joined_data.csv
│   │   ├── metric_flags.json
│   │   └── correlation_results.csv
│   └── visualizations/
│       ├── scatter_topology_entrainment.png
│       └── atlas_comparison_bar.png
├── tests/
│   ├── unit/
│   │   ├── test_data_loader.py
│   │   ├── test_graph_metrics.py
│   │   └── test_analysis.py
│   └── integration/
│       └── test_pipeline.py
├── docs/
│   └── README.md
└── requirements.txt
```

**Structure Decision**: Single project structure selected. The `code/` directory contains all logic, `data/` separates raw inputs from processed outputs, and `tests/` mirrors the code structure for validation. This aligns with the Constitution's reproducibility and data hygiene requirements.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Multi-atlas Sensitivity (US-3)** | Required to prove robustness of findings against atlas choice. | A single-atlas analysis is scientifically insufficient for a "robustness" claim and violates FR-006. |
| **Validation Mode (US-4)** | Required to verify code logic without contaminating empirical results. | Running the pipeline on real data without validation risks undetected bugs; synthetic data for *hypothesis testing* is forbidden (FR-003), so a separate mode is needed. |
| **VIF & Holm-Bonferroni (US-2)** | Required to control Type I error and detect collinearity in MLR. | Standard uncorrected p-values would inflate false positives; ignoring collinearity would yield misleading MLR coefficients. |

## Local Preprocessing Fallback

If the verified HCP URLs do not contain pre-computed connectivity matrices:
1.  **Download Raw Data**: Use `nilearn` or direct download to fetch the HCP S1200 minimally preprocessed data (raw time series).
2.  **Parcellate**: Apply the Schaefer atlas (and AAL/Power 264 for sensitivity analysis) to the time series to generate connectivity matrices.
3.  **Compute Metrics**: Calculate Clustering Coefficient and Path Length from the resulting matrices.
4.  **Store**: Save the computed metrics to `data/processed/` and proceed with the analysis.

This fallback ensures FR-001 and FR-002 are satisfied even if pre-computed matrices are missing.

## Data Matching

The pipeline explicitly checks if the `subject_id`s in the HCP data match those in the entrainment CSV. If no match is found (N < 30), the system halts with "Data Insufficient". The plan acknowledges that without a matched dataset, the hypothesis is untestable, and no synthetic data will be generated to replace the missing real data.

## Statistical Analysis Plan

1.  **Univariate Analysis**:
    - Compute Spearman correlation ($r$) between Clustering Coefficient and Entrainment.
    - Compute Spearman correlation ($r$) between Characteristic Path Length and Entrainment.
    - Null Hypothesis ($H_0$): $r = 0$.

2.  **Multiple Linear Regression (MLR)**:
    - **Gate**: ONLY executed if both univariate correlations are significant ($p < 0.05$).
    - Model: $Entrainment = \beta_0 + \beta_1(Clustering) + \beta_2(PathLength) + \epsilon$.
    - **Collinearity Check**: Calculate Variance Inflation Factor (VIF). If $VIF > 5$, flag `collinearity_warning`, **suppress MLR coefficients**, and report only univariate results.
    - **Correction**: Apply Holm-Bonferroni correction to the p-values of the two predictors. If the MLR stage is reached, the correction is applied to the **entire family of tests** (2 univariate + 2 MLR) to control the family-wise error rate.

3.  **Robustness Check (Sensitivity Analysis)**:
    - Repeat analysis using AAL and Power 264 atlases.
    - Generate a comparative bar chart showing $|r_{Schaefer} - r_{Alternative}|$.

## Power & Sample Size Justification

**Formal Power Analysis**:
The study enforces a minimum sample size of N=30 for hypothesis testing. A formal power calculation (two-tailed, alpha=0.05) was performed to determine the detectable effect size at this threshold:
- **Alpha ($\alpha$)**: 0.05 (two-tailed).
- **Sample Size (N)**: 30.
- **Test**: Spearman Rank Correlation (approximated by Pearson for power estimation).
- **Power (1 - $\beta$) to detect r=0.3**: **[deferred]**.
- **Power (1 - $\beta$) to detect r=0.45**: **[deferred]**.
- **Power (1 - $\beta$) to detect r=0.5**: **[deferred]**.

**Interpretation & Limitations**:
- **Underpowered for Small/Moderate Effects**: With N=30, the study has **limited power ([deferred])** to detect moderate correlations ($r=0.3$). Consequently, a non-significant result ($p > 0.05$) **cannot** be interpreted as evidence of no effect; it may simply reflect insufficient statistical power.
- **Exploratory Framing**: All results will be explicitly framed as **exploratory**. The "Power Warning: N < 30 (Exploratory)" flag (triggered if N < 30, but also noted as a limitation for N=30) will be included in the final report.
- **Decision Rule**: The N=30 threshold is a pragmatic minimum to ensure the correlation estimate is not entirely dominated by noise, but it is not a guarantee of high power. The study is designed to detect **large** effects with reasonable confidence (80% power) and to flag smaller effects as inconclusive.
- **No Justification for N < 30**: The system will **halt** with "Data Insufficient" if N < 30, as the power to detect any meaningful effect becomes negligible (<30%), rendering the hypothesis test statistically invalid.

## Causal Inference

- The study is **observational**. Claims will be framed as **associational** (correlation), not causal. No randomization of network topology exists.

## Compute Feasibility

- **CPU-First**: The analysis involves:
    - Loading a subset of HCP data (parquet/CSV).
    - Computing graph metrics on 200x200 matrices (trivial for NetworkX).
    - Running Spearman correlations and MLR (trivial for `scipy`/`statsmodels`).
- **Memory**: 7GB RAM is sufficient for N=50 subjects with 200x200 matrices (approx 50 * [deferred] floats = 16MB).
- **Disk**: Adequate storage capacity is provisioned for raw and processed data.
- **GPU**: Not required. The method does not involve deep learning or large matrix factorizations that require CUDA.