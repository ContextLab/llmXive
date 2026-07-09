# Research: The Impact of Simulated Social Exclusion on Subsequent Prosocial Behavior

## Dataset Strategy

The project relies on aggregating open behavioral datasets containing social exclusion manipulations (e.g., Cyberball) and prosocial outcomes (monetary donation/allocation).

**Constraint**: Per the project constitution and input requirements, we must use **ONLY** the verified dataset URLs provided in the "# Verified datasets" block. We **cannot** invent URLs or assume the existence of specific OSF datasets if they are not in the verified list.

### Verified Datasets Analysis

Upon review of the provided "Verified datasets" block, the following observations are made regarding the specific needs of this study:

1.  **Requirement**: Datasets must contain `condition` (exclusion vs. inclusion), `prosocial_amount` (continuous or binary outcome), and `randomized` flag.
2.  **Available Sources**:
    *   `OSF (parquet)`: Contains log-likelihood and graph covariate data. These appear to be network/graph datasets, not behavioral exclusion/prosociality experiments.
    *   `RCTs (jsonl)`: Contains TSAR (Task-oriented Sentence Rewriting) data and PubMed RCT metadata. These are NLP or medical trial metadata, not social exclusion behavioral data.
    *   `IRI (jsonl)`: Contains IRI (Interpersonal Reactivity Index) QA data and the Iris dataset. The Iris dataset is a classic botanical dataset; the IRI data is QA, not behavioral experiment results.
    *   `ZIG (jsonl)`: Contains image data ("zigwheels") and zip files. Irrelevant.
    *   `NOT (json)`: Contains notebook error logs. Irrelevant.
    *   `URLs (json)`: Contains URL lists. Irrelevant.
    *   `AnalysisResult (parquet)`: Contains analysis results, but not the raw experimental data needed to *generate* those results.

**Critical Finding**: The provided "Verified datasets" block **does not contain** any dataset that matches the specific requirements of this study (Social Exclusion + Prosocial Behavior). The available datasets are related to NLP, graph theory, medical metadata, or generic QA, but none contain the `condition`, `prosocial_amount`, or `randomized` columns required for FR-001.5.

### Implication for Implementation

Since the spec assumes "The Open Science Framework contains at least 3 public datasets..." (Assumption in spec), but the **verified** list provided to the plan contains none, the implementation pipeline **MUST** handle this gracefully:

1.  **Halt Condition**: As per FR-008 and US-1, if fewer than 3 valid datasets are found, the system MUST halt.
2.  **Strategy**: The `ingestion.py` script will attempt to load the provided verified URLs. It will perform schema validation. Since none of the verified URLs contain the required columns, they will all be rejected.
3.  **Outcome**: The pipeline will trigger the "Insufficient Data" error and exit with a non-zero status code, satisfying the spec's requirement to prevent analysis on invalid data.

**Note**: If the user intended for the system to *fetch* real OSF datasets (e.g., by querying OSF API directly), this capability is **not** supported by the current "Verified datasets" constraint which forbids inventing URLs. The plan strictly adheres to the provided verified list. If the verified list is updated in the future to include actual OSF behavioral datasets (e.g., from `cjziems` or `SreekarB` that actually contain the right schema), the ingestion logic will proceed.

**Decision**: The plan proceeds with the ingestion logic designed to validate against the *schema*. The *result* of running this plan on the current verified list will be a graceful halt due to insufficient valid data, which is the correct behavior per FR-008.

## Statistical Methodology

### Model Selection
*   **Primary Model**: Zero-Inflated Gamma (ZIG) or Hurdle Model.
    *   *Rationale*: Prosocial donation data is typically right-skewed with a high frequency of zeros (non-donors). Standard OLS assumes normality; Gamma GLM cannot handle zeros. ZIG/Hurdle models the probability of zero (logistic component) and the positive amount (gamma component) separately.
*   **Alternative Model**: Logistic Regression.
    *   *Trigger*: If `prosocial_amount` is binary (0/1) rather than continuous.

### Pooling Strategy & Meta-Analysis
The analysis will be split into two pools:
1.  **Causal Pool**: Only datasets where the `randomized` flag is explicitly `true`.
2.  **Associational Pool**: Datasets where `randomized` is `false` or `unknown`.

**Meta-Analysis Unit**: The ZIG/Hurdle model yields two distinct coefficients:
1.  **Zero-Inflation Component**: Log-odds of the probability of donating (vs. not donating).
2.  **Gamma Component**: Log-scale of the amount donated (conditional on donating).

The meta-analysis will **pool these two effect sizes separately**. We will calculate a pooled log-odds ratio for the zero-inflation component and a pooled log-mean ratio for the Gamma component. This dual-component approach ensures construct validity, as ignoring one component would misestimate the total causal effect of exclusion on prosocial behavior.

*   **Method**: Random-Effects Meta-Analysis (DerSimonian-Laird or REML) for both components.
*   **Metric**: Pooled effect size (coefficient $\beta$) and heterogeneity ($I^2$) for each component.
*   **Requirement**: Minimum 3 datasets per pool to calculate $I^2$ and pooled effect.

### Sensitivity Analysis (Revised)
The previous plan proposed a "zero-inflation threshold" sweep, which is methodologically invalid for ZIG/Hurdle models as the zero state is a latent class, not a continuous threshold. The revised sensitivity analysis will:
1.  **Link Function Sweep**: Re-run the zero-inflation component using **logit** vs. **probit** link functions.
2.  **Distributional Assumption Sweep**: Re-run the positive component using **Gamma** vs. **Log-Normal** distributions.
3.  **Stability Metric**: The variance of the effect size coefficient ($\beta$) across these sweeps must be < 10% for the result to be considered robust.

### Meta-Analytic Power Assessment
To address the risk of Type II error (false negative) in the meta-analysis:
*   **Method**: Calculate the detectable effect size given the number of studies ($k$), their sample sizes, and observed heterogeneity ($I^2$).
*   **Tool**: Use the `metafor` package (or equivalent in Python) to estimate power.
*   **Reporting**: Report the minimum detectable effect size (MDES) for the pooled analysis. If the observed effect is smaller than the MDES, the study will be flagged as potentially underpowered.

## Statistical Rigor & Assumptions

*   **Multiple Comparisons**: Not applicable for the primary single hypothesis (exclusion effect), but sensitivity sweeps are descriptive.
*   **Power**: The system will filter datasets with $n_{exclusion} < 5$ (FR-006) AND perform a formal meta-analytic power assessment (see above).
*   **Causal Assumptions**:
    *   *Randomization*: Assumed valid for the Causal Pool.
    *   *Unconfoundedness*: Cannot be guaranteed for the Associational Pool; results will be framed as "associational".
*   **Collinearity**: If covariates (e.g., empathy) are present, VIF will be checked. However, the primary analysis is univariate (Condition -> Amount) to maximize data compatibility across heterogeneous datasets.

## Compute Feasibility

*   **Environment**: GitHub Actions Free Tier (limited CPU, 7 GB RAM).
*   **Strategy**:
    *   No GPU required (ZIG/Hurdle via `statsmodels` or `scipy` on CPU).
    *   Data size: Estimated < 100 MB total (CSV/Parquet).
    *   Runtime: < 1 hour for ingestion and analysis.
    *   Libraries: `pandas` (CPU), `statsmodels` (CPU), `scipy` (CPU), `metafor` (or equivalent). No heavy transformers or LLMs.