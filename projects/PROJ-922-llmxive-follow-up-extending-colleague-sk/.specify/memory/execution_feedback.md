# Execution failures — fix these before the analysis can run

## ⚠ COMPUTE-ENVIRONMENT failure — RE-SCOPE the method, don't just edit the script

These commands failed because the analysis needs hardware the FREE, CPU-only CI runner does NOT have (a GPU/CUDA, 8-bit quantization via bitsandbytes, or more RAM than is available). This is NOT a code bug you can patch by tweaking the failing line — the analysis MUST run on a CPU-only free runner (Constitution IV). RE-SCOPE the approach: drop `load_in_8bit` / `device_map='cuda'` and load in default precision on CPU; use a SMALLER model; REDUCE the dataset subset / sample / batch size; prefer a CPU-tractable method. Change the METHOD, not just the line that threw:

- `python -c "import torch; print('CUDA available:', torch.cuda.is_available())"`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 run-book script(s) missing (plan/impl path mismatch): python code/data/generators/profile_generator.py --count [variable] --seed 42; python code/data/generators/task_generator.py --count [sufficient_sample_size] --seed 42; python code/evaluation/score.py --input data/interim/inference_outputs.jsonl; 1 command(s) failed: python code/scripts/run_inference.py --model Llama-3-8B-Q4 --backend cpu (rc=1); 4 declared deliverable(s) absent: data/processed/final_results.csv; data/processed/glm_results.json; data/processed/hypothesis_verification.json

## Failing / missing run-book commands

- python -c "import torch; print('CUDA available:', torch.cuda.is_available())" -> rc=1

Traceback (most recent call last):
  File "<string>", line 1, in <module>
ModuleNotFoundError: No module named 'torch'

- python code/data/generators/profile_generator.py --count [variable] --seed 42 -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-922-llmxive-follow-up-extending-colleague-sk/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-922-llmxive-follow-up-extending-colleague-sk/code/data/generators/profile_generator.py': [Errno 2] No such file or directory

- python code/data/generators/task_generator.py --count [sufficient_sample_size] --seed 42 -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-922-llmxive-follow-up-extending-colleague-sk/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-922-llmxive-follow-up-extending-colleague-sk/code/data/generators/task_generator.py': [Errno 2] No such file or directory

- python code/scripts/run_inference.py --model Llama-3-8B-Q4 --backend cpu -> rc=1
{"timestamp": "2026-10-09T10:23:29.170346Z", "level": "INFO", "logger": "data_generation.profiles", "message": "Starting run_inference script.", "module": "run_inference", "function": "main", "line": 220}
{"timestamp": "2026-10-09T10:23:29.170637Z", "level": "ERROR", "logger": "data_generation.profiles", "message": "Profiles file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-922-llmxive-follow-up-extending-colleague-sk/data/raw/profiles.json", "module": "(unknown)", "function": null, "line": 0}


- python code/evaluation/score.py --input data/interim/inference_outputs.jsonl -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-922-llmxive-follow-up-extending-colleague-sk/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-922-llmxive-follow-up-extending-colleague-sk/code/evaluation/score.py': [Errno 2] No such file or directory

- python code/analysis/stats.py --input data/processed/evaluation_results.jsonl -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-922-llmxive-follow-up-extending-colleague-sk/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-922-llmxive-follow-up-extending-colleague-sk/code/analysis/stats.py': [Errno 2] No such file or directory


## Declared deliverables still missing

- data/processed/final_results.csv
- data/processed/glm_results.json
- data/processed/hypothesis_verification.json
- data/raw/tasks.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/final_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/scripts/verify_hypothesis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/final_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/glm_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/scripts/verify_hypothesis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/glm_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/hypothesis_verification.json` is declared but was NOT written. Scripts referencing it:
    - `code/scripts/verify_hypothesis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/hypothesis_verification.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/tasks.json` is declared but was NOT written. Scripts referencing it:
    - `code/data_generation/tasks.py` — NOT invoked by the run-book
    - `code/evaluation/validators.py` — NOT invoked by the run-book
    - `code/scripts/run_inference.py` — IS a run-book command
  Make ONE of these WRITE `data/raw/tasks.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
