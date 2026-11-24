# Research: Assessing the Validity of Statistical Significance in Randomized Controlled Trials with Missing Data

## Problem Definition
Complete‑Case (CC) analysis is the default handling of missing data in many randomized controlled trials (RCTs). Under Missing Not At Random (MNAR) or Missing At Random (MAR) conditions, CC can inflate Type I error rates, leading to false claims of efficacy. This study quantifies that inflation, identifies missingness‑rate “tipping points” where CC becomes unreliable, and evaluates whether Multiple Imputation (MI) and Inverse‑Probability Weighting (IPW) restore nominal error rates.

**Limitation**: No open‑source RCT dataset with genuine treatment and outcome columns is verified for this project. Consequently, we **simulate** an RCT by adding synthetic treatment and outcome variables to verified observational datasets (and to any verified RCTs that lack the required columns). This approach preserves a known null hypothesis while respecting data‑availability constraints.

## Dataset Strategy
Only the datasets listed in the verified block are used. When a dataset lacks a treatment or outcome column, we synthesize them as described in the methodology.

| Dataset | Verified URL | Format | Role |
|---------|--------------|--------|------|
| **RCT‑1** (synthetic treatment/outcome if needed) | https://huggingface.co/datasets/cardiffnlp/TSAR2025_SharedTask_RCTS_Trial-Data/resolve/main/tsar2025_trial.jsonl | JSONL | Primary RCT source (used if it already contains treatment/outcome). |
| **MCAR‑0** | https://huggingface.co/datasets/mcarthuradal/malawi/resolve/main/booklets/bk0-00000-of-00001.parquet | Parquet | Observational source for MCAR simulations. |
| **MAR‑0** | https://huggingface.co/datasets/markov-ai/cad-1000-hours/resolve/main/autocad/59f5afb1-7193-4434-83ef-bad577bf09ed/output_files/output.csv | CSV | Observational source for MAR simulations. |

*No verified MNAR or IPW datasets exist; the MNAR mechanism is simulated algorithmically (see Methodology).*

## Methodology

### 1. Data Preparation
- Load each verified dataset via `datasets.load_dataset` or `pandas`.
- Verify that at least two numeric covariates exist; if not, generate **independent** synthetic covariates `X1`, `X2` (no imposed correlation).
- If a binary treatment column is missing, create `treatment` ~ Bernoulli(0.5).
- If an outcome column is missing, generate a continuous outcome `outcome` ~ N(0,1); for binary scenarios, threshold at 0 to obtain a 0/1 variable.

### 2. Ground‑Truth Calibration (FR‑003)
- **Permutation**: Randomly shuffle the `treatment` column (fixed seed) to guarantee a true null effect. For MNAR simulations, also shuffle the outcome column before missingness injection.
- Verify the null by running a quick t‑test (continuous) or chi‑square test (binary); the p‑value should be > 0.5.

### 3. Missingness Simulation (FR‑002)
- **MCAR**: Randomly mask a proportion *p* of rows, independent of any variable.
- **MAR**: Mask rows with probability proportional to a selected observed covariate (e.g., `X1`). Probability function:  
  `p_i = min(1, rate * (X1_i - min(X1)) / (max(X1) - min(X1)))`.
- **MNAR**: Mask rows with probability proportional to the **permuted outcome** values (preserves the null hypothesis).  
- Missingness rates sweep from **0.05 to 0.25** in **0.05** increments (5 steps) as required by FR‑004.

### 4. Analysis Methods (FR‑005)
| Method | Implementation |
|--------|----------------|
| **Complete‑Case (CC)** | Drop any row with a missing value;<br>– Continuous outcome → Student’s *t*‑test;<br>– Binary outcome → **Logistic regression** (fallback to chi‑square/Fisher’s exact when expected cell counts < 5) (FR‑007). |
| **Multiple Imputation (MI)** | Use `miceforest` with `m=5` imputations; pool test statistics via Rubin’s Rules; binary outcomes analysed with logistic regression. |
| **Inverse‑Probability Weighting (IPW)** | Fit a logistic model of missingness using observed covariates; compute inverse‑probability weights; run weighted *t*‑test (continuous) or weighted logistic regression (binary). |

### 5. Error Metric Computation (FR‑003, SC‑001, SC‑003, SC‑004)
- For each (dataset, mechanism, missingness rate, method) condition, run **≥ 15 000** Monte‑Carlo iterations (fixed seed) using batch processing.
- Record each p‑value → `PValueDistribution` contract (**FR‑010**); also store iteration‑level metadata as `ErrorMetric`.
- Empirical Type I error = proportion of p‑values < 0.05.
- Conduct a **Kolmogorov‑Smirnov (KS) test** comparing the observed p‑value distribution to Uniform(0,1) (α = 0.05) to satisfy SC‑003.

### 6. Tipping‑Point Identification (FR‑004)
- Aggregate empirical error rates across the five missingness rates for each mechanism.
- Declare a *tipping point* as the **lowest missingness rate** where:  
  1. Empirical CC error > 0.055 (i.e., >10 % relative increase over 0.05).  
  2. The dataset has **N ≥ 100** rows (otherwise the condition is flagged and excluded).  
- Record the flag in the `ComparisonResult` artifact (SC‑002).

### 7. Comparative Validation (FR‑005, SC‑005)
- At each identified tipping point, construct a paired 2 × 2 table of per‑iteration rejection outcomes for CC vs. MI (and CC vs. IPW).
- Apply a **McNemar’s test** to assess whether CC has a significantly higher rejection rate than the comparator (paired design).
- Compute the ratio `error_CC / error_MI` (or `/ error_IPW`).
- Use a **paired bootstrap** (e.g., 2000 resamples) to obtain a 95 % confidence interval for this ratio; declare `validated_tipping_point` true if the lower bound exceeds 2 **and** the McNemar’s test p‑value < 0.05.
- Store the McNemar p‑value, bootstrap CI, and boolean flag in `ComparisonResult`.

### 8. Statistical Rigor Summary
- **Multiple Comparisons**: Benjamini‑Hochberg correction applied only to the set of McNemar’s tests across mechanisms (consistent with the original scope; FR‑008 was removed).  
- **Power**: 15 000 iterations give a standard error of √[0.05·0.95/15000] ≈ 0.0018, satisfying the ≥ 80 % power requirement for detecting a relative increase to 0.055 (SC‑004).  
- **Causal Assumptions**: Treatment permutation ensures a purely observational null; any causal language is limited to “association under the null”.  
- **Measurement Validity**: Continuous outcomes use *t*‑test; binary outcomes use logistic regression (or chi‑square/Fisher when appropriate) (FR‑007).  
- **Collinearity**: Synthetic covariates are generated independently to avoid multicollinearity concerns.

## Decision / Rationale
- **Synthetic RCT Construction**: Because verified RCTs with full treatment/outcome metadata are scarce, we synthesize missing columns while preserving a true null hypothesis. This satisfies FR‑001 and is explicitly noted as a limitation.  
- **MNAR Mechanism**: Implemented using the *permuted* outcome values, guaranteeing the null and adhering to FR‑002.  
- **Binary Outcome Tests**: Unified on logistic regression (with chi‑square/Fisher fallback when appropriate) complying with FR‑007.  
- **CPU‑First Strategy**: All libraries run efficiently on the free‑tier runner; no GPU off‑load is required.  

---


