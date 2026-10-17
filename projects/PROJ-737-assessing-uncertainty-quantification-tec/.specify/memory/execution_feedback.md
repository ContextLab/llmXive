# Execution failures — fix these before the analysis can run

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python -m code.main --thin`
- `python code/main.py  --max-samples 2000  --mc-dropout-passes 50  --ensemble-size 3  --coverage-sweep-start 0.80  --coverage-sweep-stop 0.99  --coverage-sweep-step 0.01  --seed 42`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 command(s) failed: python -m code.main --thin (rc=1); python code/main.py  --max-samples 2000  --mc-dropout-passes 50  --ensemble-size 3  --coverage-sweep-start 0.80  --coverage-sweep-stop 0.99  --coverage-sweep-step 0.01  --seed 42 (rc=1); 4 declared deliverable(s) absent: data/results/cost_metrics.csv; data/results/metrics_raw.csv; data/results/pipeline_log.csv

## Failing / missing run-book commands

- python -m code.main --thin -> rc=1
 created successfully.
2026-10-17 17:16:11,744 INFO __main__: Downloading raw datasets (if not present).
2026-10-17 17:16:11,744 INFO download: Downloading https://huggingface.co/datasets/oqmd/band_gap/resolve/main/band_gap.csv
Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-737-assessing-uncertainty-quantification-tec/code/main.py", line 363, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-737-assessing-uncertainty-quantification-tec/code/main.py", line 223, in main
    download_all()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-737-assessing-uncertainty-quantification-tec/code/download.py", line 145, in download_all
    _download_csv(info["url"], csv_path)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-737-assessing-uncertainty-quantification-tec/code/download.py", line 120, in _download_csv
    raise RuntimeError(f"Failed to download {url}: HTTP {response.status_code}")
RuntimeError: Failed to download https://huggingface.co/datasets/oqmd/band_gap/resolve/main/band_gap.csv: HTTP 401

- python code/main.py  --max-samples 2000  --mc-dropout-passes 50  --ensemble-size 3  --coverage-sweep-start 0.80  --coverage-sweep-stop 0.99  --coverage-sweep-step 0.01  --seed 42 -> rc=1
ple_errors.schema.yaml
2026-10-17 17:16:14,098 INFO create_skeleton: Project skeleton verified and schema created successfully.
2026-10-17 17:16:14,098 INFO __main__: Downloading raw datasets (if not present).
2026-10-17 17:16:14,098 INFO download: Downloading https://huggingface.co/datasets/oqmd/band_gap/resolve/main/band_gap.csv
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-737-assessing-uncertainty-quantification-tec/code/main.py", line 363, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-737-assessing-uncertainty-quantification-tec/code/main.py", line 223, in main
    download_all()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-737-assessing-uncertainty-quantification-tec/code/download.py", line 145, in download_all
    _download_csv(info["url"], csv_path)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-737-assessing-uncertainty-quantification-tec/code/download.py", line 120, in _download_csv
    raise RuntimeError(f"Failed to download {url}: HTTP {response.status_code}")
RuntimeError: Failed to download https://huggingface.co/datasets/oqmd/band_gap/resolve/main/band_gap.csv: HTTP 401


## Declared deliverables still missing

- data/results/cost_metrics.csv
- data/results/metrics_raw.csv
- data/results/pipeline_log.csv
- data/results/uq_methods.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/results/cost_metrics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/pipeline.py` — NOT invoked by the run-book
    - `code/tests/test_full_pipeline.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/cost_metrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/metrics_raw.csv` is declared but was NOT written. Scripts referencing it:
    - `code/generate_metrics_raw.py` — NOT invoked by the run-book
    - `code/metrics/generate_metrics_raw.py` — NOT invoked by the run-book
    - `code/tests/test_metrics.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/metrics_raw.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/pipeline_log.csv` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/pipeline.py` — NOT invoked by the run-book
    - `code/tests/test_full_pipeline.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/pipeline_log.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/uq_methods.csv` is declared but was NOT written. Scripts referencing it:
    - `code/pipeline.py` — NOT invoked by the run-book
    - `code/tests/test_full_pipeline.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/uq_methods.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
