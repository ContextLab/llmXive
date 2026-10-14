# Research: Evaluating the Effectiveness of Differential Privacy in Federated Learning

## Research Question
*Does increasing data heterogeneity (lower Dirichlet concentration α) amplify the utility loss of Differentially Private Federated Learning for minority clients, and is there a critical α ≤ 0.1 where this effect becomes statistically significant?*

## Dataset Strategy

| Dataset | Verified URL(s) | Load Method | Reason for Inclusion |
|---------|----------------|-------------|----------------------|
| **FEMNIST** | <https://huggingface.co/datasets/flwrlabs/femnist/resolve/main/data/train-00000-of-00001.parquet> (train) <br> <https://huggingface.co/datasets/J-C-03/femnist/resolve/main/femnist_test.parquet> (test) | `datasets.load_dataset("flwrlabs/femnist", split="train", streaming=True)` → write to `data/raw/femnist.parquet` | Directly downloadable, image classification, matches the spec’s required format. |
| **Shakespeare** | *None (no verified source)* | N/A | Spec explicitly excludes Shakespeare. The partitioning script raises `ValueError("Shakespeare excluded per plan.md Gap Analysis")` if requested, satisfying FR‑001 and the verification requirement T000 (the exclusion message will be the only Shakespeare reference, yielding grep exit = 0 for exclusion and exit = 1 for “supported”). |

### Partitioning (Heterogeneity Simulation)
1. **Download** the full FEMNIST parquet (≈ 800 k records) via streaming.  
2. **Normalize** pixel values to `[0, 1]`.  
3. **Dirichlet Split**: For each seed `s` and α ∈ {0.1, 0.5, 1.0}, sample a client‑label probability matrix `p_i ∼ Dirichlet(α)`. Assign each example to the client with the highest sampled probability.  
4. **Minority Definition**: Compute empirical label‑entropy per client; flag the bottom **30 %** of clients (by entropy) as `is_minority=True`. This definition is *independent* of α, preventing circularity.  
5. **Validation**: Verify that label variance across clients grows as α decreases, matching Dirichlet theory. Store metadata in `data/partitions/partition_femnist_{seed}_{alpha}.json`.

## Computational Strategy

### Hardware & Runtime
- **Primary**: GitHub Actions free‑tier CPU (2 vCPU, ≈ 7 GB RAM). All libraries are CPU‑only.  
- **GPU Escape Hatch**: Not required; Opacus runs efficiently on CPU for the tiny CNN (~30 k parameters).  

### Algorithmic Details
| Component | Method | Key Parameters |
|-----------|--------|----------------|
| **Model** | Tiny CNN (2 Conv layers + 1 FC) | Batch size = 32, learning rate = 0.01 |
| **Federated Optimizer** | FedAvg | Local epochs = 1, communication rounds ≤ 50 (early stop possible) |
| **Differential Privacy** | Opacus `GradSampleModule` + Gaussian noise | Clip norm = 1.0, noise multiplier derived from target ε (δ = 1e‑5). Moments Accountant tracks cumulative ε. |
| **Non‑DP Baseline** | Same FedAvg without Opacus (ε = ∞) | Logs `epsilon="inf"` and `is_dp=False`. |
| **Early‑Stop / Time‑Budget Logic** | After each round, estimate remaining wall‑clock time (30 s/round). If projected time exceeds the 6 h budget, cap remaining rounds (`max_rounds = floor((budget - overhead) / 30)`). Runs that hit the cap are marked `is_time_limited=True` and excluded from downstream statistical tests. |

### Deterministic Seed Handling
- The orchestrator (`T018c`) runs **exactly 5 seeds** per (α, ε) configuration.  
- If a seed crashes (OOM, timeout), the orchestrator retries with the next integer seed up to 3 attempts; persistent failures are logged, and the missing seed is noted in `validation_report.md`.

## Statistical Analysis Plan

### Hypotheses
| # | Null Hypothesis (H₀) | Alternative (H₁) |
|---|----------------------|------------------|
| **H₁₁** | DP does **not** change global accuracy (paired difference = 0). | DP reduces global accuracy (difference < 0). |
| **H₁₂** | Minority clients suffer the same degradation as majority clients. | Minority degradation > majority degradation. |
| **H₁₃** | No interaction between α and ε on minority degradation. | Lower α amplifies degradation, especially for ε ≤ 0.5. |

### Paired t‑tests (FR‑005 requirement)
- For each (α, ε) pair, compute the paired difference in **global accuracy** between DP and non‑DP runs **across the 5 seeds** (same partition).  
- Apply a **two‑sided paired t‑test**.  
- When > 5 tests are performed (15 total: 3 α × 5 ε), apply **Bonferroni correction** (α_adj ≈ 0.0033).

### Mixed‑Effects Model (Minority vs. Majority)
- Response: `degradation = accuracy_nonDP – accuracy_DP` per client.  
- Fixed effect: `Group` (`is_minority`).  
- Random intercepts for `seed` and, if CPU budget permits, `seed:client`. Implemented via `statsmodels.MixedLM`.  
- Report coefficient, 95 % CI, and Bonferroni‑adjusted p‑value.

### Power & Sample‑Size
- **Seeds**: 5 per configuration (mandated by FR‑004).  
- With 5 paired observations, the detectable effect size at α = 0.05 (two‑sided) is ≈ Cohen’s d = 1.1. This limitation is explicitly disclosed; the study is powered only for relatively large DP‑induced degradations.

### Multiple‑Comparison Correction
- Bonferroni across the 15 (α, ε) tests (α_adj = 0.05/15 ≈ 0.0033).

### Utility‑Collapse Filtering (SC‑005)
- Random‑guessing threshold for FEMNIST (62 classes) is `1/62 ≈ 0.01613`.  
- Any run with `global_accuracy < 0.01613` is removed before statistical testing (`T035`).

### Reporting
- `results/final_stats.csv` – p‑values, effect sizes, confidence intervals, significance flag.  
- Overlay plot `figures/minority_vs_global_overlay.png` (minority vs. global accuracy curves).  
- Sensitivity curves `figures/sensitivity_alpha.png` (accuracy vs. ε for each α).  
- Summary tables `results/summary.csv`, `results/p_values_by_seed.json`.  
- Human‑readable `results/validation_report.md` documenting checksum verification, seed completeness, and any excluded runs.

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| **CPU timeout** | Medium – could exceed 6 h | Deterministic early‑stop; round cap based on real‑time estimate; flagged runs excluded from analysis. |
| **Seed failure** | High – would violate FR‑004 | Orchestrator retries up to 3 times; missing seeds logged; final report notes any gaps. |
| **Utility collapse (ε = 0.1)** | Low – may produce near‑random accuracy | Filtering step (`T035`) removes such runs before testing. |
| **Opacus overhead** | Medium – slows training | Small batch size (32), single local epoch, pre‑profiled runtime to set `estimated_time_per_round`. |
| **Shakespeare request** | Low – spec mentions but data unavailable | Partitioning script raises `ValueError` with the exact mandated message; verification T000 passes because only the exclusion message is present. |

---
