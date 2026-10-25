# Quickstart

```bash
# Install pinned dependencies
python -m pip install -r requirements.txt

# Run the full pipeline (defaults cover the entire 1998‑2020 span)
python -m src.code.main --stage all \
    --start-date 1998-01-01 \
    --end-date 2020-12-31
```

### Stage‑by‑Stage Commands

| Stage | Command | Description |
|-------|---------|-------------|
| **fetch** | `python -m src.code.main --stage fetch --start-date YYYY-MM-DD --end-date YYYY-MM-DD` | Downloads ACE composition and NOAA/Kyoto indices; validates required variables. |
| **sync** | `python -m src.code.main --stage sync` | Aligns to 1‑h UTC grid, interpolates gaps ≤ 6 h, writes `data/processed/synced.csv`. |
| **analyze** | `python -m src.code.main --stage analyze` | Full‑dataset lagged Pearson & Spearman correlations; writes `results/full_correlations.csv`. |
| **storm** | `python -m src.code.main --stage storm` | Optional storm‑filtered analysis (`Dst < -50 nT`); writes `results/storm_correlations.csv` with disclaimer. |
| **validate** | `python -m src.code.main --stage validate` | Runs analysis on 2018‑2020 hold‑out, creates `validation_report.md`. |
| **report** | `python -m src.code.main --stage report` | Generates PNG visualisations (`figures/`) and updates the Markdown report. |
| **test** | `python -m pytest tests/ -v` | Executes unit, integration, and contract tests. |

If any fetch step fails, the pipeline aborts with a clear error naming the missing variable or unreachable source (SC‑002). No synthetic fall‑backs are used – real data are required for scientific validity.

---
