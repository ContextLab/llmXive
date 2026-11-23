# Execution failures — fix these before the analysis can run

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- data/derived/auditory_trials.csv: header only, ZERO data rows — the analysis produced no rows
- data/derived/trial_data.csv: column(s) confidence_rating are EMPTY in every one of 150 rows — that measure was never recorded
- data/derived/visual_trials.csv: column(s) confidence_rating are EMPTY in every one of 150 rows — that measure was never recorded
- data/results/correlation_metrics.json: metric is null/NaN (d_prime) — not a real measurement

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 hollow-result signal(s) — the analysis ran but computed nothing: data/derived/auditory_trials.csv: header only, ZERO data rows — the analysis produced no rows; data/derived/trial_data.csv: column(s) confidence_rating are EMPTY in every one of 150 rows — that measure was never recorded; data/derived/visual_trials.csv: column(s) confidence_rating are EMPTY in every one of 150 rows — that measure was never recorded; 1 command(s) failed: python -m pytest tests/ (rc=2)

## Failing / missing run-book commands

- python -m pytest tests/ -> rc=2
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests/unit/test_validate_data.py:14: in <module>
    from data.validate_data import (
E   ImportError: cannot import name 'find_input_file' from 'data.validate_data' (/home/runner/work/llmXive/llmXive/projects/PROJ-179-the-influence-of-metacognitive-awareness/code/data/validate_data.py)
=========================== short test summary info ============================
ERROR tests/integration/test_quickstart.py
ERROR tests/integration/test_robustness_report.py - NameError: name 'Optional...
ERROR tests/test_env_config.py
ERROR tests/unit/test_download.py
ERROR tests/unit/test_generate_report.py - NameError: name 'Optional' is not ...
ERROR tests/unit/test_generate_robustness_report.py - NameError: name 'Option...
ERROR tests/unit/test_preprocess.py
ERROR tests/unit/test_validate_data.py
!!!!!!!!!!!!!!!!!!! Interrupted: 8 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 8 errors in 0.97s ===============================


