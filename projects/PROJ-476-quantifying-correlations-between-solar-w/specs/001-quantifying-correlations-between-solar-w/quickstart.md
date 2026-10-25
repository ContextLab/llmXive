# Quickstart

Install pinned dependencies and run the full pipeline:

```bash
python -m pip install -r requirements.txt
# Example: user‑specified date range (defaults shown)
python -m code.main --stage all --start-date 1998-01-01 --end-date 2020-12-31
```

Stages (in order; each writes verifiable files):

```bash
# Fetch data for a **user‑specified** window (default shown above)
python -m code.main --stage fetch --start-date 1998-01-01 --end-date 2020-12-31

# Align and interpolate to 1‑hour UTC grid
python -m code.main --stage sync

# **Storm‑filtered** correlation analysis (Dst < -50 nT)
python -m code.main --stage analyze

# Detrending sensitivity checks (first‑difference & 27‑day detrended)
python -m code.main --stage detrend

# Validation on 2018‑2020 hold‑out (storm‑filtered)
python -m code.main --stage validate

# Generate figures (PNG ≤ 5 MB each)
python -m code.main --stage report
```

Run the test suite (unit + contract + integration):

```bash
python -m pytest tests/ -v
```

If `--stage fetch` fails, the pipeline aborts with an explicit error naming the missing variable or unreachable source; do not retry with fixture data — the study requires the real downloads.
