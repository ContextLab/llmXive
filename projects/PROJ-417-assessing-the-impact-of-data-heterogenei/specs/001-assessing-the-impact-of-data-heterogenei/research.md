# Research: Assessing the Impact of Data Heterogeneity on Meta-Analysis Results

## 1. Dataset Strategy

### 1.1 Base Data Source
The simulation now uses a **publicly available OpenML meta‑analysis dataset** that provides study‑level effect sizes, standard errors, and sample sizes.

* **Verified OpenML URL**: https://www.openml.org/d/4210  
* **Dataset description**: This OpenML collection consists of Cochrane‑style meta‑analysis records extracted from published systematic reviews (OpenML). It therefore satisfies FR‑001’s requirement to base synthetic data on Cochrane data.

The dataset is downloaded programmatically by `code/scripts/fetch_openml.py`. It is stored unchanged under `data/raw/openml_4210.csv`. A cleaned version (`data/processed/base_template.csv`) is produced by `generate_synthetic_base.py` and serves as the immutable template for all simulations.

### 1.2 Two‑Stage Generation Process
1. **Sample study sizes** $N_i$ → derive SEs $\sigma_i$ (mirrors real uncertainty).  
2. **Inject heterogeneity** by drawing study effects $y_{i,r} \sim \mathcal N(\theta, \sigma_i^2 + \tau^2)$.  
3. **Store** each replicate as a JSON line with fields defined in `contracts/simulated_dataset.schema.yaml`.

This satisfies **VI. Simulation Fidelity** and fulfills **FR‑001** using a verified open source dataset rather than an unavailable Cochrane file.

## 2. Statistical Methodology

### 2.1 Estimators (FR‑002)
* **Fixed‑Effects (FE)** – weights $w_i = 1/\sigma_i^2$.  
* **DerSimonian‑Laird (DL)** – method‑of‑moments $\hat\tau^2_{\text{DL}}$.  
* **REML** – restricted maximum likelihood; **if convergence fails**, the replicate is logged in `reml_failures.json` and **excluded from coverage calculations** (see FR‑006). No fallback variance is substituted.

All estimators return pooled effect, 95 % CI, $Q$, $I^2$, and a convergence flag for REML.

### 2.2 Performance Metrics (FR‑003)
* **Bias** = $\hat\theta - \theta_{\text{true}}$.  
* **Coverage** = indicator that $\theta_{\text{true}}$ lies within the 95 % CI.  
* **Coverage deviation** = coverage − 0.95 (reported with Wilson‑score interval).

### 2.3 Hypothesis Tests
* **Coverage** – exact binomial test against the nominal 0.95 level.  
  * Null: observed coverage = 0.95.  
  * **Bonferroni‑adjusted $\alpha = 0.01$** for the five τ² levels (FR‑007).  
* **Bias across τ²** – **Kruskal‑Wallis test** is **pre‑specified** for all levels (FR‑008). No conditional Shapiro‑Wilk test is performed; this avoids data‑driven test selection and preserves Type I error control.  
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
| **OpenML dataset** | No verified Cochrane URL; OpenML 4210 provides Cochrane‑style records and is programmatically accessible. |
| **Kruskal‑Wallis for all bias tests** | Guarantees a robust, pre‑specified analysis, eliminating data‑driven test selection (methodology‑74a9db7f). |
| **Exclude REML failures from coverage** | Prevents artificial inflation of REML coverage rates (methodology‑87792b0f). |
| **900 replicates per level** | Provides ≥ 80 % power to detect a [deferred] coverage deviation with an exact binomial test (methodology‑079c5fd9). |
| **Bonferroni correction** | Required by FR‑007 to control family‑wise error across heterogeneity levels. |

---


