# Evaluating the Robustness of Common Statistical Tests to Non‑Independence

**Repository:** `projects/PROJ-483-evaluating-the-robustness-of-common-stat`

## Purpose

This project provides a reproducible research pipeline that quantifies how the violation of the independence assumption influences:

* **Type I error rates** of Student's t‑test, one‑way ANOVA, and chi‑squared tests.
* **Statistical power** when true effects are present.

The analysis is performed on real public datasets (UCI Machine Learning Repository / OpenML) with **controlled dependency injection** (temporal AR(1), hierarchical block bootstrap, spatial kernel smoothing). Results inform researchers about the robustness of standard parametric tests under realistic non‑independent data conditions.

## Key Features

* **Verified data sources** – datasets are fetched from canonical URLs defined in `data/manifests/datasets.yaml`.
* **Dependency injection** – AR(1) autocorrelation, block bootstrap, and spatial kernel smoothing (including a feature‑space clustering proxy).
* **Monte‑Carlo simulation** – 10 000 replications per configuration (FR‑004) using fully vectorised NumPy operations.
* **Exact confidence intervals** – Clopper‑Pearson intervals for error‑rate estimates (SC‑003).
* **Trend verification** – Spearman and Mann‑Kendall tests to confirm monotonic error‑rate inflation (US‑1 AC‑2).
* **Logistic‑regression modeling** – Relates error probability to dependency strength (Constitution VII).
* **Comprehensive documentation** – `docs/overview.md`, `quickstart.md`, and in‑code docstrings.

## Quick Start

1. **Clone the repository**
 ```bash
 git clone <repo-url>
 cd projects/PROJ-483-evaluating-the-robustness-of-common-stat
 ```

2. **Create a virtual environment and install dependencies**
 ```bash
 python -m venv venv
 source venv/bin/activate # Windows: venv\Scripts\activate
 pip install -r code/requirements.txt
 ```

3. **Run the pipeline**
 ```bash
 # Download and validate datasets
 python code/main.py --action download

 # Execute the full Monte‑Carlo simulation (type‑I error & power)
 python code/main.py --action simulate

 # Generate visualisations
 python code/main.py --action plot
 ```

4. **Inspect results**
 * Aggregated metrics: `results/aggregated_us1.csv`, `results/aggregated_us2.csv`, `results/aggregated_us3.csv`
 * Markdown summary table: `results/type1_error_table.md`
 * Figures: `results/figures/` (error‑rate curves, power curves)
 * Performance log: `results/perf_log.json`

For detailed configuration options (e.g., choosing a subset of datasets, adjusting replication counts, enabling streaming) see `code/config.yaml` and the **Methodology** section in `docs/overview.md`.

## Project Structure

```
.
├── code/ # Core implementation
│ ├── __init__.py
│ ├── config.py
│ ├── data_loader.py
│ ├── dependency_injector.py
│ ├── simulation_runner.py
│ ├── main.py
│ └── metrics.py
├── data/
│ ├── raw/ # Downloaded datasets (CSV)
│ ├── processed/ # Dependency‑injected versions
│ └── manifests/
│ ├── datasets.yaml
│ └── checksums.json
├── docs/
│ └── overview.md
├── results/
│ ├── aggregated_us1.csv
│ ├── aggregated_us2.csv
│ ├── aggregated_us3.csv
│ ├── type1_error_table.md
│ ├── figures/
│ └── perf_log.json
├── tests/
│ ├── unit/
│ └── integration/
├── quickstart.md
├── README.md # ← This file
└── requirements.txt
```

## Reproducibility

* **Random seed** – Defined in `code/config.yaml` (`seed: 42`). All stochastic functions respect this seed.
* **Versioned data** – Checksums stored in `data/manifests/checksums.json`. The pipeline aborts if any checksum mismatch is detected.
* **Artifact tracking** – `results/state.yaml` records content hashes for all generated files.

## Contributing

Contributions are welcome. Please follow the existing code style (black, flake8) and add unit tests for new functionality. See `tests/` for examples.

## License

This project is released under the MIT License. Third‑party libraries used are listed in `code/requirements.txt` and are compatible with this license.

---

*For a full description of the scientific methodology, see `docs/overview.md`.*