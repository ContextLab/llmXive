# Research: Investigating the Impact of Telomere Length on Lifespan Variation in Wild Bird Populations

## Executive Summary

This research phase defines the data strategy, statistical methodology, and computational feasibility for analyzing the relationship between telomere length and lifespan in wild birds. The core challenge is integrating heterogeneous data from Dryad (telomere) and AnAge (longevity/ecology) while accounting for phylogenetic non-independence. The analysis will use Phylogenetic Generalized Least Squares (PGLS) to test the primary hypothesis (telomere length predicts lifespan) and the secondary hypothesis (migration status moderates this relationship).

**Unit of Analysis**: Species. The analysis aggregates individual measurements to species means (filtered for early-life) and regresses against species-level maximum lifespan. The sample size `N` is the number of species, not the number of individuals.

## Dataset Strategy

### Data Discovery (Phase 0)
Before ingestion, the pipeline executes a **Data Discovery** step to identify specific dataset IDs.
- **Dryad Query**: The pipeline runs a Dryad API search for `query: "telomere" AND "bird" AND "wild"`.
- **Success Condition**: If the query returns a list of dataset IDs (e.g., ``), the pipeline proceeds.
- **Failure Condition**: If the query returns zero results, the pipeline halts with a `Data Discovery Error` and logs the query used. This prevents the "blind halt" and ensures a defined mechanism for ID discovery.
- **AnAge**: The pipeline targets the AnAge database export (specifically the `anage.csv` or API endpoint for maximum lifespan and ecological traits).

### Data Sources

| Data Type | Source | Description | Access Strategy | Verified URL |
|-----------|--------|-------------|-----------------|--------------|
| Telomere Length | Dryad | Raw CSVs of telomere measurements (qPCR/TRF) from wild bird studies. | Programmatic fetch via Dryad API using IDs found in Phase 0. | *Determined by Phase 0 Query (e.g.,)* |
| Longevity & Ecology | AnAge | Species-level maximum lifespan, migration status, body mass. | Programmatic fetch via AnAge API or parsing of the AnAge CSV export. | *AnAge Database (via API/Export)* |
| Phylogeny | Jetz et al. (2012) | Global bird phylogeny (Hackett backbone). | Download via `rotl` (R package) using the species list from the merged dataset. | ` Name or service not known)"))] (via `rotl`) |

**Critical Gap Handling**: If the specific Dryad/AnAge datasets required for the spec's "Assumptions" (>15 species) are not accessible via the implementation's fetch logic, the pipeline will halt with a "Data Availability Error" and log the missing species. This prevents the "inappropriate dataset" fatal flaw.

### Data Integration Plan

1. **Ingestion**: Download raw CSVs. Log checksums (Principle III).
2. **Standardization**:
 * Convert all telomere lengths to **kilobases (kb)**.
 * If a study reports relative units (qPCR Ct) without a standard curve, flag as "unconvertible" and exclude from primary analysis (US-1, FR-002).
 * **Filter for Early-Life**: Retain only records where `age` is "juvenile", "fledgling", or "hatch-year". If age is unknown, exclude the record (to avoid confounding by sampling age structure).
 * **Tissue Filter**: Retain only blood or feather samples; exclude others if metadata indicates high variability.
3. **Merging**: Join on `species_name` (standardized spelling).
 * Records in Dryad but missing in AnAge: Exclude from analysis, log to `missing_data_log.csv`.
 * Records in AnAge but missing in Dryad: Ignored (no telomere data).
 * **Aggregation**: Calculate species-mean telomere length from the filtered individual records.
4. **Phylogeny Alignment**:
 * Fetch the **Jetz et al. (2012)** tree using `rotl` in R, matching the exact species list from the merged dataset.
 * If <15 species remain, the pipeline will proceed with a **Low Power** flag (see Statistical Methodology).

## Statistical Methodology

### Primary Model: PGLS
* **Model Formula**: `lifespan ~ telomere_length + tissue_type + phylogenetic_covariance`
 * *Note*: `tissue_type` is included as a covariate to control for biological confounds (addressing scientific soundness concerns). `age` is controlled via the strict early-life filter.
* **Method**: Phylogenetic Generalized Least Squares (PGLS).
* **Rationale**: Accounts for evolutionary non-independence among species (Assumption: Methodological Validity). A simple LMM is insufficient.
* **Implementation**: **R** `phylolm` package (via `rpy2` from Python).
 * **Iterative Lambda**: `phylolm` estimates Pagel's lambda iteratively during model fitting, satisfying the requirement for signal estimation (addressing methodology concern).
* **Assumptions**:
 * **Associational**: Findings are framed as associational, not causal (Assumption: Observational Framing).
 * **Collinearity**: Telomere length and body mass may be correlated; if collinearity is high (VIF > 5), report descriptive relationship and acknowledge limitation.
 * **Unit of Analysis**: Species-Mean. The sample size `N` is the number of species (not individuals).

### Secondary Model: Moderator Analysis
* **Model Formula**: `lifespan ~ telomere_length * migration_status + phylogenetic_covariance`
* **Goal**: Test if the slope of telomere length on lifespan differs between "Migratory" and "Resident" species.
* **Degrees of Freedom Check**:
 * If `N < 30`, the interaction model is **skipped** to avoid overfitting (scientific soundness).
 * A flag `interaction_skipped_low_power` is set to `true` in the output.
 * The `ModelResult` schema marks `interaction_effect` and `p_value_interaction` as **optional** in this case.

### Sensitivity Analysis (Robustness)
* **Method**: Leave-One-Out Cross-Validation (LOOCV) by species.
 * If species count < 10, switch to Jackknife by study.
* **Goal**: Ensure the telomere-lifespan coefficient is not driven by a single high-impact study (FR-006).
* **Output**: Range of coefficients and stability metric (SC-004).

### Power and Sample Size
* **Metric**: **Partial R-squared** (or standardized regression coefficient) for continuous regression, NOT Cohen's d.
* **Calculation**: Simulation-based power analysis for PGLS (e.g., using `pwr` or custom simulation in R) based on the final species count (N).
* **Reporting**: If power < 0.8, explicitly state this limitation in the results (SC-005).
* **Correction**: The previous reference to "Cohen's d" was a construct validity error; this plan uses the correct metric for regression.

### Low Power / Convergence Fallback
* If `N < 15`:
 1. Attempt PGLS with iterative lambda estimation.
 2. If convergence fails or lambda estimation is unstable (wide CIs):
 * Re-fit model with **fixed lambda = 0** (no phylogeny) and **fixed lambda = 1** (Brownian Motion).
 * Report results as "Low Power: Model fitted with fixed lambda. Interpret with caution."
 * **Do NOT skip the analysis**; report the wide confidence intervals and power estimates. This provides scientific value even in low-power scenarios (addressing scientific soundness concern).

## Computational Feasibility

* **Hardware**: GitHub Actions Free Tier (2 CPU, 7 GB RAM, 6h limit).
* **Strategy**:
 * **No GPU**: All operations are CPU-based.
 * **Memory**: Data subset to < 2 GB. PGLS matrix operations on < 500 species are trivial for 7 GB RAM.
 * **Libraries**: Use `rpy2` to call R (`phylolm`, `ape`, `rotl`). Avoid heavy deep learning libraries.
 * **Timeout**: The pipeline is linear and lightweight; expected runtime < 30 minutes.
 * **Tree Fetching**: The tree is downloaded from `rotl` *after* species list is known, ensuring the covariance matrix is valid and avoiding circular dependencies.