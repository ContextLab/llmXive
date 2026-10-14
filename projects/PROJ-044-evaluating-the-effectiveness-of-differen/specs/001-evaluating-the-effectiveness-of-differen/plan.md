# Implementation Plan: Evaluating the Effectiveness of Differential Privacy in Federated Learning

**Branch**: `001-evaluating-dp-federated-learning` | **Date**: 2026-10-14 | **Spec**: `specs/001-evaluating-dp-federated-learning/spec.md`  
**Input**: Feature specification from `/specs/001-evaluating-dp-federated-learning/spec.md`

## Summary
Implement a reproducible CPU‑only study that (1) streams the open FEMNIST parquet dataset, (2) creates Dirichlet‑based client partitions for α ∈ {0.1, 0.5, 1.0} with deterministic seeds, (3) trains a tiny CNN with FedAvg both with Opacus‑based Differential Privacy (Gaussian noise, Moments Accountant) and without DP (ε = ∞), (4) records per‑round and per‑client metrics for **5 seeds** per configuration, (5) filters out utility‑collapse runs, and (6) carries out the paired t‑tests and minority‑vs‑majority mixed‑effects analysis required by FR‑005 and Principle VII.

All steps are designed to complete within the 6‑hour CPU budget of a GitHub Actions free‑tier runner.

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
- **Performance Goal**: ≤ 6 h wall‑clock for the full sweep (5 seeds × 3 α × 5 ε).  

## Constitution Check
| Principle | Status | Rationale |
|-----------|--------|-----------|
| I. Reproducibility | ✅ | All random generators are explicitly seeded; dataset URL is fixed; checksum recorded. |
| II. Verified Accuracy | ✅ | Only the FEMNIST URLs listed in the “Verified datasets” block are used. |
| III. Data Hygiene | ✅ | Raw parquet is never mutated; SHA‑256 stored; every derived file has a new name. |
| IV. Single Source of Truth | ✅ | `results/raw_logs.csv` is the sole source for all downstream analyses. |
| V. Versioning Discipline | ✅ | Artifact hashes are recorded in `state/projects/PROJ-044‑…yaml`. |
| VI. Heterogeneity‑Aware Evaluation | ✅ | Minority clients are defined by the bottom 30 % of label‑entropy *within each partition*, independent of α. |
| VII. Statistical Rigor | ✅ | Paired t‑tests, mixed‑effects model, Bonferroni correction, and power discussion are all present. |

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
│   │   └── femnist.parquet
│   └── partitions/
│       └── partition_femnist_{seed}_{alpha}.json
├── code/
│   ├── __init__.py
│   ├── config.py
│   ├── data/
│   │   ├── download.py          # streaming → parquet, checksum
│   │   └── partition.py         # Dirichlet split, entropy, minority flag
│   ├── models/
│   │   └── cnn.py               # ~30 k‑parameter tiny ConvNet
│   ├── training/
│   │   ├── fedavg.py            # core FedAvg loop (DP optional)
│   │   └── dp_utils.py          # Opacus wrapper, Moments Accountant
│   ├── analysis/
│   │   ├── stats.py             # paired t‑test, LMM, Bonferroni
│   │   └── plots.py             # overlay & sensitivity curves
│   └── main.py                  # orchestrator (T018c)
├── results/
│   ├── raw_logs.csv
│   ├── filtered_data.csv
│   ├── filtered_time.csv
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
| **FR‑001** | Support FEMNIST; reject Shakespeare with `ValueError` | `T011` (download), `T012` (partition validation) – code raises `ValueError("Shakespeare excluded per plan.md Gap Analysis")` if dataset argument is `"shakespeare"`. |
| **FR‑002** | Dirichlet heterogeneity (α = 0.1, 0.5, 1.0) with reproducible seed | `T012` – generates partitions for each seed/α. |
| **FR‑003** | DP via Opacus; track ε with Moments Accountant | `T018b` (DP FedAvg) + `T018a` (common utilities). |
| **FR‑004** | Run experiments across **5 seeds** per config | `T018c` – orchestrator loops over seeds, retries up to 3 times per seed. |
| **FR‑005** | Paired t‑tests DP vs. non‑DP; majority vs. minority tests | `T024a` (paired t‑test), `T024b` (LMM for minority vs. majority). |
| **SC‑I** (implicit) | Convergence speed measurement | `T025` records `rounds_to_80` (first round achieving ≥ 0.80 global accuracy). |
| **SC‑II** (implicit) | Privacy‑utility curves | `T018c` logs `global_accuracy` vs. ε; `T026` plots curves. |
| **SC‑III** (implicit) | Minority‑client degradation | `T024b` directly tests this. |
| **SC‑IV** (implicit) | Statistical significance (p < 0.05) | All tests report Bonferroni‑adjusted p‑values; significance flag in `final_stats.csv`. |
| **SC‑V** (implicit) | Utility‑collapse filtering | `T035` removes rows with `global_accuracy < 1/62 ≈ 0.01613`. |
| **SC‑VI** (implicit) | Result summary tables | `T028` aggregates into `summary.csv` and `final_stats.csv`. |

## Detailed Task List (high‑level, production‑ready)

| ID | Name | Type | Dependencies | Notes |
|----|------|------|--------------|-------|
| **T011** | Download FEMNIST (stream → parquet) | P | – | Streams via `datasets.load_dataset(..., streaming=True)`, writes `data/raw/femnist.parquet`, computes SHA‑256 `data/raw/femnist.sha256`. |
| **T012** | Dirichlet client partitioning | P | T011 | For each `seed` ∈ {42,43,44,45,46} and `alpha` ∈ {0.1,0.5,1.0}, samples a client‑label probability matrix from `Dirichlet(alpha)`, assigns examples, computes per‑client label entropy, flags bottom 30 % as `is_minority`. Writes JSON to `data/partitions/partition_femnist_{seed}_{alpha}.json`. |
| **T018a** | Shared training utilities (model, data loader) | P | T012 | Builds tiny CNN, normalizes images, provides PyTorch `DataLoader`s for each client. |
| **T018b** | DP‑enabled FedAvg | P | T018a | Wraps model with `opacus.PrivacyEngine`, uses Gaussian noise, tracks cumulative ε via Moments Accountant. |
| **T018d** | Non‑DP FedAvg baseline | P | T018a | Same loop without Opacus; logs `epsilon="inf"`. |
| **T018c** | Orchestrator (sweep) | P | T018b, T018d | Loops over seeds, α, ε; runs DP then non‑DP on the *same* partition; records per‑round metrics to `results/raw_logs.csv`. Implements deterministic early‑stop: after each round checks remaining wall‑clock time (estimated 30 s/round) and caps rounds (`max_rounds`). Retries failed seeds up to 3 times; missing seeds are logged in `validation_report.md`. |
| **T025** | Convergence detection | P | T018c | Computes `rounds_to_80` (first round where `global_accuracy ≥ 0.80`) and writes to `results/filtered_time.csv`. Excludes rows with `is_time_limited=True`. |
| **T035** | Utility‑collapse filter | P | T018c | Drops any run with `global_accuracy < 1/62 ≈ 0.01613`; writes `results/filtered_data.csv`. |
| **T024a** | Paired t‑test (global accuracy) | P | T035 | For each (α, ε) computes paired differences across the 5 seeds; applies two‑sided paired t‑test; Bonferroni‑adjusts across all 15 tests. Writes `final_stats.csv` entries with `test_name="paired_t_test"`. |
| **T024b** | Minority‑vs‑majority mixed‑effects analysis | P | T035 | Fits `statsmodels.MixedLM` with `degradation ~ is_minority + (1|seed) + (1|seed:client)` (if CPU budget permits; otherwise uses robust SEs). Writes LMM coefficient entry to `final_stats.csv` (`test_name="lmm_minor_vs_major"`). |
| **T026** | Plot generation | P | T024a, T024b, T025 | Produces `figures/minority_vs_global_overlay.png` (minority vs. global accuracy curves) and `figures/sensitivity_alpha.png` (accuracy vs. ε for each α). |
| **T028** | Final aggregation & validation report | P | T024a, T024b, T025, T026, T035 | Writes `results/summary.csv`, `results/validation_report.md`, and `results/p_values_by_seed.json`. |
| **T029** | Documentation (README & QUICKSTART) | P | – | Updates `quickstart.md` (this file) and `README.md` with reproducibility checklist. |
| **T032** | Unit‑test suite | P | – | Adds tests for partition reproducibility, DP wrapper correctness, and filter logic. |
| **T033** | Quickstart verification | P | T028, T029 | Executes the QUICKSTART script on a fresh runner; stores log `quickstart_verification.log`. |

All tasks produce concrete files that are validated against the JSON‑Schema contracts in `contracts/`.

---
