# Execution failures — fix these before the analysis can run

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python src/data/download.py`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 5 command(s) failed: python src/data/download.py (rc=1); python src/data/validate.py (rc=2); python code/src/data/clean.py (rc=1)

## Failing / missing run-book commands

- python src/data/download.py -> rc=1

2026-10-18 18:28:24,248 INFO __main__: Starting VAERS data download
2026-10-18 18:28:24,248 INFO __main__: Downloading https://vaers.hhs.gov/data/datasets/2020VAERSDATA.csv.zip
2026-10-18 18:28:24,334 ERROR __main__: Failed to download https://vaers.hhs.gov/data/datasets/2020VAERSDATA.csv.zip: 404 Client Error: Not Found for url: https://vaers.hhs.gov/data/datasets/2020VAERSDATA.csv.zip
2026-10-18 18:28:24,334 ERROR __main__: Failed to process year 2020: 404 Client Error: Not Found for url: https://vaers.hhs.gov/data/datasets/2020VAERSDATA.csv.zip

- python src/data/validate.py -> rc=2
2026-10-18 18:28:24,713 - validate - INFO - Loading schema from contracts/dataset.schema.yaml
2026-10-18 18:28:24,716 - validate - INFO - Loading data from data/processed/cleaned_vaers.parquet
2026-10-18 18:28:24,716 - validate - ERROR - Data file not found: data/processed/cleaned_vaers.parquet


- python code/src/data/clean.py -> rc=1

2026-10-18 18:28:25,125 - clean - INFO - Starting data cleaning process
2026-10-18 18:28:25,125 - clean - ERROR - No VAERS CSV files found in /home/runner/work/llmXive/llmXive/projects/PROJ-305-statistical-analysis-of-publicly-availab/code/data/raw

- python src/main.py -> rc=1
2026-10-18 18:28:25,736 - matplotlib.font_manager - INFO - Failed to extract font properties from /usr/share/fonts/truetype/noto/NotoColorEmoji.ttf: In FT2Font: Can not load face (unknown file format; error code 0x2)
2026-10-18 18:28:25,795 - matplotlib.font_manager - INFO - generated new fontManager
2026-10-18 18:28:26,053 - pipeline - INFO - No action specified. Use --full or --phase N


- python -m pytest -q tests/contract/ -> rc=4

no tests ran in 0.00s

ERROR: file or directory not found: tests/contract/


