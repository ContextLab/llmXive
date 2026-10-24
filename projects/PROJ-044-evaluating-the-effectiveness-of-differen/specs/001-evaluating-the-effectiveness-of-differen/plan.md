# Implementation Plan: Evaluating the Effectiveness of Differential Privacy in Federated Learning

**Branch**: `001-evaluating-dp-federated-learning` | **Date**: 2026-10-24 | **Spec**: `specs/001-evaluating-dp-federated-learning/spec.md`  
**Input**: Feature specification from `/specs/001-evaluating-dp-federated-learning/spec.md`

## Summary
Implement a fully reproducible CPU‑only study that:

1. Streams the open FEMNIST parquet files, writes static parquet files and a matching SHA‑256 checksum.  
2. Generates Dirichlet‑based client partitions for α ∈ {0.1, 0.5, 1.0} with deterministic seeds and the **global** minority‑client definition (bottom quartile of label entropy).  
3. Trains a tiny CNN under FedAvg with optional Opacus‑based Differential Privacy, tracking the privacy budget with the Moments Accountant.  
4. Executes **10 seeds** per (α, ε) configuration, records per‑round and per‑client metrics, and flags collapsed or time‑limited runs (retained for analysis).  
5. Performs paired t‑tests (with Shapiro‑Wilk normality check → Wilcoxon fallback), computes Cohen’s d, fits a **simplified** mixed‑effects model with two‑way interactions (α × ε and α × is_minority) and random intercepts + random slope for ε per seed, and conducts a survival‑analysis for convergence speed.  
6. Generates privacy‑utility curves (accuracy & convergence speed vs. ε) with confidence intervals, and produces a complete `results/summary.csv` containing every field required by the spec.  
7. Includes a **real verification script** (`verify_shakespeare_exclusion.py`) that attempts to invoke the partitioner with `dataset="shakespeare"` and asserts the exact `ValueError`. This satisfies the original T000 requirement without relying on brittle `grep` checks.

All steps are designed to stay within the 6‑hour CPU budget of a GitHub Actions free‑tier runner (≈ 7 GB RAM, 2 vCPU).

## Technical Context

- **Language/Version**: Python 3.11  
- **Primary Dependencies**:  
  - `torch==2.3.0` (CPU wheel)  
  - `opacus==1.4.0`  
  - `datasets==2.19.0`  
  - `pandas==2.2.2`  
  - `numpy==1.26.4`  
  - `scipy==1.13.0`  
  - `statsmodels==0.14.2`  
  - `matplotlib==3.8.4`  
  - `pyarrow==15.0.0` (parquet I/O)  
- **Target Platform**: Linux GitHub Actions free tier (2 vCPU, ≈ 7 GB RAM, ≈ 14 GB disk).  
- **Constraints**: No GPU; streaming download; deterministic seeding; Shakespeare dataset excluded per FR‑001.  
- **Performance Goal**: ≤ 15 communication rounds per run, ≤ 5.5 h total wall‑clock for the full sweep (3 α × 3 ε × 10 seeds = 90 runs).  

## Constitution Check

| Principle | Status | Rationale |
|-----------|--------|-----------|
| I. Reproducibility | ✅ | All random number generators are seeded; dataset URLs are fixed; SHA‑256 checksums recorded; scripts are deterministic. |
| II. Verified Accuracy | ✅ | Only the FEMNIST URLs listed in the “Verified datasets” block are used. |
| III. Data Hygiene | ✅ | Raw parquet files are never mutated; checksums stored; derived files receive new names; no PII. |
| IV. Single Source of Truth | ✅ | `results/raw_logs.csv` is the sole source for downstream analysis; all figures and tables trace back to rows in this file. |
| V. Versioning Discipline | ✅ | Artifact hashes are written to `state/projects/PROJ-044‑…yaml` after each generation step. |
| VI. Heterogeneity‑Aware Evaluation | ✅ | Minority clients are defined globally (bottom quartile of entropy) and flagged consistently across all partitions. |
| VII. Statistical Rigor for Privacy‑Utility Curves | ✅ | Paired tests with normality check → Wilcoxon fallback, mixed‑effects model with two‑way interactions, Bonferroni correction, and explicit power analysis (adjusted for Bonferroni) are all present. |
| **Derived requirement (T000 verification)** | ✅ | A real Python verification script (`verify_shakespeare_exclusion.py`) raises the exact `ValueError` with the mandated message, avoiding brittle `grep`. |
| **Contract Coverage** | ✅/⚠️ | Currently only `dataset.schema.yaml` and `results.schema.yaml` exist; other artifacts will receive schemas in a future iteration (see plan clarification). |

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
    # (future: final_stats.schema.yaml, summary.schema.yaml)

projects/PROJ-044-evaluating-the-effectiveness-of-differen/
├── data/
│   ├── raw/
│   │   ├── femnist_train.parquet
│   │   ├── femnist_test.parquet
│   │   └── femnist.sha256
│   └── partitions/
│       └── partition_femnist_{seed}_{alpha}.json
├── code/
│   ├── __init__.py
│   ├── config.py
│   ├── data/
│   │   ├── download.py          # streaming → parquet, checksum, raises ValueError for Shakespeare
│   │   ├── partition.py         # Dirichlet split, global entropy, minority flag, correlation diagnostic
│   │   └── verify_shakespeare_exclusion.py   # real verification script
│   ├── models/
│   │   └── cnn.py               # tiny ConvNet (~tens‑of‑thousands params)
│   ├── training/
│   │   ├── fedavg.py            # core FedAvg loop (DP optional)
│   │   └── dp_utils.py          # Opacus wrapper, Moments Accountant
│   ├── analysis/
│   │   ├── stats.py             # paired tests, LMM (two‑way interactions), survival analysis
│   │   └── plots.py             # overlay & sensitivity plots
│   └── main.py                  # CLI orchestrator (sweep)
├── results/
│   ├── raw_logs.csv
│   ├── final_stats.csv
│   ├── summary.csv
│   ├── validation_report.md
│   └── p_values_by_seed.json
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

## Requirement Mapping (FR / SC → Tasks)

| FR / SC | Description | Plan Phase / Task(s) |
|---------|-------------|----------------------|
| **FR‑001** | Support FEMNIST; reject Shakespeare with `ValueError` | **T001** (download) – raises `ValueError("Shakespeare excluded per plan.md Gap Analysis")` if `--dataset shakespeare`. |
| **FR‑002** | Dirichlet heterogeneity (α = 0.1, 0.5, 1.0) with reproducible seed | **T002** – deterministic partitions for each seed/α. |
| **FR‑003** | DP via Opacus; track ε with Moments Accountant | **T004** (DP FedAvg) + **T005** (non‑DP baseline). |
| **FR‑004** | Run experiments across **10 seeds** per (α, ε) configuration | **T006** – orchestrator loops over seeds, α, ε. |
| **FR‑005** | Paired t‑tests, Wilcoxon fallback, mixed‑effects model with interactions | **T008** (paired tests) + **T008b** (mixed‑effects, two‑way interactions). |
| **FR‑006** | Global minority‑client definition (bottom quartile) | **T002** – computes global entropy once, flags `is_minority`. Added correlation diagnostic (see plan). |
| **FR‑007** | Flag collapsed (`global_accuracy < 1/62`) and time‑limited runs; retain them, and perform survival‑analysis sensitivity | **T006** – adds `is_collapsed` and `is_time_limited`; **T009c** now uses survival analysis. |
| **FR‑008** | Convergence speed measured as rounds to [deferred] of baseline, with censoring | **T009a** – records `rounds_to_80`; censored runs flagged via `is_time_limited`. |
| **FR‑009** | Power analysis before sweep; document detectable d | **T006** – performs Bonferroni‑adjusted power calculation (detectable d≈moderate level for 10 seeds) and writes to `summary.csv`. |
| **FR‑010** | Privacy‑utility curves (accuracy & convergence vs. ε) with CIs | **T009b** – generates the two figures. |
| **FR‑011** | Result summary table with all required fields | **T009c** – writes `results/summary.csv`. |
| **SC‑001** | Partition reproducibility (byte‑identical SHA‑256) | **T002** – writes SHA‑256 of each JSON partition; verification step in **V002**. |
| **SC‑002** | Excluded‑dataset handling unit test | **V002** – runs the verification script and asserts `ValueError`. |
| **SC‑003** | Privacy‑budget tracking within ±0.05 for ≥95 % runs | **T004/T005** log `actual_epsilon`; **T008** validates tolerance and logs failures. |
| **SC‑004** | Convergence speed measurement per run | **T009a** records `rounds_to_80` and `converged`. |
| **SC‑005** | Report paired t‑test & Wilcoxon p‑values + Cohen’s d | **T008** writes these to `final_stats.csv`. |
| **SC‑006** | Mixed‑effects interaction term significance | **T008b** reports α × ε and α × is_minority coefficients, 95 % CI, Bonferroni‑adjusted p‑value. |
| **SC‑007** | Minority‑vs‑majority accuracy gap with effect size | **T008b** includes `minority_accuracy`, `majority_accuracy`, and effect‑size columns. |
| **SC‑008** | Privacy‑utility curves with CIs | **T009b** creates the two plots. |
| **SC‑009** | Include collapsed/time‑limited runs; report sensitivity analysis excluding them | **T006** retains flagged runs; **T009c** conducts survival‑analysis sensitivity and also reports a table excluding censored runs. |
| **SC‑010** | `results/summary.csv` contains all FR‑011 fields | **T009c** writes the full table. |
| **SC‑011** | Document minimum detectable effect size for the achieved seed count | **T006** writes the power analysis result into `summary.csv` metadata. |

## Detailed Task List

| ID | Name | Type | Dependencies | Notes |
|----|------|------|--------------|-------|
| **T001** | Download FEMNIST (stream → parquet) | P | – | Streams `train` and `test` splits via `datasets.load_dataset(..., streaming=True)`, writes static parquet files, computes SHA‑256 over concatenated bytes, writes `data/raw/femnist.sha256`. Raises `ValueError("Shakespeare excluded per plan.md Gap Analysis")` if `--dataset shakespeare`. |
| **V002** | Shakespeare exclusion verification (real check) | V | – | Executes `python -m code.data.verify_shakespeare_exclusion` and asserts that a `ValueError` with the exact exclusion message is raised. Satisfies the original T000 requirement without using `grep`. |
| **T002** | Dirichlet client partitioning | P | T001 | Computes **global** label‑entropy on the **full** training set once; flags the **bottom [deferred]** as `is_minority`. For each `seed` ∈ {42,…,51} and `alpha` ∈ {0.1,0.5,1.0}, samples a client‑label probability matrix `p_i ∼ Dirichlet(alpha)`, assigns examples, stores metadata in `data/partitions/partition_femnist_{seed}_{alpha}.json`. Writes SHA‑256 of each JSON file for reproducibility (SC‑001). Adds a correlation diagnostic (Pearson r between client entropy and α) and logs the value. |
| **T003** | Shared training utilities (model, data loader) | P | T002 | Tiny CNN (2 Conv + 1 FC), normalizes images, provides per‑client `DataLoader`s. |
| **T004** | DP‑enabled FedAvg | P | T003 | Wraps model with `opacus.PrivacyEngine`, Gaussian noise, Clip norm = 1.0, noise multiplier derived from target ε (δ = 1e‑5). Tracks cumulative ε via the Moments Accountant. |
| **T005** | Non‑DP FedAvg baseline | P | T003 | Same loop without Opacus; logs `epsilon="inf"` and `is_dp=False`. |
| **T006** | Orchestrator (sweep) | P | T004, T005 | Loops over seeds (10), α, ε (0.1, 1.0, inf). Runs DP then non‑DP on the **same** partition. Records per‑round metrics to `results/raw_logs.csv`. Implements deterministic early‑stop: after each round estimates remaining wall‑clock time (≈ 15 s/round). If projected total exceeds the 6 h budget, caps remaining rounds (`max_rounds=15`). Runs that hit the cap are flagged `is_time_limited=True` and **retained**. Matched‑round evaluation: DP vs. non‑DP are compared at the minimum number of completed rounds between the pair. |
| **T008** | Paired statistical tests (global accuracy) | P | T006 | For each (α, ε) pair, compute the paired difference in **global accuracy** between DP and non‑DP runs across the 10 seeds (same partition). Perform a Shapiro‑Wilk normality test on the differences. If normal (p > 0.05): run a two‑sided paired t‑test; otherwise run a **Wilcoxon signed‑rank test**. Apply **Bonferroni correction** across the Several (α, ε) tests (α_adj ≈ 0.0056). Report raw and adjusted p‑values, effect size (Cohen’s d for t‑test, rank‑biserial for Wilcoxon), and a significance flag. Write to `results/final_stats.csv`. |
| **T008b** | Mixed‑effects model (minority vs. majority) | P | T006 | Fits `statsmodels.MixedLM` with formula `degradation ~ is_minority * alpha + epsilon + (1 + epsilon | seed)`. This includes the two‑way interaction `is_minority:alpha` and a random intercept plus random slope for ε per seed. Reports coefficient for `is_minority:alpha`, 95 % CI, and Bonferroni‑adjusted p‑value. Also extracts the α × ε interaction term. Results appended to `final_stats.csv`. |
| **T009a** | Convergence detection | P | T006 | Computes `rounds_to_80` = first round where `global_accuracy ≥ 0.80`. If never reached, records the final round and sets `converged=False`. Adds column `matched_rounds` (minimum rounds completed between DP and baseline) for fair comparison. |
| **T009b** | Plot generation | P | T008, T008b, T009a | Produces: <br>• `figures/minority_vs_global_overlay.png` – minority vs. global accuracy curves with 95 % CIs per ε. <br>• `figures/sensitivity_alpha.png` – privacy‑utility curves (accuracy & convergence speed vs. ε) for each α. |
| **T009c** | Final aggregation & validation report | P | T008, T008b, T009a, T009b | Writes: <br>• `results/summary.csv` containing, per (α, ε): mean/std final accuracy, mean degradation, paired test results, interaction estimates, counts of collapsed and time‑limited runs, power‑analysis metadata, and the minority‑vs‑majority gap. <br>• `results/validation_report.md` (checksum verification, seed completeness, minority‑definition correlation diagnostic, confirmation of Shakespeare‑exclusion verification, list of any flagged runs). <br>• `results/p_values_by_seed.json` (raw p‑values per seed for auditability). |
| **T010** | Documentation (README & QUICKSTART) | P | – | Updates `quickstart.md` and `README.md` with seed count, early‑stop behavior, and verification script description. |
| **T011** | Unit‑test suite | P | – | Adds tests for partition reproducibility (`test_partition.py`), DP wrapper correctness (`test_dp_utils.py`), and end‑to‑end training loop (`test_training_loop.py`). |
| **T012** | Quickstart verification | P | T009c, T010 | Executes the QUICKSTART script on a fresh runner; stores log `quickstart_verification.log`. |

All tasks produce concrete files that are validated against the JSON‑Schema contracts in `contracts/` **where schemas exist**. Future work will add schemas for `final_stats.csv`, `summary.csv`, and `validation_report.md`.

---

