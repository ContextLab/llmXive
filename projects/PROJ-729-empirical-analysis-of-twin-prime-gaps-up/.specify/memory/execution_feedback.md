# Execution failures — fix these before the analysis can run

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/results/expected_count.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: every produced artifact is gitignored (data/results/expected_count.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 4 run-book script(s) missing (plan/impl path mismatch): python code/analyze_gaps.py; python code/analyze_local.py; python code/verify_citations.py; 3 command(s) failed: python code/generate_primes.py (rc=1); python code/validate_schema.py (rc=1); python -m pytest tests/ (rc=2); 2 declared deliverable(s) absent: data/raw/twin_primes.csv; data/results/performance_gen.json

## Failing / missing run-book commands

- python code/generate_primes.py -> rc=1

2026-10-12 01:08:14 - utils - ERROR - ERROR: primesieve library is required. Install with: pip install primesieve

- python code/validate_schema.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-729-empirical-analysis-of-twin-prime-gaps-up/code/validate_schema.py", line 163, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-729-empirical-analysis-of-twin-prime-gaps-up/code/validate_schema.py", line 137, in main
    logger = setup_logging("validate_schema")
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-729-empirical-analysis-of-twin-prime-gaps-up/code/utils.py", line 18, in setup_logging
    logging.basicConfig(
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/logging/__init__.py", line 2062, in basicConfig
    root.setLevel(level)
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/logging/__init__.py", line 1464, in setLevel
    self.level = _checkLevel(level)
                 ^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/logging/__init__.py", line 207, in _checkLevel
    raise ValueError("Unknown level: %r" % level)
ValueError: Unknown level: 'validate_schema'

- python code/analyze_gaps.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-729-empirical-analysis-of-twin-prime-gaps-up/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-729-empirical-analysis-of-twin-prime-gaps-up/code/analyze_gaps.py': [Errno 2] No such file or directory

- python code/analyze_local.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-729-empirical-analysis-of-twin-prime-gaps-up/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-729-empirical-analysis-of-twin-prime-gaps-up/code/analyze_local.py': [Errno 2] No such file or directory

- python code/verify_citations.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-729-empirical-analysis-of-twin-prime-gaps-up/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-729-empirical-analysis-of-twin-prime-gaps-up/code/verify_citations.py': [Errno 2] No such file or directory

- python code/report.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-729-empirical-analysis-of-twin-prime-gaps-up/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-729-empirical-analysis-of-twin-prime-gaps-up/code/report.py': [Errno 2] No such file or directory

- python -m pytest tests/ -> rc=2
==================== ERRORS ====================================
______________ ERROR collecting tests/unit/test_expected_count.py ______________
ImportError while importing test module '/home/runner/work/llmXive/llmXive/projects/PROJ-729-empirical-analysis-of-twin-prime-gaps-up/tests/unit/test_expected_count.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests/unit/test_expected_count.py:13: in <module>
    from compute_expected_count import get_theoretical_count, HARDY_LITTLEWOOD_CONSTANT
E   ImportError: cannot import name 'HARDY_LITTLEWOOD_CONSTANT' from 'compute_expected_count' (/home/runner/work/llmXive/llmXive/projects/PROJ-729-empirical-analysis-of-twin-prime-gaps-up/code/compute_expected_count.py)
=========================== short test summary info ============================
ERROR tests/unit/test_expected_count.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
=============================== 1 error in 0.55s ===============================



## Declared deliverables still missing

- data/raw/twin_primes.csv
- data/results/performance_gen.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/raw/twin_primes.csv` is declared but was NOT written. Scripts referencing it:
    - `code/compute_expected_count.py` — IS a run-book command
    - `code/generate_primes.py` — IS a run-book command
    - `code/generate_primes_fixed.py` — NOT invoked by the run-book
    - `code/hash_artifacts.py` — IS a run-book command
    - `code/setup_project.py` — NOT invoked by the run-book
    - `code/validate_schema.py` — IS a run-book command
  Make ONE of these WRITE `data/raw/twin_primes.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/performance_gen.json` is declared but was NOT written. Scripts referencing it:
    - `code/generate_primes_fixed.py` — NOT invoked by the run-book
    - `code/measure_gen_performance.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/performance_gen.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
