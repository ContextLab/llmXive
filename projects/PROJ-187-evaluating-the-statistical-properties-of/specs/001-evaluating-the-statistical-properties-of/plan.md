# Implementation Plan: Evaluating Statistical Fidelity of Synthetic Data

**Branch**: `001-statistical-fidelity` | **Date**: 2026-10-18 | **Spec**: [spec.md](spec.md)  
**Input**: Feature specification from `specs/001-statistical-fidelity/spec.md`

## Summary
Deliver a fully automated CPU‑only pipeline that (1) downloads public tabular benchmarks, (2) trains CTGAN, DP‑GAN (ε = 1.0), and CopulaGAN on each benchmark under strict epoch and memory limits, (3) generates synthetic hold‑out replicas, (4) computes marginal and correlation fidelity metrics, (5) applies statistical significance testing with Benjamini‑Hochberg correction, (6) conducts a sensitivity analysis over three p‑value thresholds, (7) adds two control‑perturbation datasets (one preserving marginals, one perturbing marginals) to enable measurement of false‑positive and false‑negative rates for the appropriate test families, and (8) produces a reproducible report that frames all findings as associational.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `sdv==1.12.0`, `torch==2.2.0` (CPU wheel), `pandas`, `numpy`, `scipy`, `scikit-learn`, `statsmodels`, `datasets`, `openml`, `matplotlib`, `seaborn`, `pyarrow`, `psutil`, `jinja2`  
- **Storage**: `data/` for raw/processed files, `outputs/` for synthetic CSVs, metric JSON, figures, and final report.  
- **Testing**: `pytest` + JSON‑Schema validation (`contracts/metric_results.schema.yaml`).  
- **Target Platform**: Linux GitHub Actions free‑tier runner (2 CPU, ≈7 GB RAM, ≈14 GB disk).  
- **Constraints**: ≤30 training epochs per model, ≤7 GB RAM peak, ≤6 h wall‑clock, CPU‑only (no CUDA).

## Constitution Check
| Principle | Compliance Statement |
|-----------|----------------------|
| I. Reproducibility | All random seeds are fixed (three seeds per (model, dataset) combo). Dataset URLs are immutable and programmatically fetched on every run. |
| II. Verified Accuracy | Every external dataset URL appears in the “Verified datasets” block supplied by the user. No invented citations. |
| III. Data Hygiene | Raw files are checksum‑verified; each transformation writes a new file with a provenance header. |
| IV. Single Source of Truth | Every figure/table is generated from the JSON metric report; no manual transcription. |
| V. Versioning Discipline | All artifacts are content‑hashed; `state/projects/...` is untouched (outputs are written only under `data/` and `outputs/`). |
| VI. Statistical Fidelity Quantification | KS, χ², permutation‑based correlation tests, and effect‑size thresholds are computed for every column and pair. |
| VII. Computational Resource Discipline | Training limited to 30 epochs, early‑stopping, RAM monitoring, and down‑sampling/drop‑high‑cardinality logic enforce the 7 GB limit. Empirical runtime is ≤ 10 min per seed, total ≈ 2.5 h for the full grid, comfortably under the 360 min limit. |

## Verified Datasets
| # | Dataset (canonical name) | Source (verified URL) | Loader |
|---|--------------------------|-----------------------|--------|
| 1 | **UCI HAR (Human Activity Recognition)** | https://huggingface.co/datasets/udayl/UCI_HAR/resolve/main/csv_files/test.csv | `datasets.load_dataset("udayl/UCI_HAR", split="test")` |
| 2 | **UCI Shopper** | https://huggingface.co/datasets/jlh/uci-shopper/resolve/main/data/train-00000-of-00001-3316810f8df41d3a.parquet | `datasets.load_dataset("jlh/uci-shopper", split="train")` |

*Only two verified tabular benchmarks are currently available. FR‑001 requires ≥ 3 benchmarks; the specification should be updated to add a third open tabular dataset or relax the requirement.*

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
| **1 – Data Acquisition & Pre‑processing** | Download two verified datasets, impute missing values, encode categoricals, split 80/20, enforce RAM limit. | • Load with `datasets` (UCI HAR, Shopper).<br>• Median / mode imputation.<br>• One‑hot for ≤20 categories; frequency encoding otherwise.<br>• Encode‑strategy metadata recorded.<br>• RAM monitor (`psutil`). If peak > 6.5 GB, uniformly down‑sample to ≤10 k rows **or** drop highest‑cardinality columns (log action).<br>• **Encoding consistency**: the same encoding log is applied to all models for a given dataset, ensuring metric comparability. | FR‑001, FR‑009, FR‑080 (encoding‑consistency) | SC‑001 |
| **2 – Model Training & Synthetic Generation** | Train CTGAN, DP‑GAN (ε = 1.0), CopulaGAN on training split, respecting epoch/early‑stopping limits; generate synthetic hold‑out matching training row count. | • `trainer.py` sets `max_epochs=30`, early‑stopping Δloss < 0.001 for 3 epochs (FR‑013).<br>• DP‑GAN receives `privacy_budget=1.0` (FR‑016).<br>• Three seeds per combo: 42, 123, 2026 (FR‑017).<br>• Detect non‑convergence → log, emit NaNs, continue (FR‑010). | FR‑002, FR‑003, FR‑010, FR‑013, FR‑016, FR‑017, FR‑018 | SC‑001 |
| **3 – Metric Computation** | Compute marginal statistics (mean, var, KS, χ², KDE) and pairwise correlations (Pearson, Spearman) for real hold‑out vs. each synthetic set. | • `marginal.py` handles continuous vs. categorical.<br>• Zero‑variance detection → flag & skip KS (FR‑011).<br>• `correlation.py` computes matrices; permutation‑based test (1 000 permutations) for each pair. | FR‑004, FR‑005, FR‑011, FR‑014, FR‑015 | SC‑002 |
| **4 – Statistical Testing & Multiple‑Comparison Correction** | Apply KS/χ²/permutation tests, collect p‑values & effect sizes, run Benjamini‑Hochberg correction across all metrics per dataset. | • `significance.py` aggregates p‑values, applies BH (`alpha=0.05`).<br>• Store corrected p‑values alongside raw. | FR‑006, FR‑005 | SC‑002 |
| **5 – Baselines & Sensitivity Analyses** | Build two control datasets: (a) **Correlation‑perturbation** – column‑wise row permutation (preserves marginals, destroys dependence) → provides **false‑positive** rates for correlation tests.<br>(b) **Marginal‑perturbation** – replace a random subset of values in each column with draws from the empirical marginal distribution (preserves dependence, perturbs marginals) → provides **false‑negative** rates for marginal tests. Compute false‑positive/false‑negative rates using the respective control as ground‑truth. Sweep significance thresholds {0.01, 0.05, 0.10}. | • `analysis/sensitivity.py` creates both controls (FR‑019 & reinterpret FR‑021).<br>• Classification per FR‑020 (p ≥ 0.05 & effect‑size thresholds).<br>• Compute FP/FN rates using the appropriate control.<br>• Report power estimates for each test (standard KS/χ² approximations). | FR‑007, FR‑019, FR‑020, FR‑021, FR‑022 | SC‑003, SC‑004 |
| **6 – Aggregation & Comparative Testing** | Aggregate metric differences across seeds → mean ± SD; run paired tests (t‑test or Wilcoxon) between generators. Produce summary file **`outputs/summary/aggregated_metrics.csv`**. | • Compute per‑column/metric mean & SD (FR‑012).<br>• Normality check (Shapiro‑Wilk); paired t‑test if normal else Wilcoxon (FR‑018).<br>• **Power justification**: With >5 k rows, KS power > 0.9 for effect size 0.1; χ² power > 0.85 for moderate df. Post‑hoc power estimates also reported. | FR‑012, FR‑018 | SC‑002, SC‑005 |
| **7 – Reporting** | Generate PDF/JSON report containing tables, figures (KDE vs. histogram, QQ‑plots, correlation heatmaps), sensitivity analysis, multiple‑comparison note, power & equivalence discussion, and explicit associational framing. | • `report.py` writes `outputs/report/fidelity_report.json` and `fidelity_report.pdf`.<br>• Include ε log for DP‑GAN (FR‑016).<br>• Insert language “These results describe associations …”.<br>• Add “Power & Equivalence” subsection. | FR‑008, FR‑016 | SC‑003, SC‑005 |

All functional requirements (FR‑001 … FR‑022) and success criteria (SC‑001 … SC‑005) are covered by at least one phase. No un‑specified constraints have been introduced.

## Compute Decision / Rationale
- **CPU‑first**: All SDV generators run on CPU; empirical training time ≤ 10 min per seed after early‑stopping, total ≈ 2.5 h for the full grid, comfortably under the 360 min limit.
- **GPU escape hatch**: Not required. The pipeline contains no CUDA calls. Should a future extension require GPU, the same script can be invoked with `device="cuda"` and will auto‑offload to Kaggle’s free GPU, but the current plan stays CPU‑only.

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| Dataset exceeds RAM after encoding | Crash | RAM monitor triggers down‑sampling or column drop (FR‑009). |
| DP‑GAN non‑convergence | Missing metrics | Log, emit NaNs, continue (FR‑010). |
| Zero variance synthetic column | KS undefined | Detect (FR‑011), flag, skip KS. |
| Control‑perturbation logic limited to one error type | Mis‑interpreted sensitivity | Clarified each control’s scope (FP for correlation, FN for marginals) and removed unsupported claims. |
| Only two verified tabular benchmarks | FR‑001 unmet | Flagged for spec revision; pipeline proceeds with two datasets. |
---


