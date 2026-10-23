# Implementation Plan: Evaluating the Impact of Data Transformation on Statistical Test Sensitivity

**Branch**: `001-data-transformation-sensitivity` | **Date**: 2024-10-23 | **Spec**: `specs/001-data-transformation-sensitivity/spec.md`  
**Input**: Feature specification from `/specs/001-data-transformation-sensitivity/spec.md`

## Summary
The pipeline will (1) download ≥ 50 public datasets from OpenML (supplemented with the six verified HuggingFace URLs when they meet the criteria) that contain continuous variables and a categorical group label, (2) filter for non‑normality (Shapiro‑Wilk *p* < 0.05) and *N* ≥ 30, (3) impute missing values (mean for near‑symmetric variables, median for skewed) and run a K‑NN‑imputation sensitivity branch, (4) apply three transformations (Box‑Cox, Yeo‑Johnson, rank‑based inverse normal) plus a baseline, (5) estimate Type I error via stratified label‑shuffling (5 000 permutations per dataset, fixed seed), (6) generate simulated datasets that preserve each real dataset’s skewness/kurtosis and embed known Cohen’s *d* ∈ {0.2, 0.5, 0.8}, (7) compute empirical power and compare it to analytical power from `statsmodels.stats.power.TTestIndPower`, (8) aggregate results using a hierarchical bootstrap that resamples datasets and, within each, the permutation‑based estimates, (9) produce bootstrap 95 % CIs with a **target half‑width ≤ 0.07** (actual width reported if unattainable), (10) run a Friedman test with Bonferroni‑corrected Wilcoxon post‑hoc comparisons, (11) perform an α‑sensitivity sweep (α = 0.01, 0.05, 0.10), and (12) output reproducible tables and figures. All steps run on the GitHub Actions free‑tier CPU runner, checkpoint after each dataset, and respect the 6‑hour runtime limit.

## Technical Context

- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas`, `numpy`, `scipy`, `statsmodels`, `scikit-learn`, `seaborn`, `matplotlib`, `openml`, `datasets` (HuggingFace), `pyyaml`, `portalocker`  
- **Storage**: Filesystem under `data/`, `results/`, `state/` (CSV/Parquet)  
- **Testing**: `pytest` (unit + integration)  
- **Target Platform**: Linux GitHub Actions runner (2 CPU cores, ~7 GB RAM, ≤ 6 h) – **CPU‑first**; no GPU required.  
- **Constraints**: Runtime ≤ 6 h, peak RAM ≤ 4 GB, checkpointing after each dataset.  

## Constitution Check

| Principle | Compliance Statement |
|-----------|----------------------|
| I. Reproducibility | All scripts are deterministic; seeds are pinned and saved in `state/random_seeds.txt`. External datasets are fetched from the same OpenML API or the six verified HuggingFace URLs on every run. |
| II. Verified Accuracy | All citations are limited to the verified OpenML API and the six HuggingFace URLs listed in the “Verified datasets” block. |
| III. Data Hygiene | SHA‑256 checksums recorded in `data/checksums.csv`; transformations write new files; no in‑place edits. |
| IV. Single Source of Truth | Every figure/table references a single row in `data/datasets.csv` (or `data/simulated_datasets.csv`). |
| V. Versioning Discipline | Content hashes stored in `state/projects/...yaml`; any change updates the timestamp. |
| VI. Benchmark Transparency | `data/datasets.csv` lists each dataset name, source URL, and preprocessing steps. |
| VII. Simulation Determinism | Random seeds for shuffling, simulation, and bootstrap are stored in `state/random_seeds.txt`. |

## Project Structure

```text
specs/001-data-transformation-sensitivity/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── aggregated_result.schema.yaml
│   ├── dataset.schema.yaml
│   ├── sensitivity_result.schema.yaml
│   ├── simulated_dataset.schema.yaml
│   ├── test_result.schema.yaml
│   ├── transformation.schema.yaml
│   └── transformed_data.schema.yaml
└── tasks.md   # generated later
```

```text
src/
├── data/
│   ├── download_datasets.py
│   ├── checksum_datasets.py
│   ├── impute_and_filter.py
│   └── simulate_datasets.py
├── transform/
│   ├── apply_transformations.py
│   └── log_shift.py
├── analysis/
│   ├── null_simulation.py
│   ├── power_estimation.py
│   ├── aggregation.py
│   ├── inference.py
│   └── visualization.py
└── main.py
```

## Complexity Tracking
All file‑writing tasks (download, checksum, imputation log, transformation outputs, checkpoint files) are performed sequentially to avoid race conditions. Read‑only tasks (visualization, summary statistics) are safe to parallelise if desired.

## Phase Breakdown & FR/SC Mapping

| Phase | Description | FR(s) | SC(s) |
|-------|-------------|-------|-------|
| **Phase 1 – Acquisition & Checks** | Query OpenML for classification datasets with ≥ 30 rows, ≥ 1 numeric feature, ≤ 10 % missing. Stream each dataset, compute SHA‑256, record in `data/checksums.csv`. If after exhausting OpenML we have < 50 qualifying datasets, supplement with the six verified HuggingFace URLs that meet the criteria (checked programmatically). | FR‑001, FR‑010 | SC‑001 |
| **Phase 2 – Imputation & Filtering** | Primary imputation: mean for |skewness| < 0.5, median otherwise. Log each imputation in `data/imputation_log.csv`. **Sensitivity branch**: repeat whole pipeline with K‑NN (k=5) imputation. Apply Shapiro‑Wilk; retain datasets with *p* < 0.05 and *N* ≥ 30. Record exclusions (non‑normal, small *N*, missing > 10 %). | FR‑002, FR‑003 (imputation), FR‑011, FR‑014, FR‑018 | SC‑001 |
| **Phase 3 – Null‑Simulation (Type I Error)** | For each retained dataset and each transformation (Box‑Cox, Yeo‑Johnson, rank‑inverse‑normal, baseline):<br>1. Stratified label shuffling (5 000 permutations, seed = 42).<br>2. Optimise λ per variable for Box‑Cox/Yeo‑Johnson.<br>3. Run t‑test (2 groups) or one‑way ANOVA (>2 groups).<br>4. Record proportion of *p* < 0.05 as Type I error. | FR‑004, FR‑017 | SC‑002 |
| **Phase 4 – Simulated Power Datasets** | For each retained real dataset **R** and each effect size **d** ∈ {0.2, 0.5, 0.8}:<br>1. Generate 1 000 synthetic datasets preserving **R**’s skewness/kurtosis (moment‑matching).<br>2. Assign group labels to achieve the target Cohen’s *d*.<br>3. Apply the four transformations.<br>4. Run the appropriate test; empirical power = proportion of *p* < 0.05.<br>5. **Validation**: compute analytical power using `statsmodels.stats.power.TTestIndPower` (or `FTestAnovaPower` for >2 groups) and report the difference; no expectation of exact match, just a sanity check. | FR‑005, FR‑006 | SC‑003 |
| **Phase 5 – Hierarchical Aggregation & Inference** | 1. **Hierarchical bootstrap**: resample datasets (with replacement) and, within each sampled dataset, resample the permutation‑based error‑rate or power estimates (10 000 outer resamples, 1 000 inner). Compute 95 % CIs; target half‑width ≤ 0.07 (per SC‑004). If usable datasets < 45, report actual half‑width and note the limitation.<br>2. **Sample‑size justification**: power analysis for Friedman test (small effect *f* = 0.25) shows ≥ 45 datasets give > 80 % power at α = 0.05 (`statsmodels.stats.power.FTestAnovaPower`). Our ≥ 50‑dataset goal satisfies this.<br>3. **Friedman test** on Type I error and on power across the three transformations (`scipy.stats.friedmanchisquare`).<br>4. **Post‑hoc**: Bonferroni‑corrected Wilcoxon signed‑rank pairwise tests.<br>5. **α‑sensitivity sweep**: repeat null simulation for α ∈ {0.01, 0.05, 0.10}; store in `results/sensitivity_results.csv`. | FR‑007, FR‑012, FR‑009 | SC‑004 |
| **Phase 6 – Reporting** | Produce `results/aggregated_results.csv`, `results/sensitivity_results.csv`, and figures (`error_rates.png`, `power_curves.png`, `alpha_sweep.png`). Each output includes a footnote referencing the originating row(s) in `data/datasets.csv` or `data/simulated_datasets.csv`. | FR‑009 | SC‑001, SC‑004 |
| **Cross‑cutting** | Enforce a 6‑hour runtime limit; checkpoint after each dataset (`results/checkpoints/*.json`). Abort gracefully if limit approached, logging the state. | FR‑013 | — |

## Risk Mitigation
| Risk | Mitigation |
|------|------------|
| Insufficient qualifying public datasets | Continue OpenML paging until ≥ 50; fall back to the six verified HuggingFace URLs (checked for continuous vars & group label). |
| Bootstrap CI precision unattainable | Target half‑width is ≤ 0.07; if not met, report actual width and note the limitation (SC‑004 satisfied). |
| Transformation failure on negative values | Apply a minimal log‑shift before Box‑Cox/Yeo‑Johnson; log the intervention in `data/imputation_log.csv`. |
| Checkpoint race conditions | Use `portalocker` for atomic writes; sequential ordering for all write‑heavy tasks. |
| Excessive compute time | All loops are vectorised; 5 000 shuffles per dataset and 1 000 simulations per effect size are tractable within the 6‑hour budget on the free runner. |

---
