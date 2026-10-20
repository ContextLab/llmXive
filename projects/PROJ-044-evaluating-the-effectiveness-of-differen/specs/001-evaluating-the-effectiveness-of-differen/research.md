# Research: Evaluating the Effectiveness of Differential Privacy in Federated Learning

## Research Question
*Does increasing data heterogeneity (lower Dirichlet concentration α) amplify the utility loss of Differentially Private Federated Learning for minority clients, and is there a critical α ≤ 0.1 where this effect becomes statistically significant?*

## Dataset Strategy

| Dataset | Verified URL(s) | Load Method | Reason for Inclusion |
|---------|----------------|-------------|----------------------|
| **FEMNIST (train)** | <https://huggingface.co/datasets/flwrlabs/femnist/resolve/main/data/train-00000-of-00001.parquet> | `datasets.load_dataset("flwrlabs/femnist", split="train", streaming=True)` → write to `data/raw/femnist_train.parquet` | Directly downloadable, image classification, matches the spec’s required format. |
| **FEMNIST (test)** | <https://huggingface.co/datasets/J-C-03/femnist/resolve/main/femnist_test.parquet> | `datasets.load_dataset("J-C-03/femnist", split="test", streaming=True)` → write to `data/raw/femnist_test.parquet` | Provides a held‑out test set for evaluation. |
| **Shakespeare** | *None (no verified source)* | N/A | Spec explicitly excludes Shakespeare. The partitioning script raises `ValueError("Shakespeare excluded per plan.md Gap Analysis")` if requested, satisfying FR‑001 and the verification requirement T000. |

### Partitioning (Heterogeneity Simulation)
1. **Download** the two FEMNIST parquet files via streaming (Task **T001**).  
2. **Normalize** pixel values to `[0, 1]`.  
3. **Global Entropy Computation**: Compute label‑entropy for every client on the **full** training set once; flag the **bottom [deferred]** (by entropy) as `is_minority=True`. This definition is **global**, not dependent on α, ensuring construct validity.
4. **Dirichlet Split**: For each seed `s` and α ∈ {0.1, 0.5, 1.0}, sample a client‑label probability matrix `p_i ∼ Dirichlet(α)`. Assign each example to the client with the highest sampled probability.  
5. **Validation**: Verify that label variance across clients grows as α decreases, matching Dirichlet theory. Store metadata in `data/partitions/partition_femnist_{seed}_{alpha}.json`.

## Computational Strategy

### Hardware & Runtime
- **Primary**: GitHub Actions free‑tier CPU (2 vCPU, ≈ 7 GB RAM). All libraries are CPU‑only.  
- **GPU Escape Hatch**: Not needed; Opacus runs efficiently on CPU for the tiny CNN with on the order of tens of thousands of parameters.  

### Algorithmic Details
| Component | Method | Key Parameters |
|-----------|--------|----------------|
| **Model** | Tiny CNN (2 Conv layers + 1 FC) | Batch size = 32, learning rate = 0.01 |
| **Federated Optimizer** | FedAvg | Local epochs = 1, communication rounds ≤ 15 (early stop possible) |
| **Differential Privacy** | Opacus `GradSampleModule` + Gaussian noise | Clip norm = 1.0, noise multiplier derived from target ε (δ = 1e‑5). Moments Accountant tracks cumulative ε. |
| **Non‑DP Baseline** | Same FedAvg without Opacus (ε = ∞) | Logs `epsilon="inf"` and `is_dp=False`. |
| **Early‑Stop / Time‑Budget Logic** | After each round, estimate remaining wall‑clock time (approximately a brief interval per round). If projected time exceeds the 6 h budget, cap remaining rounds (`max_rounds=15`). Runs that hit the cap are marked `is_time_limited=True` **and are retained** for analysis. |

### Deterministic Seed Handling
- The orchestrator (`T006`) runs **exactly 10 seeds** per (α, ε) configuration.  
- If a seed crashes (OOM, timeout), the orchestrator retries with the next integer seed up to 3 attempts; persistent failures are logged, and the missing seed is noted in `validation_report.md`.

## Power & Sample‑Size
- **Seeds**: 10 per configuration (mandated by FR‑004).  
- With n=10, a two‑sided paired test (α = 0.05, Bonferroni‑adjusted α≈0.0056) can detect a moderate effect size of **Cohen’s d ≈ 0.78**, which is realistic for DP‑FL utility degradations.  
- This increase is explicitly disclosed; the study is powered to detect moderate to large DP‑induced degradations.

## Statistical Analysis Plan

### Hypotheses
| # | Null Hypothesis (H₀) | Alternative (H₁) |
|---|----------------------|------------------|
| **H₁₁** | DP does **not** change global accuracy (paired difference = 0). | DP reduces global accuracy (difference < 0). |
| **H₁₂** | Minority clients suffer the same degradation as majority clients. | Minority degradation > majority degradation. |
| **H₁₃** | No interaction between α and DP‑induced degradation for minority clients. | Lower α amplifies degradation for minority clients (α × is_minority interaction). |

### Paired Tests (FR‑005 requirement)
- For each (α, ε) pair, compute the paired difference in **global accuracy** between DP and non‑DP runs **across the 10 seeds** (same partition).  
- Perform a **Shapiro‑Wilk normality test** on the differences.  
  - If normal (p > 0.05): run a two‑sided paired t‑test.  
  - Otherwise: run a **Wilcoxon signed‑rank test** (non‑parametric).  
- Apply **Bonferroni correction** across the 9 tests (α_adj ≈ 0.0056).  
- Report raw and adjusted p‑values, effect size (Cohen’s d for t‑test, rank‑biserial for Wilcoxon), and a significance flag (`p_adj < 0.05`).

### Mixed‑Effects Model (Minority‑vs‑Majority)
- Response: `degradation = accuracy_nonDP – accuracy_DP` per client.  
- Fixed effects: `is_minority`, `alpha`, `epsilon`, `is_time_limited`, `utility_collapse`, and the interaction `is_minority * alpha`.  
- Random effects: intercept **and** slopes for `epsilon` and `alpha` per `seed` → `(1 + epsilon + alpha | seed)`.  
- Fit using `statsmodels.MixedLM`.  
- Report coefficient for `is_minority:alpha`, 95 % CI, and Bonferroni‑adjusted p‑value.

### Multiple‑Comparison Correction
- Bonferroni across the 9 (α, ε) tests (α_adj ≈ 0.0056).

### Reporting
- `results/final_stats.csv` – p‑values, effect sizes, confidence intervals, significance flag.  
- Overlay plot `figures/minority_vs_global_overlay.png` (minority vs. global accuracy curves).  
- Sensitivity curves `figures/sensitivity_alpha.png` (accuracy vs. ε for each α).  
- Summary tables `results/summary.csv`, `results/validation_report.md`, and `results/p_values_by_seed.json`.  
- Validation report includes:
  * FEMNIST checksum verification.  
  * Confirmation that the only occurrence of “Shakespeare” is inside the mandated exclusion message (via `verify_shakespeare_exclusion.py`).  
  * Seed completeness and any flagged runs.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **CPU timeout** | Medium – could exceed 6 h budget | Deterministic early‑stop; round cap (`max_rounds=15`) and runtime estimate; flagged runs retained for analysis. |
| **Seed failure** | High – would violate FR‑004 | Orchestrator retries up to 3 times; missing seeds logged; final report notes any gaps. |
| **Utility collapse (ε = 0.1)** | Low – may produce near‑random accuracy | Runs are **retained**; `utility_collapse` flag added; analysis includes them as a covariate. |
| **Opacus overhead** | Medium – slows training | Small batch size (32), single local epoch, pre‑profiled runtime to set `estimated_time_per_round`. |
| **Normality violation** | High – paired t‑test assumption may fail | Normality check with Shapiro‑Wilk; fallback to Wilcoxon signed‑rank test. |
| **Model misspecification** | Medium – omitted random slopes could bias | Mixed‑effects model includes random slopes for ε and α, and interaction term for α × minority. |
| **Early‑stop bias** | Medium – DP may need more rounds | Time‑limited runs are **kept** and used as covariate; no exclusion. |

---



