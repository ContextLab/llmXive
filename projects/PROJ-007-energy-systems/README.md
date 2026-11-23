# PROJ-007: Energy Systems – Causal Inference Pipeline

This project implements a rigorous causal inference pipeline to estimate the impact of distributed energy resources (solar, microgrids) on energy cost burdens in low-income communities. The analysis relies on US EIA RECS and ACS data, adhering strictly to Functional Requirements FR-001 through FR-009.

## Scope & Principles

- **Causal Identification Rigor**: Adheres to Constitution Principle VI. All causal claims are derived via Propensity Score Matching (PSM) with balance validation (SMD ≤ 0.1) and, where longitudinal data exists, Difference-in-Differences (DiD).
- **No Scaling Laws**: This project does **not** include scaling law analysis (e.g., Geoffrey West critique). The scope is limited to causal estimation on microdata.
- **Reproducibility**: All random seeds are pinned in `src/config.yaml` and enforced via `src/utils/logging.py`.
- **Fail-Loudly**: The pipeline halts with explicit errors if data requirements (e.g., minimum adopters, longitudinal columns) are not met. No synthetic fallbacks are used.

## Quickstart

```bash
# Install dependencies
pip install -r requirements.txt

# Run the full pipeline
python src/main.py --config src/config.yaml

# Output
# Results are saved to: data/outputs/analysis_result.json
```

## Architecture Overview

The pipeline executes in three primary stages:

1. **Data Ingestion & Preprocessing (US1)**
 - Ingests EIA RECS and ACS data.
 - Filters for low-income households (<150% FPL).
 - Constructs treatment flags and handles missing values (median imputation).
 - Validates statistical power (≥50 adopters).

2. **Propensity Score Matching & Balance (US2)**
 - Estimates propensity scores via logistic regression.
 - Performs nearest-neighbor matching with caliper reduction logic.
 - Validates covariate balance (SMD ≤ 0.1) via `src/analysis/balance.py`.
 - Executes a placebo test on pre-treatment outcomes to gate causal estimation.

3. **Causal Estimation & Sensitivity (US3)**
 - Estimates ATT using OLS with cluster-robust standard errors.
 - Falls back to DiD if PSM balance fails and longitudinal data is available.
 - Performs sensitivity analysis by sweeping caliper values.
 - Serializes results to JSON.

## Directory Structure

```
.
├── src/
│ ├── analysis/ # PSM, Balance, Causal Estimation, Sensitivity
│ ├── data/ # Ingestion, Preprocessing
│ ├── models/ # Pydantic schemas, Output serialization
│ ├── utils/ # Logging, Seeding
│ ├── config.yaml # Configuration (seeds, paths, thresholds)
│ └── main.py # Pipeline entry point
├── data/
│ ├── raw/ # Downloaded source data
│ ├── processed/ # Cleaned, matched datasets
│ └── outputs/ # Final analysis results (JSON)
├── tests/
│ ├── unit/ # Unit tests for components
│ └── integration/ # End-to-end pipeline tests
├── docs/
│ └── architecture.md # Detailed design documentation
└── requirements.txt
```

## Functional Requirements Adherence

| Requirement | Implementation Status |
|:--- |:--- |
| FR-001: Data Source | EIA RECS / ACS via official APIs |
| FR-002: Low-Income Filter | <150% FPL via ACS tract median |
| FR-003: Covariates | Income, Housing Type, Location |
| FR-004: PSM Balance | SMD ≤ 0.1 enforced via iterative matching |
| FR-005: Placebo Gate | Pre-treatment outcome test (p > 0.05) |
| FR-006: Causal Estimator | OLS (Cluster-Robust) or DiD |
| FR-007: Sensitivity | Caliper sweep analysis |
| FR-008: Reproducibility | Fixed seeds, deterministic execution |
| FR-009: Output Format | JSON with ATT, CI, p-value, methodology |

## Safety & Security

- **PII Scanner**: Integrated `detect-secrets` scan in CI (`.github/workflows/ci.yml`).
- **Data Handling**: No PII is stored in `data/processed/`. All identifiers are hashed or removed.
- **Power Checks**: Pipeline halts if sample size < 50 adopters to prevent spurious results.
