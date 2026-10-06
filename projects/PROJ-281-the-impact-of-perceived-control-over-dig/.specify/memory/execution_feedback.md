# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/profiling.py --check-only`
  - script usage: `profiling.py [-h] [--sample-size SAMPLE_SIZE] [--no-enforce-limit]`
  - argparse error: `profiling.py: error: unrecognized arguments: --check-only`
- run-book command: `python code/profiling.py --output data/processed/custom_report.json`
  - script usage: `profiling.py [-h] [--sample-size SAMPLE_SIZE] [--no-enforce-limit]`
  - argparse error: `profiling.py: error: unrecognized arguments: --output data/processed/custom_report.json`

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python code/services/data_ingestion.py`
- `python code/profiling.py`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 6 command(s) failed: python code/main.py (rc=1); python code/services/data_ingestion.py (rc=1); python code/services/anxiety_scoring.py (rc=1); 7 declared deliverable(s) absent: data/processed/correlation_plot.png; data/processed/coverage_report.json; data/processed/final_analysis.csv

## Failing / missing run-book commands

- python code/main.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-281-the-impact-of-perceived-control-over-dig/code/main.py", line 13, in <module>
    from code.config import Config, RuntimeLimitExceededError
ImportError: cannot import name 'RuntimeLimitExceededError' from 'code.config' (/home/runner/work/llmXive/llmXive/projects/PROJ-281-the-impact-of-perceived-control-over-dig/code/config.py)
- python code/services/data_ingestion.py -> rc=1
    - __main__ - INFO - Starting data ingestion pipeline
2026-10-06 04:11:27,382 - __main__ - INFO - Downloading dataset: cardiffnlp/tweet_sentiment_extraction (split=train, revision=main)
2026-10-06 04:11:27,382 - __main__ - INFO - Loading with streaming=True to sample 10000 rows
2026-10-06 04:11:27,445 - httpx2 - INFO - HTTP Request: GET https://huggingface.co/api/agent-harnesses "HTTP/1.1 200 OK"
2026-10-06 04:11:27,464 - httpx2 - INFO - HTTP Request: HEAD https://huggingface.co/datasets/cardiffnlp/tweet_sentiment_extraction/resolve/main/README.md "HTTP/1.1 401 Unauthorized"
2026-10-06 04:11:27,465 - __main__ - ERROR - Failed to download dataset: Dataset 'cardiffnlp/tweet_sentiment_extraction' doesn't exist on the Hub or cannot be accessed.
2026-10-06 04:11:27,465 - __main__ - ERROR - Ingestion pipeline failed: Failed to download dataset cardiffnlp/tweet_sentiment_extraction: Dataset 'cardiffnlp/tweet_sentiment_extraction' doesn't exist on the Hub or cannot be accessed.
2026-10-06 04:11:27,465 - __main__ - ERROR - Failed: Failed to download dataset cardiffnlp/tweet_sentiment_extraction: Dataset 'cardiffnlp/tweet_sentiment_extraction' doesn't exist on the Hub or cannot be accessed.
- python code/services/anxiety_scoring.py -> rc=1
    INFO:__main__:Loading input data from data/processed/preprocessed_text.csv
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-281-the-impact-of-perceived-control-over-dig/code/services/anxiety_scoring.py", line 351, in <module>
    run_full_scoring_pipeline_from_config()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-281-the-impact-of-perceived-control-over-dig/code/services/anxiety_scoring.py", line 347, in run_full_scoring_pipeline_from_config
    return run_full_scoring_pipeline(input_path, output_path, config)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-281-the-impact-of-perceived-control-over-dig/code/services/anxiety_scoring.py", line 316, in run_full_scoring_pipeline
    raise FileNotFoundError(f"Input file not found: {input_path}")
FileNotFoundError: Input file not found: data/processed/preprocessed_text.csv
- python code/profiling.py -> rc=1
    ode.services.data_ingestion - INFO - Loading with streaming=True to sample 10000 rows
2026-10-06 04:11:33,186 - httpx2 - INFO - HTTP Request: HEAD https://huggingface.co/datasets/cardiffnlp/tweet_sentiment_extraction/resolve/main/README.md "HTTP/1.1 401 Unauthorized"
2026-10-06 04:11:33,187 - code.services.data_ingestion - ERROR - Failed to download dataset: Dataset 'cardiffnlp/tweet_sentiment_extraction' doesn't exist on the Hub or cannot be accessed.
2026-10-06 04:11:33,187 - code.services.data_ingestion - ERROR - Ingestion pipeline failed: Failed to download dataset cardiffnlp/tweet_sentiment_extraction: Dataset 'cardiffnlp/tweet_sentiment_extraction' doesn't exist on the Hub or cannot be accessed.
2026-10-06 04:11:33,187 - __main__ - INFO - Stage 1 completed in 0.06s
2026-10-06 04:11:33,187 - __main__ - INFO - Starting Stage 2: Preprocessing & Anxiety Scoring
2026-10-06 04:11:33,187 - __main__ - ERROR - Pipeline failed: run_full_scoring_pipeline() missing 2 required positional arguments: 'input_path' and 'output_path'
2026-10-06 04:11:33,187 - __main__ - ERROR - Pipeline failed: run_full_scoring_pipeline() missing 2 required positional arguments: 'input_path' and 'output_path'
- python code/profiling.py --check-only -> rc=2
    usage: profiling.py [-h] [--sample-size SAMPLE_SIZE] [--no-enforce-limit]
profiling.py: error: unrecognized arguments: --check-only
- python code/profiling.py --output data/processed/custom_report.json -> rc=2
    usage: profiling.py [-h] [--sample-size SAMPLE_SIZE] [--no-enforce-limit]
profiling.py: error: unrecognized arguments: --output data/processed/custom_report.json

## Declared deliverables still missing

- data/processed/correlation_plot.png
- data/processed/coverage_report.json
- data/processed/final_analysis.csv
- data/processed/preprocessed_text.csv
- data/processed/proxy_results.csv
- data/processed/scoring_results.csv
- data/raw/social_media.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/correlation_plot.png` is declared but was NOT written. Scripts referencing it:
    - `code/viz/save_visualization.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/correlation_plot.png` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/coverage_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/services/coverage_validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/coverage_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/final_analysis.csv` is declared but was NOT written. Scripts referencing it:
    - `code/profiling.py` — IS a run-book command
    - `code/services/merge_and_save.py` — NOT invoked by the run-book
    - `code/services/__init__.py` — NOT invoked by the run-book
    - `code/viz/plot_results.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/final_analysis.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/preprocessed_text.csv` is declared but was NOT written. Scripts referencing it:
    - `code/services/anxiety_scoring.py` — IS a run-book command
    - `code/services/coverage_validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/preprocessed_text.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/proxy_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/services/merge_and_save.py` — NOT invoked by the run-book
    - `code/services/proxy_saver.py` — NOT invoked by the run-book
    - `code/services/proxy_extractor.py` — IS a run-book command
    - `code/services/__init__.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/proxy_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/scoring_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/services/merge_and_save.py` — NOT invoked by the run-book
    - `code/services/anxiety_scoring.py` — IS a run-book command
    - `code/services/scoring_saver.py` — NOT invoked by the run-book
    - `code/services/coverage_validation.py` — NOT invoked by the run-book
    - `code/services/__init__.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/scoring_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/social_media.csv` is declared but was NOT written. Scripts referencing it:
    - `code/profiling.py` — IS a run-book command
    - `code/services/data_ingestion.py` — IS a run-book command
    - `code/services/proxy_extractor.py` — IS a run-book command
  Make ONE of these WRITE `data/raw/social_media.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `data/processed/preprocessed_text.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/services/anxiety_scoring.py`, `code/services/coverage_validation.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/processed/preprocessed_text.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/services/anxiety_scoring.py`, `code/services/coverage_validation.py`.
