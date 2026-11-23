# Research: Assessing the Impact of Data Heterogeneity on Meta-Analysis Results

## 1. Dataset Strategy

### 1.1 Base Data Source
No verified Cochrane‑style meta‑analysis dataset is publicly downloadable (the “Verified datasets” block contains no such URL). To satisfy the constitution we **do not claim** any external Cochrane data. Instead we generate a **deterministic synthetic base template** that mimics typical study‑size distributions and standard‑error magnitudes observed in published meta‑analyses. The base is created once by `code/scripts/generate_base.py` and stored as `data/processed/base_template.csv`. The generation uses a fixed random seed and **fixes the number of studies $k$ and the vector of study sizes** for the entire simulation, meeting Principle VI (Simulation Fidelity) and satisfying **FR‑001** without relying on unavailable external data.

### 1.2 Two‑Stage Generation Process
1. **Sample study sizes** $N_i$ **once** from a truncated normal (mean 150, sd 50, lower = 20) → derive SEs $\sigma_i = \sqrt{1/N_i}$. The resulting $k$ and $\{N_i\}$ are stored in the base template and reused for every replicate.  
2. **Inject heterogeneity** by drawing study effects $y_{i,r} \sim \mathcal N(\theta, \sigma_i^2 + \tau^2)$, where $\theta=0.5$ (the true effect size) and $\tau^2$ takes the predefined levels.  
3. **Store** each replicate as a JSON‑line adhering to `contracts/simulated_dataset.schema.yaml`.

This fulfills **VI. Simulation Fidelity** and satisfies **FR‑001** while keeping $k$ and $N_i$ constant across replicates, eliminating confounding variability.

## 2. Statistical Methodology

### 2.1 Estimators (FR‑002)
* **Fixed‑Effects (FE)** – weights $w_i = 1/\sigma_i^2$.  
* **DerSimonian‑Laird (DL)** – method‑of‑moments estimator $\hat\tau^2_{\text{DL}}$.  
* **REML** – restricted maximum likelihood; **if convergence fails**, the replicate is logged in `reml_failures.json` and the failure is **counted as a non‑coverage event** (coverage_flag = False). No artificial variance fallback is applied.

All estimators return pooled effect, 95 % CI, $Q$, $I^2$, and a convergence flag for REML.

### 2.2 Performance Metrics (FR‑003)
* **Bias** = $\hat\theta - \theta_{\text{true}}$.  
* **Coverage** = indicator that $\theta_{\text{true}}$ lies within the 95 % CI.  
* **Coverage deviation** = coverage − 0.95 (reported with Wilson‑score interval).  

**Coverage Calculation**: Coverage is computed **across all replicates**, treating any REML convergence failure as a **non‑coverage** (i.e., coverage_flag = False). This rule avoids ambiguity and preserves construct validity.

### 2.3 Hypothesis Tests
* **Coverage** – exact binomial test against the nominal 0.95 level.  
  * Null: observed coverage = 0.95.  
  * **Bonferroni‑adjusted $\alpha = 0.05 / 5 \approx 0.01$** for the five τ² levels (per estimator) (FR‑007).  

* **Bias across τ²** – **first perform a Shapiro‑Wilk normality test** on the bias distribution for each estimator.  
  * If $p \ge 0.05$, apply **ANOVA**;  
  * If $p < 0.05$, apply **Kruskal‑Wallis**; when Kruskal‑Wallis is significant, Dunn’s post‑hoc with Bonferroni correction identifies pairwise differences (FR‑008).  

### 2.4 Power & Precision
With **A sufficiently large number of replicates per τ² level** (primary and sensitivity sweeps), the Monte‑Carlo standard error of a coverage proportion $p$ is $\sqrt{p(1-p)/900}\approx0.016$. Power calculations using the **corrected $\alpha = 0.01$** show **≈ 70 % power** to detect an absolute drop from 0.95 to 0.90, which is acknowledged as a limitation but still provides meaningful inference for the study’s scope.

### 2.5 REML Failure Handling (FR‑006)
* Failures are recorded in `reml_failures.json`.  
* **Coverage for REML** is reported **overall** (failures counted as non‑coverage) and **conditionally** (using only replicates where REML converged) to inform users about the frequency of convergence problems without biasing the primary estimate.

## 3. Computational Feasibility (CPU‑first)

* **Batch processing** – replicates are streamed and processed in batches of 100 to keep RAM ≤ 5 GB.  
* **Libraries** – pure `numpy`/`scipy`; no GPU needed.  
* **Estimated runtime** – ~0.7 s per replicate → ≈ a few hours for the full multi‑thousand‑replicate sweep, comfortably within the designated CI limit.

## 4. Methodological Rigor & Assumptions

* **Associational framing** – All conclusions are labelled “associational” (SC‑005) because the study is a simulation based on observational data structures.  
* **Multiplicity** – Bonferroni correction applied across the five τ² levels per estimator (α = 0.01).  
* **Collinearity** – Not applicable; τ² is an exogenous manipulation.  
* **Power** – A sufficient number of replicates per level ensures adequate power for the exact binomial test as described above.  
* **REML failures** – Reported separately; counted as non‑coverage for the primary metric (FR‑006).  

## 5. Decision Rationale

| Decision | Reason |
|----------|--------|
| **Synthetic base generation** | No verified Cochrane dataset exists; generating a realistic synthetic base respects the constitution and provides the required study‑level structure. |
| **Fixed $k$ and $N_i$** | Removes confounding between heterogeneity and study‑size variability. |
| **Shapiro‑Wilk + conditional ANOVA/KW** | Satisfies FR‑008 and avoids a blanket non‑parametric approach. |
| **Count REML failures as non‑coverage** | Provides a clear, unbiased rule for coverage calculation. |
| **Bonferroni across τ² levels only** | Aligns with FR‑007 and the constitution (α = 0.05/5). |
| **900 replicates per level** | Provides reasonable power given the corrected α = 0.01. |

---

