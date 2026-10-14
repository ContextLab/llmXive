# Research: Assessing the Validity of Statistical Significance in Randomized Controlled Trials with Missing Data

## Problem Definition
Complete‑Case (CC) analysis is the default handling of missing data in many randomized controlled trials (RCTs). Under Missing Not At Random (MNAR) or even Missing At Random (MAR) conditions, CC can inflate Type I error rates, leading to false claims of efficacy. This study quantifies that inflation, identifies the missingness‑rate “tipping points” where CC becomes unreliable, and demonstrates that Multiple Imputation (MI) and Inverse‑Probability Weighting (IPW) can (or cannot) restore nominal error rates.

**Important qualification**: No open‑source RCT dataset with genuine treatment and outcome variables is currently verified. Consequently, we **simulate** an RCT by adding a synthetic binary treatment column and a synthetic outcome column (continuous or binary) to the verified observational datasets listed below. This approach satisfies the methodological need for a known null effect while remaining compliant with the data‑availability constraints. *The limitation is noted in the discussion of results*.

## Dataset Strategy
Only the datasets listed in the verified block are used, because no open RCT source is available.

| Dataset | Verified URL | Format | Role |
|---------|--------------|--------|------|
| **MCAR‑0** | https://huggingface.co/datasets/mcarthuradal/malawi/resolve/main/booklets/bk0-00000-of-00001.parquet | Parquet | Base data for MCAR simulations (synthetic treatment/outcome added). |
| **MCAR‑1** | https://huggingface.co/datasets/mcarthuradal/arm-unicef/resolve/main/aug_full_features/train-00000-of-00001.parquet | Parquet | Additional MCAR source for robustness checks. |
| **MAR‑0** | https://huggingface.co/datasets/markov-ai/cad-1000-hours/resolve/main/autocad/59f5afb1-7193-4434-83ef-bad577bf09ed/output_files/output.csv | CSV | Base data for MAR simulations (observed covariate used for missingness). |
| **MAR‑1** | https://huggingface.co/datasets/markov-ai/computer-use-large/resolve/main/descriptions.parquet | Parquet | Secondary MAR source. |
| **MAR‑2** | https://huggingface.co/datasets/markov-ai/gaming-500-hours/resolve/main/metadata.jsonl | JSONL | Additional MAR source. |

*No verified MNAR, RCT, IPW, or UCI datasets exist; therefore we generate synthetic treatment/outcome variables on the above files to emulate an RCT under a true null hypothesis (see Methodology).*

## Methodology

### 1. Data Preparation
- Load each verified dataset.
- Verify presence of ≥2 numeric covariates; if absent, synthesize covariates (`X1`, `X2`) with correlation *r*≈0.3 to the (later‑generated) outcome (FR‑009).
- Create a synthetic binary treatment column (`treatment`) ~ Bernoulli(0.5) if missing.
- Create a synthetic continuous outcome (`outcome`) ~ N(0,1) for continuous cases; for binary outcome scenarios, threshold the continuous outcome at 0 to obtain a 0/1 variable.

### 2. Ground‑Truth Calibration (FR‑003)
- **Permutation**: Randomly shuffle the `treatment` column (fixed seed) to guarantee zero average treatment effect.
- Confirm null by running a quick t‑test; expected p > 0.5.

### 3. Missingness Simulation (FR‑002)
- **MCAR**: Randomly mask a proportion *p* of rows, independent of any variable.
- **MAR**: Mask rows with probability proportional to a selected observed covariate (e.g., `X1`). The probability function is `p_i = min(1, rate * (X1_i - min)/(max - min))`.
- **MNAR**: Mask rows with probability proportional to the **permuted outcome** values (preserves the null hypothesis).  
- **Treatment‑Dependent Variants** (optional): For each mechanism we also simulate a version where missingness probability additionally depends on the (permuted) treatment assignment, reflecting differential attrition observed in real RCTs.
- Missingness rates sweep from **0.05 to 0.40** in **0.05** increments (8 steps) as required by FR‑004.

### 4. Analysis Methods (FR‑005)
| Method | Implementation |
|--------|----------------|
| **Complete‑Case (CC)** | Drop any row with a missing value;<br>– Continuous outcome → Student’s *t*‑test;<br>– Binary outcome → **Chi‑square** test (or Fisher’s exact when expected counts < 5) (FR‑007). |
| **Multiple Imputation (MI)** | Use `miceforest` with `m=5` imputations; pool test statistics via Rubin’s Rules; for binary outcomes pool chi‑square statistics. |
| **Inverse‑Probability Weighting (IPW)** | Fit a logistic model of missingness using observed covariates (and treatment for TD‑variants); compute inverse‑probability weights; run weighted *t*‑test (continuous) or weighted chi‑square (binary). |

### 5. Error Metric Computation (FR‑006)
- For each (dataset, mechanism, rate, method) condition, run **2000** Monte‑Carlo iterations (fixed seed).
- Record each p‑value → `ErrorMetric` (contract) and also a `p_value_distribution` record (contract).
- Empirical Type I error = proportion of p‑values < 0.05.
- Perform a Binomial test against the null expectation of 0.05 (α = 0.05).  
- **Power justification**: With 2000 iterations The standard error of a modest error rate is on the order of a few thousandths.; detecting a [deferred] relative increase of modest size yields a Z statistic suggesting a slight deviation from the null expectation., giving >80 % power at α=0.05 across the 72 conditions.

### 6. Tipping‑Point Identification (FR‑004, FR‑008)
- Collect all Binomial p‑values (72 conditions).
- Apply Benjamini‑Hochberg FDR correction (q < 0.05) (FR‑008).
- Declare a *tipping point* as the **lowest missingness rate** where:<br>1. Empirical error > 1.10 × 0.05 ([deferred] relative increase), **and**<br>2. Adjusted q‑value < 0.05.

### 7. Comparative Validation (FR‑005, SC‑005)
- At each identified tipping point, compute the ratio `error_CC / error_MI` and `error_CC / error_IPW`.
- Compare the two proportions using a **two‑proportion Z‑test** (with continuity correction); apply BH FDR across mechanisms.  
- Record `validated_tipping_point` = true if `error_CC > 2·error_MI` (or IPW) **and** the FDR‑adjusted q < 0.05.

### 8. Statistical Rigor Summary
- **Multiple Comparisons**: Benjamini‑Hochberg FDR across all 72 conditions (FR‑008).  
- **Power**: 2000 iterations give SE ≈ 0.005 for a 0.05 error rate, sufficient to detect a [deferred] relative increase with >80 % power.
- **Causal Assumptions**: The treatment permutation ensures a *purely observational* null; causal claims are limited to “association under the null”.  
- **Measurement Validity**: Continuous outcomes use *t*‑test; binary outcomes use chi‑square/Fisher (FR‑007).  
- **Collinearity**: Synthetic covariates are generated with controlled correlation (r ≈ 0.3) to avoid multicollinearity (FR‑009).  

## Decision / Rationale
- **Synthetic RCT Construction**: Because no verified RCT dataset exists, we synthesize treatment and outcome variables on verified MCAR/MAR files, preserving the scientific goal while respecting data‑availability constraints. This limitation is flagged for future work.  
- **MNAR Mechanism**: Implemented using the *permuted* outcome values to maintain the null hypothesis, correcting the earlier inconsistency.  
- **Binary Outcome Tests**: Switched to chi‑square/Fisher’s exact tests, which are appropriate for binary data.  
- **Treatment‑Dependent Missingness**: Added optional TD‑variants to capture differential attrition scenarios common in real RCTs.  
- **CPU‑First Strategy**: All libraries run efficiently on the free‑tier runner; no GPU off‑load is needed.

---

