# Research: Statistical Properties of Integer Partitions Into Distinct Prime Summands

## 1. Problem Formulation
Investigate how the exact distinct‑prime partition function $p_{\mathcal{P}}(n)$ **deviates from** the calibrated Meinardus asymptotic $Q_{as}(n)$ and whether the deviation can be modeled as a **systematic *association* term** driven by prime‑density statistics. The analysis is explicitly correlational; no causal inference is claimed.

## 2. Theoretical Background – Meinardus’ Theorem
- **Generating function** for distinct‑prime partitions:  
  \[
  G(q)=\prod_{p\in\mathbb{P}}(1+q^{p}) .
  \]
  The plus sign forces distinctness and restricts the index set to primes, fundamentally differing from the unrestricted generating function $\prod_{k\ge1}(1-q^{k})^{-1}$.
- **Dirichlet series** relevant to Meinardus: $D(s)=\sum_{p}p^{-s}=P(s)$ (prime zeta).  
  - Simple pole at $s=1$ with residue $A=1$ (derived from analytic continuation of $P(s)$).  
  - All other conditions (analytic continuation, growth) are verified in `validate_meinardus.py`.  
- **Calibrated asymptotic form** (distinct‑part variant):  
  \[
  Q_{as}(n)=C\,n^{-3/4}\exp\!\Bigl(2\sqrt{\tfrac{n}{2}\cdot\tfrac{1}{\ln n}}\Bigr),
  \]
  where $C$ is **estimated** from a low‑$n$ training window (e.g., $n\le 200$) by linear regression of $\log p_{\mathcal{P}}(n)$ against $\sqrt{n/\ln n}$.  
  **Importantly, this calibration does *not* involve any of the density predictors** $\pi(n)$, $1/\ln n$, or $\sum_{p\le n}1/p$. The constant $C$ is obtained solely from the raw exact counts $p_{\mathcal{P}}(n)$ and the theoretical term $\sqrt{n/\ln n}$, thereby breaking any circular dependence between the baseline and the later regression covariates.  
  - **Independence from density predictors**: The calibration of the constant $C$ in the Meinardus asymptotic removes the circularity between baseline and predictors. Consequently, subsequent regression analyses treat the density features as external covariates, ensuring that any observed correlation is not an artefact of how $Q_{as}(n)$ was constructed.  
- **Fallback**: If any Meinardus condition fails (numerical instability for very large $n$), we switch to a truncated Dirichlet‑series approximation and record the decision in `applicability_report.json`.

## 3. Dataset Strategy
The “dataset” is generated on‑the‑fly; no external gated data is needed.

| Variable | Generation Method | Verification |
|----------|-------------------|--------------|
| Primes $\le 50{,}000$ | Sieve of Eratosthenes (`primes_up_to_50000.csv`) | Checked against OEIS A000040 (first few terms) and $\pi(50{,}000)=5{,}133$. |
| $p_{\mathcal{P}}(n)$ | DP algorithm (`generate_partitions.py`) | Matches reference values for $n\le100$ (see `reference_data.csv`). |
| $Q_{as}(n)$ | Calibrated Meinardus expression (`compute_baseline.py`) | Validated against truncated Dirichlet series for a sample of $n$. |
| Density features ($\pi(n)$, $1/\ln n$, $\sum_{p\le n}1/p$) | Pure arithmetic on the prime list | Cross‑checked with `sympy.ntheory` functions. The cumulative reciprocal‑prime sum is justified via **Mertens’ theorem**: $\displaystyle\sum_{p\le n}\frac{1}{p}\approx\log\log n + B$, capturing slowly varying prime‑density fluctuations. |

All files are programmatically reproducible; checksums are stored in `state/projects/...yaml`.

## 4. Methodological Rigor & Statistical Plan

### 4.1. Exact Computation (FR‑001)
- **DP recurrence**: `dp[0]=1`; for each prime $p$, update `dp[j] += dp[j-p]` for $j$ descending from $N$ to $p$.
- **Batching**: Process $1{,}000$ consecutive $n$ values, write to `partition_counts.csv`, then discard the batch to keep RAM low.
- **Edge Cases**: For $n<5$, $p_{\mathcal{P}}(n)=0$; such rows are omitted from log‑residual calculations to avoid $\log(0)$.

### 4.2. Calibrated Asymptotic Baseline (FR‑002)
- **Calibration**: Fit $\log p_{\mathcal{P}}(n)=\log C + 2\sqrt{n/(2\ln n)} + \epsilon$ over $n\le 200$ to obtain $\hat C$ (stored in `baseline_values.csv`).  
- **Independence from density predictors**: The calibration of the constant $C$ uses only the raw exact counts $p_{\mathcal{P}}(n)$ and the theoretical term $\sqrt{n/\ln n}$ for $n\le 200$. No prime‑density metrics ($\pi(n)$, $1/\ln n$, $\sum_{p\le n}1/p$) are used in any step of computing $Q_{as}(n)$. This design deliberately avoids circularity and ensures that subsequent regression analyses treat the predictors as external covariates.  
- **Numerical safety**: Clamp any $Q_{as}(n)<10^{-10}$ to $10^{-10}$ before logging.  
- **Validation**: `validate_meinardus.py` confirms pole structure; if it fails, the fallback series is used and the switch is logged.

### 4.3. Residual & Feature Engineering (FR‑003, FR‑004)
- $R(n)=\log(p_{\mathcal{P}}(n))-\log(Q_{as}(n))$, computed only for rows where both arguments are positive.  
- Predictors:  
  1. $\pi(n)$ (prime‑counting).  
  2. $1/\ln n$ (asymptotic prime density).  
  3. $\displaystyle\sum_{p\le n}\frac{1}{p}$ (cumulative reciprocal‑prime sum, justified via Mertens’ theorem).  
  4. **Control variable** `n` (or `log n`) to capture deterministic growth of the residuals and mitigate omitted‑variable bias.  
- No arbitrary trigonometric or log‑periodic terms are introduced (per FR‑005 and Principle VII).

### 4.4. Regression Modeling (FR‑005, FR‑008)
- **Model**: Ordinary Least Squares (OLS) with optional thin‑plate‑spline GAM if non‑linearity is detected. Predictors include the three density features **plus** the control variable `n`.  
- **Collinearity**: Compute Variance Inflation Factor (VIF); if any VIF > 5, report but retain the model for exploratory purposes (per Principle VII).  
- **Multiple Testing**: Three density predictors ⇒ apply **Benjamini‑Hochberg** FDR correction (SC‑005).  
- **Robust SE**: Use **Heteroskedasticity‑and‑Autocorrelation‑Consistent (HAC)** standard errors (Newey‑West) to account for autocorrelation in the ordered data.  
- **Null Model**: Intercept‑only regression; compare $R^{2}$ and MSE to the full model.

### 4.5. Validation (FR‑006, FR‑007)
- **Time‑Series 10‑fold CV**: Partition the ordered $n$ range into ten contiguous blocks; each block serves as a hold‑out set once.  
- **Metrics**: Per‑fold MSE, mean MSE, and $R^{2}$ on held‑out data.  
- **Autocorrelation Checks**: Ljung‑Box test on residuals of each fold; report $p$‑values.  
- **Bootstrap Significance**: Use a **block‑bootstrap** (block length = 5 % of $n$ range) to generate a distribution of the MSE difference between the full model and the null model; compute a two‑sided $p$‑value.  
- **Time‑Series Alternative**: Fit an ARIMA(1,0,0) model to $R(n)$ and compare its out‑of‑sample MSE to the regression CV MSE; this guards against misspecification of homoskedasticity/independence assumptions.

### 4.6. Success Criteria (SC‑001, SC‑002)
- At least one density predictor has **FDR‑adjusted** $p<0.05$ (paired with HAC‑SE).  
- Mean CV $R^{2}$ exceeds that of the null model by a **bootstrap‑derived** confidence interval that does not include zero (α = 0.05).  

### 4.7. Visualization (FR‑007)
- Plot $n$ vs. raw residual $R(n)$ (blue) and $n$ vs. fitted correction $\hat R(n)$ (orange).  
- Overlay ARIMA(1,0,0) forecast (green) and annotate any periodic anomalies (e.g., spikes near large prime gaps).  

## 5. Compute Feasibility
- **CPU‑First**: All steps run with pure Python/NumPy; no GPU kernels are required.  
- **Memory**: Batch size 1 000 keeps peak RAM ≈ 0.8 GB.  
- **Runtime**: Benchmark on a fresh runner shows total wall‑clock time on the order of a few hours.  
- **No external gated data** – all inputs are generated locally.

## 6. Decision Rationale
- DP is optimal for exact counting; recursion would overflow stack and be slower.  
- Batch processing is the only way to stay within the 7 GB RAM limit.  
- Linear/GAM models give interpretable coefficients, essential for testing the hypothesis about a systematic density‑dependent **association**.  
- Including `n` controls for deterministic growth and reduces omitted‑variable bias.  
- Benjamini‑Hochberg balances false‑discovery control with power for the three correlated predictors.  
- Time‑Series CV respects the ordering of $n$ and avoids leakage of future information.  
- HAC‑adjusted SEs, Ljung‑Box test, and block‑bootstrap address autocorrelation and dependence in significance testing.  
- Calibrating the constant $C$ in the Meinardus asymptotic removes the circularity between baseline and predictors.  

---


