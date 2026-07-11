# Research: Predicting the Impact of Processing Temperature on the Grain Size of Rolled Aluminum Alloys

## Summary of Research

This research phase validates the feasibility of the data sources and defines the statistical methodology. The primary challenge is the scarcity of public datasets containing *both* rolling temperature and grain size for aluminum alloys. The plan prioritizes NOMAD, with a strict fallback to "Data Missing" if no source contains all required variables.

**Critical Finding**: The provided "Verified datasets" block contains no specific materials science datasets with the required variables. The NOMAD structure CSV is the only candidate, but it is primarily DFT/crystallographic data. The methodology is designed to handle the high probability of a "Data Missing" outcome as a valid scientific conclusion regarding the state of public data, rather than a pipeline failure.

## Dataset Strategy

The project targets three specific variables: `rolling_temperature` (°C), `alloy_composition` (wt% of Mg, Si, Cu, etc.), `grain_size` (µm), and `process_type` (to filter for Rolling).

| Dataset Source | Status | Variables Available | Verified URL | Usage Strategy |
|----------------|--------|---------------------|--------------|----------------|
| **NOMAD** | **Verified** (Structure CSV) | Likely contains crystallographic data; *Rolling Temp*, *Grain Size*, and *Process Type* are uncertain and must be pre-checked. | ` | Attempt download. Run schema pre-check for `rolling_temperature`, `grain_size`, and `process_type`. <br> **If missing**: Halt immediately with `E_DATA_MISSING`. <br> **Note**: This dataset is primarily DFT/crystallographic. The probability of finding experimental rolling process parameters is low. This outcome is treated as a valid finding (Data Unavailability). |
| **OpenML** | **Verified** (Generic) | Contains various materials datasets; specific "Aluminum Rolling" dataset must be identified by ID. | *No verified URL in the provided block matches this requirement.* The provided block contains text/code corpora (C4, Solidity). | **CRITICAL**: No verified URL in the provided block is suitable for this specific materials science task. The plan relies solely on the NOMAD pre-check. If NOMAD fails, the project halts. |
| **Materials Project** | **Assumed Missing** | Crystallographic data only; lacks processing history. | (Not in verified block) | Skip immediately via schema pre-check logic. |
| **Citrination** | **Assumed Missing** | Requires API key/registration; likely not in verified block. | (Not in verified block) | Skip. |

> **Note on Data Availability**: The "Verified datasets" block provided for this project contains primarily text/code corpora (C4, Solidity, etc.) and a generic NOMAD structure CSV. **No verified URL in the block explicitly guarantees the presence of `rolling_temperature` and `grain_size` for aluminum alloys.** The implementation MUST perform a schema pre-check on the NOMAD CSV. If the columns are absent, the project MUST halt with `E_DATA_MISSING` and not proceed to modeling. This halt is a valid scientific outcome.

## Methodological Rigor

### Statistical Approach
1. **Baseline**: Ordinary Least Squares (OLS) Linear Regression with interaction terms ($Temp \times Element$).
 * *Rationale*: Provides interpretable coefficients for main effects and linear interactions.
 * *Sample Size Constraint*: If $N < 100$, the pipeline will **skip** Random Forest training to prevent overfitting and proceed only with Linear Regression.
2. **Non-Linear**: Random Forest Regressor.
 * *Rationale*: Captures non-linear saturation effects and complex interactions without assuming a specific functional form.
 * *Condition*: Only executed if $N \ge 100$.
 * *Hyperparameters*: `n_estimators` [50, 100], `max_depth` [5, 10].
 * *Grid Search*: 5-fold Cross-Validation on the training set.
3. **Data Splitting**:
 * **Strategy**: Split by `source_study` (or `process_batch`) to prevent leakage of processing conditions.
 * **Correction**: Do NOT stratify by alloy series (a predictor variable), as this does not prevent leakage of outcome data if processing conditions are shared. If `source_study` metadata is missing, use random split with a warning.
4. **Confounder Analysis**:
 * **With Proxies**: Compare $R^2$ of model with vs. without proxy variables (e.g., strain rate).
 * **Without Proxies**: Perform **E-value calculation** to estimate the minimum strength of an unmeasured confounder required to explain away the observed effect. This replaces the "N/A" default with a quantitative sensitivity bound.

### Addressing Rigor Requirements
* **Multiple Comparisons**: Not applicable for regression coefficients directly, but the sensitivity analysis (FR-005) sweeps thresholds to ensure robustness of feature importance rankings.
* **Sample Size/Power**: **Hard Stop**: If $N < 50$, halt with `E_INSUFFICIENT_DATA`. If $50 \le N < 100$, disable non-linear modeling. This ensures statistical validity.
* **Causal Inference**: The study is **observational**. All claims will be framed as "associational" or "predictive." No causal claims of "impact" will be made without randomization.
* **Collinearity**:
 * Compute correlation matrix for all predictors.
 * If $|r| > 0.8$ between $Mg$ and $Si$ (common in 6xxx series), report as a "Joint Effect" rather than independent coefficients (FR-006).
* **Measurement Validity**: Grain size and composition are treated as ground truth from source literature. No internal validation is performed.
* **Process Context**: Filter data to include only `process_type == "Rolling"`. Exclude Casting, SPD, etc., to ensure the "Industrial Rolling Context" (Constitution Principle VII).

## Compute Feasibility
* **Hardware**: 2 CPU cores, 7GB RAM, No GPU.
* **Strategy**:
 * Use `scikit-learn` (CPU optimized).
 * Limit grid search to small ranges.
 * Implement a 4-hour timeout for the training step. If exceeded, fallback to default parameters.
 * Sample data if $N > 10,000$ to ensure fit within 7GB RAM.
 * **Critical**: If NOMAD lacks required columns, the script exits immediately, saving compute time.