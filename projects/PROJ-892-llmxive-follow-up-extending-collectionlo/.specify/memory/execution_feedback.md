# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 command(s) failed: python code/main.py (rc=1); 3 declared deliverable(s) absent: data/analysis_results.json; data/ci_report.json; data/results.csv

## Failing / missing run-book commands

- python code/main.py -> rc=1
    /code/main.py", line 232, in main
    fp16_results = run_fp16_generation(config)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-892-llmxive-follow-up-extending-collectionlo/code/main.py", line 70, in run_fp16_generation
    pipe = load_fp16_adapter_and_base_model()
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-892-llmxive-follow-up-extending-collectionlo/code/data_loader.py", line 176, in load_fp16_adapter_and_base_model
    adapter_path = get_collection_lora_adapter()
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-892-llmxive-follow-up-extending-collectionlo/code/data_loader.py", line 97, in get_collection_lora_adapter
    download_lora_adapter("llmXive/collection-lora-mirror", filename, output_dir)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-892-llmxive-follow-up-extending-collectionlo/code/data_loader.py", line 66, in download_lora_adapter
    raise FileNotFoundError(f"Could not download adapter from {repo_id}") from e
FileNotFoundError: Could not download adapter from llmXive/collection-lora-mirror

## Declared deliverables still missing

- data/analysis_results.json
- data/ci_report.json
- data/results.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/analysis_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/statistical_analysis.py` — NOT invoked by the run-book
    - `code/run_e2e_validation.py` — NOT invoked by the run-book
    - `code/summary_report.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/analysis_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/ci_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/run_pipeline_timing.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/ci_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/quantization_logging.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
    - `code/statistical_analysis.py` — NOT invoked by the run-book
    - `code/validate_data.py` — NOT invoked by the run-book
    - `code/analyze_subspace_ranks.py` — NOT invoked by the run-book
    - `code/run_e2e_validation.py` — NOT invoked by the run-book
    - `code/generator.py` — NOT invoked by the run-book
    - `code/summary_report.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
