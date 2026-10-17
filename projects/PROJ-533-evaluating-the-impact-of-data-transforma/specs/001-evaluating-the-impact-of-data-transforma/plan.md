# Implementation Plan: Evaluating the Impact of Data Transformation on Statistical Test Sensitivity

**Branch**: `001-data-transformation-sensitivity` | **Date**: 2024-10-17 | **Spec**: `specs/001-evaluating-the-impact-of-data-transforma/spec.md`  
**Input**: Feature specification from `/specs/001-evaluating-the-impact-of-data-transforma/spec.md`

## Summary
The project will (1) download ≥ 50 public datasets from UCI and OpenML, (2) filter for non‑normal continuous variables with group labels (Shapiro‑Wilk p < 0.05, N ≥ 30, < 10 % missing), (3) characterize distribution shape (skewness, kurtosis), (4) **estimate Type I error by shuffling group labels on the filtered real datasets** (multiple iterations, fixed seed), exactly as FR‑004 and US‑2 mandate, (5) generate simulated datasets with known Cohen’s d (small, medium, large) for power analysis, (6) apply Box‑Cox, Yeo‑Johnson, and rank‑based inverse‑normal transformations, (7) run t‑tests and ANOVAs, (8) aggregate results, compute bootstrap confidence intervals (target half‑width ± 0.02), (9) **assess transformation effects with a Friedman test (non‑parametric repeated‑measures ANOVA) and Bonferroni‑corrected post‑hoc pairwise comparisons**, and (10) produce summary tables and bar plots. All steps are fully reproducible, checkpointed, and executed on the GitHub Actions free‑tier CPU runner.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas`, `numpy`, `scipy`, `statsmodels`, `scikit-learn`, `seaborn`, `matplotlib`, `datasets` (HuggingFace), `pyyaml`  
- **Storage**: Filesystem under `data/`, `results/`, `state/` (CSV/Parquet)  
- **Testing**: `pytest` (unit + integration)  
- **Target Platform**: Linux runner (2 CPU cores, ~7 GB RAM, ~14 GB disk, ≤ 6 h) – **CPU‑first**; no GPU required.  
- **Constraints**: Open‑source datasets only, SHA‑256 checksums, fixed random seeds, checkpointing after each dataset, streaming/chunked I/O for large files.

## Constitution Check
| Principle | Compliance | Evidence / Plan |
|-----------|------------|-----------------|
| I. Reproducibility | ✅ | Fixed seeds recorded (`results/simulation_seeds.txt`); all code runs from `code/` on a fresh runner; `requirements.txt` pins dependencies. |
| II. Verified Accuracy | ✅ | All dataset URLs are taken from the verified list provided in the spec; any additional OpenML queries use the public API (no hidden sources). |
| III. Data Hygiene | ✅ | SHA‑256 checksums saved to `data/checksums.csv`; raw files never overwritten; transformations write new files; PII‑free public data. |
| IV. Single Source of Truth | ✅ | Every figure/table derives from CSVs in `results/`; no hand‑typed numbers. |
| V. Versioning Discipline | ✅ | Artifact hashes stored in `state/projects/PROJ-533-evaluating-the-impact-of-data-transforma.yaml`. |
| VI. Benchmark Transparency | ✅ | `data/datasets.csv` lists URL, name, and preprocessing steps for every dataset. |
| VII. Simulation Determinism | ✅ | All stochastic steps (label shuffling, simulation) use seeds logged in `results/simulation_seeds.txt`. |

## Project Structure
```text
specs/001-data-transformation-sensitivity/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── dataset.schema.yaml
│   ├── transformation.schema.yaml
│   ├── test_result.schema.yaml
│   ├── aggregated_result.schema.yaml
│   ├── simulated_dataset.schema.yaml
│   ├── sensitivity_result.schema.yaml
│   └── transformed_data.schema.yaml
└── tasks.md   # generated later

code/
├── __init__.py
├── main.py                # orchestrates the pipeline
├── config.py
├── utils/
│   ├── logging_config.py
│   ├── checkpointing.py   # implements save_state / load_state / delete_checkpoint
│   └── statistical_tests.py
├── data/
│   ├── download_datasets.py
│   ├── filters.py
│   ├── transformations.py
│   └── simulations.py
├── analysis/
│   ├── type1_error.py
│   ├── power_analysis.py
│   ├── sensitivity.py
│   └── aggregation.py
└── tests/
    ├── unit/
    │   ├── test_statistical_tests.py
    │   └── test_transformations.py
    └── integration/
        └── test_pipeline.py   # verifies end‑to‑end execution, dataset count, etc.

data/
├── datasets.csv          # populated by download step
├── checksums.csv
├── raw/
├── filtered/
├── transformed/
├── simulated/
├── imputation_log.csv
└── exclusions.csv

results/
├── pipeline.log
├── simulation_seeds.txt
├── type1_error_results.csv
├── power_results.csv
├── sensitivity_results.csv
├── aggregated_results.csv
├── friedman_summary.txt
└── figures/
    ├── error_rates.png
    ├── power_curves.png
    └── sensitivity_curves.png

state/
└── projects/PROJ-533-evaluating-the-impact-of-data-transforma.yaml
```

## Complexity Tracking & Missing‑Task Resolution
| Missing Task | Resolution (added to plan) |
|--------------|----------------------------|
| **T004** – `utils/checkpointing.py` | Added to **Task T004** (see Task Ordering). Implements `save_state(state: dict)`, `load_state()`, `delete_checkpoint()`. Uses `portalocker` for file locking and atomic writes via temporary file rename. |
| **T012a** – `tests/integration/test_pipeline.py` | Added to **Task T012a**. The test loads `data/datasets.csv`, asserts ≥ 50 rows, runs `code/main.py --dry-run`, and checks that `results/aggregated_results.csv` contains ≥ 1 row. |
| **T013** – `data/datasets.csv` creation | Added to **Task T013**. `download_datasets.py` writes a header + one row per successful download (URL, name, checksum, N, etc.). |
| **T013b** – verification logic in `download_datasets.py` | Added to **Task T013b**. Function `is_source_verified(url)` checks URL against the verified list; only verified URLs are written to `datasets.csv`. |
| **T014** – `code/checksum_datasets.py` | Added to **Task T014**. Computes SHA‑256 for each raw file and writes `data/checksums.csv`. |
| **T015** – `filter_datasets.py` imputation & exclusion logging | Added to **Task T015**. Handles missing‑value imputation (mean/median), logs imputation rates to `imputation_log.csv`, excludes > 10 % missing datasets, writes to `exclusions.csv`. |
| **T016** – Shapiro‑Wilk & sample‑size filtering | Added to **Task T016**. Performs Shapiro‑Wilk per continuous variable, retains datasets with any variable p < 0.05 and N ≥ 30, updates `datasets.csv` status, logs exclusions. |
| **T017** – Ensure `data/datasets.csv` exists and is populated | Covered by **T013** and **T016**; final file contains ≥ 50 rows. |
| **T018** – Simulated Null Generation (optional sanity check) | Generates null datasets preserving marginal shapes; used ONLY as a diagnostic sanity check, never for the primary FR‑004 estimate (which uses real‑data label shuffling, T021). |
| **T019** – Simulated Alternative Generation | Generates alternative datasets with known Cohen’s d (small, medium, large). |
| **T020** – Apply Transformations | Apply Box‑Cox, Yeo‑Johnson, rank‑based to all real (post‑shuffling) and simulated datasets; log λ and any log‑shift interventions. |
| **T021** – **Real‑Data Type I Error Estimation (primary FR‑004)** | For each filtered real dataset, shuffle group labels **N = 5000** times (fixed seed recorded in `results/simulation_seeds.txt`), run t‑test/ANOVA on each transformed version, and compute the proportion of p < 0.05 as the Type I error estimate. This is the primary FR‑004 estimator, per US‑2 acceptance scenario 2. |
| **T022** – Power Estimation | For each simulated alternative dataset, run tests and compute power (proportion p < 0.05). |
| **T023** – Aggregation | Bootstrap (10 000 resamples) CI half‑width ≤ 0.02, compute mean error/power per transformation‑test combo. |
| **T024** – **Friedman Test & Post‑hoc (FR‑008)** | Perform Friedman test (non‑parametric repeated‑measures ANOVA, `scipy.stats.friedmanchisquare`) on per‑dataset error/power outcomes across the three transformations; follow with Bonferroni‑corrected pairwise Wilcoxon signed‑rank post‑hoc comparisons. Results recorded in `results/friedman_summary.txt` and modeled by the `FriedmanResult` entity (see data-model.md). |
| **T025** – Sensitivity Sweep | Sweep α ∈ {0.01, 0.05, 0.10} and recompute error rates; store in `results/sensitivity_results.csv`. |
| **T026** – Visualization | Generate bar plots (error rates, power, α‑sweep) under `results/figures/`. |
| **T027** – Reporting | Write summary tables (`results/aggregated_results.csv`) and ensure they trace back to single source rows. |
| **T028** – Clean‑up | Delete temporary checkpoint after successful run. |

## Mapping Functional Requirements (FR) & Success Criteria (SC) to Plan Phases
| FR | Description | Plan Phase(s) |
|----|--------------------------------------|---------------|
| FR‑001 | Download ≥ 50 public datasets, record URLs & metadata | T013, T013b |
| FR‑002 | Filter datasets (Shapiro‑Wilk p < 0.05, N ≥ 30, < 10 % missing) | T015, T016 |
| FR‑003 | Apply Box‑Cox, Yeo‑Johnson, rank‑based to each continuous variable | T020 |
| FR‑004 | Estimate Type I error **by shuffling group labels on the filtered real datasets** (multiple iterations, fixed seed) and computing the proportion of t‑test/ANOVA p‑values < 0.05 | T021 |
| FR‑005 | Generate simulated datasets with known effect sizes (Cohen’s d ∈ {small, medium, large}) | T019 |
| FR‑006 | Compute statistical power on simulated alternative data | T022 |
| FR‑007 | Aggregate results, compute mean error/power & bootstrap CIs | T023 |
| FR‑008 | Perform **Friedman test** (non‑parametric repeated‑measures ANOVA) to assess transformation effect, Bonferroni post‑hoc, α‑sweep sensitivity | T024, T025 |
| FR‑009 | Produce summary tables & bar plots | T026, T027 |
| FR‑010 | Compute SHA‑256 checksums for all downloaded datasets | T014 |

| SC | Measured Against | Plan Phase |
|----|------------------|------------|
| SC‑001 | ≥ 50 datasets, correct filtering, metadata preservation | T013, T016 |
| SC‑002 | Type I error rate vs nominal α = 0.05 | T021 |
| SC‑003 | Power vs known effect sizes | T022 |
| SC‑004 | Bootstrap CI half‑width ≤ 0.02 | T023 |

All FRs and SCs are explicitly addressed exactly as the spec states them; no requirement is amended or left uncovered.

## Compute Feasibility
- All statistical operations (t‑test, ANOVA, Shapiro‑Wilk, Friedman test) are CPU‑light.  
- Real‑data Type I error: 5000 shuffles × 3 transformations × 2 tests per dataset; simulated power: 1000 simulations per effect size × 3 transformations × 2 tests – comfortably within 6 h on 2 CPU cores.  
- Memory: Streaming CSV loads (`chunksize=10 000`) and parquet shards keep peak RAM well under the ~7 GB runner limit.  
- No GPU required; all libraries run on CPU.  

## Risks & Mitigations
| Risk | Mitigation |
|------|------------|
| Insufficient verified URLs for 50 datasets | Use OpenML API to discover additional datasets; each discovered URL is validated at download time. |
| Transformation fails on negative values | Log‑shift to make data positive; intervention logged in `data/imputation_log.csv`. |
| Runtime exceeds 6 h | Checkpoint after each dataset (T004) and resume (`--resume` flag). |
| Friedman test degenerate cases (e.g., tied per‑dataset rankings) | Fall back to pairwise Wilcoxon signed‑rank tests with Bonferroni correction; fallback is logged in `results/friedman_summary.txt`. |
| Missing group label | Exclude and record in `data/exclusions.csv`. |