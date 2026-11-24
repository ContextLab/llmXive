# Quickstart: The Impact of Simulated Social Comparison on Self-Evaluation in Online Environments

## 1️⃣ Setup
```bash
cd projects/PROJ-389-the-impact-of-simulated-social-compariso
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## 2️⃣ Data Availability Gate
```bash
python -m src.ingest.reddit_ingest --check-availability --output data/availability_report.json
```
- Verifies that the verified Reddit dataset (`allenai/reddit_comments`) containing `subreddit`, `body`, `created_utc`, and `author` (including `about` field) is reachable. If not, the gate writes a structured mismatch report and exits non‑zero. Real results cannot be produced until a verified source is supplied.

## 3️⃣ Ingestion (requires verified source)
```bash
python -m src.ingest.reddit_ingest --source allenai/reddit_comments \
    --streaming --output data/raw_user_comments.parquet
```
- Streams comments in chunks, scrubs PII, **retains the `about` profile field** for demographic extraction, aggregates per user; also writes `data/subreddit_metadata.parquet`.

## 4️⃣ Feature Extraction
```bash
python -m src.features.extract_features \
    --user-comments data/raw_user_comments.parquet \
    --subreddit-metadata data/subreddit_metadata.parquet \
    --output data/processed_features.csv --seed 42
```
- Predictors from the exposure/community stream; `self_eval_score` from the user's own comments only (Principle VI).

## 5️⃣ Power Check
```bash
python -m src.utils.power_check --features data/processed_features.csv --target_n 500 --effect_size 0.15
```
- Targets the exposure × authenticity interaction; logs a warning if estimated power < 0.80.

## 6️⃣ Regression & Diagnostics
```bash
python -m src.analysis.moderation_regression \
    --features data/processed_features.csv --results data/regression_results.csv --seed 42
```
- Hierarchical OLS, VIF, BH-FDR, cluster-robust SEs by subreddit, associational framing.

## 7️⃣ Stratification & Plots
```bash
python -m src.viz.demographic_plots \
    --features data/processed_features.csv --results data/regression_results.csv \
    --output reports/interaction_plots.pdf
```

## 8️⃣ Sensitivity Sweep
```bash
python -m src.analysis.sensitivity_sweep \
    --features data/processed_features.csv --output reports/sensitivity_summary.csv
```
- Writes the sensitivity summary referenced in `data-model.md`.

## 9️⃣ Tests
```bash
pytest -q tests/
```
- Unit tests run on synthetic fixtures (clearly labeled, never used as results) and contract tests validate both output schemas.

**Runner limits respected**: CPU‑only, ≤ 6 h, RAM ≤ 6 GB (FR‑008, FR‑015, SC‑005).

