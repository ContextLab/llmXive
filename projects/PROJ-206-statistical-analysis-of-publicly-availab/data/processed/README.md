# Processed Data Directory

This directory holds all derived datasets produced by the pipeline.

- `poll_data_cleaned.csv` – Harmonized poll records with weekly bins and placeholder columns.
- `historical_weights.csv` – Pollster‑specific RMSE‑based weights.
- `frequentist_forecasts.csv` – Simple and weighted average forecasts.
- `bayesian_forecasts.csv` – Posterior mean forecasts with 95 % credible intervals.
- Additional evaluation files (metrics, meta‑analysis results, etc.).

Files in this folder are version‑controlled via SHA‑256 hashes recorded in
`state/projects/PROJ-206-statistical-analysis-of-publicly-availab.yaml`.
