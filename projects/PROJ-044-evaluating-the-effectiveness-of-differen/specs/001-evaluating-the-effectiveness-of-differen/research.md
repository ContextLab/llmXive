# Research: Evaluating the Effectiveness of Differential Privacy in Federated Learning

## Research Question
*Does increasing data heterogeneity (low Dirichlet concentration α) amplify the utility loss of Differentially Private Federated Learning for minority clients, and is there a critical α ≤ 0.1 where this effect becomes statistically significant?*

## Dataset Strategy

| Dataset | Verified URL(s) | Load Method | Reason for Inclusion |
|---------|----------------|-------------|----------------------|
| **FEMNIST** | <https://huggingface.co/datasets/flwrlabs/femnist/resolve/main/data/train-00000-of-00001.parquet> (train) <br> <https://huggingface.co/datasets/J-C-03/femnist/resolve/main/femnist_test.parquet> (test) | `datasets.load_dataset("flwrlabs/femnist", split="train", streaming=False)` → write to `data/raw/femnist.parquet` | Directly downloadable, image classification, matches spec's required format. |
| **Shakespeare** | *None (no verified source)* | N/A | Spec mentions Shakespeare, but the verified‑datasets block contains no URL. The project therefore **excludes** Shakespeare and raises a `ValueError` if requested (FR‑001). |

### Partitioning (Heterogeneity Simulation)
1. **Download** the full FEMNIST parquet (≈ 814 k records).  
2. **Normalize** pixel values to `[0, 1]`.  
3. **Dirichlet Split**: For each seed `s` and α ∈ {0.1, 0.5, 1.0} generate a client‑label probability matrix `p_i ∼ Dirichlet(α)`. Assign each training example to the client with the highest sampled probability.  
4. **Minority Definition**: Compute empirical label‑entropy for each client within a partition. Flag the **bottom [deferred]** of clients (by entropy) as `is_minority=True`. This definition is **pre‑specified** and independent of the Dirichlet concentration α, avoiding post‑hoc selection bias.
5. **Validation**: Compute empirical label variance; ensure it matches theoretical expectations (higher variance for lower α). Store metadata in `data/partitions/partition_femnist_{seed}_{alpha}.json`.

## Computational Strategy

### Hardware & Runtime
- **Primary**: GitHub Actions free‑tier CPU (2 vCPU, ≈ 7 GB RAM). All libraries are CPU‑only.  
- **GPU Escape Hatch**: None required; Opacus runs efficiently on CPU for modestly sized models (on the order of tens of thousands of parameters).  

### Algorithmic Details
| Component | Method | Key Parameters |
|-----------|--------|----------------|
| **Model** | Tiny CNN (2 Conv layers + 1 FC) | Batch size = 32, learning rate = 0.01 |
| **Federated Optimizer** | FedAvg | Local epochs = 1, communication rounds ≤ 50 (early stop possible) |
| **Differential Privacy** | Opacus `GradSampleModule` + Gaussian noise | Clip norm = 1.0, Noise multiplier derived from target ε (δ = 1e‑5). Moments Accountant tracks cumulative ε. |
| **Non‑DP Baseline** | Same FedAvg without Opacus (ε = "inf") | The log entry records `epsilon="inf"` and `is_dp=False`. |
| **Early‑Stop / Time‑Budget Logic** | Deterministic round cap based on a conservative estimate of 30 s per round; runs exceeding the budget are truncated, flagged `is_time_limited=True`, and **excluded from all downstream statistical analyses**. | 

### Deterministic Seed Handling
- The orchestrator (`T018c`) iterates **exactly 5 seeds** per (α, ε) configuration.  
- If a seed crashes (OOM, timeout), a fresh seed is drawn (incremented integer) and retried **up to 3 attempts**; after 3 failures the seed is dropped and the issue is recorded in `results/validation_report.md`.  

## Statistical Analysis Plan

### Hypotheses
| # | Null Hypothesis (H₀) | Alternative (H₁) |
|---|----------------------|------------------|
| **H₁₁** | DP does **not** change global accuracy relative to non‑DP (paired difference = 0). | DP reduces global accuracy (difference < 0). |
| **H₁₂** | Minority clients experience the **same** accuracy degradation as majority clients. | Minority degradation > majority degradation. |
| **H₁₃** | No interaction between α and ε on minority degradation. | Lower α (more heterogeneity) amplifies degradation, especially for ε ≤ 0.5. |

### Paired Tests (Requirement: **paired t‑test** only)
- For each seed, compute **global accuracy** for DP and non‑DP runs on the *same* partition → paired differences.  
- Apply a **two‑sided paired t‑test** across the 5 seeds.  
- **Bonferroni correction** if > 5 simultaneous tests (e.g., when sweeping multiple ε).  

### Mixed‑Effects Model (Minority vs. Majority)
- Response: `degradation = accuracy_nonDP – accuracy_DP` per client.  
- Fixed effect: `Group` (Minority = 1, Majority = 0).  
- Random effects: **Intercept for Seed** *and* **Intercept for Client nested within Seed** (if CPU budget permits; otherwise robust SEs are used).  
- Implemented via `statsmodels` `MixedLM`.  
- Report coefficient, 95 % CI, and Bonferroni‑adjusted p‑value.  

### Power & Sample‑Size Considerations
- **Seeds**: 5 independent seeds per configuration (as mandated by FR‑004).  
- With 5 paired observations, the minimum detectable effect size at α = 0.05 (two‑sided) is ≈ 1.1 SD (Cohen’s d). This is acknowledged as a limitation; the study is powered to detect only relatively large DP‑induced degradations.  

### Multiple‑Comparison Correction
- When testing across **5 ε values** × **3 α values** (15 tests), apply **Bonferroni** (α_adj = 0.05/15 ≈ 0.0033).  

### Utility‑Collapse Filtering (SC‑005)
- Define **random‑guessing threshold** as `1 / N_classes`. FEMNIST consists of multiple classes → threshold = 1/62 ≈ 0.01613.  
- Any run with `global_accuracy < 0.01613` is dropped before statistical testing (implemented in `T035`).  

### Reporting
- Produce `results/final_stats.csv` containing p‑values, effect sizes, and confidence intervals.  
- Generate overlay plot `figures/minority_vs_global_overlay.png` and sensitivity curves `figures/sensitivity_alpha.png`.  
- Summarize in `results/summary.csv`, `results/validation_report.md`, and `results/p_values_by_seed.json`.  

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| **CPU Timeout** | Medium – could exceed 6 h | Deterministic early‑stop rule; rounds reduced only after time check; flagged runs excluded from analyses. |
| **Insufficient Seeds** (e.g., a seed fails repeatedly) | High – would break FR‑004 | Orchestrator retries up to 3 times; if still failing, logs warning and proceeds with next seed; final report notes any missing seeds. |
| **Utility Collapse (ε = 0.1)** | Low – may produce near‑random accuracy | Filtering step removes such runs before statistical tests. |
| **Opacus CPU Overhead** | Medium – slows training | Use modest batch size (32) and limit local epochs to 1; profile once on a dry run to calibrate `estimated_time_per_round`. |
| **Shakespeare Request** | Low – spec mentions but data unavailable | Partitioning script raises `ValueError` with prescribed message; verification task T000 ensures only exclusion references appear. |

---

