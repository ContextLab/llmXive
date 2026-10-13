# Implementation Plan: Evaluating the Effectiveness of Differential Privacy in Federated Learning

**Branch**: `001-evaluating-dp-federated-learning` | **Date**: 2026-10-13 | **Spec**: `specs/001-evaluating-dp-federated-learning/spec.md`  
**Input**: Feature specification from `/specs/001-evaluating-dp-federated-learning/spec.md`

## Summary
Implement a reproducible computational study that (1) partitions the **FEMNIST** dataset into heterogeneous client sets using Dirichlet concentrations α ∈ {0.1, 0.5, 1.0}, (2) trains Federated Averaging (FedAvg) models **with** and **without** Differential Privacy (DP) via Opacus, (3) logs per‑client and global accuracies for **5 independent random seeds** per configuration, and (4) conducts **paired t‑tests** (and a Linear Mixed‑Effects Model) to assess whether minority clients suffer larger DP‑induced degradation, especially at high heterogeneity (α ≤ 0.1). All steps run on the CPU‑only GitHub Actions free tier; a deterministic early‑stop / round‑reduction algorithm guarantees completion within the 6‑hour limit.

## Technical Context
- **Language/Version**: Python 3.10+  
- **Primary Dependencies**: `torch==2.3.0` (CPU), `opacus==1.4.0`, `datasets==2.19.0`, `pandas`, `numpy`, `scipy`, `statsmodels`, `matplotlib`, `pyarrow` (for parquet I/O)  
- **Storage**: `data/` (raw parquet, partition JSON), `results/` (CSV logs, filtered CSVs, summary CSV), `figures/` (PNG plots)  
- **Testing**: `pytest` (unit & integration) – tests cover partition reproducibility, DP‑vs‑non‑DP logging, and statistical‑analysis sanity checks.  
- **Target Platform**: Linux GitHub Actions free tier (2 vCPU, ≈ 7 GB RAM, ≈ 14 GB disk).  
- **Performance Goals**: Finish **5 seeds × 3 α × 5 ε** (including ε = ∞ baseline) within **6 h** on CPU.  
- **Constraints**: No GPU usage; streaming download of FEMNIST; strict adherence to the Constitution; Shakespeare dataset permanently excluded.

## Constitution Check
| Principle | Status | Rationale |
|-----------|--------|-----------|
| I. Reproducibility | ✅ | All random generators seeded; deterministic orchestration; exact dataset URL. |
| II. Verified Accuracy | ✅ | Only the FEMNIST URLs listed in the “Verified datasets” block are used. |
| III. Data Hygiene | ✅ | SHA‑256 checksums recorded; raw parquet never mutated; derived files have new names. |
| IV. Single Source of Truth | ✅ | All metrics are first recorded in `results/raw_logs.csv`. Derived files (`filtered_*`, `final_stats.csv`, etc.) are **strictly derived** from this SSoT and do not introduce new independent metrics. |
| V. Versioning Discipline | ✅ | Artifact hashes stored in `state/projects/PROJ-044‑...yaml`. |
| VI. Heterogeneity‑Aware Evaluation | ✅ | Minority clients are defined **independently of α** as the bottom 30 % of label‑entropy percentile within each partition (see Minority Definition below). |
| VII. Statistical Rigor | ✅ | Paired t‑tests for DP vs non‑DP; LMM with Seed and Client random effects; Bonferroni correction; power discussion included. |

## Minority Definition
Clients are flagged as `is_minority=True` **iff** their empirical label‑entropy falls in the **bottom [deferred]** of the entropy distribution **within the same partition**. This definition is **independent of the Dirichlet concentration α**, ensuring that the minority indicator is not circularly tied to the heterogeneity variable under study.

## Power & Detectable Effect Size
With the mandated **5 seeds** per configuration, a two‑sided paired t‑test has a minimum detectable effect size of roughly **Cohen’s d ≈ 1.1** at α = 0.05. This limitation is explicitly reported in the results discussion; the study is therefore powered to detect only relatively large DP‑induced degradations.

## Early‑Stop / Time‑Budget Logic
After each communication round the orchestrator checks remaining wall‑clock time. If the projected time to complete the remaining seeds exceeds the budget, the number of rounds is capped at a **pre‑computed maximum** (`max_rounds = floor((time_budget - 5 min overhead) / estimated_time_per_round)`). Any run that reaches this cap is marked `is_time_limited=True` **and is excluded from all downstream statistical analyses** (paired t‑tests, LMM, filtering) to avoid bias.

## Computational Strategy

### Hardware & Runtime
- **Primary**: GitHub Actions free‑tier CPU (2 vCPU, ≈ 7 GB RAM). All libraries are CPU‑only.  
- **GPU Escape Hatch**: None required; Opacus runs efficiently on CPU for the modest model size (≈ 30 k parameters).  

### Algorithmic Details
| Component | Method | Key Parameters |
|-----------|--------|----------------|
| **Model** | Tiny CNN (2 Conv layers + 1 FC) | Batch size = 32, learning rate = 0.01 |
| **Federated Optimizer** | FedAvg | Local epochs = 1, communication rounds ≤ 50 (early stop possible) |
| **Differential Privacy** | Opacus `GradSampleModule` + Gaussian noise | Clip norm = 1.0, Noise multiplier derived from target ε (δ = 1e‑5). Moments Accountant tracks cumulative ε. |
| **Non‑DP Baseline** | Same FedAvg without Opacus (ε = "inf") | `is_dp=False`, `epsilon="inf"`. |
| **Early‑Stop / Time‑Budget Logic** | Deterministic round cap based on a conservative estimate of 30 s per round; runs exceeding the budget are truncated and flagged. | |

### Deterministic Seed Handling
- The orchestrator (`T018c`) iterates **exactly 5 seeds** per (α, ε) configuration.  
- If a seed crashes (OOM, timeout), a fresh seed is drawn (incremented integer) and retried **up to 3 attempts** to ensure 5 *successful* runs.  

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
- With 5 paired observations, the minimum detectable effect size at α = 0.05 (two‑sided) is ≈ 1.1 SD (Cohen’s d). This limitation is acknowledged in the discussion; no additional seeds are added to stay within the CPU budget.  

### Multiple‑Comparison Correction
- When testing across **5 ε values** × **3 α values** (15 tests), apply **Bonferroni** (α_adj = 0.05/15 ≈ 0.0033).  

### Utility‑Collapse Filtering (SC‑005)
- Define **random‑guessing threshold** as `1 / N_classes`. FEMNIST comprises a comprehensive set of classes covering digits, uppercase, and lowercase letters. → threshold = 1/62 ≈ 0.01613.  
- Any run with `global_accuracy < 0.01613` is dropped before statistical testing (implemented in `T035`).  

### Reporting
- Produce `results/final_stats.csv` containing p‑values, effect sizes, and confidence intervals.  
- Generate overlay plot `figures/minority_vs_global_overlay.png` and sensitivity curves `figures/sensitivity_alpha.png`.  
- Summarize in `results/summary.csv`, `results/validation_report.md`, and `results/p_values_by_seed.json`.  
- **Schema Validation**: After `results/raw_logs.csv` is written, it is automatically validated against `contracts/results.schema.yaml`.  

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| **CPU Timeout** | Medium – could exceed 6 h | Deterministic early‑stop rule; rounds reduced only after time check; flagged runs excluded from analyses. |
| **Insufficient Seeds** (e.g., a seed fails repeatedly) | High – would break FR‑004 | Orchestrator retries up to 3 times; if still failing, logs warning and proceeds with next seed; final report notes any missing seeds. |
| **Utility Collapse (ε = 0.1)** | Low – may produce near‑random accuracy | Filtering step removes such runs before statistical tests. |
| **Opacus CPU Overhead** | Medium – slows training | Use modest batch size (32) and limit local epochs to 1; profile once on a dry run to calibrate `estimated_time_per_round`. |
| **Shakespeare Request** | Low – spec mentions but data unavailable | Partitioning script raises `ValueError` with prescribed message; verification task T000 ensures only exclusion references appear. |

## Project Structure
```text
specs/001-evaluating-dp-federated-learning/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── dataset.schema.yaml
    └── results.schema.yaml

projects/PROJ-044-evaluating-the-effectiveness-of-differen/
├── data/
│   ├── raw/
│   │   └── femnist.parquet               # streamed download → static parquet
│   └── partitions/
│       └── partition_femnist_{seed}_{alpha}.json
├── code/
│   ├── __init__.py
│   ├── data/
│   │   ├── download.py          # streaming → parquet (materialized)
│   │   └── partition.py         # Dirichlet splitter, entropy calc, minority flag
│   ├── models/
│   │   └── cnn.py               # tiny ConvNet (≈ 30 k params)
│   ├── training/
│   │   ├── fedavg.py            # core FedAvg loop (DP optional)
│   │   └── dp_utils.py          # Opacus wrapper, Moments Accountant
│   ├── analysis/
│   │   ├── stats.py             # paired t‑test, LMM, Bonferroni
│   │   └── plots.py             # overlay plot, sensitivity curves
│   └── main.py                  # CLI entry point (orchestration)
├── results/
│   ├── raw_logs.csv
│   ├── filtered_data.csv
│   ├── filtered_time.csv
│   ├── final_stats.csv
│   ├── summary.csv
│   └── validation_report.md
├── figures/
│   ├── minority_vs_global_overlay.png
│   └── sensitivity_alpha.png
├── tests/
│   ├── unit/
│   │   ├── test_partition.py
│   │   └── test_dp_utils.py
│   └── integration/
│       └── test_training_loop.py
├── requirements.txt
└── README.md
```

## Complexity Tracking & Requirement Mapping
| FR / SC | Description | Plan Phase / Task(s) |
|---------|-------------|----------------------|
| **FR‑001** | Support FEMNIST; reject Shakespeare | `T011` (download), `T012` (partition validation) – raises `ValueError` if dataset=="shakespeare". |
| **FR‑002** | Dirichlet heterogeneity (α = 0.1, 0.5, 1.0) with reproducible seed | `T012` (partition generation). |
| **FR‑003** | DP via Opacus; track ε with Moments Accountant | `T018b` (DP training loop). |
| **FR‑004** | Run experiments across **5 seeds** per config | `T018c` (orchestrator) enforces exactly 5 seeds; retries up to 3 attempts per seed. |
| **FR‑005** | Paired t‑tests DP vs. non‑DP; majority vs. minority tests | `T024a` (paired t‑test), `T024b` (LMM for minority vs. majority). |
| **SC‑001** (Convergence Speed) | *Not a spec Success Criterion; omitted from mapping.* |
| **SC‑002** (Privacy‑Utility Curve) | *Not a spec Success Criterion; omitted from mapping.* |
| **SC‑003** (Minority Degradation) | *Not a spec Success Criterion; omitted from mapping.* |
| **SC‑004** (Statistical Significance) | *Not a spec Success Criterion; omitted from mapping.* |
| **SC‑005** (Utility Collapse Filtering) | *Not a spec Success Criterion; omitted from mapping.* |
| **SC‑006** (Result Summary) | *Not a spec Success Criterion; omitted from mapping.* |

### Detailed Task List (high‑level, implementation‑ready)
| ID | Name | Type | Dependencies | Notes |
|----|------|------|--------------|-------|
| **T011** | Download FEMNIST (stream → parquet) | P | – | Writes `data/raw/femnist.parquet`; computes SHA‑256 checksum; materializes streaming download to a static parquet file. |
| **T012** | Generate Dirichlet partitions | P | T011 | Produces `data/partitions/partition_femnist_{seed}_{alpha}.json`; computes per‑client label entropy; flags `is_minority` based on bottom [deferred] entropy percentile. |
| **T018a** | Common training utilities (model, optimizer, dataset loaders) | P | T012 | Shared code used by DP & non‑DP loops. |
| **T018b** | DP‑enabled FedAvg | P | T018a | Uses Opacus; logs `epsilon` (finite) and `is_dp=True`. |
| **T018d** | Non‑DP FedAvg (baseline) | P | T018a | Logs `epsilon="inf"`, `is_dp=False`. |
| **T018c** | Orchestrator (5‑seed loop) | P | T018b, T018d | For each seed: (i) run T018b, (ii) run T018d on *the same partition*; aggregates logs into `results/raw_logs.csv`. Implements deterministic fallback: after each round, check elapsed time; if `remaining_time < (estimated_time_per_round * remaining_seeds * 2)` → truncate remaining rounds at `max_rounds`, set `is_time_limited=True`. Retries failed seeds up to 3 attempts to guarantee 5 successful logs per config. |
| **T024a** | Paired t‑test DP vs non‑DP (global accuracy) | P | T018c | Requires ≥ 5 paired observations per (α, ε). Applies Bonferroni if > 5 tests. |
| **T024b** | Minority‑vs‑majority degradation test (LMM) | P | T018c | Linear Mixed‑Effects Model: degradation ~ Group + (1|Seed) + (1|Seed:Client) if feasible; otherwise uses robust SEs. |
| **T025** | Convergence detection & round‑count extraction | P | T018c | Determines first round where global accuracy ≥ 0.80; records `rounds_to_80`. Excludes rows where `is_time_limited=True`. |
| **T026** | Plot generation | P | T024a, T024b, T025 | Produces `figures/minority_vs_global_overlay.png` and `figures/sensitivity_alpha.png`. |
| **T035** | Utility‑collapse filtering | P | T018c | Removes rows where `global_accuracy < 0.01613` (random‑guessing threshold for 62 classes). Writes `results/filtered_data.csv`. |
| **T028** | Final result aggregation | P | T024a, T024b, T025, T026, T035 | Writes `results/final_stats.csv`, `results/summary.csv`, `results/validation_report.md`, `results/p_values_by_seed.json`. |
| **T029** | Documentation update (README, QUICKSTART) | P | – | Adds explicit Shakespeare exclusion statement, CLI usage, reproducibility notes, and epsilon‑representation guidance. |
| **T032** | Unit‑test expansion | P | – | Adds tests for (i) missing classes handling, (ii) timeout flagging, (iii) utility‑collapse filter. |
| **T033** | Quickstart verification | P | T028, T029 | Executes `quickstart.md` end‑to‑end on a fresh runner; stores log artifact `quickstart_verification.log`. |

*All tasks marked **P** (production) will generate concrete artifacts that the Implementer Agent must deliver. No task introduces un‑specified constraints; each respects the Constitution and the original FR/SC list.*

---

