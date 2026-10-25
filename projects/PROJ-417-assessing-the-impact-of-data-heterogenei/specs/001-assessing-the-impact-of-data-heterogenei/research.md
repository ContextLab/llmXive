# Research: Assessing the Impact of Data Heterogeneity on Meta-Analysis Results

## 1. Dataset Strategy

### 1.1 Base Data Source
No verified Cochrane‑style meta‑analysis dataset is publicly downloadable (the “Verified datasets” block contains no such URL). To satisfy the constitution we **do not claim** any external Cochrane data. Instead we generate a **deterministic synthetic base template** that mimics typical study‑size distributions and standard‑error magnitudes observed in published meta‑analyses (e.g., mean study size ≈ a moderate sample (on the order of hundreds), SE distribution approximated by a scaled chi‑square). The base is created once by `code/scripts/generate_base.py` and stored as `data/processed/base_template.csv`. The generation uses a fixed random seed and **fixes the number of studies $k$ and the vector of study sizes** for the entire simulation, meeting Principle VI (Simulation Fidelity) and satisfying **FR‑001** without relying on unavailable external data.

### 1.2 Two‑Stage Generation Process
1. **Sample study sizes** $N_i$ **once** from a truncated normal (mean 150, sd 50, lower = 20) → derive SEs $\sigma_i = \sqrt{1/N_i}$. The resulting $k$ and $\{N_i\}$ are stored in the base template and reused for every replicate.  
2. **Inject heterogeneity** by drawing study effects $y_{i,r} \sim \mathcal N(\theta, \sigma_i^2 + \tau^2)$, where $\theta=0.5$ (the true effect size) and $\tau^2$ takes the predefined levels.  
3. **Store** each replicate as a JSON‑line adhering to `contracts/simulated_dataset.schema.yaml`.

This fulfills **VI. Simulation Fidelity** and satisfies **FR‑001** while keeping $k$ and $N_i$ constant across replicates, eliminating confounding variability.

## 2. Statistical Methodology

### 2.1 Estimators (FR‑002)
* **Fixed‑Effects (FE)** – weights $w_i = 1/\sigma_i^2$.  
* **DerSimonian‑Laird (DL)** – method‑of‑moments estimator $\hat\tau^2_{\text{DL}}$.  
* **REML** – restricted maximum likelihood; **if convergence fails**, the replicate is logged in `reml_failures.json` and **excluded only from the conditional coverage calculation** (see below). No artificial variance fallback is applied.

All estimators return pooled effect, 95 % CI, $Q$, $I^2$, and a convergence flag for REML.

### 2.2 Performance Metrics (FR‑003)
* **Bias** = $\hat\theta - \theta_{\text{true}}$.  
* **Coverage** = indicator that $\theta_{\text{true}}$ lies within the 95 % CI.  
* **Coverage deviation** = coverage − 0.95 (reported with Wilson‑score interval).  

**Coverage Calculation**: Coverage is computed **across all replicates**, regardless of REML convergence status, ensuring an unbiased estimate of estimator performance. In addition, a **conditional coverage** metric is reported for the subset of replicates where REML converged, allowing users to assess the impact of convergence failures without biasing the primary coverage estimate.

### 2.3 Hypothesis Tests
* **Coverage** – exact binomial test against the nominal 0.95 level.  
  * Null: observed coverage = 0.95.  
  * **Bonferroni‑adjusted $\alpha = 0.05 / (5 \times 3) \approx 0.0033$** for the fifteen tests (five τ² levels × three estimators) (FR‑007).  

* **Bias across τ²** – **first perform a Shapiro‑Wilk normality test** on the bias distribution for each estimator.  
  * If $p \ge 0.05$, apply **ANOVA**;  
  * If $p < 0.05$, apply **Kruskal‑Wallis**; when Kruskal‑Wallis is significant, Dunn’s post‑hoc with Bonferroni correction identifies pairwise differences (FR‑008).  

### 2.4 Power & Precision
With **900 replicates per τ² level** (primary and sensitivity sweeps), the Monte‑Carlo standard error of a coverage proportion $p$ is $\sqrt{p(1-p)/900}\approx0.016$. Power calculations for an exact binomial test show **≥ 80 % power to detect a [deferred] absolute drop in coverage** (from 0.95 to 0.90) at the adjusted $\alpha$, satisfying the scientific requirement.

### 2.5 REML Failure Handling (FR‑006)
* Failures are recorded in `reml_failures.json`.  
* **Coverage for REML is reported both**  
  1. **Overall** (using all replicates, treating failures as missing for the CI but still counting them in the denominator), and  
  2. **Conditionally** (using only replicates where REML converged).  
* This dual reporting avoids upward bias while still informing the user about the frequency of convergence problems.

## 3. Computational Feasibility (CPU‑first)

* **Batch processing** – replicates are streamed and processed in batches of 100 to keep RAM ≤ 5 GB.  
* **Libraries** – pure `numpy`/`scipy`; no GPU needed.  
* **Estimated runtime** – ~0.7 s per replicate → ≈ 3 h for the full multi‑thousand‑replicate sweep, comfortably within the 6 h CI limit.

## 4. Methodological Rigor & Assumptions

* **Associational framing** – All conclusions are labelled “associational” (SC‑005) because the study is a simulation based on observational data structures.  
* **Multiplicity** – Bonferroni correction applied across all fifteen coverage tests (FR‑007).  
* **Collinearity** – Not applicable; τ² is an exogenous manipulation.  
* **Power** – A sufficient number of replicates per level ensures adequate power. for the exact binomial test as described above.  
* **REML failures** – Reported separately; excluded from conditional coverage to avoid bias (FR‑006).  

## 5. Decision Rationale

| Decision | Reason |
|----------|--------|
| **Synthetic base generation** | No verified Cochrane dataset exists; generating a realistic synthetic base respects the constitution and provides the required study‑level structure. |
| **Fixed $k$ and $N_i$** | Removes confounding between heterogeneity and study‑size variability, isolating the effect of τ². |
| **Shapiro‑Wilk + conditional ANOVA/KW** | Satisfies FR‑008 and avoids a blanket non‑parametric approach. |
| **Report both conditional and overall REML coverage** | Prevents bias from conditioning on convergence while still informing about estimator stability. |
| **Bonferroni across estimators** | Controls family‑wise error for all 15 hypothesis tests (FR‑007). |
| **900 replicates per level** | Provides ≥ 80 % power to detect a [deferred] absolute drop in coverage (methodology‑2bced2e6). |

---


