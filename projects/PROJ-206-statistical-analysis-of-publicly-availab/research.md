# Research & Mathematical Formulations

This document details the mathematical foundations of the statistical methods implemented in the llmXive pipeline (PROJ-206) for the analysis of publicly available election poll aggregates. It also explicitly documents **Sanctioned Architectural Exceptions** where implementation decisions diverged from the initial project plan to adhere to specific feature requirements in the specification.

## 1. Data Acquisition and Harmonization

### 1.1 Data Sources
The pipeline ingests time-series polling data from **FiveThirtyEight (538)** and election outcome data from the **MIT Election Data and Science Lab (MEDSL)** or **FEC**.

**Sanctioned Architectural Exception (T009b): Exclusion of RealClearPolitics (RCP)**
* **Requirement**: The project plan emphasizes "Verified Accuracy" and excludes RCP due to methodological opacity.
* **Implementation**: The `src/data/download.py` module explicitly excludes fetching RCP data.
* **Justification**: Adhering to FR-001 and the Plan's "Verified Accuracy" principle. The exclusion is logged as a "Source Excluded" warning, and this architectural decision is documented here as a sanctioned exception to the general "poll aggregation" scope.

### 1.2 Harmonization
Raw data is parsed, dates unified to ISO 8601, and binned into weekly intervals to reduce noise and align heterogeneous polling schedules.
* **Bin**: $B_w = \{ t \mid \text{start}_w \le t < \text{end}_w \}$
* **Aggregation**: Polls within a bin are prepared for weighted averaging.

## 2. Weight Calculation: Historical RMSE

Pollster reliability is quantified using **Out-of-Sample Historical RMSE**.

Let $P$ be a set of pollsters and $C$ be a set of election cycles.
For a given pollster $p$ and current cycle $T$, we calculate the error on all previous cycles $t < T$.

$$ \text{RMSE}_{p, T} = \sqrt{ \frac{1}{N} \sum_{i=1}^{N} (v_{i, p} - v_{i, \text{actual}})^2 } $$

Where:
* $v_{i, p}$ is the pollster $p$'s prediction for outcome $i$ in historical cycles.
* $v_{i, \text{actual}}$ is the actual election result.
* $N$ is the number of historical polls for $p$ prior to cycle $T$.

**Weights**: The weight $w_{p, T}$ assigned to pollster $p$ in cycle $T$ is inversely proportional to their RMSE:
$$ w_{p, T} = \frac{1}{\text{RMSE}_{p, T} + \epsilon} $$
Where $\epsilon$ is a small constant to prevent division by zero, and weights are normalized such that $\sum w_{p, T} = 1$.

**Sanctioned Architectural Exception (T012)**: Default median weight assignment for new pollsters with no history is implemented to ensure pipeline stability, preventing division-by-zero errors and ensuring all pollsters contribute to the aggregate.

## 3. Frequentist Aggregation Methods

### 3.1 Simple Unweighted Averaging
The forecast $\hat{y}_t$ for a given time $t$ is the arithmetic mean of all polls $x_{i,t}$ in the bin:
$$ \hat{y}_t^{\text{simple}} = \frac{1}{n} \sum_{i=1}^{n} x_{i,t} $$

### 3.2 Accuracy-Weighted Averaging
The forecast uses the weights derived from Section 2:
$$ \hat{y}_t^{\text{weighted}} = \sum_{i=1}^{n} w_{i} \cdot x_{i,t} $$
Where $w_i$ is the normalized weight of the pollster conducting poll $i$.

## 4. Bayesian Hierarchical Modeling (Random Walk)

**Sanctioned Architectural Exception (T021): Random Walk vs. Static Parameter**
* **Plan Decision**: The initial plan favored a "Static Parameter" model for simplicity.
* **Spec Mandate**: The Feature Specification (FR-005) explicitly requires a **Random Walk** model to capture temporal dynamics.
* **Implementation**: We implement a Random Walk prior for the latent preference state $\theta_t$, overriding the Plan's static decision. This is documented as a hypothesis test: "Random Walk vs. Static".

### 4.1 Model Formulation
We model the latent preference $\theta_t$ (e.g., vote share) as a stochastic process:

**State Equation (Random Walk):**
$$ \theta_t \sim \mathcal{N}(\theta_{t-1}, \sigma_{\text{rw}}^2) $$
For $t=1$, $\theta_1 \sim \mathcal{N}(\mu_0, \sigma_0^2)$.

**Observation Equation:**
$$ y_{i,t} \sim \mathcal{N}(\theta_t, \tau_i^2) $$
Where $y_{i,t}$ is the observed poll result $i$ at time $t$, and $\tau_i^2$ represents the specific observation noise (often derived from sample size $n_i$: $\tau_i^2 \approx \frac{p(1-p)}{n_i}$).

### 4.2 Inference
We use **No-U-Turn Sampler (NUTS)** within the PyMC framework for Markov Chain Monte Carlo (MCMC) sampling.
* **Convergence**: Checked via $\hat{R}$ (R-hat). The pipeline halts if $\hat{R} > 1.05$ for any parameter (T023).
* **Output**: Posterior distributions for $\theta_t$ provide point forecasts (mean/median) and credible intervals (e.g., 95% CI).

## 5. Model Evaluation and Meta-Analysis

### 5.1 Coverage Reliability
We verify that the 95% credible intervals contain the true election outcome with the expected frequency.
* **Metric**: Coverage Rate = $\frac{1}{K} \sum_{k=1}^{K} \mathbb{I}(y_{\text{actual}} \in \text{CI}_k)$
* **Statistical Test**: A binomial test against the null hypothesis $H_0: p = 0.95$ with $\alpha = 0.05$ (T025).

### 5.2 Diebold-Mariano (DM) Test
To compare the predictive accuracy of two competing forecasting methods (e.g., Simple vs. Weighted, or Bayesian vs. Frequentist), we employ the Diebold-Mariano test.

Let $e_{1,t}$ and $e_{2,t}$ be the forecast errors of method 1 and 2 at time $t$.
The loss differential is $d_t = L(e_{1,t}) - L(e_{2,t})$, where $L$ is a loss function (e.g., squared error).

$$ H_0: E[d_t] = 0 $$
$$ H_1: E[d_t] \neq 0 $$

The DM statistic is:
$$ DM = \frac{\bar{d}}{\sqrt{\frac{2\pi \hat{f}_d(0)}{T}}} $$
Where $\hat{f}_d(0)$ is the spectral density of $d_t$ at frequency zero (accounting for autocorrelation).

**Sanctioned Architectural Exception (T026): Westfall-Young Correction**
* **Plan Decision**: The plan rejected DM tests for static forecasts.
* **Spec Mandate**: FR-006 and SC-003 require pairwise DM tests with **Westfall-Young correction** to control the Family-Wise Error Rate (FWER) when comparing multiple models.
* **Implementation**: We implement a custom permutation-based step-down max-t strategy with 1000 permutations. This overrides the Plan's rejection and is documented here as a necessary adherence to the Spec's rigorous comparison requirements.

## 6. Framing of Results

Consistent with FR-007, all results are framed in terms of:
* **Predictive Accuracy**: How well the model predicts the outcome (RMSE, MAE, DM tests).
* **Associational Uncertainty**: The range of plausible values given the data (Credible Intervals), avoiding causal language unless explicitly modeled.

## 7. Summary of Architectural Exceptions

| ID | Component | Original Plan | Spec Requirement | Decision |
|:--- |:--- |:--- |:--- |:--- |
| **T009b** | Data Source | Aggregating all major sources | Exclude RCP | **Exclude RCP** (Verified Accuracy Principle) |
| **T021** | Model Prior | Static Parameter | Random Walk | **Random Walk** (Temporal dynamics required) |
| **T026** | Evaluation | No DM tests | DM + Westfall-Young | **DM + Westfall-Young** (Rigorous comparison required) |

These exceptions are intentional, documented deviations to satisfy the Feature Specification's higher-priority requirements for accuracy and rigorous statistical validation.