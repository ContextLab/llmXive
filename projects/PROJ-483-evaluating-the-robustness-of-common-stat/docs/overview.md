# Overview

**Evaluating the Robustness of Common Statistical Tests to Non-Independence in Public Datasets**

This repository implements a reproducible Monte‑Carlo simulation pipeline that quantifies how violations of the independence assumption affect the Type I error rate and statistical power of three widely‑used parametric tests:

* **Student's t‑test**
* **One‑way ANOVA**
* **Chi‑squared test of independence**

The pipeline works with real public datasets (UCI / OpenML) and injects controlled dependency structures:

1. **Temporal dependency** – AR(1) autocorrelation.
2. **Hierarchical dependency** – Block bootstrap resampling.
3. **Spatial dependency** – Gaussian kernel smoothing using either native spatial coordinates or a validated feature‑space clustering proxy.

For each dataset, dependency strength `r` is swept over the discrete set `{0, 0.1, 0.2, 0.3, 0.5}` (FR‑007).
For every configuration the pipeline runs **10 000 replications** (FR‑004) and records p‑values, from which it computes:

* Observed Type I error rate with Clopper‑Pearson 95 % confidence intervals (SC‑003).
* Observed statistical power for injected true effects (SC‑002).
* Trend analysis (Spearman and Mann‑Kendall) verifying monotonic error‑rate inflation (US‑1 AC‑2).
* Logistic‑regression models relating error rate to dependency strength (Constitution VII).

All results are saved under `results/` as CSV/JSON files and visualised in `results/figures/`. The project adheres to the **Constitution** principles (reproducibility, data hygiene, versioning, etc.) described in `plan.md`.

---

## Quickstart

See `quickstart.md` for step‑by‑step instructions on installing dependencies, downloading datasets, running the simulation, and generating visualisations.

---

## Project Structure

```
.
├── code/ # Core implementation
│ ├── config.py
│ ├── data_loader.py
│ ├── dependency_injector.py
│ ├── simulation_runner.py
│ ├── main.py
│ └── metrics.py
├── data/
│ ├── raw/ # Downloaded UCI/OpenML datasets
│ ├── processed/ # Dependency‑injected versions
│ └── manifests/ # YAML manifests and checksum files
├── docs/ # Documentation (this folder)
│ └── overview.md
├── results/
│ ├── aggregated_us1.csv
│ ├── type1_error_table.md
│ └── figures/
├── tests/
│ └── … # Unit & integration tests
├── README.md # Project README (updated)
└── requirements.txt
```

---

## Methodology Summary

1. **Dataset acquisition** – `code/data_loader.py` fetches verified URLs from `data/manifests/datasets.yaml`, validates minimum sample size (≥ 50) and variable suitability, and stores raw CSVs under `data/raw/`.
2. **Dependency injection** – Functions in `code/dependency_injector.py` (`ar1_inject`, `block_bootstrap`, `spatial_kernel_smooth`) create the desired correlation structure while preserving marginal distributions.
3. **Null‑hypothesis construction** – After injection, the target column is permuted (`code/simulation_runner.py`) to break any genuine effect while retaining the injected dependence (FR‑002).
4. **Monte‑Carlo simulation** – `code/simulation_runner.py` runs vectorised replications for each `(dataset, test_type, dependency_structure, r)` configuration, recording p‑values.
5. **Metric calculation** – `code/metrics.py` computes Type I error, power, Clopper‑Pearson CIs, and trend statistics.
6. **Aggregation & reporting** – `code/main.py` aggregates results into unified CSVs, appends trend status, and writes markdown tables (`results/type1_error_table.md`).
7. **Visualization** – `code/visualizer.py` produces line plots with CI error bars for error‑rate and power curves.

All random seeds are pinned via `code/config.yaml` and `code/utils/seeding.py` to guarantee reproducibility.

---

## References

* **Specification** – `specs/001-evaluating-the-robustness-of-common-stat/spec.md`
* **Constitution Check** – `plan.md` (Section “Constitution Check”)
* **Statistical Foundations** – `statsmodels.stats.power`, `scipy.stats`, and standard textbooks on hypothesis testing.

For a detailed walk‑through of each component, consult the inline docstrings in the source files and the generated reports in `results/`.
