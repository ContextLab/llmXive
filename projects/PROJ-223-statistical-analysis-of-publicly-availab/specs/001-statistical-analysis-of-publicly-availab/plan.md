# Implementation Plan: Traffic-Weather Severity Analysis

**Branch**: `001-traffic-weather-severity` | **Date**: 2026-06-26 | **Spec**: `specs/001-traffic-weather-severity/spec.md`
**Input**: Feature specification from `/specs/001-traffic-weather-severity/spec.md`

## Summary

This feature implements a statistical analysis pipeline to quantify the associational influence of weather conditions (precipitation, visibility, temperature) on traffic accident severity (Property Damage, Injury, Fatality). The approach utilizes an Ordinal Logistic Regression (Cumulative Link Model) on a merged dataset of FARS crash records and NOAA ISD weather data. The implementation strictly adheres to the project's constitutional requirements for reproducibility, data hygiene, and verified accuracy, while ensuring all computational steps are feasible on a CPU-only GitHub Actions free-tier runner (limited CPU and memory resources).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `statsmodels`, `geopy`, `pyyaml`, `matplotlib`, `seaborn`, `pyarrow`, `h3` (for spatial indexing)  
**Storage**: Local CSV/Parquet files under `data/` (raw and derived)  
**Testing**: `pytest` (unit tests for data ingestion logic, model convergence checks)  
**Target Platform**: Linux (GitHub Actions Free Tier: 2 CPU, 7GB RAM, No GPU)  
**Project Type**: Data Analysis Pipeline / Research Script  
**Performance Goals**: Full pipeline execution ≤ 6 hours; Model fit ≤ 60 seconds on sampled data; Memory usage < 6GB peak.  
**Constraints**: No GPU; No external API calls requiring keys; All data must be checksummed; No causal claims (associational only).  
**Scale/Scope**: A single year of FARS data; A substantial volume of records after merge..

> **Dataset Fit Warning & Resolution**: The "Verified datasets" block in the spec may contain mislabeled URLs. The plan **explicitly pins** deterministic fallback sources (NHTSA for FARS, HuggingFace `noaa/isd-hourly` for NOAA) to ensure reproducibility. If the provided URLs fail validation, the system will use the pinned fallbacks and **update the spec's "Verified datasets" block** to reflect the working source, ensuring the Single Source of Truth (SSoT) is correct.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Status | Evidence / Action Plan |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Plan mandates `random_state=42` everywhere. `requirements.txt` pins versions. Scripts run end-to-end on fresh runner. |
| **II. Verified Accuracy** | **PASS** | The plan explicitly includes a **pre-run step** to invoke the Reference-Validator Agent to verify the pinned fallback URLs (NHTSA 2022, HuggingFace `noaa/isd-hourly`) before execution. Runtime schema checks are supplementary (Data Hygiene). |
| **III. Data Hygiene** | **PASS** | Raw data downloaded to `data/raw/` with checksums. Derived data to `data/processed/`. No in-place edits. PII scan enforced. |
| **IV. Single Source of Truth** | **PASS** | All statistics in `paper/` will be generated programmatically from `data/processed/` outputs. No manual entry. |
| **V. Versioning Discipline** | **PASS** | Content hashes for `data/` and `code/` will be updated in `state/` upon artifact changes. |

## Project Structure

### Documentation (this feature)

```text
specs/001-traffic-weather-severity/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── __init__.py
├── config.py            # Paths, seeds, constants
├── ingest.py            # FR-001: Download, Pre-filter, Merge, Contract Validation
├── model.py             # FR-002, FR-003: Ordinal Logistic Regression + Splines
├── diagnostics.py       # FR-004, FR-005: VIF, Brant, Sensitivity (Continuous Subset + Binary Hypothesis)
├── utils.py             # Helper functions (geo-matching, encoding)
└── main.py              # Orchestration script

tests/
├── __init__.py
├── test_ingest.py       # Tests for merge logic, missing data handling, contract validation
├── test_model.py        # Tests for model convergence, VIF calculation
└── test_diagnostics.py  # Tests for sensitivity analysis

data/
├── raw/                 # Downloaded CSVs (checksummed)
├── processed/           # Merged CSVs, excluded summaries, model outputs
└── reports/             # Plots, final summaries
```

**Structure Decision**: Single project structure (`code/`, `tests/`, `data/`) is selected. This is a linear analysis pipeline. The separation of `ingest`, `model`, and `diagnostics` ensures modularity and testability per the spec's user stories. **Crucially, `ingest.py` now includes a contract validation step** to ensure the output matches `merged_dataset.schema.yaml`, specifically populating the `match_method` field based on the logic: 'interpolated' if time delta > 0, else 'nearest'.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Spatial-Temporal Merge** | FARS and NOAA require matching by Lat/Lon and Timestamp. | Simple CSV join is insufficient; requires geospatial proximity logic (a defined radius) and time interpolation. |
| **Ordinal Regression** | Outcome is ordinal (0,1,2), not nominal or continuous. | Standard Logistic or Linear Regression would violate the ordinal nature of severity, leading to biased estimates. |
| **Sensitivity Analysis** | FR-005 requires testing robustness of the continuous predictor. | Binary sweep tests a *different* hypothesis (presence vs. absence), not the stability of the continuous slope. **Correction**: Primary robustness uses subset-based continuous coefficient stability; binary sweep is a distinct secondary hypothesis. |
| **NOAA Pre-filtering** | Full NOAA ISD is too large for 7GB RAM. | A naive merge would OOM. **Solution**: Pre-filter NOAA stations to those within 100km of FARS centroids using H3/geohash indexing. |

## FR/SC Coverage Map

| FR/SC ID | Plan Phase / Step | Implementation Detail |
| :--- | :--- | :--- |
| **FR-001** | `ingest.py` | Download FARS/NOAA (with fallbacks), Pre-filter NOAA, Merge, Validate Contract (including `match_method`). |
| **FR-002** | `ingest.py` | Encode severity (0,1,2) and exclude invalid records. |
| **FR-003** | `model.py` | Fit Cumulative Logit Model with weather + controls + `distance_km`. |
| **FR-004** | `diagnostics.py` | Calculate VIF for all predictors; flag > 5.0. |
| **FR-005** | `diagnostics.py` | **Primary Robustness**: Re-fit model on subsets defined by precipitation thresholds (>0.01, >0.05) to test stability of *continuous* coefficient. **Secondary Hypothesis**: Binary threshold sweep (low, medium, high) as a distinct hypothesis (presence vs. absence), not a stability check. |
| **FR-006** | `paper/` | All outputs framed as associational. |
| **SC-001** | `ingest.py` | Log coverage rate; target ≥ 85%. |
| **SC-002** | `model.py` | Log convergence rate; target ≥ 95%. |
| **SC-003** | `diagnostics.py` | **Note**: Spec requires binary sweep stability. Plan implements continuous subset stability as primary robustness (resolving category error) + binary sweep as distinct hypothesis. (Spec update required for terminology alignment). |
| **SC-004** | `diagnostics.py` | Brant test; if p < 0.05, fit PPO on a small sample first, then full data or flag limitation with specific interpretation. |
| **SC-005** | `main.py` | Total runtime ≤ 6h (Pre-filtering ensures this). |