# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 run-book script(s) missing (plan/impl path mismatch): python code/analyze_gaps.py; python code/analyze_local.py; python code/verify_citations.py; 4 command(s) failed: python code/generate_primes.py (rc=1); python code/validate_schema.py (rc=1); python code/hash_artifacts.py (rc=1); 3 declared deliverable(s) absent: data/raw/twin_primes.csv; data/results/expected_count.json; data/results/performance_gen.json

## Failing / missing run-book commands

- python code/generate_primes.py -> rc=1

ERROR: primesieve library is required. Install with: pip install primesieve

- python code/validate_schema.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-729-empirical-analysis-of-twin-prime-gaps-up/code/validate_schema.py", line 12, in <module>
    import yaml
ModuleNotFoundError: No module named 'yaml'

- python code/analyze_gaps.py -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-729-empirical-analysis-of-twin-prime-gaps-up/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-729-empirical-analysis-of-twin-prime-gaps-up/code/analyze_gaps.py': [Errno 2] No such file or directory

- python code/analyze_local.py -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-729-empirical-analysis-of-twin-prime-gaps-up/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-729-empirical-analysis-of-twin-prime-gaps-up/code/analyze_local.py': [Errno 2] No such file or directory

- python code/hash_artifacts.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-729-empirical-analysis-of-twin-prime-gaps-up/code/hash_artifacts.py", line 4, in <module>
    import yaml
ModuleNotFoundError: No module named 'yaml'

- python code/verify_citations.py -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-729-empirical-analysis-of-twin-prime-gaps-up/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-729-empirical-analysis-of-twin-prime-gaps-up/code/verify_citations.py': [Errno 2] No such file or directory

- python code/report.py -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-729-empirical-analysis-of-twin-prime-gaps-up/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-729-empirical-analysis-of-twin-prime-gaps-up/code/report.py': [Errno 2] No such file or directory

- python -m pytest tests/ -> rc=1

/home/runner/work/llmXive/llmXive/projects/PROJ-729-empirical-analysis-of-twin-prime-gaps-up/code/.venv/bin/python: No module named pytest


## Declared deliverables still missing

- data/raw/twin_primes.csv
- data/results/expected_count.json
- data/results/performance_gen.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/raw/twin_primes.csv` is declared but was NOT written. Scripts referencing it:
    - `code/compute_expected_count.py` — NOT invoked by the run-book
    - `code/generate_primes.py` — IS a run-book command
    - `code/generate_primes_fixed.py` — NOT invoked by the run-book
    - `code/hash_artifacts.py` — IS a run-book command
    - `code/validate_schema.py` — IS a run-book command
  Make ONE of these WRITE `data/raw/twin_primes.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/expected_count.json` is declared but was NOT written. Scripts referencing it:
    - `code/compute_expected_count.py` — NOT invoked by the run-book
    - `code/generate_primes.py` — IS a run-book command
  Make ONE of these WRITE `data/results/expected_count.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/performance_gen.json` is declared but was NOT written. Scripts referencing it:
    - `code/generate_primes_fixed.py` — NOT invoked by the run-book
    - `code/measure_gen_performance.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/performance_gen.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
