# Research: Evaluating the Effectiveness of Differential Privacy in Federated Learning

## Research Question
*Does increasing data heterogeneity (lower Dirichlet concentration α) amplify the utility loss of Differentially Private Federated Learning for minority clients, and is there a critical α ≤ 0.1 where this effect becomes statistically significant?*

## Dataset Strategy

| Dataset | Verified URL(s) | Load Method | Reason for Inclusion |
|---------|----------------|-------------|----------------------|
| **FEMNIST (train)** | <https://huggingface.co/datasets/flwrlabs/femnist/resolve/main/data/train-00000-of-00001.parquet> | `datasets.load_dataset("flwrlabs/femnist", split="train", streaming=True)` → write to `data/raw/femnist_train.parquet` | Directly downloadable, image classification, matches the spec’s required format. |
| **FEMNIST (test)** | <https://huggingface.co/datasets/J-C-03/femnist/resolve/main/femnist_test.parquet> | `datasets.load_dataset("J-C-03/femnist", split="test", streaming=True)` → write to `data/raw/femnist_test.parquet` | Provides a held‑out test set for evaluation. |
| **Shakespeare** | *None (no verified source)* | N/A | Explicitly excluded by FR‑001. The system raises `ValueError("Shakespeare excluded per plan.md Gap Analysis")` if requested, satisfying the exclusion requirement and the original T000 verification via a real script. |

### Partitioning (Heterogeneity Simulation)
1. **Download** the two FEMNIST parquet files via streaming (**T001**).  
2. **Normalize** pixel values to `[0, 1]`.  
3. **Global Entropy Computation**: Compute label‑entropy for every client on the **full** training set once; flag the **bottom [deferred]** as `is_minority=True`. This definition is **global**, not α‑dependent, preserving construct validity (FR‑006, Principle VI). A Pearson correlation between client entropy and α is computed; if |r| > 0.3 a warning is logged and the value recorded in `results/validation_report.md`.
4. **Dirichlet Split**: For each seed `s` and α ∈ {0.1, 0.5, 1.0}, sample a client‑label probability matrix `p_i ∼ Dirichlet(α)`. Assign each example to the client with the highest sampled probability. Store metadata in `data/partitions/partition_femnist_{seed}_{alpha}.json`.  
5. **Validation**: Verify that label variance across clients increases as α decreases, matching Dirichlet theory. Confirm byte‑identical partition files for repeated runs (SHA‑256 hash check – SC‑001).  

## Computational Strategy

### Hardware & Runtime
- **Primary**: GitHub Actions free‑tier CPU (2 vCPU, ≈ 7 GB RAM). All libraries run on CPU.  
- **GPU Escape Hatch**: Not required; Opacus operates efficiently on CPU for the tiny CNN.  

### Algorithmic Details
| Component | Method | Key Parameters |
|-----------|--------|----------------|
| **Model** | Tiny CNN (2 Conv layers + 1 FC) | Batch size = 32, learning rate = 0.01 |
| **Federated Optimizer** | FedAvg | Local epochs = 1, communication rounds ≤ 15 (early‑stop possible) |
| **Differential Privacy** | Opacus `GradSampleModule` + Gaussian noise | Clip norm = 1.0, noise multiplier derived from target ε (δ = 1e‑5). Moments Accountant tracks cumulative ε. |
| **Non‑DP Baseline** | Same FedAvg without Opacus (ε = ∞) | Logs `epsilon="inf"` and `is_dp=False`. |
| **Early‑Stop / Time‑Budget Logic** | After each round, estimate remaining wall‑clock time (≈ 15 s/round). If projected total exceeds the 6 h budget, caps remaining rounds (`max_rounds=15`). Runs that hit the cap are flagged `is_time_limited=True` and **retained**. DP vs. non‑DP are compared at the **minimum number of completed rounds** between the pair (matched‑round evaluation) to avoid confounding training duration with privacy noise. |
| **Survival‑Analysis for Convergence** | Cox proportional‑hazards model on `rounds_to_80` with right‑censoring for time‑limited runs. Hazard ratios are reported; a secondary table excludes censored runs for comparison. |

### Deterministic Seed Handling
- The orchestrator (**T006**) runs **10 seeds** per (α, ε) configuration (seeds 42‑51).  
- If a seed crashes (OOM, timeout), the orchestrator retries up to 3 times; persistent failures are logged in `validation_report.md`.  

## Power & Sample‑Size
- **Seeds**: 10 per configuration (mandated by FR‑004).  
- With *n* = 10, a two‑sided paired t‑test at α = 0.05 (Bonferroni‑adjusted α≈0.0056) has 80 % power to detect **Cohen’s d ≈ 1.25**. This larger detectable effect size (relative to the unadjusted d≈0.94) is documented in `results/summary.csv` metadata (SC‑011).  
- If the compute budget forces a reduction to **6 seeds**, the power analysis is re‑run; the detectable effect rises to **d ≈ 1.6**, and the updated value is recorded.  

## Statistical Analysis Plan

### Hypotheses
| # | Null Hypothesis (H₀) | Alternative (H₁) |
|---|----------------------|------------------|
| **H₁₁** | DP does **not** change global accuracy (paired difference = 0). | DP reduces global accuracy (difference < 0). |
| **H₁₂** | Minority clients suffer the same degradation as majority clients. | Minority degradation > majority degradation. |
| **H₁₃** | No interaction between α and DP‑induced degradation for minority clients. | Lower α amplifies degradation for minority clients (α × is_minority interaction). |

### Paired Tests (FR‑005)
- For each (α, ε) pair, compute the paired difference in **global accuracy** between DP and non‑DP runs across the 10 seeds (same partition).  
- Perform a **Shapiro‑Wilk normality test** on the differences.  
  - If normal (p > 0.05): run a two‑sided paired t‑test.  
  - Otherwise: run a **Wilcoxon signed‑rank test** (non‑parametric).  
- Apply **Bonferroni correction** across the 9 (α, ε) tests (α_adj ≈ 0.0056).  
- Report raw and adjusted p‑values, effect size (Cohen’s d for t‑test, rank‑biserial for Wilcoxon), and a significance flag (`p_adj < 0.05`).  

### Mixed‑Effects Model (Minority‑vs‑Majority, FR‑005)
- Response: `degradation = accuracy_nonDP – accuracy_DP` per client.  
- Fixed effects: `is_minority`, `alpha`, `epsilon`, and the **two‑way** interaction `is_minority * alpha`.  
- Random effects: intercept **and** a random slope for `epsilon` per `seed` → `(1 + epsilon | seed)`.  
- Fit using `statsmodels.MixedLM`.  
- Report coefficient for `is_minority:alpha`, 95 % CI, and Bonferroni‑adjusted p‑value. Also extract the α × ε interaction term.  

### Convergence Speed (FR‑008)
- Compute `rounds_to_80` = first round where `global_accuracy ≥ 0.80`.  
- Use a **survival‑analysis** (Cox model) with `is_time_limited` as right‑censoring.  
- Report hazard ratios for ε and α, and provide a secondary table that excludes censored runs.  

### Reporting
- `results/final_stats.csv` – p‑values, effect sizes, interaction estimates, and significance flags.  
- Overlay plot `figures/minority_vs_global_overlay.png` (minority vs. global accuracy curves).  
- Sensitivity plot `figures/sensitivity_alpha.png` (accuracy & convergence speed vs. ε for each α).  
- Summary tables `results/summary.csv`, `results/validation_report.md`, and `results/p_values_by_seed.json`.  
- Validation report includes:  
  * FEMNIST checksum verification.  
  * Confirmation that the only occurrence of “Shakespeare” is inside the mandated exclusion message (via `verify_shakespeare_exclusion.py`).  
  * Seed completeness and any flagged runs.  
  * Minority‑definition correlation diagnostic (Pearson r).  

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **CPU timeout** | Medium – could exceed 6 h budget | Deterministic early‑stop; round cap (`max_rounds=15`) and runtime estimate; flagged runs retained; survival analysis accounts for censoring. |
| **Seed failure** | High – would violate FR‑004 | Orchestrator retries up to 3 times; seed completeness logged; final report notes any gaps. |
| **Utility collapse (ε = 0.1)** | Low – may produce near‑random accuracy | Runs are **retained**; `utility_collapse` flag added; diagnostic included in survival model. |
| **Opacus overhead** | Medium – slows training | Small batch size (32), single local epoch, pre‑profiled runtime to set `estimated_time_per_round`. |
| **Normality violation** | High – paired t‑test assumption may fail | Shapiro‑Wilk normality check; fallback to Wilcoxon signed‑rank test (SC‑005). |
| **Model over‑parameterisation** | Medium – three‑way interaction removed; simplified model reduces risk (addressed in methodology‑957977f0). |
| **Early‑stop confound** | Medium – matched‑round evaluation eliminates bias (addressed in methodology‑f84971fa). |
| **Censoring bias** | Medium – survival analysis replaces simple exclusion (addressed in methodology‑122d32b8). |
| **Minority‑definition correlation** | Medium – diagnostic added; if correlation >0.3 a warning is logged (addressed in methodology‑8fae6a94). |

---

