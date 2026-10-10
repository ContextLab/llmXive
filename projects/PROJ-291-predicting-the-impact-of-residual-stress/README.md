# Predicting the Impact of Residual Stress on Fatigue Life

This repository implements a reproducible research pipeline that quantifies how residual stress mediates the relationship between manufacturing process parameters and fatigue life across material classes.

## Project overview

- **Goal**: Evaluate the added predictive value of residual‑stress information (measured or proxy) for fatigue‑life prediction and quantify its mediation effect.
- **Key steps**:
 1. Ingest public fatigue datasets (NIST Materials Data Repository, UCI Machine Learning Repository, OpenML).
 2. Standardise units, median‑impute missing values, and compute a proxy residual‑stress estimate when measurements are absent.
 3. Build three feature sets (process‑only, process + measured stress, process + material properties).
 4. Train Random Forest, Gradient Boosting, and a shallow PyTorch neural network using 5‑fold CV and a held‑out test set.
 5. Perform statistical evaluation (paired t‑tests, cross‑material transfer, bootstrap mediation analysis).
 6. Generate a full report with tables and figures.

## Data sources

The pipeline automatically downloads the following open datasets:

- **NIST Materials Data Repository** – Fatigue life data for steels and aluminum alloys.
 URL: ` (example DOI; the script uses the canonical link provided by NIST).

- **UCI Machine Learning Repository – Fatigue‑Life**
 URL: `

- **OpenML – Fatigue Dataset**
 Project ID: `123456` (accessed via the `datasets` library).

All raw files are stored under `data/raw/` after download. [UNRESOLVED-CLAIM: c_4c158658 — status=not_enough_info] Their SHA‑256 checksums are recorded in the unified CSV (`data/processed/unified_fatigue.csv`) for provenance tracking. [UNRESOLVED-CLAIM: c_c6a7bc17 — status=not_enough_info]

## Getting started

1. Follow the instructions in [quickstart.md](quickstart.md) to create a virtual environment and install the exact pinned dependencies listed in `requirements.txt`.
2. Run `make env-check` to verify that the environment is correctly set up.
3. Execute the full analysis with a single command:
 ```bash
 bash run_pipeline.sh
 ```
 This will produce all intermediate files, model artifacts, and the final report (`reports/report.md`).

## Reproducibility

- All random seeds are fixed at `SEED=42` across scripts.
- Data integrity is ensured by SHA‑256 checksums.
- The full list of package versions is pinned in `requirements.txt`.
- Runtime and memory usage are logged in `results/runtime_summary.csv` and must stay within the GitHub Actions free‑tier limits (≤ 6 h, ≤ 7 GB RAM).

## License

This project is released under the MIT License. See the `LICENSE` file for details.
