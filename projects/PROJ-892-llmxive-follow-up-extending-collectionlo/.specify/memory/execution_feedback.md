# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 5 command(s) failed: python code/main.py --phase prepare (rc=1); python code/main.py --phase generate --level FP16 (rc=1); python code/main.py --phase generate --level INT8 (rc=1); 4 declared deliverable(s) absent: data/analysis_results.json; data/references/other_effect_refs.json; data/results.csv

## Failing / missing run-book commands

- python code/main.py --phase prepare -> rc=1
    16_adapter_and_base_model() missing 2 required positional arguments: 'adapter_path' and 'base_model_path'
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-892-llmxive-follow-up-extending-collectionlo/code/main.py", line 303, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-892-llmxive-follow-up-extending-collectionlo/code/main.py", line 280, in main
    baseline_results = run_baseline_generation_loop()
                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-892-llmxive-follow-up-extending-collectionlo/code/main.py", line 222, in run_baseline_generation_loop
    results = run_fp16_generation(prompts, seeds, config)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-892-llmxive-follow-up-extending-collectionlo/code/main.py", line 70, in run_fp16_generation
    adapter, base_model = load_fp16_adapter_and_base_model()
                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: load_fp16_adapter_and_base_model() missing 2 required positional arguments: 'adapter_path' and 'base_model_path'
- python code/main.py --phase generate --level FP16 -> rc=1
    16_adapter_and_base_model() missing 2 required positional arguments: 'adapter_path' and 'base_model_path'
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-892-llmxive-follow-up-extending-collectionlo/code/main.py", line 303, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-892-llmxive-follow-up-extending-collectionlo/code/main.py", line 280, in main
    baseline_results = run_baseline_generation_loop()
                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-892-llmxive-follow-up-extending-collectionlo/code/main.py", line 222, in run_baseline_generation_loop
    results = run_fp16_generation(prompts, seeds, config)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-892-llmxive-follow-up-extending-collectionlo/code/main.py", line 70, in run_fp16_generation
    adapter, base_model = load_fp16_adapter_and_base_model()
                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: load_fp16_adapter_and_base_model() missing 2 required positional arguments: 'adapter_path' and 'base_model_path'
- python code/main.py --phase generate --level INT8 -> rc=1
    16_adapter_and_base_model() missing 2 required positional arguments: 'adapter_path' and 'base_model_path'
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-892-llmxive-follow-up-extending-collectionlo/code/main.py", line 303, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-892-llmxive-follow-up-extending-collectionlo/code/main.py", line 280, in main
    baseline_results = run_baseline_generation_loop()
                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-892-llmxive-follow-up-extending-collectionlo/code/main.py", line 222, in run_baseline_generation_loop
    results = run_fp16_generation(prompts, seeds, config)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-892-llmxive-follow-up-extending-collectionlo/code/main.py", line 70, in run_fp16_generation
    adapter, base_model = load_fp16_adapter_and_base_model()
                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: load_fp16_adapter_and_base_model() missing 2 required positional arguments: 'adapter_path' and 'base_model_path'
- python code/main.py --phase generate --level INT4 -> rc=1
    16_adapter_and_base_model() missing 2 required positional arguments: 'adapter_path' and 'base_model_path'
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-892-llmxive-follow-up-extending-collectionlo/code/main.py", line 303, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-892-llmxive-follow-up-extending-collectionlo/code/main.py", line 280, in main
    baseline_results = run_baseline_generation_loop()
                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-892-llmxive-follow-up-extending-collectionlo/code/main.py", line 222, in run_baseline_generation_loop
    results = run_fp16_generation(prompts, seeds, config)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-892-llmxive-follow-up-extending-collectionlo/code/main.py", line 70, in run_fp16_generation
    adapter, base_model = load_fp16_adapter_and_base_model()
                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: load_fp16_adapter_and_base_model() missing 2 required positional arguments: 'adapter_path' and 'base_model_path'
- python code/main.py --phase analyze -> rc=1
    16_adapter_and_base_model() missing 2 required positional arguments: 'adapter_path' and 'base_model_path'
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-892-llmxive-follow-up-extending-collectionlo/code/main.py", line 303, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-892-llmxive-follow-up-extending-collectionlo/code/main.py", line 280, in main
    baseline_results = run_baseline_generation_loop()
                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-892-llmxive-follow-up-extending-collectionlo/code/main.py", line 222, in run_baseline_generation_loop
    results = run_fp16_generation(prompts, seeds, config)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-892-llmxive-follow-up-extending-collectionlo/code/main.py", line 70, in run_fp16_generation
    adapter, base_model = load_fp16_adapter_and_base_model()
                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: load_fp16_adapter_and_base_model() missing 2 required positional arguments: 'adapter_path' and 'base_model_path'

## Declared deliverables still missing

- data/analysis_results.json
- data/references/other_effect_refs.json
- data/results.csv
- data/subspace_ranks_merged.json

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### `load_fp16_adapter_and_base_model` — defined in `code/data_loader.py`; called 3 way(s):

- code/generator.py: pipe = load_fp16_adapter_and_base_model()
- code/main.py: adapter, base_model = load_fp16_adapter_and_base_model()
- code/main.py: _, base_model = load_fp16_adapter_and_base_model()

Make `load_fp16_adapter_and_base_model` in `code/data_loader.py` accept ALL of the above.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/analysis_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/summary_report.py` — NOT invoked by the run-book
    - `code/statistical_analysis.py` — NOT invoked by the run-book
    - `code/run_e2e_validation.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
  Make ONE of these WRITE `data/analysis_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/references/other_effect_refs.json` is declared but was NOT written. Scripts referencing it:
    - `code/dependency_checker.py` — NOT invoked by the run-book
    - `code/data_loader.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/references/other_effect_refs.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/validate_results.py` — NOT invoked by the run-book
    - `code/generator.py` — NOT invoked by the run-book
    - `code/summary_report.py` — NOT invoked by the run-book
    - `code/final_hash_check.py` — NOT invoked by the run-book
    - `code/quantization_logging.py` — NOT invoked by the run-book
    - `code/statistical_analysis.py` — NOT invoked by the run-book
    - `code/metrics.py` — NOT invoked by the run-book
    - `code/run_e2e_validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/subspace_ranks_merged.json` is declared but was NOT written. Scripts referencing it:
    - `code/validate_results.py` — NOT invoked by the run-book
    - `code/statistical_analysis.py` — NOT invoked by the run-book
    - `code/dependency_checker.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/subspace_ranks_merged.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
