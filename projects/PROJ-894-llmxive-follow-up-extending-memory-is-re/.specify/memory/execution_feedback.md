# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/benchmark_full_traversal.py: synthetic/fake INPUT data not authorized by the spec — “…rategy.  This script: 1. Generates a synthetic memory graph of varying…”
- code/benchmark_full_traversal.py: synthetic/fake INPUT data not authorized by the spec — “…nx.DiGraph:     """     Generates a synthetic directed graph for bench…”

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python code/data_loader.py --download --generate-graphs --seed 42`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 fabricated/simulated-result signal(s) — results are not real measurements: code/benchmark_full_traversal.py: synthetic/fake INPUT data not authorized by the spec — “…rategy.  This script: 1. Generates a synthetic memory graph of varying…”; code/benchmark_full_traversal.py: synthetic/fake INPUT data not authorized by the spec — “…nx.DiGraph:     """     Generates a synthetic directed graph for bench…”; 3 run-book script(s) missing (plan/impl path mismatch): python code/analysis.py --results data/processed/results/; python code/analysis.py --results data/processed/results/; python code/utils/hash_artifacts.py; 1 command(s) failed: python code/data_loader.py --download --generate-graphs --seed 42 (rc=1); 8 declared deliverable(s) absent: data/processed/baseline_results.csv; data/processed/greedy_results.csv; data/processed/lazy_results.csv

## Failing / missing run-book commands

- python code/data_loader.py --download --generate-graphs --seed 42 -> rc=1
    3.11/site-packages/datasets/load.py", line 1166, in dataset_module_factory
    raise DatasetNotFoundError(f"Dataset '{path}' doesn't exist on the Hub or cannot be accessed.") from e
datasets.exceptions.DatasetNotFoundError: Dataset 'locomo/locomo-benchmark' doesn't exist on the Hub or cannot be accessed.

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/code/data_loader.py", line 198, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/code/data_loader.py", line 186, in main
    tasks = fetch_locomo_dataset(subset=5) # Small subset for testing
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/code/data_loader.py", line 67, in fetch_locomo_dataset
    raise RuntimeError(f"Cannot proceed without real data. Fetch failed: {e}")
RuntimeError: Cannot proceed without real data. Fetch failed: Dataset 'locomo/locomo-benchmark' doesn't exist on the Hub or cannot be accessed.
- python code/analysis.py --results data/processed/results/ -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/code/analysis.py': [Errno 2] No such file or directory
- python code/analysis.py --results data/processed/results/ -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/code/analysis.py': [Errno 2] No such file or directory
- python code/utils/hash_artifacts.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/code/utils/hash_artifacts.py': [Errno 2] No such file or directory

## Declared deliverables still missing

- data/processed/baseline_results.csv
- data/processed/greedy_results.csv
- data/processed/lazy_results.csv
- data/processed/noisy_baseline_results.csv
- data/processed/noisy_greedy_results.csv
- data/processed/noisy_lazy_results.csv
- data/processed/stats_report.json
- data/processed/sweep_results.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/baseline_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/utils/validate_results.py` — NOT invoked by the run-book
    - `code/analysis/stats.py` — NOT invoked by the run-book
    - `code/strategies/baseline_runner.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/baseline_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/greedy_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/utils/validate_results.py` — NOT invoked by the run-book
    - `code/analysis/stats.py` — NOT invoked by the run-book
    - `code/strategies/noisy_greedy_runner.py` — NOT invoked by the run-book
    - `code/strategies/greedy_runner.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/greedy_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/lazy_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/utils/validate_results.py` — NOT invoked by the run-book
    - `code/analysis/stats.py` — NOT invoked by the run-book
    - `code/strategies/noisy_lazy_runner.py` — NOT invoked by the run-book
    - `code/strategies/lazy_runner.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/lazy_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/noisy_baseline_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/utils/validate_results.py` — NOT invoked by the run-book
    - `code/analysis/stats.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/noisy_baseline_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/noisy_greedy_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/utils/validate_results.py` — NOT invoked by the run-book
    - `code/analysis/stats.py` — NOT invoked by the run-book
    - `code/strategies/noisy_greedy_runner.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/noisy_greedy_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/noisy_lazy_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/utils/validate_results.py` — NOT invoked by the run-book
    - `code/analysis/stats.py` — NOT invoked by the run-book
    - `code/strategies/noisy_lazy_runner.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/noisy_lazy_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/stats_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/analysis/generate_docs.py` — NOT invoked by the run-book
    - `code/analysis/report_generator.py` — NOT invoked by the run-book
    - `code/analysis/stats.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/stats_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/sweep_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/analysis/stats.py` — NOT invoked by the run-book
    - `code/strategies/sweep_runner.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/sweep_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
