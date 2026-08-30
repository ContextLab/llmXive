# Implementation Plan: Quantifying the Impact of Magnetic Field Topology on Plasma Confinement

**Branch**: `001-quantify-topology-confinement` | **Date**: 2024-05-22 | **Spec**: `specs/001-quantify-topology-confinement/spec.md`

## Summary

This feature implements a data pipeline and statistical analysis engine to estimate the effect size of the association between magnetic field topology (specifically magnetic island width) and plasma energy confinement time ($\tau_E$) using DIII-D public archive data. The system retrieves pre-reconstructed EFIT equilibria and confinement metrics, calculates topological predictors, performs power analysis, and computes Spearman rank correlations with bootstrap confidence intervals. 

**Critical Methodological Note**: Given the pilot sample size (N=5-10), this study is statistically underpowered to confirm or reject the hypothesis (power < 10% for |r|=0.5). The primary goal is reframed from "quantify the impact" to "estimate effect size bounds and assess feasibility". The expected outcome is an "Inconclusive" flag, with the observed effect size and its wide confidence interval reported as exploratory data.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `scipy`, `numpy`, `pandas`, `matplotlib`, `requests`, `pyyaml`, `pytest`  
**Storage**: Local temporary files (CI runner ephemeral storage), final artifacts in `data/` and `outputs/`.  
**Testing**: `pytest` (unit tests for parsing, integration tests for pipeline flow, synthetic data tests for correlation logic).  
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 CPU, 7GB RAM, 14GB disk).  
**Project Type**: Scientific Data Pipeline / CLI Tool.  
**Performance Goals**: Complete pipeline execution (retrieval + analysis) within 6 hours; memory usage < 6GB.  
**Constraints**: No local GPU; no authentication for data (public archive only); strict adherence to constitutional data hygiene (checksums, no in-place modification).  
**Scale/Scope**: Pilot study processing -10 DIII-D discharges.

> **Note on Data Feasibility**: The spec assumes the DIII-D MDSplus archive is accessible via `wget` without authentication. The "Verified datasets" block indicates **NO verified source found** for the live DIII-D MDSplus archive. The implementation plan attempts direct retrieval from the DIII-D public archive. If this fails (unreachable or restricted), the pipeline fails with a retry mechanism as per FR-001. A fallback to static verified data (if available) is attempted only as a demonstration, explicitly labeled as such. The plan does **not** use the placeholder HuggingFace URLs listed in the "Verified datasets" block (which appear to be unrelated test data) as a substitute for DIII-D data, as they do not contain the required physics variables (q-profile, island width, tau_e).

## Constitution Check

| Principle | Status | Action/Reference |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Plan includes fixed random seeds (`FR-005`), `requirements.txt` pinning, and explicit data retrieval commands. |
| **II. Verified Accuracy** | **PASS** | Phase 0 includes a step to run the `Reference-Validator Agent` to verify all citations in `research.md` before analysis begins. |
| **III. Data Hygiene** | **PASS** | Plan mandates checksums for raw downloads (`data/`), derivation of new files for processed data, and exclusion of PII (none expected in public plasma data). |
| **IV. Single Source of Truth** | **PASS** | `data-model.md` defines the canonical schema; `contracts/` enforce validation; all stats trace to `data/` rows. |
| **V. Versioning Discipline** | **PASS** | Plan includes content hashing of artifacts in `state/` updates. |
| **VI. Archival Data Provenance** | **PASS** | Plan strictly retrieves from DIII-D public MDSplus (or fails); no synthesis of raw diagnostic data. |
| **VII. Statistical Rigor** | **PASS** | Plan mandates Spearman correlation, bootstrap (sufficient iterations), power analysis (`FR-008`), and acknowledges low power limitations. |

## Project Structure

### Documentation (this feature)

```text
specs/001-quantify-topology-confinement/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/
    ├── dataset.schema.yaml
    └── output.schema.yaml
```

### Source Code (repository root)

```text
projects/PROJ-332-quantifying-the-impact-of-magnetic-field/
├── code/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── data_retrieval.py       # MDSplus fetch & parsing (FR-001, FR-002, FR-003)
│   ├── topology_metrics.py     # Island width calc (FR-002)
│   ├── statistical_analysis.py # Spearman, Bootstrap, Power (FR-004, FR-005, FR-008, FR-010, FR-011)
│   ├── visualization.py        # Plot generation (FR-006)
│   └── main.py                 # Pipeline orchestrator
├── data/
│   ├── raw/                    # Downloaded MDSplus files (checksummed)
│   └── processed/              # Unified CSV/Parquet
├── outputs/
│   ├── topology_vs_confinement.png
│   └── summary_report.json
├── tests/
│   ├── unit/
│   │   ├── test_topology_metrics.py
│   │   └── test_statistics.py
│   └── integration/
│       └── test_pipeline.py
└── contracts/
    ├── dataset.schema.yaml
    └── output.schema.yaml
```

**Structure Decision**: Single project structure (Option 1) is selected. The project is a linear scientific pipeline (Retrieve -> Process -> Analyze -> Visualize) with no need for separate frontend/backend services. This minimizes overhead on the constrained CI runner.

## Phase Breakdown

### Phase 0: Data Retrieval, Validation & Reference Check (FR-001, FR-009, Constitution II)
1.  **Input**: List of 10 target DIII-D discharge IDs.
2.  **Action**: Execute `data_retrieval.py` to fetch EFIT, island, and tau_e data from DIII-D public MDSplus via `wget`/`requests`.
3.  **Retry Logic**: Implement multiple retries with 10s intervals on timeout. (Edge Case 1).
4.  **Fallback**: If live archive fails, attempt to load a static, verified subset of DIII-D data (if available in a verified public repository like Zenodo/HuggingFace) as a *demonstration* only. If no verified static data exists, fail.
5.  **Reference Validation**: Execute the `Reference-Validator Agent` to verify all citations in `research.md` before proceeding.
6.  **Validation**: Parse raw files into a unified DataFrame. Check for missing `island_width`, `tau_e`, or `q-profile`. Exclude invalid discharges.
7.  **Gate**: Fail if valid N < 5 (FR-001). Generate checksums for raw files.

### Phase 1: Topological Metric Calculation (FR-002, FR-011)
1.  **Input**: Processed EFIT data.
2.  **Action**: Calculate resonant surface density (count of rational q surfaces per $\rho_{tor}$) for **descriptive reporting only**.
3.  **Fallback**: If pre-calculated island width missing, derive via Rutherford equation **only if independent perturbation amplitude is available**. If inputs missing, exclude discharge.
4.  **Collinearity Check**: Skipped for density (tautological). If `q_max - q_min` correlates > 0.95 with density, density is excluded from any multivariate analysis (already excluded by design).
5.  **Output**: `data/processed/metrics.csv` with `discharge_id`, `island_width`, `resonant_surface_density` (descriptive), `tau_e`, `mode` (derived from `h98y2`), `q_min`, `q_max`.

### Phase 2: Statistical Analysis (FR-004, FR-005, FR-008, FR-010)
1.  **Input**: `metrics.csv`.
2.  **Power Analysis**: Calculate power to detect |r|=0.5 with current N. If < 20%, flag "Inconclusive" (FR-008). **Explicitly state that with N<10, power is likely < 10% and the study is underpowered.**
3.  **Stratification**: Check N per mode (L/H). If N < 3 for any mode, skip stratification and run global correlation with a prominent warning: "Simpson's Paradox highly likely due to mixed modes; result is exploratory only" (FR-010).
4.  **Correlation**: Compute Spearman r and p-value for `island_width` vs `tau_e` only. Perform a sufficient number of bootstrap iterations for the confidence interval..
5.  **Output**: `outputs/summary_report.json` with r, p, CI, power, and hypothesis status (expected: "Inconclusive").

### Phase 3: Visualization & Reporting (FR-006, SC-001)
1.  **Action**: Generate `topology_vs_confinement.png` scatter plot with regression line (if applicable) and error bars (CI).
2.  **Output**: Save plot and final report.
3.  **Gate**: Ensure execution time < 6 hours (FR-007).

## Compute Feasibility Strategy

- **CPU-First**: All operations (parsing, Rutherford approximation, Spearman correlation, bootstrap) are purely CPU-bound and lightweight. No GPU required.
- **Memory**: Streaming data retrieval and processing one discharge at a time ensures RAM usage stays well below 7GB.
- **Time**: Processing 10 discharges with 1000 bootstrap iterations is estimated at < 5 minutes on 2 CPUs. The 6-hour limit is a safety buffer for network retries.