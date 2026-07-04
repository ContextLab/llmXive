# Research: Statistical Analysis of Publicly Available Election Poll Aggregates

## Overview

This research document outlines the data strategy, methodological approach, and feasibility analysis for comparing polling aggregation methods. It addresses the specific requirements of the feature specification, ensuring that all Functional Requirements (FRs) and Success Criteria (SCs) are supported by viable data sources and statistical techniques.

## Dataset Strategy

The project relies on verified sources only. **RealClearPolitics (RCP) is excluded** from the implementation scope because no verified URL exists in the allowed list, ensuring compliance with the 'Verified Accuracy' principle.

| Dataset Name | Description | Verified Source URL | Usage Strategy |
|:--- |:--- |:--- |:--- |
| **FiveThirtyEight Polls** | Comprehensive archive of US election polls with pollster metadata, sample sizes, and historical accuracy. | `https://projects.fivethirtyeight.com/polls/` | Primary source. Data will be downloaded via `requests` and parsed. This source is verified and stable. |
| **Election Outcomes** | Final popular vote results by state/year. | ` (MIT Election Data and Science Lab) | Used as ground truth for RMSE/MAE calculations. Specific CSV files from MEDSL are cited to ensure deterministic ingestion. |

**Dataset Variable Fit Check**:
- **Required Variables**: `date`, `pollster`, `vote_share` (or candidate margin), `sample_size`, `state` (if applicable), `election_year`.
- **FiveThirtyEight Fit**: Contains all required variables. Historical RMSE is pre-calculated or derivable from past election results.
- **Missing Data Handling**: If a required variable (e.g., sample size) is missing for a specific poll, the system will impute using the median sample size for that pollster or exclude the poll with a warning, as per FR-008.

## Methodological Approach

### 1. Data Harmonization (FR-001, FR-002)
- **Ingestion**: Parse CSV/JSON from verified sources (FiveThirtyEight only).
- **Cleaning**: Standardize date formats to weekly bins (e.g., "2020-10-01" to "2020-10-05").
- **Strict Temporal Separation (Look-Ahead Bias Prevention)**:
 - **Training Window Definition**: Weights for a given election cycle (Year T) are calculated **strictly** using historical RMSE from cycles **T-1, T-2,...** (all prior cycles).
 - **Exclusion Rule**: No data from Year T (including polls released in Year T) is used to derive weights for Year T.
 - *Formula*: $RMSE_{pollster, \text{train}} = \sqrt{\frac{1}{N} \sum_{k < T} (forecast_{i, k} - outcome_{i, k})^2}$
 - *Default*: If a pollster has no history prior to Year T, assign the **median RMSE of all pollsters** calculated from all prior cycles (T-1, T-2,...).
 - **Validation**: The `weights.py` script will include a check to ensure the `election_year` of the data used for RMSE calculation is strictly less than the `election_year` of the forecast being generated.
- **Global Checks**:
 - **FR-010**: If total poll count < 500, halt and report error.
 - **FR-008**: If < 5 polls in 30 days OR < 3 distinct election cycles, halt and report warning.

### 2. Frequentist Aggregation (FR-003, FR-004)
- **Simple Average**: $\hat{y}_{t} = \frac{1}{n} \sum_{i=1}^{n} y_{i,t}$
- **Weighted Average**: $\hat{y}_{t} = \sum_{i=1}^{n} w_{i} y_{i,t}$ where $w_{i} = \frac{1/RMSE_{i}}{\sum (1/RMSE_{j})}$.
- **Normalization**: Weights are normalized to sum to 1.0.

### 3. Bayesian Hierarchical Modeling (FR-005)
- **Model Structure**:
 - **Latent State**: $\theta \sim \text{Normal}(\mu_{prior}, \sigma_{prior}^2)$ (Static parameter representing the final election outcome).
 - **Observation**: $y_{i,t} \sim \text{Normal}(\theta, \tau_{i,t}^2)$
 - **Time-Decay Variance**: $\tau_{i,t}^2$ decreases as $t$ approaches election day to model increasing poll precision.
 - Priors: Weakly informative priors for $\mu_{prior}$ and $\sigma_{prior}$.
- **Inference**: NUTS sampler (PyMC).
- **Feasibility**: Runs on CPU. Will use a subset of data or a simplified model if convergence takes > 4 hours.
- **Correction**: The model replaces the invalid "Random Walk" formulation to correctly model the static nature of the election outcome.

### 4. Evaluation & Comparison (FR-006, SC-001, SC-002, SC-003)
- **Metrics**: RMSE, MAE against actual election outcomes.
- **Calibration**: Calculate the proportion of actual outcomes falling within the 95% Credible Interval (CI). Target: $\ge 90\%$ (SC-002).
 - **Statistical Test**: Binomial test against null hypothesis $p_0 = 0.95$ (nominal level).
- **Significance**: **Hierarchical Meta-Analysis** of Mean Absolute Errors (MAE) across the 10 election cycles.
 - **Method**: Treat each election cycle as a cluster. Compare the mean MAE of the three methods using a random-effects meta-analysis.
 - **Multiple Comparison Correction**: Apply **Westfall-Young permutation-based correction** for multiple comparisons (FR-006).
 - **Rationale**: The errors of the Simple, Weighted, and Bayesian methods are highly correlated because they are derived from the same underlying poll data. Standard methods like Benjamini-Hochberg assume independence or positive dependence and may fail to control the Family-Wise Error Rate (FWER) under this correlation structure. The Westfall-Young method resamples the joint distribution of errors to account for this dependency, ensuring valid Type I error control.
 - **Implementation**: The `meta_analysis.py` module will perform a sufficient number of permutations of the method labels within each cycle to generate the null distribution for the test statistics.
- **Causal Framing**: All results framed as "predictive accuracy" and "associational uncertainty" (FR-007).

## Statistical Rigor & Constraints

- **Multiple Comparisons**: Since we compare multiple methods (pairwise tests), we apply a Westfall-Young correction to control the Family-Wise Error Rate (FWER) under dependency.
- **Power Justification**: The dataset spans multiple election cycles with hundreds of polls. This is sufficient for estimating RMSE and conducting meta-analysis.
- **Causal Assumptions**: The study is observational. Claims are limited to "forecast accuracy" and "calibration," not causal voter behavior.
- **Collinearity**: Polls from the same pollster are not independent. The hierarchical model accounts for this via the latent state $\theta$.

## Compute Feasibility

- **Hardware**: 2 CPU cores, 7GB RAM.
- **Strategy**:
 - PyMC will be run with `target_accept=0.9` and `tune=1000, draws=1000` (adjustable).
 - If the full dataset causes memory issues, we will sample [deferred] of polls per cycle (stratified by pollster).
 - No GPU usage. No 8-bit quantization.
 - Total runtime target: < 4 hours.