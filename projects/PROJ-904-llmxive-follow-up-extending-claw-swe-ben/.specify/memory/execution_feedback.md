# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/analysis/calibration.py: synthetic/fake INPUT data not authorized by the spec — “…Creates a small synthetic sample for the pilot run.…”
- code/analysis/calibration.py: synthetic/fake INPUT data not authorized by the spec — “…sample: The synthetic sample data.          Returns:…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 fabricated/simulated-result signal(s) — results are not real measurements: code/analysis/calibration.py: synthetic/fake INPUT data not authorized by the spec — “…Creates a small synthetic sample for the pilot run.…”; code/analysis/calibration.py: synthetic/fake INPUT data not authorized by the spec — “…sample: The synthetic sample data.          Returns:…”; 6 run-book script(s) missing (plan/impl path mismatch): python experiments/run_strategies.py --model 1B --strategy tfidf --output data/intermediate/hf_run_1b_tfidf.jsonl; python experiments/run_strategies.py --model 1B --strategy diff_aware --output data/intermediate/hf_run_1b_diff.jsonl; python experiments/run_strategies.py --model 1B --strategy summarization --output data/intermediate/hf_run_1b_summ.jsonl; 4 command(s) failed: python code/experiments/run_baseline.py --model 1B --strategy baseline --output data/intermediate/baseline_run.jsonl (rc=1); python code/analysis/failure_classifier.py --input 'data/intermediate/*.jsonl' --output data/intermediate/classified_results.jsonl (rc=1); python code/analysis/glm_analyzer.py --input data/results.csv --output data/glm_results.json (rc=1); 3 declared deliverable(s) absent: data/analysis_flags.json; data/filtered_swe_bench_v1.parquet; data/results.csv

## Failing / missing run-book commands

- python code/experiments/run_baseline.py --model 1B --strategy baseline --output data/intermediate/baseline_run.jsonl -> rc=1

INFO:root:Running baseline with model 1B, strategy baseline
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/experiments/run_baseline.py", line 55, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/experiments/run_baseline.py", line 52, in main
    run_baseline(args.model, args.strategy, args.output)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/experiments/run_baseline.py", line 28, in run_baseline
    instances = load_filtered_instances("data/filtered_swe_bench_v1.parquet")
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/experiments/run_baseline.py", line 11, in load_filtered_instances
    raise FileNotFoundError(f"Filtered dataset not found: {path}")
FileNotFoundError: Filtered dataset not found: data/filtered_swe_bench_v1.parquet

- python experiments/run_strategies.py --model 1B --strategy tfidf --output data/intermediate/hf_run_1b_tfidf.jsonl -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/experiments/run_strategies.py': [Errno 2] No such file or directory

- python experiments/run_strategies.py --model 1B --strategy diff_aware --output data/intermediate/hf_run_1b_diff.jsonl -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/experiments/run_strategies.py': [Errno 2] No such file or directory

- python experiments/run_strategies.py --model 1B --strategy summarization --output data/intermediate/hf_run_1b_summ.jsonl -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/experiments/run_strategies.py': [Errno 2] No such file or directory

- python experiments/run_scaling.py --model 7B --strategy baseline --output data/intermediate/hf_run_7b_baseline.jsonl -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/experiments/run_scaling.py': [Errno 2] No such file or directory

- python experiments/run_scaling.py --model 7B --strategy tfidf --output data/intermediate/hf_run_7b_tfidf.jsonl -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/experiments/run_scaling.py': [Errno 2] No such file or directory

- python code/analysis/failure_classifier.py --input 'data/intermediate/*.jsonl' --output data/intermediate/classified_results.jsonl -> rc=1

ERROR:__main__:File not found: data/intermediate/*.jsonl

- python analysis/metrics.py --input data/intermediate/classified_results.jsonl --output data/results.csv -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/analysis/metrics.py': [Errno 2] No such file or directory

- python code/analysis/glm_analyzer.py --input data/results.csv --output data/glm_results.json -> rc=1

INFO:root:statsmodels version: 0.15.0
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/analysis/glm_analyzer.py", line 150, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/analysis/glm_analyzer.py", line 147, in main
    run_glm_analysis(args.input, args.output)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/analysis/glm_analyzer.py", line 100, in run_glm_analysis
    df = load_results_data(input_path)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/analysis/glm_analyzer.py", line 23, in load_results_data
    raise FileNotFoundError(f"Results file not found: {input_path}")
FileNotFoundError: Results file not found: data/results.csv

- python -m pytest tests/contract/ -v -> rc=4
============================= test session starts ==============================
platform linux -- Python 3.11.17, pytest-9.1.1, pluggy-1.6.0 -- /home/runner/work/llmXive/llmXive/projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/.venv/bin/python
cachedir: .pytest_cache
rootdir: /home/runner/work/llmXive/llmXive
configfile: pyproject.toml
plugins: anyio-4.15.1
collecting ... collected 0 items

============================ no tests ran in 0.00s =============================

ERROR: file or directory not found: tests/contract/



## Declared deliverables still missing

- data/analysis_flags.json
- data/filtered_swe_bench_v1.parquet
- data/results.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/analysis_flags.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/generate_comparison_report.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/analysis_flags.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/filtered_swe_bench_v1.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/checksum_recorder.py` — NOT invoked by the run-book
    - `code/analysis/construct_validity.py` — NOT invoked by the run-book
    - `code/analysis/representativeness_validator.py` — NOT invoked by the run-book
    - `code/analysis/threshold_validator.py` — NOT invoked by the run-book
    - `code/experiments/run_7b_experiments.py` — NOT invoked by the run-book
    - `code/experiments/run_baseline.py` — IS a run-book command
    - `code/experiments/run_high_fidelity.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/filtered_swe_bench_v1.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/apply_failure_classification.py` — NOT invoked by the run-book
    - `code/analysis/checksum_recorder.py` — NOT invoked by the run-book
    - `code/analysis/construct_validity.py` — NOT invoked by the run-book
    - `code/analysis/failure_classifier.py` — IS a run-book command
    - `code/analysis/generate_comparison_report.py` — NOT invoked by the run-book
    - `code/analysis/glm_analyzer.py` — IS a run-book command
    - `code/analysis/merge_results.py` — NOT invoked by the run-book
    - `code/analysis/merge_results_runner.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
