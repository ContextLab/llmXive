# Quickstart

Run the full pipeline with the following command:

```bash
python -m code.main --stage all
```

This executes every stage in order: fetch (real ACE/NOAA downloads), align
(writes `data/processed/synced.csv`), analyze (writes
`results/correlations.csv`), and validate (writes
`results/validation_correlations.csv`).

Individual stages can be run separately:

```bash
python -m code.main --stage fetch --start 1998-01-01 --end 2020-12-31
python -m code.main --stage align
python -m code.main --stage analyze --lags 0,1,2,3,6
python -m code.main --stage validate
```

Use `python -m code.main --help` for the full list of options.