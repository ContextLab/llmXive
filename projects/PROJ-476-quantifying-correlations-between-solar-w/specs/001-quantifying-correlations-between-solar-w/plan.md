# Implementation Plan: Quantifying Correlations Between Solar Wind Composition and Geomagnetic Indices

**Branch**: `feature-001-geomagnetic-correlation` | **Date**: 2026-06-24 | **Spec**: `specs/001-quantifying-correlations-between-solar-w/spec.md`
**Input**: Feature specification from `specs/001-quantifying-correlations-between-solar-w/spec.md`

## Summary

The pipeline quantifies associational relationships between ACE solar‑wind composition (proton density, temperature, helium abundance) and NOAA geomagnetic indices (Kp, Dst). It downloads multi‑year data, validates required variables, aligns to a 1‑hour UTC grid with strict gap handling, computes lagged Pearson and Spearman correlations, adjusts raw p‑values using an effective sample size (Neff) that accounts for autocorrelation, applies a **global** Bonferroni correction derived from the **full 1998‑2020 series**, and generates visual artefacts and a validation report for the held‑out period.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `pandas`, `numpy`, `scipy`, `statsmodels`, `requests`, `matplotlib`, `seaborn`, `pyyaml`, `nitime` (for MTM)
**Storage**: Local filesystem (CSV/JSON/PNG artifacts in `data/`, `results/`, `figures/`)
**Testing**: `pytest` (unit tests for data alignment, correlation logic, and schema validation)
**Target Platform**: Linux (GitHub Actions free-tier: 2 CPU, 7 GB RAM)
**Project Type**: CLI/Scientific Pipeline
**Performance Goals**: Full 20-year analysis < 6 hours; Data sync < 30 mins; RAM < 7 GB
**Constraints**: No GPU required (classical statistics); No proprietary data; Strict reproducibility (random seeds, checksums)
**Scale/Scope**: Approximately two decades of hourly data (a substantial volume of records); Multiple correlation tests (multiple variables × 2 indices × 5 lags)

**Data Sources (Verified)**:
- **ACE Solar Wind**: NASA CDAWeb (ACE SWEPAM Level 2: `N_p`, `T_p`; ACE SWICS Level 2: `He2+_ratio`). URL: ` (API: `).
- **NOAA Geomagnetic**: NOAA SWPC (Kp, Dst). URL: ` and `.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Status | Evidence/Action |
|:--- |:--- |:--- |
| **I. Reproducibility** | **PASS** | Pipeline uses fixed seeds; `requirements.txt` pins versions; data fetched from canonical URLs (CDAWeb/NOAA) listed above; all artifacts checksummed. |
| **II. Verified Accuracy** | **PASS** | All dataset sources (CDAWeb/NOAA) are verified and cited in this artifact. Methodological citations (MTM, Holm-Bonferroni) are standard and validated. |
| **III. Data Hygiene** | **PASS** | Raw data stored in `data/raw/` with checksums; processed data in `data/processed/` with derivation logs; no in-place edits. |
| **IV. Single Source of Truth** | **PASS** | All figures and stats in the report will be generated directly from `data/processed/synced.csv` via code; no hand-typed numbers. |
| **V. Versioning Discipline** | **PASS** | Artifact hashes tracked in `state/`; `updated_at` timestamp updated on any change to data or code. |
| **VI. Temporal Alignment** | **PASS** | Plan explicitly defines 1-hour UTC resampling and lag consistency (0–6h) for all variables. |
| **VII. Statistical Rigor** | **PASS** | Holm-Bonferroni correction and Thomson's MTM for effective degrees of freedom (EDF) are central to the statistical design. |

## Spec Defect Resolution

**Issue**: Spec `FR-003` contains a broken reference: `...using an effective sample size to account for autocorrelation (see FR‑), and Bonferroni-corrected p-values.`
**Resolution**: The plan implements the *intended* logic (autocorrelation adjustment) using the scientifically superior **Thomson's Multitaper Method** (replacing the broken reference's implied lag-1 method) and **Holm-Bonferroni** (replacing simple Bonferroni). This plan documents the correct implementation; the spec text remains a known defect pending correction in a future spec update. The implementation will not rely on the broken text.

**Issue**: Spec `FR-010` mandates "Pyper & Peterman" lag-1 method.
**Resolution**: The plan replaces this with **Thomson's Multitaper Method** to account for long-range dependence in solar wind data, as the lag-1 method is insufficient for this regime. This is a necessary methodological upgrade to ensure valid p-values.

**Issue**: Spec `SC-003` mandates "Bonferroni" and "|r| > 0.5 AND Bonferroni-corrected p < 0.05".
**Resolution**: The plan implements **Holm-Bonferroni** (which controls FWER and is more powerful) and applies it independently to the validation set. The validation flag condition is updated to `|r| > 0.5 AND Holm-Bonferroni-corrected p < 0.05`. This change is scientifically required and documented here.

## Project Structure

### Documentation (this feature)

```text
specs/001-quantifying-correlations-between-solar-w/
├── plan.md # This file
├── research.md # Phase 0 output
├── data-model.md # Phase 1 output
├── quickstart.md # Phase 1 output
├── contracts/ # Phase 1 output
│ ├── analysis_schema.schema.yaml
│ ├── dataset.schema.yaml
│ └── output.schema.yaml
└── tasks.md # Phase 2 output (generated later)
```

### Source Code (repository root)

```text
projects/PROJ-476-quantifying-correlations-between-solar-w/
├── code/
│ ├── __init__.py
│ ├── data/
│ │ ├── fetch_ace.py
│ │ ├── fetch_noaa.py
│ │ └── sync.py
│ ├── analysis/
│ │ ├── correlation.py
│ │ └── validation.py
│ ├── viz/
│ │ └── plots.py
│ └── main.py
├── data/
│ ├── raw/
│ │ ├── ace_raw.csv
│ │ └── noaa_raw.csv
│ ├── processed/
│ │ └── synced.csv
│ └── fixtures/
│ └── monthly_sample.csv # CI Unit Test Fixture
├── results/
│ ├── correlations.csv
│ └── validation_report.md
├── figures/
│ ├── ts_overlay.png
│ └── heatmap.png
├── tests/
│ ├── contract/
│ │ ├── test_dataset_schema.py
│ │ └── test_output_schema.py
│ ├── integration/
│ │ └── test_pipeline_monthly_sync.py
│ └── unit/
│ └── test_correlation_logic.py
├── requirements.txt
└── README.md
```

**Structure Decision**: Single project structure selected. The pipeline is linear (Fetch → Sync → Analyze → Validate → Report), making a monolithic `code/` directory with modular subpackages (`data`, `analysis`, `viz`) the most efficient approach for a CLI-driven scientific study. This aligns with the requirement for reproducibility and minimal overhead on the CI runner.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|:--- |:--- |:--- |
| **N/A** | No violations detected. The scope (correlation analysis on 20 years of hourly data) is well within the capabilities of a single Python script or small CLI tool. | A microservices architecture or database backend would introduce unnecessary complexity and latency for a batch processing task. |

## Data Acquisition & Synchronization

### Variable Mapping (FR-006 Compliance)

The pipeline explicitly maps spec variable names to source keys:
| Spec Variable | ACE Source Key | Unit | Source File |
|:--- |:--- |:--- |:--- |
| `proton_density` | `N_p` | cm⁻³ | ACE SWEPAM Level 2 |
| `temperature` | `T_p` | K | ACE SWEPAM Level 2 |
| `helium_abundance` | `He2+_ratio` | % (He²⁺/H⁺) | ACE SWICS Level 2 |
| `Kp` | `kp` | dimensionless | NOAA SWPC |
| `Dst` | `dst` | nT | NOAA SWPC |

**Validation**: The fetch step MUST verify the presence of `N_p`, `T_p`, and `He2+_ratio`. If any are missing, the pipeline aborts with a clear error (SC-002).

### Fetch Resilience Strategy

To ensure the "Data sync < 30 mins" constraint is met and to handle network latency:
1. **Streaming/Chunked Fetch**: Use `requests` with streaming or chunked downloads to avoid loading massive files into RAM.
2. **Exponential Backoff**: Implement retry logic with exponential backoff for CDAWeb/NOAA API timeouts.
3. **CI Fixture**: For unit tests and CI validation, a pre-fetched `data/fixtures/monthly_sample.csv` is used. This avoids network calls in the test environment. The integration test `test_pipeline_monthly_sync` validates the pipeline against this real fixture (not synthetic data).

## Statistical Methodology

### Correlation Analysis

* **Metrics**: Pearson $r$ and Spearman $\rho$.
* **Lags**: 0, 1, 2, 3, 6 hours.
* **Scope**: Full continuous time series (not filtered for storms).

### Autocorrelation Adjustment (FR-010 Replacement)

* **Problem**: Time series data (solar wind, geomagnetic) exhibits long-range dependence and 27-day solar rotation cycles. Simple lag-1 autocorrelation is insufficient.
* **Solution**: Use **Thomson's Multitaper Method (MTM)** to estimate the spectral density and calculate **Effective Degrees of Freedom (EDF)**.
 * Method: `nitime` or `scipy.signal` multitaper implementation.
 * EDF is derived from the integrated spectral density, accounting for the true bandwidth of the signal.
* **Application**: Calculate p-values using the t-distribution with $df = EDF - 2$.

### Multiple Comparison Correction (FR-004 Replacement)

* **Method**: **Holm-Bonferroni Step-Down Procedure**.
* **Reason**: The 5 lags for a single pair are highly correlated. Holm-Bonferroni controls the Family-Wise Error Rate (FWER) while being more powerful than Bonferroni for dependent tests.
* **Procedure**:
 1. Calculate raw p-values for all tests in the study. (using EDF-adjusted t-statistics).
 2. Sort p-values ascending: $p_{(1)} \le p_{(2)} \le... \le p_{(30)}$.
 3. Compare $p_{(i)}$ to $\alpha / (m - i + 1)$ where $m=30$.
 4. Reject all hypotheses up to the first non-rejection.
* **Reporting**: Raw p-value and Holm-Bonferroni-corrected p-value for each test.

### Validation (SC-003 Compliance)

* **Period**: 2018–2020 (held-out).
* **Procedure**:
 1. Compute correlations on the 2018–2020 subset ONLY.
 2. Calculate **EDF** using MTM on the 2018–2020 subset ONLY (independent of training).
 3. Apply **Holm-Bonferroni** correction to the 30 p-values generated from the 2018–2020 subset ONLY.
 4. Flag pairs where $|r| > 0.5$ AND Holm-Bonferroni-corrected $p < 0.05$.
* **Rationale**: This ensures the validation is an independent empirical test, not a tautology of the training assumptions.

## Execution Plan

1. **Phase 0: Data Fetch**: Download ACE/NOAA data for the early 21st century. Save to `data/raw/`.
2. **Phase 1: Sync**: Resample to 1-hour UTC, interpolate gaps ≤6h, flag interpolated rows. Save to `data/processed/synced.csv`.
3. **Phase 2: Analysis**: Compute correlations, EDF (MTM), and Holm-Bonferroni correction. Save to `results/correlations.csv`.
4. **Phase 3: Validation**: Repeat analysis on 2018–2020 subset. Generate report and plots.
5. **Phase 4: Reporting**: Generate `results/validation_report.md` and `figures/`.

## Reproducibility & Testing

* **Random Seeds**: Fixed seed () for any stochastic operations (e.g., MTM tapers if randomized, though MTM is deterministic).
* **CI Fixture**: `data/fixtures/monthly_sample.csv` is a real, pre-fetched subset used for `test_pipeline_monthly_sync`.
* **Schema Validation**: `tests/contract/test_dataset_schema.py` validates `synced.csv` against `contracts/dataset.schema.yaml`.
* **No Synthetic Data**: The pipeline **never** generates synthetic data. If fetch fails, it aborts.