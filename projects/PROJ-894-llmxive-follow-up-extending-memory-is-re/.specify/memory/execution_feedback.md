# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/analysis/sensitivity_analysis.py: self-declared fabricated metric — “…this iteration to avoid empty/fake results.             logger.warning(…”
- code/analysis/sensitivity_analysis.py: synthetic/fake INPUT data not authorized by the spec — “…the task implies we must generate synthetic sensitivity curves…”
- code/benchmark_full_traversal.py: synthetic/fake INPUT data not authorized by the spec — “…rategy.  This script: 1. Generates a synthetic memory graph of varying…”
- code/benchmark_full_traversal.py: synthetic/fake INPUT data not authorized by the spec — “…nx.DiGraph:     """     Generates a synthetic directed graph for bench…”

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/processed/stats_report.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 fabricated/simulated-result signal(s) — results are not real measurements: code/analysis/sensitivity_analysis.py: self-declared fabricated metric — “…this iteration to avoid empty/fake results.             logger.warning(…”; code/analysis/sensitivity_analysis.py: synthetic/fake INPUT data not authorized by the spec — “…the task implies we must generate synthetic sensitivity curves…”; code/benchmark_full_traversal.py: synthetic/fake INPUT data not authorized by the spec — “…rategy.  This script: 1. Generates a synthetic memory graph of varying…”; every produced artifact is gitignored (data/processed/stats_report.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 5 command(s) failed: python code/data_loader.py --download (rc=1); python code/runner.py --strategy Full --input data/processed/graphs/graph_clean.json --output data/processed/results/baseline_results.csv (rc=1); python code/runner.py --strategy Lazy --input data/processed/graphs/graph_clean.json --output data/processed/results/lazy_results.csv --threshold 0.7 (rc=1); 11 declared deliverable(s) absent: data/intermediate/graphs_raw.json; data/processed/baseline_results.csv; data/processed/correlation_results.json

## Failing / missing run-book commands

- python code/data_loader.py --download -> rc=1
    File "/home/runner/work/llmXive/llmXive/projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/code/data_loader.py", line 105
    Args:
         ^
SyntaxError: invalid syntax
- python code/runner.py --strategy Full --input data/processed/graphs/graph_clean.json --output data/processed/results/baseline_results.csv -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/code/runner.py", line 34, in <module>
    from data_loader import load_graphs, load_noisy_graphs
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/code/data_loader.py", line 105
    Args:
         ^
SyntaxError: invalid syntax
- python code/runner.py --strategy Lazy --input data/processed/graphs/graph_clean.json --output data/processed/results/lazy_results.csv --threshold 0.7 -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/code/runner.py", line 34, in <module>
    from data_loader import load_graphs, load_noisy_graphs
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/code/data_loader.py", line 105
    Args:
         ^
SyntaxError: invalid syntax
- python code/runner.py --strategy Greedy --input data/processed/graphs/graph_clean.json --output data/processed/results/greedy_results.csv --topk 5 -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/code/runner.py", line 34, in <module>
    from data_loader import load_graphs, load_noisy_graphs
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/code/data_loader.py", line 105
    Args:
         ^
SyntaxError: invalid syntax
- python code/runner.py --strategy Lazy --input data/processed/graphs/graph_noise_42.json --output data/processed/results/lazy_noisy_results.csv --threshold 0.7 -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/code/runner.py", line 34, in <module>
    from data_loader import load_graphs, load_noisy_graphs
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/code/data_loader.py", line 105
    Args:
         ^
SyntaxError: invalid syntax

## Declared deliverables still missing

- data/intermediate/graphs_raw.json
- data/processed/baseline_results.csv
- data/processed/correlation_results.json
- data/processed/graphs/graph_noise_42.json
- data/processed/greedy_results.csv
- data/processed/lazy_results.csv
- data/processed/noisy_baseline_results.csv
- data/processed/report_data.json
- data/processed/statistical_results.json
- data/processed/status_counts.json
- data/processed/threshold_analysis.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/intermediate/graphs_raw.json` is declared but was NOT written. Scripts referencing it:
    - `code/data_loader.py` — IS a run-book command
    - `code/strategies/noisy_baseline_runner.py` — NOT invoked by the run-book
    - `code/strategies/baseline_runner.py` — NOT invoked by the run-book
    - `code/utils/verify_seeds.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/intermediate/graphs_raw.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/baseline_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/analysis/noisy_stats.py` — NOT invoked by the run-book
    - `code/analysis/correlation_analysis.py` — NOT invoked by the run-book
    - `code/analysis/stats.py` — IS a run-book command
    - `code/analysis/threshold_analysis.py` — NOT invoked by the run-book
    - `code/analysis/sensitivity_analysis.py` — NOT invoked by the run-book
    - `code/analysis/power_analysis.py` — NOT invoked by the run-book
    - `code/strategies/noisy_baseline_runner.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/baseline_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/correlation_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/correlation_analysis.py` — NOT invoked by the run-book
    - `code/report/aggregate_results.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/correlation_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/graphs/graph_noise_42.json` is declared but was NOT written. Scripts referencing it:
    - `code/data_loader.py` — IS a run-book command
    - `code/strategies/noisy_lazy_runner.py` — NOT invoked by the run-book
    - `code/strategies/noisy_baseline_runner.py` — NOT invoked by the run-book
    - `code/strategies/noisy_greedy_runner.py` — NOT invoked by the run-book
    - `code/utils/generate_audit_report.py` — NOT invoked by the run-book
    - `code/utils/verify_seeds.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/graphs/graph_noise_42.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/greedy_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/analysis/noisy_stats.py` — NOT invoked by the run-book
    - `code/analysis/correlation_analysis.py` — NOT invoked by the run-book
    - `code/analysis/stats.py` — IS a run-book command
    - `code/analysis/power_analysis.py` — NOT invoked by the run-book
    - `code/strategies/greedy_runner.py` — NOT invoked by the run-book
    - `code/utils/validate_results.py` — NOT invoked by the run-book
    - `code/report/categorize_status_counts.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/greedy_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/lazy_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/analysis/noisy_stats.py` — NOT invoked by the run-book
    - `code/analysis/correlation_analysis.py` — NOT invoked by the run-book
    - `code/analysis/stats.py` — IS a run-book command
    - `code/analysis/threshold_analysis.py` — NOT invoked by the run-book
    - `code/analysis/sensitivity_analysis.py` — NOT invoked by the run-book
    - `code/analysis/power_analysis.py` — NOT invoked by the run-book
    - `code/strategies/noisy_lazy_runner.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/lazy_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/noisy_baseline_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/analysis/noisy_stats.py` — NOT invoked by the run-book
    - `code/analysis/correlation_analysis.py` — NOT invoked by the run-book
    - `code/analysis/stats.py` — IS a run-book command
    - `code/strategies/noisy_baseline_runner.py` — NOT invoked by the run-book
    - `code/utils/validate_results.py` — NOT invoked by the run-book
    - `code/report/categorize_status_counts.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/noisy_baseline_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/report_data.json` is declared but was NOT written. Scripts referencing it:
    - `code/report/aggregate_results.py` — NOT invoked by the run-book
    - `code/report/generate_report.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/report_data.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/statistical_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/noisy_stats.py` — NOT invoked by the run-book
    - `code/report/aggregate_results.py` — NOT invoked by the run-book
    - `code/report/generate_report.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/statistical_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/status_counts.json` is declared but was NOT written. Scripts referencing it:
    - `code/report/aggregate_results.py` — NOT invoked by the run-book
    - `code/report/generate_report.py` — NOT invoked by the run-book
    - `code/report/categorize_status_counts.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/status_counts.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/threshold_analysis.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/__init__.py` — NOT invoked by the run-book
    - `code/analysis/threshold_analysis.py` — NOT invoked by the run-book
    - `code/report/aggregate_results.py` — NOT invoked by the run-book
    - `code/report/generate_report.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/threshold_analysis.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
