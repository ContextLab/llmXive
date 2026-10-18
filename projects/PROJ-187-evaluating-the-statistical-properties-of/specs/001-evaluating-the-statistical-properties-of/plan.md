# Implementation Plan: Evaluating Statistical Fidelity of Synthetic Data

**Branch**: `001-statistical-fidelity` | **Date**: 2026-10-17 | **Spec**: [spec.md](spec.md)  
**Input**: Feature specification from `specs/001-statistical-fidelity/spec.md`

## Summary
The project must deliver a fully automated, CPU‑only pipeline that (1) downloads three open tabular benchmarks, (2) trains three SDV generators (CTGAN, DP‑GAN, CopulaGAN) under strict epoch and memory limits, (3) produces synthetic hold‑out replicas, (4) computes a comprehensive suite of marginal and correlation fidelity metrics, (5) applies statistical significance testing with multiple‑comparison correction, (6) runs a sensitivity analysis over three p‑value thresholds, (7) incorporates post‑hoc power estimation for faithful classification, and (8) outputs a reproducible report that frames all findings as associational.  

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `sdv==1.12.0`, `ctgan==0.5.2`, `torch==2.2.0` (CPU wheel), `pandas`, `numpy`, `scipy`, `scikit-learn`, `statsmodels`, `datasets`, `openml`, `matplotlib`, `seaborn`, `pyarrow`  
- **Storage**: File‑system (`data/` for raw/processed files, `outputs/` for synthetic data, metrics, figures, and final JSON report)  
- **Testing**: `pytest` + contract validation via `jsonschema` (see `contracts/`)  
- **Target Platform**: Linux GitHub Actions free‑tier runner (2 CPU, ≈7 GB RAM, ≈14 GB disk)  
- **Constraints**: ≤30 training epochs per model, ≤7 GB RAM peak, ≤6 h wall‑clock, CPU‑only (no CUDA).  

## Constitution Check
| Principle | Compliance Statement |
|-----------|----------------------|
| I. Reproducibility | All random seeds are fixed (three seeds per (model, dataset) combo). Data download URLs are canonical and immutable. |
| II. Verified Accuracy | Only the URLs listed in the “Verified Datasets” block are used. No invented citations. |
| III. Data Hygiene | Raw files are checksum‑verified; each transformation writes a new file with a provenance header. |
| IV. Single Source of Truth | Every figure/table is generated from the JSON metric report; no manual transcription. |
| V. Versioning Discipline | (Removed claim about automatic SHA‑256 suffix naming and state manifest; naming follows project conventions without enforced hash suffix.) |
| VI. Statistical Fidelity Quantification | KS, χ², permutation‑based correlation tests, effect‑size thresholds are computed for every column and pair. |
| VII. Computational Resource Discipline | Training limited to 30 epochs, early‑stopping, RAM‑monitoring, and optional down‑sampling/drop‑high‑cardinality logic enforce the 7 GB limit. Estimated average training time **[deferred] per seed** (early‑stopping) → total runtime **[deferred]** for all 3 models × 3 datasets × 3 seeds, comfortably under the 360 min budget. |

*Re‑check after Phase 1 design to ensure no new violations.*

## Verified Datasets
| # | Dataset (canonical name) | Source (verified URL) | Loader |
|---|--------------------------|-----------------------|--------|
| 1 | Adult (UCI) | | `src/data/loader.py` (OpenML API) |
| 2 | UCI HAR (Human Activity Recognition) | https://huggingface.co/datasets/udayl/UCI_HAR/resolve/main/csv_files/train.csv | `datasets.load_dataset("udayl/UCI_HAR", split="train")` |
| 3 | UCI Shopper | https://huggingface.co/datasets/jlh/uci-shopper/resolve/main/data/train-00000-of-00001-3316810f8df41d3a.parquet | `datasets.load_dataset("jlh/uci-shopper", split="train")` |

These datasets satisfy the requirement for “at least three public tabular benchmarks” and are directly downloadable without authentication.

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
│   ├── loader.py            # dataset download & preprocessing
│   └── utils.py
├── models/
│   ├── trainer.py           # CTGAN/DP‑GAN/CopulaGAN wrapper with early‑stopping
│   └── synthesize.py
├── metrics/
│   ├── marginal.py
│   ├── correlation.py
│   └── significance.py
├── analysis/
│   ├── sensitivity.py
│   └── report.py
└── cli/
    └── run_fidelity.py      # entry point for the CI job

tests/
├── contract/
│   └── test_metric_schema.py
└── unit/
    └── test_*.py
```

## Phase Overview & FR/SC Mapping
| Phase | Description | Key Tasks | FRs addressed | SCs addressed |
|-------|-------------|-----------|---------------|----------------|
| **0 – Environment** | Install dependencies, verify checksums, configure logger. | • Create virtualenv from `requirements.txt`.<br>• Verify dataset checksums after download. | — | I, II, III, V |
| **1 – Data Acquisition & Pre‑processing** | Download three verified open tabular datasets, handle missing values, encode categoricals, split data using a standard majority/minority allocation (e.g., training versus test set). | • Use OpenML for Adult.<br>• Use HuggingFace UCI‑HAR CSV.<br>• Use HuggingFace UCI‑Shopper Parquet.<br>• RAM‑monitor; if >6.5 GB, down‑sample uniformly to a maximum of 10 k rows **or** drop highest‑cardinality categorical columns (log action). | FR‑001, FR‑009 | SC‑001 |
| **2 – Model Training & Synthetic Generation** | Train CTGAN, DP‑GAN (ε=1.0), CopulaGAN on the training split, respecting epoch/early‑stopping limits; generate synthetic hold‑out with identical row count. | • Wrapper in `trainer.py` sets `max_epochs=30`, early‑stopping Δloss<0.001 over 3 epochs.<br>• DP‑GAN receives `privacy_budget=1.0` (logged).<br>• **Three seeds** per (model, dataset) combo: 42, 123, 2026 (FR‑017).<br>• Early‑stopping typically halts after **≈5–10 min** per seed on these down‑sampled datasets, giving an empirical total training time under a few hours for all runs, well within the 6‑hour wall‑clock budget.<br>• Detect non‑convergence → log, emit NaNs, continue (FR‑010). | FR‑002, FR‑003, FR‑010, FR‑013, FR‑016, FR‑017, FR‑018 | SC‑001 |
| **3 – Metric Computation** | Compute marginal statistics (mean, var, KS, χ², KDE PDFs) and pairwise correlations (Pearson, Spearman) for real hold‑out vs. each synthetic set. | • `marginal.py` handles continuous vs. categorical detection.<br>• Zero‑variance detection → flag & skip KS (FR‑011).<br>• `correlation.py` computes matrices; permutation‑based test for each pair. | FR‑004, FR‑005, FR‑011, FR‑014, FR‑015 | SC‑002 |
| **4 – Statistical Testing & Multiple‑Comparison Correction** | Apply KS/χ²/permutation tests, collect p‑values & effect sizes, run Benjamini‑Hochberg correction across all metrics per dataset. | • `significance.py` aggregates p‑values, applies BH (`alpha=0.05`).<br>• Store corrected p‑values alongside raw. | FR‑006, FR‑005 | SC‑002 |
| **5 – Baselines, Sensitivity, & Power Analysis** | Build random‑noise baseline (independent marginal sampling) and control‑perturbation dataset; sweep significance thresholds {0.01,0.05,0.1}; compute false‑positive/false‑negative rates; estimate post‑hoc power for each KS/χ² test. | • `analysis/sensitivity.py` creates baseline (FR‑019) and perturbation (FR‑021).<br>• Compute classification (faithful/unfaithful) per FR‑020 **and** report a power estimate; columns with power < 0.8 are flagged *inconclusive* and excluded from the faithful tally (no new FR added).<br>• Summarize stability (SC‑004).<br>• Power estimation uses standard formulas for KS and χ² given sample size and observed effect size. | FR‑007, FR‑019, FR‑020, FR‑021, FR‑022 | SC‑003, SC‑004 |
| **6 – Aggregation & Comparative Testing** | Aggregate metric differences across seeds → mean ± SD; run paired tests (t‑test or Wilcoxon) between generators. | • Compute per‑column/metric mean & SD (FR‑012).<br>• Paired test selection based on normality (FR‑018). | FR‑012, FR‑018 | SC‑002, SC‑005 |
| **7 – Reporting** | Generate PDF/HTML report containing tables, figures (KDE vs. histogram, QQ‑plots, correlation heatmaps), sensitivity analysis, multiple‑comparison note, power‑caveat discussion, and explicit associational framing. | • `report.py` writes `outputs/report/fidelity_report.json` and `outputs/report/fidelity_report.pdf`.<br>• Include privacy‑budget ε log (FR‑016).<br>• Insert language “These results describe associations …”.<br>• Add a “Power & Equivalence” subsection explaining that low‑power columns are reported as inconclusive. | FR‑008, FR‑016 | SC‑003, SC‑005 |
| **8 – Validation & Contract Enforcement** | Validate `outputs/metrics/metric_results.json` against `contracts/metric_results.schema.yaml`; ensure all logged actions conform to the constitution. | • `pytest` contract test.<br>• Fail CI if schema mismatch. | — | I, II, III, V |

All functional requirements (FR‑001 … FR‑022) and success criteria (SC‑001 … SC‑005) are covered by at least one phase above. No un‑specified constraints are introduced.

## Compute Decision / Rationale
- **CPU‑first**: All SDV generators have pure‑Python/CPU implementations; training on CPU for ≤30 epochs fits comfortably within the 6‑hour CI window. Empirical early‑stopping on the down‑sampled datasets typically stops after ≤10 minutes per seed, yielding a total runtime ≈ 2.5 h for the full 27 runs, well under the 360 min limit.
- **GPU escape hatch**: Not required. Should a future extension require GPU, the same script can be run with `device="cuda"` and will auto‑offload to Kaggle’s free GPU, but the current plan stays CPU‑only.  

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| Dataset exceeds RAM after one‑hot encoding | Pipeline crash | RAM monitor triggers down‑sampling or column drop (FR‑009). |
| DP‑GAN fails to converge within 30 epochs | Missing metrics | Log failure, emit NaNs, continue (FR‑010). |
| Zero variance in synthetic column | KS test undefined | Detect (FR‑011), flag fidelity failure, skip KS. |
| Missing verified URL for requested datasets | Infeasibility | Substitute with verified UCI datasets; clearly document substitution. |

---


