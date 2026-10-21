# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/src/evaluation/reporting.py: self-declared fabricated metric — “…ld load them here.          # Simulated metrics based on typical outputs fro…”
- code/verify_artifacts.py: self-declared fabricated metric — “…# Check for obvious placeholder values         # Common fabrication…”
- code/verify_artifacts.py: self-declared fabricated metric — “…olumn '{col}' contains likely placeholder value: {val}")                 elif…”
- code/verify_artifacts.py: self-declared fabricated metric — “…"Column '{col}' contains only placeholder value: {val}")             elif df[…”

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/processed/dummy_poll.csv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 fabricated/simulated-result signal(s) — results are not real measurements: code/src/evaluation/reporting.py: self-declared fabricated metric — “…ld load them here.          # Simulated metrics based on typical outputs fro…”; code/verify_artifacts.py: self-declared fabricated metric — “…# Check for obvious placeholder values         # Common fabrication…”; code/verify_artifacts.py: self-declared fabricated metric — “…olumn '{col}' contains likely placeholder value: {val}")                 elif…”; every produced artifact is gitignored (data/processed/dummy_poll.csv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 4 command(s) failed: python src/data/download.py (rc=1); python src/data/harmonize.py (rc=1); python code/src/main.py --run-all (rc=1); 4 declared deliverable(s) absent: data/processed/bayesian_forecasts.csv; data/processed/frequentist_forecasts.csv; data/processed/meta_analysis_results.csv

## Failing / missing run-book commands

- python src/data/download.py -> rc=1

WARNING (pytensor.tensor.blas): Using NumPy C-API based implementation for BLAS functions.
2026-10-21 06:33:34 - __main__ - INFO - Starting data acquisition (T006).
2026-10-21 06:33:34 - __main__ - WARNING - RealClearPolitics (RCP) data is excluded from the pipeline per project constraints.
2026-10-21 06:33:34 - __main__ - INFO - Downloading CSV from https://raw.githubusercontent.com/fivethirtyeight/pollster-data/master/polls.csv
2026-10-21 06:33:34 - __main__ - ERROR - Network error while fetching https://raw.githubusercontent.com/fivethirtyeight/pollster-data/master/polls.csv: 404 Client Error: Not Found for url: https://raw.githubusercontent.com/fivethirtyeight/pollster-data/master/polls.csv
2026-10-21 06:33:34 - __main__ - ERROR - Critical: Failed to fetch FiveThirtyEight poll data. Aborting.

- python src/data/harmonize.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-206-statistical-analysis-of-publicly-availab/src/data/harmonize.py", line 12, in <module>
    from src.utils.logging import get_logger
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-206-statistical-analysis-of-publicly-availab/code/src/utils/logging.py", line 97, in <module>
    def set_log_level(level: Union[str, int]) -> None:
                             ^^^^^
NameError: name 'Union' is not defined

- python code/src/main.py --run-all -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-206-statistical-analysis-of-publicly-availab/code/src/main.py", line 9, in <module>
    from src.utils.logging import get_logger
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-206-statistical-analysis-of-publicly-availab/code/src/utils/logging.py", line 97, in <module>
    def set_log_level(level: Union[str, int]) -> None:
                             ^^^^^
NameError: name 'Union' is not defined

- python code/src/evaluation/metrics.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-206-statistical-analysis-of-publicly-availab/code/src/evaluation/metrics.py", line 14, in <module>
    from src.utils.logging import get_logger
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-206-statistical-analysis-of-publicly-availab/code/src/utils/logging.py", line 97, in <module>
    def set_log_level(level: Union[str, int]) -> None:
                             ^^^^^
NameError: name 'Union' is not defined


## Declared deliverables still missing

- data/processed/bayesian_forecasts.csv
- data/processed/frequentist_forecasts.csv
- data/processed/meta_analysis_results.csv
- data/processed/poll_data_cleaned.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/bayesian_forecasts.csv` is declared but was NOT written. Scripts referencing it:
    - `code/code/verify_artifacts.py` — NOT invoked by the run-book
    - `code/create_data_hierarchy.py` — NOT invoked by the run-book
    - `code/src/evaluation/metrics.py` — IS a run-book command
    - `code/src/models/bayesian.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/bayesian_forecasts.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/frequentist_forecasts.csv` is declared but was NOT written. Scripts referencing it:
    - `code/code/verify_artifacts.py` — NOT invoked by the run-book
    - `code/create_data_hierarchy.py` — NOT invoked by the run-book
    - `code/src/evaluation/meta_analysis.py` — NOT invoked by the run-book
    - `code/src/evaluation/metrics.py` — IS a run-book command
    - `code/src/models/frequentist.py` — NOT invoked by the run-book
    - `code/tests/unit/test_metrics.py` — NOT invoked by the run-book
    - `code/validate_schemas.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/frequentist_forecasts.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/meta_analysis_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/src/evaluation/meta_analysis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/meta_analysis_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/poll_data_cleaned.csv` is declared but was NOT written. Scripts referencing it:
    - `code/code/verify_artifacts.py` — NOT invoked by the run-book
    - `code/create_data_hierarchy.py` — NOT invoked by the run-book
    - `code/src/data/harmonize.py` — NOT invoked by the run-book
    - `code/src/data/weights.py` — NOT invoked by the run-book
    - `code/src/models/bayesian.py` — NOT invoked by the run-book
    - `code/src/models/frequentist.py` — NOT invoked by the run-book
    - `code/src/utils/state_manager.py` — NOT invoked by the run-book
    - `code/validate_schemas.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/poll_data_cleaned.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `.github/`, `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
