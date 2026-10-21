# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/save_results.py: synthetic/fake INPUT data not authorized by the spec — “…sn't exist, as we cannot fake data.         # But wait, the…”

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/processed/preprocess_stats.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python code/ingest.py`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/save_results.py: synthetic/fake INPUT data not authorized by the spec — “…sn't exist, as we cannot fake data.         # But wait, the…”; every produced artifact is gitignored (data/processed/preprocess_stats.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 4 command(s) failed: python code/ingest.py (rc=1); python code/preprocess.py (rc=1); python code/report.py (rc=1); 3 declared deliverable(s) absent: data/processed/daily_aggregates.csv; data/processed/model_results.json; data/raw/bronze.parquet

## Failing / missing run-book commands

- python code/ingest.py -> rc=1
 url: /dataset/StudentLife_Dataset.zip (Caused by ConnectTimeoutError(<HTTPConnection(host='studentlife.cs.dartmouth.edu', port=80) at 0x7f3105da4310>, 'Connection to studentlife.cs.dartmouth.edu timed out. (connect timeout=30)'))

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-715-physical-activity-levels-and-mood-variab/code/ingest.py", line 335, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-715-physical-activity-levels-and-mood-variab/code/ingest.py", line 331, in main
    download_and_verify()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-715-physical-activity-levels-and-mood-variab/code/ingest.py", line 293, in download_and_verify
    raise RuntimeError(
RuntimeError: Failed to download the StudentLife dataset from any real source. Attempted sources and errors:
  - OSF (DOI 10.17605/OSF.IO/5B1A9) (https://osf.io/download/5b1a9f1b9ad5a10018669804/): download failed
  - Dartmouth StudentLife canonical (http://studentlife.cs.dartmouth.edu/dataset/StudentLife_Dataset.zip): download failed
No synthetic fallback is permitted; fix the network access or the source URLs in code/config.py and re-run.

- python code/preprocess.py -> rc=1
__main__ - ERROR - Preprocessing failed: Bronze data not found at /home/runner/work/llmXive/llmXive/projects/PROJ-715-physical-activity-levels-and-mood-variab/data/raw/bronze.parquet. Run T063/T007 first.

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-715-physical-activity-levels-and-mood-variab/code/preprocess.py", line 264, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-715-physical-activity-levels-and-mood-variab/code/preprocess.py", line 258, in main
    preprocess(data_source)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-715-physical-activity-levels-and-mood-variab/code/preprocess.py", line 229, in preprocess
    df_bronze = load_bronze_data()
                ^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-715-physical-activity-levels-and-mood-variab/code/preprocess.py", line 23, in load_bronze_data
    raise FileNotFoundError(f"Bronze data not found at {path}. Run T063/T007 first.")
FileNotFoundError: Bronze data not found at /home/runner/work/llmXive/llmXive/projects/PROJ-715-physical-activity-levels-and-mood-variab/data/raw/bronze.parquet. Run T063/T007 first.

- python code/report.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-715-physical-activity-levels-and-mood-variab/code/report.py", line 73, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-715-physical-activity-levels-and-mood-variab/code/report.py", line 70, in main
    generate_report()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-715-physical-activity-levels-and-mood-variab/code/report.py", line 59, in generate_report
    results = load_model_results()
              ^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-715-physical-activity-levels-and-mood-variab/code/report.py", line 16, in load_model_results
    raise FileNotFoundError(f"Model results file not found at {path}. Run analysis first.")
FileNotFoundError: Model results file not found at /home/runner/work/llmXive/llmXive/projects/PROJ-715-physical-activity-levels-and-mood-variab/data/processed/model_results.json. Run analysis first.

- python -m pytest tests/contract/ -> rc=3
ook_name, methods, kwargs, firstresult)
INTERNALERROR>            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
INTERNALERROR>   File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pluggy/_execution.py", line 195, in _multicall
INTERNALERROR>     raise exception
INTERNALERROR>   File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pluggy/_execution.py", line 147, in _multicall
INTERNALERROR>     res = hook_impl.function(*args)
INTERNALERROR>           ^^^^^^^^^^^^^^^^^^^^^^^^^
INTERNALERROR>   File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/_pytest/debugging.py", line 72, in pytest_configure
INTERNALERROR>     import pdb
INTERNALERROR>   File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/pdb.py", line 77, in <module>
INTERNALERROR>     import code
INTERNALERROR>   File "/home/runner/work/llmXive/llmXive/projects/PROJ-715-physical-activity-levels-and-mood-variab/code/__init__.py", line 8, in <module>
INTERNALERROR>     from .config import (
INTERNALERROR> ImportError: cannot import name 'BASE_DIR' from 'code.config' (/home/runner/work/llmXive/llmXive/projects/PROJ-715-physical-activity-levels-and-mood-variab/code/config.py)


## Declared deliverables still missing

- data/processed/daily_aggregates.csv
- data/processed/model_results.json
- data/raw/bronze.parquet

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/daily_aggregates.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis.py` — IS a run-book command
    - `code/output_validator.py` — NOT invoked by the run-book
    - `code/preprocess.py` — IS a run-book command
    - `code/report.py` — IS a run-book command
    - `code/save_daily_aggregates.py` — NOT invoked by the run-book
    - `code/validate_quickstart.py` — NOT invoked by the run-book
    - `code/verify_raw_mood_std.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/daily_aggregates.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/model_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis.py` — IS a run-book command
    - `code/config.py` — NOT invoked by the run-book
    - `code/report.py` — IS a run-book command
    - `code/save_results.py` — NOT invoked by the run-book
    - `code/validate_quickstart.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/model_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/bronze.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/config.py` — NOT invoked by the run-book
    - `code/ingest.py` — IS a run-book command
    - `code/preprocess.py` — IS a run-book command
    - `code/validate_quickstart.py` — NOT invoked by the run-book
    - `code/validate_raw.py` — NOT invoked by the run-book
    - `code/verify_raw_data.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/bronze.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
