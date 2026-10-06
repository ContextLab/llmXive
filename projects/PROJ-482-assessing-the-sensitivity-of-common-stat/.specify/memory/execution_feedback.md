# Execution failures — fix these before the analysis can run

## ⚠ REGRESSIONS — your last fix BROKE these (they passed before)

These commands were NOT failing in the previous round and ARE failing now — your last edit broke previously-working code. REVERT or correct whatever change broke each one BEFORE touching anything else; do not trade one passing script for another (that oscillation is what burns the fix-round budget toward escalation):

- `python code/analyzers.py --input data/processed/error_rates.csv --output data/analysis/`
- `python code/run_data_gen.py --config code/config.yaml`
- `python code/simulation_runner.py --config code/config.yaml`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 run-book script(s) missing (plan/impl path mismatch): python code/simulation_runner.py --config code/config.yaml; python code/analyzers.py --input data/processed/error_rates.csv --output data/analysis/; 1 command(s) failed: python code/run_data_gen.py --config code/config.yaml (rc=1); 4 declared deliverable(s) absent: data/processed/error_rates.csv; data/processed/raw_pvalues.csv; data/processed/stability_trend.csv

## Failing / missing run-book commands

- python code/run_data_gen.py --config code/config.yaml -> rc=1
    2026-10-06 11:27:03,772 - __main__ - INFO - Generating scenario: n=10, dist=normal, effect=0.0
2026-10-06 11:27:03,772 - __main__ - ERROR -   -> Failed for scenario {'n': 10, 'dist': 'normal', 'effect': 0.0}: generate_data() got an unexpected keyword argument 'sample_size'
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-482-assessing-the-sensitivity-of-common-stat/code/run_data_gen.py", line 148, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-482-assessing-the-sensitivity-of-common-stat/code/run_data_gen.py", line 145, in main
    generate_validation_dataset(output_path)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-482-assessing-the-sensitivity-of-common-stat/code/run_data_gen.py", line 86, in generate_validation_dataset
    data_dict = generate_data(
                ^^^^^^^^^^^^^^
TypeError: generate_data() got an unexpected keyword argument 'sample_size'
- python code/simulation_runner.py --config code/config.yaml -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-482-assessing-the-sensitivity-of-common-stat/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-482-assessing-the-sensitivity-of-common-stat/code/simulation_runner.py': [Errno 2] No such file or directory
- python code/analyzers.py --input data/processed/error_rates.csv --output data/analysis/ -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-482-assessing-the-sensitivity-of-common-stat/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-482-assessing-the-sensitivity-of-common-stat/code/analyzers.py': [Errno 2] No such file or directory

## Declared deliverables still missing

- data/processed/error_rates.csv
- data/processed/raw_pvalues.csv
- data/processed/stability_trend.csv
- data/raw/sample_validation.csv

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### `generate_data` — defined in `code/data_generator.py`; called 2 way(s):

- code/run_ground_truth_validation.py: sample1, sample2 = generate_data(n, dist, eff, seed=seed)
- code/run_data_gen.py: data_dict = generate_data(

Make `generate_data` in `code/data_generator.py` accept ALL of the above.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/error_rates.csv` is declared but was NOT written. Scripts referencing it:
    - `code/run_simulation.py` — NOT invoked by the run-book
    - `code/validate_quickstart.py` — NOT invoked by the run-book
    - `code/run_analyzer.py` — NOT invoked by the run-book
    - `code/export_results.py` — NOT invoked by the run-book
    - `code/visualizer.py` — NOT invoked by the run-book
    - `code/simulation_engine.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/error_rates.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/raw_pvalues.csv` is declared but was NOT written. Scripts referencing it:
    - `code/run_log_pvalue_analysis.py` — NOT invoked by the run-book
    - `code/run_simulation.py` — NOT invoked by the run-book
    - `code/validate_quickstart.py` — NOT invoked by the run-book
    - `code/run_analyzer.py` — NOT invoked by the run-book
    - `code/run_optimized_simulation.py` — NOT invoked by the run-book
    - `code/config.py` — NOT invoked by the run-book
    - `code/analyzer.py` — NOT invoked by the run-book
    - `code/run_stability_analysis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/raw_pvalues.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/stability_trend.csv` is declared but was NOT written. Scripts referencing it:
    - `code/run_simulation.py` — NOT invoked by the run-book
    - `code/validate_quickstart.py` — NOT invoked by the run-book
    - `code/analyzer.py` — NOT invoked by the run-book
    - `code/run_stability_analysis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/stability_trend.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/sample_validation.csv` is declared but was NOT written. Scripts referencing it:
    - `code/run_data_gen.py` — IS a run-book command
  Make ONE of these WRITE `data/raw/sample_validation.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
