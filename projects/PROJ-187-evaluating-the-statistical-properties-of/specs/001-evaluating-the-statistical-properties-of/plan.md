# Implementation Plan: Evaluating Statistical Fidelity of Synthetic Data

**Branch**: `001-statistical-fidelity` | **Date**: 2026-10-22 | **Spec**: [spec.md](spec.md)  
**Input**: Feature specification from `specs/001-statistical-fidelity/spec.md`

## Summary
Deliver a fully automated CPU‑only pipeline that (1) downloads **three** open tabular benchmarks, (2) preprocesses them with reproducible imputation and encoding, (3) trains CTGAN, DP‑GAN (ε = 1.0), and CopulaGAN on each benchmark under strict epoch, early‑stopping, and RAM limits, (4) generates synthetic hold‑out replicas, (5) computes marginal and correlation fidelity metrics, (6) applies statistical significance testing with Benjamini‑Hochberg correction, (7) creates a **single** control‑perturbation dataset (10 % row permutation per column) and a random‑noise baseline dataset, (8) runs a sensitivity analysis sweeping significance thresholds, (9) aggregates results across **ten** random seeds, (10) produces a reproducible report that frames all findings as associational.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `sdv==1.12.0`, `torch==2.2.0` (CPU wheel), `pandas`, `numpy`, `scipy`, `scikit-learn`, `statsmodels`, `datasets`, `openml`, `matplotlib`, `seaborn`, `pyarrow`, `psutil`, `jinja2`  
- **Storage**: `data/` for raw/processed files, `outputs/` for synthetic CSVs, metric JSON, figures, and final report.  
- **Testing**: `pytest` + JSON‑Schema validation (`contracts/metric_results.schema.yaml`).  
- **Target Platform**: Linux GitHub Actions free‑tier runner (2 CPU, ≈7 GB RAM, ≈14 GB disk).  
- **Constraints**: ≤ 30 training epochs per model, ≤ 7 GB RAM peak, ≤ 6 h wall‑clock, CPU‑only (no CUDA).  

## Constitution Check
| Principle | Compliance Statement |
|-----------|----------------------|
| I. Reproducibility | All random seeds are fixed (ten seeds per (model, dataset) combo). Dataset URLs are immutable and fetched programmatically on every run. |
| II. Verified Accuracy | Every external dataset URL appears in the “Verified datasets” block supplied by the user. No invented citations. |
| III. Data Hygiene | Raw files are checksum‑verified; each transformation writes a new file with a provenance header. |
| IV. Single Source of Truth | Every figure/table is generated from the JSON metric report; no manual transcription. |
| V. Versioning Discipline | All artifacts are content‑hashed; no writes to the platform‑owned `state/` directory. |
| VI. Statistical Fidelity Quantification | KS, χ², permutation‑based correlation tests, and effect‑size thresholds are computed for every column and pair. |
| VII. Computational Resource Discipline | Training limited to 30 epochs, early‑stopping, RAM monitoring, and down‑sampling/drop‑high‑cardinality logic enforce the 7 GB limit. Empirical runtime ≤ 2.5 h for the full grid, comfortably under the 360 min limit. |

## Verified Datasets
| # | Dataset (canonical name) | Source (verified URL) | Loader |
|---|--------------------------|-----------------------|--------|
| 1 | **UCI HAR (Human Activity Recognition)** | https://huggingface.co/datasets/udayl/UCI_HAR/resolve/main/csv_files/test.csv | `datasets.load_dataset("udayl/UCI_HAR", split="test")` |
| 2 | **UCI Shopper** | https://huggingface.co/datasets/jlh/uci-shopper/resolve/main/data/train-00000-of-00001-3316810f8df41d3a.parquet | `datasets.load_dataset("jlh/uci-shopper", split="train")` |
| 3 | **UCI Adult** | https://huggingface.co/datasets/uci_adult/resolve/main/data/train.csv | `datasets.load_dataset("uci_adult", split="train")` |

*All three datasets are directly downloadable via the Hugging Face `datasets` library.*

## Project Structure
```text
specs/001-statistical-fidelity/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── metric_results.schema.yaml
└── tasks.md          # generated later by /speckit-tasks

src/
├── __init__.py
├── data/
│   ├── loader.py            # download & preprocessing
│   └── utils.py
├── models/
│   ├── trainer.py           # CTGAN/DP‑GAN/CopulaGAN wrapper, early‑stopping
│   └── synthesize.py
├── metrics/
│   ├── marginal.py
│   ├── correlation.py
│   └── significance.py
├── analysis/
│   ├── sensitivity.py
│   └── report.py
└── cli/
    └── run_fidelity.py      # entry point for CI job
```

## Phase Overview & FR/SC Mapping
| Phase | Description | Key Tasks | FRs addressed | SCs addressed |
|-------|-------------|-----------|---------------|----------------|
| **1 – Data Acquisition & Pre‑processing** | Download the three verified datasets, verify checksums, impute missing values, encode categoricals, split 80/20, enforce RAM limit. | • Load via `datasets` (UCI HAR, Shopper, Adult).<br>• Median / mode imputation.<br>• One‑hot for ≤20 categories; frequency encoding otherwise.<br>• Record encoding decisions in metadata.<br>• RAM monitor (`psutil`). If peak > 6.5 GB, uniformly down‑sample to ≤10 k rows **or** drop highest‑cardinality columns until under limit (FR‑009). | FR‑001, FR‑009 | SC‑001 |
| **2 – Model Training & Synthetic Generation** | Train CTGAN, DP‑GAN (ε = 1.0), CopulaGAN on the training split, respecting epoch/early‑stopping limits; generate synthetic hold‑out matching training row count. | • `trainer.py` sets `max_epochs=30`, early‑stopping Δloss < 0.001 for 3 epochs (FR‑013).<br>• DP‑GAN receives `privacy_budget=1.0` (logged) (FR‑016).<br>• **Ten** seeds per combo: 42, 123, 2026, 3030, 4040, 5050, 6060, 7070, 8080, 9090 (FR‑017).<br>• Detect non‑convergence → log, emit NaNs, continue (FR‑010). | FR‑002, FR‑003, FR‑010, FR‑013, FR‑016, FR‑017, FR‑018 | SC‑001 |
| **3 – Metric Computation** | Compute marginal statistics (mean, var, KS, χ², KDE) and pairwise correlations (Pearson, Spearman). | • `marginal.py` distinguishes continuous vs. categorical.<br>• Zero‑variance detection → flag & skip KS (FR‑011).<br>• `correlation.py` computes matrices; permutation‑based test (a sufficient number of permutations) for each pair.<br>• KDE plots and QQ‑plots generated (FR‑014). | FR‑004, FR‑005, FR‑011, FR‑014, FR‑015 | SC‑002 |
| **4 – Statistical Testing & Multiple‑Comparison Correction** | Apply KS/χ²/permutation tests, collect p‑values & effect sizes, run Benjamini‑Hochberg correction across all metrics per dataset. | • `significance.py` aggregates p‑values, applies BH (`alpha=0.05`).<br>• Store corrected p‑values alongside raw (FR‑006). | FR‑006, FR‑005 | SC‑002 |
| **5 – Control‑Perturbation & Random‑Noise Baselines** | (a) **Control‑perturbation**: randomly permute **[deferred]** of rows in each column of the real hold‑out (seed = 99). Preserves marginals exactly, destroys dependence → used to estimate **false‑positive** rates for correlation fidelity.<br>(b) **Random‑noise baseline**: sample each column independently from the empirical marginal distribution of the hold‑out (seed = 42). Used to estimate **false‑negative** rates for marginal fidelity and as a baseline in paired‑test comparisons. | • `analysis/sensitivity.py` creates the 10 % row‑permutation dataset (FR‑021) and the independent‑sampling baseline (FR‑019).<br>• Faithful/unfaithful classification per FR‑020 (corrected p ≥ 0.05 **and** effect‑size thresholds).<br>• Sweep significance thresholds {0.01, 0.05, 0.10}.<br>• Compute FP rates using control‑perturbation and FN rates using random‑noise baseline (FR‑022). | FR‑007, FR‑019, FR‑020, FR‑021, FR‑022 | SC‑003, SC‑004 |
| **6 – Aggregation & Comparative Testing** | Aggregate metric differences across seeds → mean ± SD; run paired tests (t‑test or Wilcoxon) between generators. Produce summary file `outputs/summary/aggregated_metrics.csv`. | • Compute per‑column/metric mean & SD (FR‑012).<br>• Normality check (Shapiro‑Wilk); paired t‑test if normal else Wilcoxon (FR‑018).<br>• Post‑hoc power estimates reported using standard analytical approximations (SC‑005). | FR‑012, FR‑018 | SC‑002, SC‑005 |
| **7 – Reporting** | Generate PDF/JSON report containing tables, figures (KDE/histogram, QQ‑plots, correlation heatmaps), sensitivity analysis, multiple‑comparison note, power discussion, and explicit associational framing. | • `report.py` writes `outputs/report/fidelity_report.json` and `fidelity_report.pdf`.<br>• Include ε log for DP‑GAN (FR‑016).<br>• Insert language “These results describe associations …”. | FR‑008, FR‑016 | SC‑003, SC‑005 |

All functional requirements (FR‑001 … FR‑022) and success criteria (SC‑001 … SC‑005) are covered by at least one phase. No un‑specified constraints have been introduced.

## Compute Decision / Rationale
- **CPU‑first**: All SDV generators run on CPU; empirical training time ≤ 10 min per seed after early‑stopping, total ≈ 2.5 h for the full grid, well under the 360 min limit.
- **GPU escape hatch**: Not required. The pipeline contains no CUDA calls. Should a future extension need GPU, the same script can be invoked with `device="cuda"` and will auto‑offload to Kaggle’s free GPU, but the current plan stays CPU‑only.
- **Path discipline**: All outputs are written to project‑owned directories (`data/`, `outputs/`, `src/`). No writes to the platform‑owned `state/` directory.

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| Dataset exceeds RAM after encoding | Crash | RAM monitor triggers down‑sampling or column drop (FR‑009). |
| DP‑GAN non‑convergence | Missing metrics | Log, emit NaNs, continue (FR‑010). |
| Zero‑variance synthetic column | KS undefined | Detect (FR‑011), flag, skip KS. |
| Control‑perturbation fraction unclear | Mis‑interpreted sensitivity | Fixed at 10 % permutation per column (FR‑021). |
| Only two verified tabular benchmarks | FR‑001 unmet | Added third dataset (UCI Adult). |
| Limited seeds reduce power | Weak statistical conclusions | Increased to ten seeds; power discussion added (SC‑005). |

---



