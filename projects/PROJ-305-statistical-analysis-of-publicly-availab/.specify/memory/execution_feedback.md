# Execution failures — fix these before the analysis can run

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python src/data/download.py`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 command(s) failed: python src/data/download.py (rc=1); python src/data/validate.py (rc=2); python src/main.py (rc=1); 2 declared deliverable(s) absent: data/meddra_soc_mapping.csv; data/processed/cleaned_vaers.parquet

## Failing / missing run-book commands

- python src/data/download.py -> rc=1
NING:__main__:Checksum file not found for vaersdata2021.csv, skipping verification
INFO:__main__:Downloading https://vaers.hhs.gov/data/datasets/vaersdata2021.csv to data/raw/vaersdata2021.csv
ERROR:__main__:Failed to download https://vaers.hhs.gov/data/datasets/vaersdata2021.csv: 404 Client Error: Not Found for url: https://vaers.hhs.gov/data/datasets/vaersdata2021.csv
WARNING:__main__:Checksum file not found for vaersdata2022.csv, skipping verification
INFO:__main__:Downloading https://vaers.hhs.gov/data/datasets/vaersdata2022.csv to data/raw/vaersdata2022.csv
ERROR:__main__:Failed to download https://vaers.hhs.gov/data/datasets/vaersdata2022.csv: 404 Client Error: Not Found for url: https://vaers.hhs.gov/data/datasets/vaersdata2022.csv
WARNING:__main__:Checksum file not found for vaersdata2023.csv, skipping verification
INFO:__main__:Downloading https://vaers.hhs.gov/data/datasets/vaersdata2023.csv to data/raw/vaersdata2023.csv
ERROR:__main__:Failed to download https://vaers.hhs.gov/data/datasets/vaersdata2023.csv: 404 Client Error: Not Found for url: https://vaers.hhs.gov/data/datasets/vaersdata2023.csv
ERROR:__main__:Failed to download data for years: [2020, 2021, 2022, 2023]

- python src/data/validate.py -> rc=2
2026-10-12 02:27:16,048 - validate - INFO - Loading schema from contracts/dataset.schema.yaml
2026-10-12 02:27:16,051 - validate - INFO - Loading data from data/processed/cleaned_vaers.parquet
2026-10-12 02:27:16,051 - validate - ERROR - Data file not found: data/processed/cleaned_vaers.parquet


- python src/main.py -> rc=1
2026-10-12 02:27:16,762 - matplotlib.font_manager - INFO - Failed to extract font properties from /usr/share/fonts/truetype/noto/NotoColorEmoji.ttf: In FT2Font: Can not load face (unknown file format; error code 0x2)
2026-10-12 02:27:16,894 - matplotlib.font_manager - INFO - generated new fontManager
2026-10-12 02:27:17,172 - pipeline - INFO - No action specified. Use --full or --phase N



## Declared deliverables still missing

- data/meddra_soc_mapping.csv
- data/processed/cleaned_vaers.parquet

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/meddra_soc_mapping.csv` is declared but was NOT written. Scripts referencing it:
    - `code/src/data/clean.py` — NOT invoked by the run-book
    - `code/src/data/download_meddra.py` — NOT invoked by the run-book
    - `code/src/utils/config.py` — NOT invoked by the run-book
    - `code/tests/unit/test_clean.py` — NOT invoked by the run-book
    - `code/tests/unit/test_download_meddra.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/meddra_soc_mapping.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/cleaned_vaers.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/src/analysis/disproportionality.py` — NOT invoked by the run-book
    - `code/src/analysis/sensitivity.py` — NOT invoked by the run-book
    - `code/src/analysis/signal_output.py` — NOT invoked by the run-book
    - `code/src/data/clean.py` — NOT invoked by the run-book
    - `src/analysis/disproportionality.py` — NOT invoked by the run-book
    - `src/data/validate.py` — IS a run-book command
    - `src/main.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/cleaned_vaers.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
