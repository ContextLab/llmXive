# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 5 command(s) failed: python code/src/entropy.py --output data/processed/entropy_results.csv --sample-size 50 (rc=1); python code/src/inference.py --output data/processed/convergence_results.csv --sample-size 50 (rc=1); python code/src/entropy.py --output data/processed/entropy_results.csv (rc=1); 5 declared deliverable(s) absent: data/processed/convergence_results.csv; data/processed/entropy_results.csv; data/processed/filtered_splits.json

## Failing / missing run-book commands

- python code/src/entropy.py --output data/processed/entropy_results.csv --sample-size 50 -> rc=1
    ^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-979-llmxive-follow-up-extending-loopcoder-v2/code/.venv/lib/python3.11/site-packages/transformers/configuration_utils.py", line 776, in _get_config_dict
    resolved_config_file = cached_file(
                           ^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-979-llmxive-follow-up-extending-loopcoder-v2/code/.venv/lib/python3.11/site-packages/transformers/utils/hub.py", line 293, in cached_file
    file = cached_files(path_or_repo_id=path_or_repo_id, filenames=[filename], **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-979-llmxive-follow-up-extending-loopcoder-v2/code/.venv/lib/python3.11/site-packages/transformers/utils/hub.py", line 469, in cached_files
    raise OSError(
OSError: codellama/CodeLlama-1.3b-Instruct-hf is not a local folder and is not a valid model identifier listed on 'https://huggingface.co/models'
If this is a private repository, make sure to pass a token having permission to this repo either by logging in with `hf auth login` or by passing `token=<your_token>`
- python code/src/inference.py --output data/processed/convergence_results.csv --sample-size 50 -> rc=1
    ^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-979-llmxive-follow-up-extending-loopcoder-v2/code/.venv/lib/python3.11/site-packages/transformers/configuration_utils.py", line 776, in _get_config_dict
    resolved_config_file = cached_file(
                           ^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-979-llmxive-follow-up-extending-loopcoder-v2/code/.venv/lib/python3.11/site-packages/transformers/utils/hub.py", line 293, in cached_file
    file = cached_files(path_or_repo_id=path_or_repo_id, filenames=[filename], **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-979-llmxive-follow-up-extending-loopcoder-v2/code/.venv/lib/python3.11/site-packages/transformers/utils/hub.py", line 469, in cached_files
    raise OSError(
OSError: codellama/CodeLlama-1.3b-Instruct-hf is not a local folder and is not a valid model identifier listed on 'https://huggingface.co/models'
If this is a private repository, make sure to pass a token having permission to this repo either by logging in with `hf auth login` or by passing `token=<your_token>`
- python code/src/entropy.py --output data/processed/entropy_results.csv -> rc=1
    ^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-979-llmxive-follow-up-extending-loopcoder-v2/code/.venv/lib/python3.11/site-packages/transformers/configuration_utils.py", line 776, in _get_config_dict
    resolved_config_file = cached_file(
                           ^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-979-llmxive-follow-up-extending-loopcoder-v2/code/.venv/lib/python3.11/site-packages/transformers/utils/hub.py", line 293, in cached_file
    file = cached_files(path_or_repo_id=path_or_repo_id, filenames=[filename], **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-979-llmxive-follow-up-extending-loopcoder-v2/code/.venv/lib/python3.11/site-packages/transformers/utils/hub.py", line 469, in cached_files
    raise OSError(
OSError: codellama/CodeLlama-1.3b-Instruct-hf is not a local folder and is not a valid model identifier listed on 'https://huggingface.co/models'
If this is a private repository, make sure to pass a token having permission to this repo either by logging in with `hf auth login` or by passing `token=<your_token>`
- python code/src/inference.py --output data/processed/convergence_results.csv -> rc=1
    ^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-979-llmxive-follow-up-extending-loopcoder-v2/code/.venv/lib/python3.11/site-packages/transformers/configuration_utils.py", line 776, in _get_config_dict
    resolved_config_file = cached_file(
                           ^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-979-llmxive-follow-up-extending-loopcoder-v2/code/.venv/lib/python3.11/site-packages/transformers/utils/hub.py", line 293, in cached_file
    file = cached_files(path_or_repo_id=path_or_repo_id, filenames=[filename], **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-979-llmxive-follow-up-extending-loopcoder-v2/code/.venv/lib/python3.11/site-packages/transformers/utils/hub.py", line 469, in cached_files
    raise OSError(
OSError: codellama/CodeLlama-1.3b-Instruct-hf is not a local folder and is not a valid model identifier listed on 'https://huggingface.co/models'
If this is a private repository, make sure to pass a token having permission to this repo either by logging in with `hf auth login` or by passing `token=<your_token>`
- python code/src/analysis.py --entropy data/processed/entropy_results.csv  --convergence data/processed/convergence_results.csv  --output data/processed/router_simulation.csv -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-979-llmxive-follow-up-extending-loopcoder-v2/code/src/analysis.py", line 222, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-979-llmxive-follow-up-extending-loopcoder-v2/code/src/analysis.py", line 218, in main
    rho, p_value = run_analysis(args.entropy, args.convergence)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-979-llmxive-follow-up-extending-loopcoder-v2/code/src/analysis.py", line 187, in run_analysis
    entropy_results = load_entropy_results(entropy_path)
                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-979-llmxive-follow-up-extending-loopcoder-v2/code/src/analysis.py", line 34, in load_entropy_results
    raise FileNotFoundError(f"Entropy results not found at {input_path}")
FileNotFoundError: Entropy results not found at data/processed/entropy_results.csv

## Declared deliverables still missing

- data/processed/convergence_results.csv
- data/processed/entropy_results.csv
- data/processed/filtered_splits.json
- data/processed/resource_metrics.json
- data/processed/sc005_metrics.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/convergence_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/tests/test_inference.py` — NOT invoked by the run-book
    - `code/tests/test_logging_utils.py` — NOT invoked by the run-book
    - `code/tests/test_robustness.py` — NOT invoked by the run-book
    - `code/tests/test_router_evaluation.py` — NOT invoked by the run-book
    - `code/tests/test_analysis.py` — NOT invoked by the run-book
    - `code/tests/test_flops_analysis.py` — NOT invoked by the run-book
    - `code/scripts/run_inference.py` — NOT invoked by the run-book
    - `code/scripts/run_model_pilot.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/convergence_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/entropy_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/tests/test_logging_utils.py` — NOT invoked by the run-book
    - `code/tests/test_robustness.py` — NOT invoked by the run-book
    - `code/tests/test_analysis.py` — NOT invoked by the run-book
    - `code/scripts/run_model_pilot.py` — NOT invoked by the run-book
    - `code/scripts/run_analysis.py` — NOT invoked by the run-book
    - `code/src/logging_utils.py` — NOT invoked by the run-book
    - `code/src/analysis.py` — IS a run-book command
    - `code/src/model_pilot.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/entropy_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/filtered_splits.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/sc005_runner.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/filtered_splits.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/resource_metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/scripts/run_resource_monitor.py` — NOT invoked by the run-book
    - `code/src/sc005_runner.py` — NOT invoked by the run-book
    - `code/src/utils.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/resource_metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/sc005_metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/sc005_runner.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/sc005_metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `data/processed/entropy_results.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/tests/test_logging_utils.py`, `code/tests/test_robustness.py`, `code/src/analysis.py`, `code/src/model_pilot.py`, `code/src/sc005_runner.py`, `code/src/aggregation.py`, `code/src/entropy.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/processed/entropy_results.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/tests/test_logging_utils.py`, `code/tests/test_robustness.py`, `code/scripts/run_analysis.py`, `code/src/analysis.py`, `code/src/model_pilot.py`, `code/src/sc005_runner.py`, `code/src/aggregation.py`, `code/src/entropy.py`.
