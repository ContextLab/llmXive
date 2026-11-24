# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/analysis/sensitivity_analysis.py: self-declared fabricated metric — “…this iteration to avoid empty/fake results.             logger.warning(…”
- code/strategies/noisy_baseline_runner.py: self-declared fabricated metric — “…nce.")             # Return a placeholder result for testing without model…”
- code/analysis/sensitivity_analysis.py: synthetic/fake INPUT data not authorized by the spec — “…the task implies we must generate synthetic sensitivity curves…”
- code/benchmark_full_traversal.py: synthetic/fake INPUT data not authorized by the spec — “…rategy.  This script: 1. Generates a synthetic memory graph of varying…”
- code/benchmark_full_traversal.py: synthetic/fake INPUT data not authorized by the spec — “…nx.DiGraph:     """     Generates a synthetic directed graph for bench…”
- code/data/download_locomo.py: synthetic/fake INPUT data not authorized by the spec — “…lls back to synthetic or mock data.     """     from datase…”

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/processed/stats_report.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/runner.py --strategy full`
  - script usage: `runner.py [-h] --strategy {Full,Lazy,Greedy} --input INPUT --output`
  - argparse error: `runner.py: error: argument --strategy: invalid choice: 'full' (choose from 'Full', 'Lazy', 'Greedy')`
- run-book command: `python code/runner.py --strategy lazy --sweep`
  - script usage: `runner.py [-h] --strategy {Full,Lazy,Greedy} --input INPUT --output`
  - argparse error: `runner.py: error: argument --strategy: invalid choice: 'lazy' (choose from 'Full', 'Lazy', 'Greedy')`
- run-book command: `python code/runner.py --strategy greedy`
  - script usage: `runner.py [-h] --strategy {Full,Lazy,Greedy} --input INPUT --output`
  - argparse error: `runner.py: error: argument --strategy: invalid choice: 'greedy' (choose from 'Full', 'Lazy', 'Greedy')`

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python code/data/download_locomo.py`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 6 fabricated/simulated-result signal(s) — results are not real measurements: code/analysis/sensitivity_analysis.py: self-declared fabricated metric — “…this iteration to avoid empty/fake results.             logger.warning(…”; code/strategies/noisy_baseline_runner.py: self-declared fabricated metric — “…nce.")             # Return a placeholder result for testing without model…”; code/analysis/sensitivity_analysis.py: synthetic/fake INPUT data not authorized by the spec — “…the task implies we must generate synthetic sensitivity curves…”; every produced artifact is gitignored (data/processed/stats_report.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 1 run-book script(s) missing (plan/impl path mismatch): python code/scripts/generate_stats_report.py; 7 command(s) failed: python code/data/download_locomo.py (rc=1); python code/scripts/generate_noisy_graphs.py (rc=1); python code/scripts/generate_noisy_graphs.py (rc=1); 11 declared deliverable(s) absent: data/intermediate/graphs_raw.json; data/processed/baseline_results.csv; data/processed/greedy_results.csv

## Failing / missing run-book commands

- python code/data/download_locomo.py -> rc=1
ry-is-re/lib/python3.11/site-packages/datasets/load.py", line 2592, in load_dataset
    builder_instance = load_dataset_builder(
                       ^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-894-llmxive-follow-up-extending-memory-is-re/lib/python3.11/site-packages/datasets/load.py", line 2264, in load_dataset_builder
    dataset_module = dataset_module_factory(
                     ^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-894-llmxive-follow-up-extending-memory-is-re/lib/python3.11/site-packages/datasets/load.py", line 1909, in dataset_module_factory
    raise e1 from None
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-894-llmxive-follow-up-extending-memory-is-re/lib/python3.11/site-packages/datasets/load.py", line 1855, in dataset_module_factory
    raise DatasetNotFoundError(
datasets.exceptions.DatasetNotFoundError: Dataset 'snap-research/locomo' doesn't exist on the Hub or cannot be accessed. If the dataset is private or gated, make sure to log in with `huggingface-cli login` or visit the dataset page at https://huggingface.co/datasets/snap-research/locomo to ask for access.

- python code/scripts/generate_noisy_graphs.py -> rc=1

2026-10-20 16:57:47,565 - __main__ - INFO - Loading clean graphs from data/intermediate/graphs_raw.json
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/code/scripts/generate_noisy_graphs.py", line 154, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/code/scripts/generate_noisy_graphs.py", line 145, in main
    generate_noisy_graphs(
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/code/scripts/generate_noisy_graphs.py", line 51, in generate_noisy_graphs
    raise FileNotFoundError(
FileNotFoundError: Input file not found: data/intermediate/graphs_raw.json. Please ensure T011a-1b-serialize has been completed.

- python code/scripts/generate_noisy_graphs.py -> rc=1

2026-10-20 16:57:50,339 - __main__ - INFO - Loading clean graphs from data/intermediate/graphs_raw.json
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/code/scripts/generate_noisy_graphs.py", line 154, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/code/scripts/generate_noisy_graphs.py", line 145, in main
    generate_noisy_graphs(
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/code/scripts/generate_noisy_graphs.py", line 51, in generate_noisy_graphs
    raise FileNotFoundError(
FileNotFoundError: Input file not found: data/intermediate/graphs_raw.json. Please ensure T011a-1b-serialize has been completed.

- python code/runner.py --strategy full -> rc=2

usage: runner.py [-h] --strategy {Full,Lazy,Greedy} --input INPUT --output
                 OUTPUT [--threshold THRESHOLD] [--noisy] [--timeout TIMEOUT]
runner.py: error: argument --strategy: invalid choice: 'full' (choose from 'Full', 'Lazy', 'Greedy')

- python code/runner.py --strategy lazy --sweep -> rc=2

usage: runner.py [-h] --strategy {Full,Lazy,Greedy} --input INPUT --output
                 OUTPUT [--threshold THRESHOLD] [--noisy] [--timeout TIMEOUT]
runner.py: error: argument --strategy: invalid choice: 'lazy' (choose from 'Full', 'Lazy', 'Greedy')

- python code/runner.py --strategy greedy -> rc=2

usage: runner.py [-h] --strategy {Full,Lazy,Greedy} --input INPUT --output
                 OUTPUT [--threshold THRESHOLD] [--noisy] [--timeout TIMEOUT]
runner.py: error: argument --strategy: invalid choice: 'greedy' (choose from 'Full', 'Lazy', 'Greedy')

- python code/scripts/generate_stats_report.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-894-llmxive-follow-up-extending-memory-is-re/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/code/scripts/generate_stats_report.py': [Errno 2] No such file or directory

- python -m pytest tests/ -> rc=2
odule
    return _bootstrap._gcd_import(name[level:], package, level)
tests/unit/test_validate_streaming.py:12: in <module>
    from utils.validate_streaming import get_memory_usage_mb, run_streaming_validation
code/utils/validate_streaming.py:13: in <module>
    from runner import process_in_chunks, save_results_to_csv, main as runner_main
E   ImportError: cannot import name 'process_in_chunks' from 'runner' (/home/runner/work/llmXive/llmXive/projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/code/runner.py)
=========================== short test summary info ============================
ERROR tests/integration/test_data_pipeline.py
ERROR tests/unit/test_audit_data_loader.py
ERROR tests/unit/test_baseline_runner.py
ERROR tests/unit/test_data_loader.py
ERROR tests/unit/test_data_loader_noisy.py
ERROR tests/unit/test_data_loader_silent_fallback.py
ERROR tests/unit/test_data_loader_streaming.py
ERROR tests/unit/test_oom_streaming_fallback.py
ERROR tests/unit/test_stats.py
ERROR tests/unit/test_validate_streaming.py
!!!!!!!!!!!!!!!!!!! Interrupted: 10 errors during collection !!!!!!!!!!!!!!!!!!!
============================== 10 errors in 3.34s ==============================



## Declared deliverables still missing

- data/intermediate/graphs_raw.json
- data/processed/baseline_results.csv
- data/processed/greedy_results.csv
- data/processed/lazy_results.csv
- data/processed/noisy_baseline_results.csv
- data/processed/noisy_lazy_results.csv
- data/processed/report_data.json
- data/processed/sensitivity_analysis.json
- data/processed/stats_clean.json
- data/processed/stats_noisy.json
- data/raw/locomo.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/intermediate/graphs_raw.json` is declared but was NOT written. Scripts referencing it:
    - `code/data_loader.py` — NOT invoked by the run-book
    - `code/run_greedy.py` — NOT invoked by the run-book
    - `code/run_lazy.py` — NOT invoked by the run-book
    - `code/runner.py` — IS a run-book command
    - `code/scripts/generate_noisy_graphs.py` — IS a run-book command
    - `code/strategies/baseline_runner.py` — NOT invoked by the run-book
    - `code/utils/verify_seeds.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/intermediate/graphs_raw.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/baseline_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/correlation_analysis.py` — NOT invoked by the run-book
    - `code/analysis/noisy_stats.py` — NOT invoked by the run-book
    - `code/analysis/power_analysis.py` — NOT invoked by the run-book
    - `code/analysis/sensitivity_analysis.py` — NOT invoked by the run-book
    - `code/analysis/stats.py` — IS a run-book command
    - `code/analysis/threshold_analysis.py` — NOT invoked by the run-book
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/report/categorize_status_counts.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/baseline_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/greedy_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/correlation_analysis.py` — NOT invoked by the run-book
    - `code/analysis/noisy_stats.py` — NOT invoked by the run-book
    - `code/analysis/power_analysis.py` — NOT invoked by the run-book
    - `code/analysis/stats.py` — IS a run-book command
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/report/categorize_status_counts.py` — NOT invoked by the run-book
    - `code/run_greedy.py` — NOT invoked by the run-book
    - `code/strategies/greedy_runner.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/greedy_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/lazy_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/correlation_analysis.py` — NOT invoked by the run-book
    - `code/analysis/noisy_stats.py` — NOT invoked by the run-book
    - `code/analysis/power_analysis.py` — NOT invoked by the run-book
    - `code/analysis/sensitivity_analysis.py` — NOT invoked by the run-book
    - `code/analysis/stats.py` — IS a run-book command
    - `code/analysis/threshold_analysis.py` — NOT invoked by the run-book
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/report/categorize_status_counts.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/lazy_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/noisy_baseline_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/correlation_analysis.py` — NOT invoked by the run-book
    - `code/analysis/noisy_stats.py` — NOT invoked by the run-book
    - `code/analysis/power_analysis.py` — NOT invoked by the run-book
    - `code/analysis/stats.py` — IS a run-book command
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/report/categorize_status_counts.py` — NOT invoked by the run-book
    - `code/run_noisy_baseline.py` — NOT invoked by the run-book
    - `code/strategies/noisy_baseline_runner.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/noisy_baseline_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/noisy_lazy_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/noisy_stats.py` — NOT invoked by the run-book
    - `code/analysis/stats.py` — IS a run-book command
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/report/categorize_status_counts.py` — NOT invoked by the run-book
    - `code/strategies/noisy_lazy_runner.py` — NOT invoked by the run-book
    - `code/utils/validate_results.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/noisy_lazy_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/report_data.json` is declared but was NOT written. Scripts referencing it:
    - `code/report/aggregate_results.py` — NOT invoked by the run-book
    - `code/report/generate_report.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/report_data.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/sensitivity_analysis.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/__init__.py` — NOT invoked by the run-book
    - `code/analysis/report_generator.py` — NOT invoked by the run-book
    - `code/analysis/sensitivity_analysis.py` — NOT invoked by the run-book
    - `code/strategies/lazy.py` — NOT invoked by the run-book
    - `code/strategies/sweep_runner.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/sensitivity_analysis.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/stats_clean.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/power_analysis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/stats_clean.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/stats_noisy.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/power_analysis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/stats_noisy.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/locomo.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data/download_locomo.py` — IS a run-book command
    - `code/data_loader.py` — NOT invoked by the run-book
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/run_lazy.py` — NOT invoked by the run-book
    - `code/run_noisy_baseline.py` — NOT invoked by the run-book
    - `code/scripts/download_locomo.py` — NOT invoked by the run-book
    - `code/strategies/baseline_runner.py` — NOT invoked by the run-book
    - `code/strategies/noisy_baseline_runner.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/locomo.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
