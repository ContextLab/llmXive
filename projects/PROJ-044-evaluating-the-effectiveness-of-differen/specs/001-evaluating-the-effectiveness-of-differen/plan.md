# Implementation Plan: Evaluating the Effectiveness of Differential Privacy in Federated Learning

**Branch**: `001-evaluating-dp-federated-learning` | **Date**: 2026-10-20 | **Spec**: `specs/001-evaluating-dp-federated-learning/spec.md`  
**Input**: Feature specification from `/specs/001-evaluating-dp-federated-learning/spec.md`

## Summary
Implement a fully reproducible CPU‑only study that:

1. Streams the **open FEMNIST** parquet files from verified Hugging‑Face URLs, writes static parquet files and a matching SHA‑256 checksum (Task **T001**).  
2. Generates Dirichlet‑based client partitions for α ∈ {0.1, 0.5, 1.0} with deterministic seeds (Task **T002**).  
3. Trains a tiny CNN using FedAvg with optional Opacus‑based Differential Privacy (Tasks **T003**‑**T005**).  
4. Records per‑round and per‑client metrics for **10 seeds** per configuration (Task **T006**).  
5. Performs paired statistical tests (t‑test with normality check, Wilcoxon fallback) and a mixed‑effects analysis that includes an `is_minority:alpha` interaction and random slopes for ε and α (Task **T008b**).  
6. Generates overlay and sensitivity plots (Task **T009b**).  
7. Produces a validation report that (a) confirms the FEMNIST checksum, (b) verifies that the only occurrence of “Shakespeare” is inside the mandated exclusion message via a real verification script (`verify_shakespeare_exclusion.py`), meeting the self‑referential T000 requirement without a non‑real‑call grep test.

All steps are designed to finish within the 6‑hour CPU budget of a GitHub Actions free‑tier runner by limiting each run to a maximum of **15 communication rounds** (≈ 15 s per round), resulting in an estimated total wall‑clock time of ~5.6 h for the full sweep (3 α × 3 ε × 10 seeds = 90 runs).  

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
- **Performance Goal**: ≤ 15 rounds per run, ≤ 5.5 h total wall‑clock.

## Constitution Check

| Principle | Status | Rationale |
|-----------|--------|-----------|
| I. Reproducibility | ✅ | All random generators are explicitly seeded; dataset URL is fixed; checksum recorded; scripts are deterministic. |
| II. Verified Accuracy | ✅ | Only the FEMNIST URLs listed in the “Verified datasets” block are used. |
| III. Data Hygiene | ✅ | Raw parquet is never mutated; SHA‑256 stored; derived files receive new names; no PII. |
| IV. Single Source of Truth | ✅ | `results/raw_logs.csv` is the sole source for all downstream analysis. |
| V. Versioning Discipline | ✅ | Artifact hashes are written to `state/projects/PROJ-044‑…yaml`. |
| VI. Heterogeneity‑Aware Evaluation | ✅ | Minority clients are defined as the global bottom [deferred] of label‑entropy (computed once on the full training set) and flagged consistently across partitions. |
| VII. Statistical Rigor | ✅ | Paired tests with normality check (Wilcoxon fallback), mixed‑effects model with `is_minority:alpha` interaction, random slopes for ε and α, Bonferroni correction, and explicit power discussion are all present. |
| V (Principle V) | ✅ | Real verification script `verify_shakespeare_exclusion.py` checks exclusion; no non‑real‑call tests remain. |

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
│   │   └── partition.py         # Dirichlet split, global entropy, minority flag
│   ├── models/
│   │   └── cnn.py               # ~tens‑of‑thousands‑parameter tiny ConvNet
│   ├── training/
│   │   ├── fedavg.py            # core FedAvg loop (DP optional)
│   │   └── dp_utils.py          # Opacus wrapper, Moments Accountant
│   ├── analysis/
│   │   ├── stats.py             # paired tests, LMM with interaction, Bonferroni
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
| **FR‑001** | Support FEMNIST; reject Shakespeare with `ValueError` | **T001** (download) – `download.py` raises `ValueError("Shakespeare excluded per plan.md Gap Analysis")` if `--dataset shakespeare` is supplied. |
| **FR‑002** | Dirichlet heterogeneity (α = 0.1, 0.5, 1.0) with reproducible seed | **T002** – generates partitions for each seed/α. |
| **FR‑003** | DP via Opacus; track ε with Moments Accountant | **T003** (DP‑enabled FedAvg) + **T004** (non‑DP baseline). |
| **FR‑004** | Run experiments across **10 seeds** per config to ensure statistical power | **T006** – orchestrator loops over seeds, retries up to 3 times per seed. |
| **FR‑005** | Paired t‑tests DP vs. non‑DP; minority vs. majority tests | **T008** (paired tests + Wilcoxon fallback) and **T008b** (mixed‑effects with `is_minority:alpha` interaction, random slopes for ε and α). |
| **SC‑I** | *Removed – not in spec* |
| **SC‑II** | *Removed – not in spec* |
| **SC‑III** | *Removed – not in spec* |
| **SC‑IV** | *Removed – not in spec* |
| **SC‑V** | *Removed – not in spec* |
| **SC‑VI** | *Removed – not in spec* |

## Detailed Task List

| ID | Name | Type | Dependencies | Notes |
|----|------|------|--------------|-------|
| **T001** | Download FEMNIST (stream → parquet) | P | – | Streams `train` and `test` splits via `datasets.load_dataset(..., streaming=True)`, writes static parquet files, computes a SHA‑256 checksum over the concatenated bytes of both files, writes `data/raw/femnist.sha256`. Supplying `--dataset shakespeare` raises the required `ValueError("Shakespeare excluded per plan.md Gap Analysis")`. |
| **V002** | Shakespeare exclusion verification (real check) | V | – | Executes `python -c "import code.data.partition as p; p.run_partition(dataset='shakespeare')"` and asserts that a `ValueError` with the exact exclusion message is raised. This satisfies T000 without a non‑real‑call grep. |
| **T002** | Dirichlet client partitioning | P | T001 | Computes **global** label‑entropy on the full training set once, flags the bottom [deferred] of clients as `is_minority=True`. For each `seed` ∈ {42,…,51} and `alpha` ∈ {0.1,0.5,1.0}, samples a client‑label probability matrix `p_i ∼ Dirichlet(α)`, assigns examples, stores metadata in `data/partitions/partition_femnist_{seed}_{alpha}.json`. |
| **T003** | Shared training utilities (model, data loader) | P | T002 | Builds tiny CNN, normalizes images, provides PyTorch `DataLoader`s for each client. |
| **T004** | DP‑enabled FedAvg | P | T003 | Wraps model with `opacus.PrivacyEngine`, uses Gaussian noise, tracks cumulative ε via Moments Accountant. |
| **T005** | Non‑DP FedAvg baseline | P | T003 | Same loop without Opacus; logs `epsilon="inf"` and `is_dp=False`. |
| **T006** | Orchestrator (sweep) | P | T004, T005 | Loops over seeds (10), α, ε (0.1, 1.0, inf); runs DP then non‑DP on the **same** partition; records per‑round metrics to `results/raw_logs.csv`. Implements deterministic early‑stop: after each round estimates remaining wall‑clock time (≈ 15 s/round) and caps remaining rounds (`max_rounds=15`). Retries failed seeds up to 3 attempts; persistent failures are logged, and the missing seed is noted in `validation_report.md`. All runs, including time‑limited and utility‑collapse ones, are retained with appropriate flags. |
| **T008** | Paired tests (global accuracy) | P | T006 | For each (α, ε) pair, compute the paired difference in **global accuracy** between DP and non‑DP runs **across the 10 seeds** (same partition). Perform a **Shapiro‑Wilk normality test** on the differences. If normal (p > 0.05): run a two‑sided paired t‑test; otherwise run a **Wilcoxon signed‑rank test**. Apply **Bonferroni correction** across the 9 tests (α_adj ≈ 0.0056). Report raw and adjusted p‑values, effect size (Cohen’s d for t‑test, rank‑biserial for Wilcoxon), and a significance flag (`p_adj < 0.05`). |
| **T008b** | Minority‑vs‑majority mixed‑effects analysis | P | T006 | Fits `statsmodels.MixedLM` with formula `degradation ~ is_minority * alpha + epsilon + is_time_limited + utility_collapse + (1 + epsilon + alpha | seed)`. Reports coefficient for the interaction `is_minority:alpha`, 95 % CI, and Bonferroni‑adjusted p‑value. |
| **T009a** | Convergence detection | P | T006 | Computes `rounds_to_80` (first round where `global_accuracy ≥ 0.80`) and adds column to `results/raw_logs.csv`. |
| **T009b** | Plot generation | P | T008, T008b, T009a | Produces `figures/minority_vs_global_overlay.png` (minority vs. global accuracy curves) and `figures/sensitivity_alpha.png` (accuracy vs. ε for each α). |
| **T009c** | Final aggregation & validation report | P | T008, T008b, T009a, T009b | Writes `results/summary.csv`, `results/validation_report.md`, and `results/p_values_by_seed.json`. The validation report includes: checksum verification, seed completeness, and confirmation of Shakespeare‑exclusion verification (via V002). |
| **T010** | Documentation (README & QUICKSTART) | P | – | Updates `quickstart.md` and `README.md` with the new seed count, early‑stop behavior, and verification script description. |
| **T011** | Unit‑test suite | P | – | Adds tests for partition reproducibility, DP wrapper correctness, and flag handling. |
| **T012** | Quickstart verification | P | T009c, T010 | Executes the QUICKSTART script on a fresh runner; stores log `quickstart_verification.log`. |

All tasks produce concrete files that are validated against the JSON‑Schema contracts in `contracts/`.

---



