# Feature Specification: Statistical Properties of Integer Partitions Into Distinct Prime Summands

**Feature Branch**: `001-statistical-properties-of-integer-partit-into-distinct-prime-summands`  
**Created**: 2026-06-30  
**Status**: Draft  
**Input**: User description: "How does the asymptotic growth rate of the partition function $p_{\mathcal{P}}(n)$ (counting partitions of $n$ into distinct primes) deviate from the predictions of Meinardus' theorem when applied to the prime set, and can these deviations be modeled as a systematic correction term dependent on the prime density?"

## User Scenarios & Testing

### User Story 1 - Compute Exact Partition Values and Asymptotic Baseline (Priority: P1)
(ID: US-1) (See US-1)

As a researcher, I need to compute the exact values of **p_P_n** for all integers $n$ from 1 to **n_max = 50 000** and generate the corresponding theoretical asymptotic values **Q_as_n** derived from the distinct‑partitions variant of Meinardus' theorem, so that I can establish the ground truth and the baseline prediction for the error analysis.

**Why this priority**: This is the foundational data generation step. Without accurate exact counts and the theoretical baseline, no error analysis or modeling can occur. It represents the core "data" of the study.

**Independent Test**: This can be fully tested by running the computation script and verifying that the output CSV contains many rows (including the header) where the first column is $n$, the second column is **p_P_n**, and the third column is **Q_as_n**, with **p_P_n > 0** for all $n \ge 2$ and **Q_as_n** matching the formula for distinct parts.

**Acceptance Scenarios**:

1. **Given** a clean Python environment with `numpy` and `math`, **When** the dynamic programming script is executed for **n_max = 50 000**, **Then** the output CSV contains **50 001** rows with non‑negative integer counts for **p_P_n** and positive float values for **Q_as_n**.
2. **Given** the computed values, **When** an automated comparison is performed against the reference table (see SC‑003), **Then** the computed counts match the reference values with exact integer equality for all $n \le 20$.

---

### User Story 2 - Calculate and Model Residual Error with Density Features (Priority: P2)
(ID: US-2) (See US-2)

As a researcher, I need to calculate the log‑residuals $R(n) = \log(p_P_n) - \log(Q_as_n)$ and fit a statistical model (ordinary least‑squares linear regression) using global prime‑density features **π(n)** and the cumulative prime‑reciprocal sum $\displaystyle\sum_{p \le n}\frac{1}{p}$ as predictors, so that I can quantify the systematic bias and determine if prime density explains the deviation.

**Why this priority**: This addresses the primary research question directly. It transforms raw data into the specific insight (systematic bias vs. random noise) required to validate or refute the hypothesis.

**Independent Test**: This can be tested by running the modeling script and checking that the output includes a regression summary with coefficients for the density features, an $R^2$ score, and a plot of residuals vs. fitted values.

**Acceptance Scenarios**:

1. **Given** the dataset of $n$, **p_P_n**, and **Q_as_n**, **When** the residual calculation and feature‑engineering script runs, **Then** the resulting dataset contains the column **R_n** and the derived density predictors, and the regression model outputs a coefficient for **π(n)** that is not `NaN`.
2. **Given** the fitted model, **When** a t‑test is performed on the density coefficients, **Then** the output includes a p‑value for each coefficient, allowing the researcher to determine statistical significance (e.g., $p < 0.05$).

---

### User Story 3 - Validate Model Robustness and Visualize Convergence (Priority: P3)
(ID: US-3) (See US-3)

As a researcher, I need to perform k‑fold cross‑validation on the regression model and generate visualizations comparing the raw residuals against the fitted correction term, so that I can assess the model's generalizability and visually inspect the convergence behavior for anomalies.

**Why this priority**: This ensures the findings are not overfitted to the specific sample and provides the necessary visual evidence for the final report. It confirms the reliability of the "systematic bias" claim.

**Independent Test**: This can be tested by running the validation script and verifying that the cross‑validation error (MSE) is reported for each fold and that a PNG plot is generated showing the residual trend.

**Acceptance Scenarios**:

1. **Given** the fitted regression model, **When** cross‑validation is executed, **Then** the output reports the Mean Squared Error (MSE) for each cross‑validation fold and the mean MSE across all folds.
2. **Given** the model results, **When** the visualization script runs, **Then** it produces a plot with $n$ on the x‑axis, showing both the raw residuals **R_n** and the predicted correction term, allowing visual identification of periodic anomalies.

---

### Edge Cases

- **Small $n$**: For $n < 5$ where no partitions into distinct primes exist, **p_P_n = 0**. In such rows the residual **R_n** is set to the numeric sentinel **-9999**; these rows are excluded from regression but retained in the dataset.
- **Memory optimisation**: The dynamic‑programming array uses a sparse representation (bitset) to ensure the full iteration up to **n_max = 50 000** fits within the RAM limit of the CI runner.
- **Numerical stability of $Q_as_n$**: If the asymptotic formula yields a value $\le 10^{-10}$, it is clamped to $10^{-10}$ before taking the logarithm to avoid domain errors.

## Requirements

### Functional Requirements

- **FR-001**: System MUST compute the exact count **p_P_n** of partitions of $n$ into distinct primes for all integers $1 \le n \le 50 000$ using a dynamic‑programming approach with memory optimisation to fit within a modest amount of RAM. (See US-1)

- **FR-002**: System MUST implement the asymptotic formula **Q_as_n** based on the distinct‑partition variant of Meinardus' theorem **without incorporating any of the density predictor variables (π(n), 1/ln n, Σ_{p≤n}1/p) into the formula**. The baseline will be computed via the prime‑zeta saddle‑point method; if the saddle‑point conditions are not satisfied, a numerically stable truncated Dirichlet‑series approximation shall be used and documented. (See US-1)

- **FR-003**: System MUST calculate the log‑residual **R_n = \log(p_P_n) - \log(Q_as_n)** for all rows where **p_P_n > 0** and **Q_as_n > 0**. When either value is non‑positive, **R_n** shall be set to the numeric sentinel **-9999** (no string markers). (See US-2)

- **FR-004**: System MUST generate predictor variables:
  - **π(n)** (prime‑counting function),
  - **CUM_RECIP_PRIME = $\displaystyle\sum_{p \le n}\frac{1}{p}$**,
  - **AVG_PRIME_GAP = average prime gap up to n**,
  and compute the Variance‑Inflation‑Factor (VIF) for each. If any VIF > 5, the predictor with the highest VIF shall be dropped before model fitting. These predictors are derived **independently** of the partition calculation and of the asymptotic baseline. (See US-2)

- **FR-005**: System MUST fit an **ordinary least‑squares linear regression** where **R_n** is the dependent variable and the retained density predictors are independent variables. No alternative model (e.g., GAM) is permitted. The output shall include coefficients, standard errors, p‑values, and $R^2$. (See US-2)

- **FR-006**: System MUST perform 10‑fold cross‑validation on the regression model to estimate the Mean Squared Error (MSE) on held‑out data, ensuring the model generalises beyond the training set. (See US-3)

- **FR-007**: System MUST generate a visualization plotting $n$ against the raw residuals **R_n** and the fitted correction term to visually inspect convergence and identify anomalies. (See US-3)

- **FR-010**: System MUST conduct a statistical power analysis (target power 0.8, significance α = 0.05) for the regression coefficients using HAC‑adjusted standard errors, and report the **minimum detectable effect size** for each predictor. (See US-2)

- **FR-012**: System MUST provide a Python script `generate_partitions.py` with a comprehensive docstring explaining the generating function $\displaystyle\prod_{p\in\mathbb{P}}(1+q^{p})$, its distinction from the unrestricted partition generating function $\displaystyle\prod_{k\ge1}(1-q^{k})^{-1}$, and the algorithmic steps used. (See US-1)

- **FR-013**: System MUST output a CSV file `data/processed/features.csv` containing all predictor columns (**π(n)**, **CUM_RECIP_PRIME**, **AVG_PRIME_GAP**) and the response **R_n** for every $n$ (rows with **R_n = -9999** are retained). The file shall contain **no null entries**; the sentinel **-9999** satisfies the non‑null numeric requirement. (See US-2)

### Key Entities

- **PartitionRecord**: Represents a single data point containing $n$, **p_P_n**, **Q_as_n**, and the calculated **R_n**.
- **DensityFeatureSet**: Represents the independent variables for a given $n$, including **π(n)**, **CUM_RECIP_PRIME**, and **AVG_PRIME_GAP**.
- **RegressionModel**: Represents the fitted statistical model, storing coefficients, intercept, and performance metrics ($R^2$, MSE).

## Success Criteria

### Measurable Outcomes

- **SC-001**: The residual analysis shall **report** p‑values for each density predictor and indicate whether they are statistically significant at the conventional α = 0.05 level. No pre‑set requirement that any predictor must achieve significance is imposed. (See US-2)

- **SC-002**: The regression model shall report the cross‑validated $R^2$ value (from the 10‑fold validation) and the mean cross‑validated MSE. These values are to be interpreted in context but no minimum threshold is mandated. (See US-3)

- **SC-003**: The computed values **p_P_n** must match known enumerations for $n = 2$ to $20$ (see inline table below) with exact integer match, measured against this reference table.  
  | $n$ | $p_P_n$ |
  |----|--------|
  | 2  | 1 |
  | 3  | 1 |
  | 4  | 1 |
  | 5  | 2 |
  | 6  | 2 |
  | 7  | 2 |
  | 8  | 3 |
  | 9  | 3 |
  | 10 | 4 |
  | 11 | 4 |
  | 12 | 5 |
  | 13 | 5 |
  | 14 | 6 |
  | 15 | 6 |
  | 16 | 7 |
  | 17 | 7 |
  | 18 | 8 |
  | 19 | 8 |
  | 20 | 9 |
  (See US-1)

- **SC-004**: The entire data generation and analysis pipeline shall complete within the resource limits of a standard GitHub Actions free‑tier runner (ubuntu‑latest, 2 vCPU, 7 GB RAM) **without exceeding** the allocated CPU time ([deferred]) **and** without exceeding **6 GB** of peak memory usage. These limits are documented for reproducibility but are not treated as scientific criteria. (See US-1, US-2, US-3)

- **SC-005**: When multiple hypothesis tests are performed, the system **may** apply the Benjamini‑Hochberg false‑discovery‑rate correction; the choice is optional and will be documented in the analysis report. (See US-2)

## Assumptions

- **Assumption about data**: The dataset of primes up to 50 000 is finite and can be pre‑computed or generated on‑the‑fly within the memory constraints of the CI runner.
- **Assumption about methodology**: The applicability of the asymptotic formula **Q_as_n** for distinct parts to the finite range $n \le 50 000$ is a hypothesis to be tested; a fallback truncated Dirichlet‑series approximation will be used if Meinardus' conditions are not met.
- **Assumption about computational resources**: The dynamic‑programming algorithm for **p_P_n** can be optimized (e.g., using a sparse bitset) to fit within the 7 GB RAM limit of the GitHub Actions free tier without requiring GPU acceleration.
- **Assumption about error nature**: The deviation between **p_P_n** and **Q_as_n** is expected to be systematic and correlated with prime density, rather than purely random noise, justifying the regression approach.
- **Assumption about statistical validity**: The sample size of 50 000 data points is sufficient to detect a meaningful correlation between the residuals and density features, as confirmed by the power analysis (FR‑010).
- **Assumption about confounding**: Including **AVG_PRIME_GAP** as a control variable mitigates potential confounding from prime‑gap structure.
- **Assumption about reference data**: A reference CSV (`reference_data.csv`) containing verified partition counts for $n \le 100$ will be supplied alongside the repository to enable validation of the exact‑count computation (see FR‑001).
