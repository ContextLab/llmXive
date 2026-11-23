# Research: Developing Novel Solutions to Address Energy Inequity in Low-Income Communities

## Problem Statement

Energy inequity persists in low-income U.S. communities, where households face disproportionate energy cost burdens despite limited income. This project investigates whether clean-energy adoption (solar/microgrid) causally reduces energy cost burden and improves socioeconomic outcomes (e.g., tract-level home value) in these communities. The challenge is observational: adoption is not randomized, and confounders (income, housing type, location) may bias estimates.

## Methodological Approach

### Causal Identification Strategy

The primary strategy is **Propensity Score Matching (PSM)** to create a balanced control group of non-adopters similar to adopters on pre-treatment covariates. The Average Treatment Effect on the Treated (ATT) is then estimated via OLS regression on the matched sample with cluster-robust standard errors.

**Fallback Strategy**: The EIA RECS and ACS datasets are **cross-sectional**. Therefore, a **Difference-in-Differences (DiD)** fallback is **methodologically impossible**. The system implements a **Graceful Degradation Protocol**: if PSM fails, the system checks for longitudinal data. If absent (which it is), it raises a `DataUnavailableError` and halts with a clear error message. No invalid DiD estimation is performed.

### Statistical Rigor

- **Multiple Comparisons**: Not applicable (single primary outcome per model), but sensitivity sweep (FR-006) addresses parameter uncertainty.
- **Sample Size/Power**: Minimum 50 adopters required for valid PSM (SC-004). Power limitations will be acknowledged if sample size is insufficient.
- **Causal Assumptions**: Unconfoundedness (selection on observables) is assumed; validated via **placebo tests on pre-treatment covariates** (e.g., years in residence) since true pre-treatment outcomes are unavailable in cross-sectional data (FR-009).
- **Measurement Validity**: Variables are drawn directly from EIA RECS and ACS; no constructed proxies without data support (Constitution Principle VII).
- **Collinearity**: Predictors (income, housing type, location) are distinct; no definitional overlap. Correlation will be reported descriptively.
- **Ecological Fallacy**: Tract-level home value is used as a proxy for individual appreciation. This is acknowledged as a limitation; the outcome is interpreted as a "Tract-Level Socioeconomic Proxy" rather than an individual causal effect.

### Dataset Strategy

| Dataset | Purpose | Source URL | Variables Used | Feasibility Check |
|---------|---------|------------|----------------|-------------------|
| **EIA RECS 2020** | Primary microdata for household energy costs, income, solar adoption, housing type | ` (Official) | `energy_cost`, `income`, `solar_installation`, `housing_type`, `census_tract` | ✅ Verified; CSV format; directly downloadable. Contains required variables. |
| **ACS 2020 Housing** | Socioeconomic proxies (median home value by tract) | `https://data.census.gov/cedsci/` (via verified API or FTP) | `home_value` (tract-level median) | ✅ Verified; Parquet/CSV format. Note: `home_value` is tract-level, not individual. |
| **PSM/SMD** | Methodological references (no dataset) | N/A | N/A | ✅ No dataset needed; methods implemented in code |

**Data Availability Note**: The EIA RECS and ACS datasets are open and programmatically downloadable. No gated data (e.g., ADNI, UK Biobank) is used. If the merged dataset exceeds available system memory, streaming (`datasets.load_dataset(..., streaming=True)`) will be used to process in chunks.

**Dataset-Variable Fit**:
- **Required**: `energy_cost`, `income`, `solar_installation` (treatment), `housing_type`, `census_tract`, `home_value`.
- **Available**: EIA RECS contains `energy_cost`, `income`, `solar_installation`, `housing_type`, `census_tract`. ACS contains `home_value` at the tract level.
- **Match**: ✅ All required variables are present. **Merge Strategy**: Household-level RECS data is merged with tract-level ACS data using `census_tract` as the key. Tract-level variables are broadcast to all households in that tract.
- **Limitation**: The `home_value` outcome is a tract-level proxy, not an individual measure. This introduces ecological fallacy risk, which is acknowledged in the analysis.

**Longitudinal Data Check**: The plan explicitly verifies that no pre/post data exists for DiD. If DiD is attempted, the system halts with "Longitudinal Data Not Available".

## Compute Feasibility

- **CPU-First**: All methods (PSM, OLS) are classical statistics and run efficiently on CPU. No GPU required.
- **Memory**: RECS/ACS merged dataset (~100k–500k rows) fits within 7 GB RAM. If larger, streaming is used.
- **Time**: Pipeline expected to complete in < 2 hours on 2 CPU cores.
- **GPU Escape Hatch**: Not needed; no transformer/diffusion models or CUDA kernels.

## Implementation Phases

### Phase 0: Setup & CI Enforcement
- Create `requirements.txt` with pinned dependencies.
- Create `.github/workflows/ci.yml` with PII scanner (`detect-secrets`) and `pytest` runner.
- Set up directory structure (`data/raw`, `data/processed`, `src/`).

### Phase 1: Data Ingestion & Preprocessing
- Download EIA RECS and ACS datasets; verify checksums.
- Merge datasets on `census_tract`; filter for low-income tracts (income < 150% FPL).
- Construct binary `treatment` (solar_installation = 1), `energy_cost_burden` (energy_cost / income), and `home_value` (tract-level median).
- **Handle outliers**: Apply log-transformation to `energy_cost` (with epsilon offset) and winsorize at 1st/99th percentiles.
- Handle missing values: impute or flag for exclusion (FR-002).

### Phase 2: Propensity Score Matching
- Fit propensity score model (logistic regression) using covariates: `income`, `housing_type`, `location`, `age`, `race`, `education`.
- Apply common support check; exclude units outside overlap (FR-007).
- Perform 1:1 nearest-neighbor matching with caliper 0.05 (FR-003).
- Validate balance: calculate SMD for all covariates; ensure SMD ≤ 0.1 (FR-004, SC-001).
- Run placebo test on pre-treatment covariate (FR-009). If p < 0.05, halt with "Unconfoundedness Violation".
- **PSM Failure**: If balance fails, halt with "Causal Identification Failure".

### Phase 3: Causal Effect Estimation
- Estimate ATT via OLS regression on matched sample with cluster-robust SE (FR-005).
- Perform sensitivity sweep: re-run PSM with calipers {0.01, 0.05, 0.1}; re-apply common support check for each; report ATT variation (FR-006, SC-003).

### Phase 4: Output & Validation
- Generate `data/outputs/att_results.json` with ATT estimate, p-value, CI, method, sensitivity data, balance status, and placebo test result.
- Generate `data/outputs/sensitivity_report.md` with caliper sweep results.
- Run unit tests (`tests/unit/test_psm.py`, `test_did.py`) and contract tests (`tests/contract/test_schemas.py`).

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Low-income filter yields < 50 adopters | Halt and report power limitation (SC-004). |
| PSM balance fails (SMD > 0.1) | Halt with "Causal Identification Failure" error. |
| Placebo test fails (p < 0.05) | Halt with "Unconfoundedness Violation" error. |
| Missing longitudinal data for DiD | Raise `DataUnavailableError` and halt (Graceful Degradation). |
| Dataset exceeds 7 GB RAM | Use streaming (`streaming=True`) to process in chunks. |
| PII leakage in data | CI pipeline fails on PII detection; no raw data committed. |
| Ecological Fallacy | Acknowledge in output; interpret tract-level home value as a proxy. |

## Limitations

- **Cross-Sectional Data**: The project relies on cross-sectional data, making DiD impossible. If PSM fails, no valid causal estimate is produced.
- **Ecological Fallacy**: Tract-level home value is used as a proxy for individual appreciation. Results are interpreted as tract-level effects.
- **Scaling Laws**: Scaling Law Analysis (T070-T074) is out of scope per Constitution Principle VI and the current spec (FR-001 to FR-009).