# Execution failures — fix these before the analysis can run

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/processed/anonymized.csv, data/processed/raw_counts.json, data/processed/scored.csv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: every produced artifact is gitignored (data/processed/anonymized.csv, data/processed/raw_counts.json, data/processed/scored.csv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 2 run-book script(s) missing (plan/impl path mismatch): python code/03_validate.py; python code/04_analyze.py; 2 command(s) failed: python -m pipeline.run (rc=1); python -m pytest tests/unit/ (rc=2)

## Failing / missing run-book commands

- python -m pipeline.run -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-050-the-effect-of-priming-on-prosocial-behav/bin/python: Error while finding module specification for 'pipeline.run' (ModuleNotFoundError: No module named 'pipeline')

- python code/03_validate.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-050-the-effect-of-priming-on-prosocial-behav/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-050-the-effect-of-priming-on-prosocial-behav/code/03_validate.py': [Errno 2] No such file or directory

- python code/04_analyze.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-050-the-effect-of-priming-on-prosocial-behav/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-050-the-effect-of-priming-on-prosocial-behav/code/04_analyze.py': [Errno 2] No such file or directory

- python -m pytest tests/unit/ -> rc=2
ers, paths
E   ImportError: cannot import name 'paths' from 'code.create_data_folders' (/home/runner/work/llmXive/llmXive/projects/PROJ-050-the-effect-of-priming-on-prosocial-behav/code/create_data_folders.py)
______________ ERROR collecting tests/unit/test_power_analysis.py ______________
ImportError while importing test module '/home/runner/work/llmXive/llmXive/projects/PROJ-050-the-effect-of-priming-on-prosocial-behav/tests/unit/test_power_analysis.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.18/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests/unit/test_power_analysis.py:18: in <module>
    import code._00_power_analysis as power_module
E   ModuleNotFoundError: No module named 'code._00_power_analysis'
=========================== short test summary info ============================
ERROR tests/unit/test_create_data_folders.py
ERROR tests/unit/test_power_analysis.py
!!!!!!!!!!!!!!!!!!! Interrupted: 2 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 2 errors in 1.18s ===============================


