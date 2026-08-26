# Research: Developing Novel Solutions to Address Energy Inequity in Low-Income Communities

## 1. Problem Statement & Methodological Approach

The core research question is: **What is the causal effect of clean-energy adoption (solar/microgrid) on energy costs and socioeconomic outcomes for low-income US households?**

### Methodological Strategy
The project employs a **Propensity Score Matching (PSM)** design to approximate a randomized controlled trial (RCT) using observational data.
1. **Treatment**: Binary indicator of clean-energy adoption.
2. **Control**: Non-adopting households matched on pre-treatment covariates (income, housing type, location).
3. **Outcome**: **Primary**: `log(energy_cost)` (to avoid definitional circularity with income). **Descriptive**: Energy Cost Burden (Cost/Income) and home value changes (if data available).
4. **Estimation**: Average Treatment Effect on the Treated (ATT) via OLS on the matched sample with cluster-robust standard errors.
5. **Validation**: Standardized Mean Difference (SMD) < 0.1 for all covariates; placebo test on pre-treatment outcomes (if longitudinal data exists).
6. **Fallback**: If PSM balance fails, the system checks for longitudinal data. If longitudinal data is present, it switches to Difference-in-Differences (DiD). If longitudinal data is absent (e.g., cross-sectional RECS), the system logs "DiD Skipped: Data Unavailable" and reports the PSM results (or failure) without attempting DiD.

### Reviewer Feedback Integration (Geoffrey West)
Reviewer comments highlighted the absence of scaling laws in the initial plan. While the primary causal question is micro-level (household), the plan will include an **exploratory scaling analysis** module. This module will test whether energy consumption in low-income tracts follows the sublinear scaling observed in cities (West et al., 2012) or deviates due to inequity. **Crucially, this scaling analysis is strictly descriptive and is excluded from the causal ATT estimation and claims.** It addresses the "novel solutions" context without conflating macro-level scaling with micro-level causality.

## 2. Dataset Strategy

The analysis relies on two primary public datasets. The plan strictly adheres to the "Verified datasets" constraint: **only URLs explicitly verified in the spec block or official programmatic sources will be cited.**

| Dataset | Role | Verified Source / Access Method | Feasibility Note |
|:--- |:--- |:--- |:--- |
| **EIA RECS** | Primary microdata for energy costs, housing characteristics, and adoption status. | **Official Source**: ` (or via `eia` Python package). **Fallback**: Verified HuggingFace proxy if official fails, but **only if** schema matches. | **Critical Gap**: If the verified source lacks `solar_installation`, `energy_cost`, or `income`, the pipeline **halts** with a "Data Mismatch" error. No synthetic data is used. |
| **ACS** | Census tract level demographics (median income, poverty rate) for filtering low-income tracts. | **Programmatic**: `censusdata` Python library (ACS 5-Year Estimates). | **Solution**: Uses API to fetch tract-level median income dynamically, satisfying the "tract-level" requirement of the spec without needing a static CSV. |
| **PSM/SMD** | Algorithmic methods (not datasets). | N/A | Implemented via `scikit-learn` and `statsmodels`. |

### Data Availability & Feasibility Assessment
* **CPU-First**: All operations (merge, PSM, OLS) are classical statistical methods executable on CPU. No GPU is required.
* **Memory**: The RECS dataset (typically ~50k-100k rows) fits comfortably within 7 GB RAM.
* **Data Mismatch Warning**: The implementation will perform a **Schema Validation** step immediately after ingestion. If required columns are missing, the process terminates with a clear error code. It does not proceed with a fallback question.
* **Longitudinal Data**: If the EIA RECS dataset lacks pre/post variables (common for cross-sectional cycles), the system will set `did_available = False` and skip the DiD attempt, reporting the constraint.

## 3. Statistical Rigor & Assumptions

* **Outcome Variable Correction**: To address the circularity of `Burden = Cost / Income`, the primary causal outcome is `log(energy_cost)`. `Income` is used as a covariate in PSM to balance groups but is **not** used in the final outcome regression. This breaks the mechanical link.
* **Unconfoundedness**: Assumes that conditional on observed covariates (income, housing, location), treatment assignment is independent of potential outcomes. This is the primary limitation of observational PSM.
* **Common Support**: Observations with propensity scores near 0 or 1 will be excluded (FR-007) to ensure overlap between treatment and control groups.
* **Multiple Comparisons**: The sensitivity sweep (3 calipers) will be reported descriptively. If hypothesis testing is performed across multiple outcomes, a Bonferroni or Benjamini-Hochberg correction will be applied to control family-wise error rate.
* **Power**: A minimum of 50 adopters is required (SC-004). If the filtered sample has <50 adopters, the analysis will halt and report a power limitation.
* **Collinearity**: Income and energy cost burden are mathematically related. The analysis will treat `log(energy_cost)` as the outcome and `Income` as a covariate in PSM, but will explicitly acknowledge the definitional relationship in the interpretation of coefficients.

## 4. Compute Feasibility

* **Environment**: GitHub Actions Free Tier (2 CPU, 7 GB RAM).
* **Strategy**:
 * Use `pandas` for in-memory data manipulation.
 * Use `scikit-learn`'s `LogisticRegression` for propensity score estimation (CPU optimized).
 * Use `statsmodels` for OLS with `cluster` option (CPU optimized).
 * No model training or fine-tuning; purely statistical estimation.
* **GPU Escape Hatch**: Not required. If the dataset size unexpectedly exceeds 14 GB (unlikely for RECS), the plan will implement streaming or chunked processing, not GPU offloading.

## 5. Decision Rationale

* **Why PSM?** It is the standard method for causal inference in observational social science when RCTs are impossible. It directly addresses the "selection on observables" assumption required by the constitution.
* **Why not DiD as primary?** DiD requires longitudinal data (pre/post treatment). RECS is typically cross-sectional. DiD is only a fallback if panel data is found or if a synthetic panel can be constructed (which is high risk). The plan now explicitly checks for data availability before attempting DiD.
* **Why `log(energy_cost)`?** To avoid the tautology of `Burden = Cost / Income`. Using `log(Cost)` as the outcome allows for a valid causal estimate of the treatment's effect on energy expenditure, independent of the denominator.
* **Why the specific verified URLs?** The project constitution mandates that no URLs be invented. The plan uses the official EIA source and the `censusdata` API, which are verified and programmatic.