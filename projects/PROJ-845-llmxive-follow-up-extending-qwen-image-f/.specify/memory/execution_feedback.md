# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 9 run-book script(s) missing (plan/impl path mismatch): python code/main.py --phase generate --output data/raw/; python code/main.py --phase validate_entropy --input data/raw/; python code/main.py --phase teacher_traces --input data/raw/ --output data/raw/; 5 declared deliverable(s) absent: data/processed/statistical_results.json; data/raw/high_entropy.csv; data/raw/low_entropy.csv

## Failing / missing run-book commands

- python code/main.py --phase generate --output data/raw/ -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-845-llmxive-follow-up-extending-qwen-image-f/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-845-llmxive-follow-up-extending-qwen-image-f/code/main.py': [Errno 2] No such file or directory
- python code/main.py --phase validate_entropy --input data/raw/ -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-845-llmxive-follow-up-extending-qwen-image-f/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-845-llmxive-follow-up-extending-qwen-image-f/code/main.py': [Errno 2] No such file or directory
- python code/main.py --phase teacher_traces --input data/raw/ --output data/raw/ -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-845-llmxive-follow-up-extending-qwen-image-f/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-845-llmxive-follow-up-extending-qwen-image-f/code/main.py': [Errno 2] No such file or directory
- python code/main.py --phase validate_traces --input data/raw/ -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-845-llmxive-follow-up-extending-qwen-image-f/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-845-llmxive-follow-up-extending-qwen-image-f/code/main.py': [Errno 2] No such file or directory
- python code/main.py --phase validate_generalization --input data/raw/ -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-845-llmxive-follow-up-extending-qwen-image-f/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-845-llmxive-follow-up-extending-qwen-image-f/code/main.py': [Errno 2] No such file or directory
- python code/main.py --phase distill --input data/raw/ --output data/processed/ -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-845-llmxive-follow-up-extending-qwen-image-f/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-845-llmxive-follow-up-extending-qwen-image-f/code/main.py': [Errno 2] No such file or directory
- python code/main.py --phase evaluate --input data/processed/ --output data/processed/ -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-845-llmxive-follow-up-extending-qwen-image-f/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-845-llmxive-follow-up-extending-qwen-image-f/code/main.py': [Errno 2] No such file or directory
- python code/main.py --phase analyze --input data/processed/ --output data/processed/stats.json -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-845-llmxive-follow-up-extending-qwen-image-f/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-845-llmxive-follow-up-extending-qwen-image-f/code/main.py': [Errno 2] No such file or directory
- python code/main.py --phase report --input data/processed/stats.json --output report.txt -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-845-llmxive-follow-up-extending-qwen-image-f/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-845-llmxive-follow-up-extending-qwen-image-f/code/main.py': [Errno 2] No such file or directory

## Declared deliverables still missing

- data/processed/statistical_results.json
- data/raw/high_entropy.csv
- data/raw/low_entropy.csv
- data/raw/target_specific.csv
- data/raw/test_set.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/statistical_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/statistical_results.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/statistical_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/high_entropy.csv` is declared but was NOT written. Scripts referencing it:
    - `code/training/run_distillation_batch.py` — NOT invoked by the run-book
    - `code/generators/generate_dataset.py` — NOT invoked by the run-book
    - `code/generators/save_datasets.py` — NOT invoked by the run-book
    - `code/generators/generate_test_set.py` — NOT invoked by the run-book
    - `code/generators/test_set_generator.py` — NOT invoked by the run-book
    - `code/generators/run_test_set_generation.py` — NOT invoked by the run-book
    - `code/generators/generate_final_datasets.py` — NOT invoked by the run-book
    - `code/analysis/metrics.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/high_entropy.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/low_entropy.csv` is declared but was NOT written. Scripts referencing it:
    - `code/training/run_distillation_batch.py` — NOT invoked by the run-book
    - `code/generators/generate_dataset.py` — NOT invoked by the run-book
    - `code/generators/save_datasets.py` — NOT invoked by the run-book
    - `code/generators/generate_test_set.py` — NOT invoked by the run-book
    - `code/generators/test_set_generator.py` — NOT invoked by the run-book
    - `code/generators/run_test_set_generation.py` — NOT invoked by the run-book
    - `code/generators/generate_final_datasets.py` — NOT invoked by the run-book
    - `code/analysis/metrics.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/low_entropy.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/target_specific.csv` is declared but was NOT written. Scripts referencing it:
    - `code/training/run_distillation_batch.py` — NOT invoked by the run-book
    - `code/generators/generate_dataset.py` — NOT invoked by the run-book
    - `code/generators/save_datasets.py` — NOT invoked by the run-book
    - `code/generators/generate_test_set.py` — NOT invoked by the run-book
    - `code/generators/test_set_generator.py` — NOT invoked by the run-book
    - `code/generators/run_test_set_generation.py` — NOT invoked by the run-book
    - `code/generators/generate_final_datasets.py` — NOT invoked by the run-book
    - `code/utils/data_hygiene.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/target_specific.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/test_set.csv` is declared but was NOT written. Scripts referencing it:
    - `code/generators/__init__.py` — NOT invoked by the run-book
    - `code/generators/generate_dataset.py` — NOT invoked by the run-book
    - `code/generators/save_datasets.py` — NOT invoked by the run-book
    - `code/generators/generate_test_set.py` — NOT invoked by the run-book
    - `code/generators/test_set_generator.py` — NOT invoked by the run-book
    - `code/generators/run_test_set_generation.py` — NOT invoked by the run-book
    - `code/generators/generate_final_datasets.py` — NOT invoked by the run-book
    - `code/analysis/evaluation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/test_set.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
