# Research: Assessing the Impact of Data Heterogeneity on Meta-Analysis Results

## 1. Dataset Strategy

### 1.1 Base Data Source
No verified Cochrane‑style meta‑analysis dataset is publicly downloadable (the “Verified datasets” block contains no such URL). To remain faithful to the constitution, we **do not claim** to use external Cochrane data. Instead we generate a **synthetic base template** that mimics typical study‑size distributions and standard‑error magnitudes observed in published meta‑analyses (e.g., mean study size ≈ 150, SE distribution approximated by a scaled chi‑square). This synthetic base is created once by `code/scripts/generate_base.py` and stored as `data/processed/base_template.csv`. The generation is deterministic (fixed seed) and documented, satisfying Principle I (Reproducibility) and Principle III (Data Hygiene).

### 1.2 Two‑Stage Generation Process
1. **Sample study sizes** $N_i$ from a truncated normal (mean 150, sd 50, lower = 20) → derive SEs $\sigma_i = \sqrt{1/N_i}$ (or another realistic mapping).  
2. **Inject heterogeneity** by drawing study effects $y_{i,r} \sim \mathcal N(\theta, \sigma_i^2 + \tau^2)$, where $\theta=0.5$ (the true effect size) and $\tau^2$ takes the predefined levels.  
3. **Store** each replicate as a JSON‑line adhering to `contracts/simulated_dataset.schema.yaml`.

This satisfies **VI. Simulation Fidelity** and fulfills **FR‑001** using a verified open‑source approach (synthetic generation) rather than an unavailable Cochrane file.

## 2. Statistical Methodology

### 2.1 Estimators (FR‑002)
* **Fixed‑Effects (FE)** – weights $w_i = 1/\sigma_i^2$.  
* **DerSimonian‑Laird (DL)** – method‑of‑moments estimator $\hat\tau^2_{\text{DL}}$.  
* **REML** – restricted maximum likelihood; **if convergence fails**, the replicate is logged in `reml_failures.json` and **excluded from coverage calculations** (FR‑006). No artificial variance fallback is applied.

All estimators return pooled effect, 95 % CI, $Q$, $I^2$, and a convergence flag for REML.

### 2.2 Performance Metrics (FR‑003)
* **Bias** = $\hat\theta - \theta_{\text{true}}$.  
* **Coverage** = indicator that $\theta_{\text{true}}$ lies within the 95 % CI.  
* **Coverage deviation** = coverage − 0.95 (reported with Wilson‑score interval).

### 2.3 Hypothesis Tests
* **Coverage** – exact binomial test against the nominal 0.95 level.  
  * Null: observed coverage = 0.95.  
  * **Bonferroni‑adjusted $\alpha = 0.01$** for the five τ² levels (FR‑007).  
* **Bias across τ²** – **Kruskal‑Wallis test** is **pre‑specified** for all levels (FR‑008). No Shapiro‑Wilk conditional branch is performed; this avoids data‑driven test selection and preserves Type I error control.  
  * If Kruskal‑Wallis is significant, Dunn’s post‑hoc with Bonferroni correction identifies pairwise differences.

### 2.4 Power & Precision
With **900 replicates per τ² level** (primary and sensitivity sweeps), the Monte‑Carlo standard error of a coverage proportion $p$ is $\sqrt{p(1-p)/900}\approx0.016$. Power calculations for an exact binomial test show ≥ 80 % power to detect a [deferred] deviation from the nominal 0.95 level, satisfying the scientific requirement.

## 3. Computational Feasibility (CPU‑first)

* **Batch processing** – replicates are streamed and processed in batches of 100 to keep RAM ≤ 5 GB.  
* **Libraries** – pure `numpy`/`scipy`; no GPU needed.  
* **Estimated runtime** – ~0.7 s per replicate → ≈ 3 h for the full 7 200‑replicate sweep, comfortably within the 6 h CI limit.

## 4. Methodological Rigor & Assumptions

* **Associational framing** – All conclusions are labelled “associational” (SC‑005) because the study is a simulation based on observational data structures.  
* **Multiplicity** – Bonferroni correction applied to all five τ²‑level coverage tests (FR‑007).  
* **Collinearity** – Not applicable; τ² is an exogenous manipulation.  
* **Power** – 900 replicates per level ensure adequate power for the exact binomial test.  
* **REML failures** – Reported separately; excluded from coverage to avoid bias (FR‑006).  

## 5. Decision Rationale

| Decision | Reason |
|----------|--------|
| **Synthetic base generation** | No verified Cochrane dataset exists; generating a realistic synthetic base respects the constitution and provides the required study‑level structure. |
| **Kruskal‑Wallis for all bias tests** | Guarantees a robust, pre‑specified analysis, eliminating data‑driven test selection (methodology‑74a9db7f). |
| **Exclude REML failures from coverage** | Prevents artificial inflation of REML coverage rates (methodology‑87792b0f). |
| **900 replicates per level** | Provides ≥ 80 % power to detect a [deferred] coverage deviation with an exact binomial test (methodology‑079c5fd9). |
| **Bonferroni correction** | Required by FR‑007 to control family‑wise error across heterogeneity levels. |

---
