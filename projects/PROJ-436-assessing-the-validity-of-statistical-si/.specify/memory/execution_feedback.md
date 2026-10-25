# Execution failures — fix these before the analysis can run

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/raw/42803.csv, data/raw/43844.csv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: every produced artifact is gitignored (data/raw/42803.csv, data/raw/43844.csv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 3 command(s) failed: python code/main.py --action download (rc=-1); python code/main.py  --action run  --datasets rct_1 mcar_0 mar_0  --iterations 15000  --rates 0.05 0.10 0.15 0.20 0.25  --mechanisms MCAR MAR MNAR  --methods CC MI IPW (rc=1); python -m pytest tests/ -v (rc=2)

## Failing / missing run-book commands

- python code/main.py --action download -> rc=-1
772b959fe7246567b949dae, got a9a2a80afe87ccb757bb0cc0c447ea92cf5ef83f5d5f728ef1bc51e9f39bc80b. Updating manifest.
2026-10-25 05:25:27,470 INFO data_loader: Processing dataset 43844
2026-10-25 05:25:27,470 INFO data_loader: Fetching OpenML dataset 43844
2026-10-25 05:25:27,557 INFO data_loader: Fetched OpenML dataset 43844 (36137 rows, 36 columns)
2026-10-25 05:25:27,557 INFO data_loader: Dataset validation passed: 36137 rows, 36 columns
2026-10-25 05:25:27,875 INFO data_loader: Dataset 43844 saved to data/raw/43844.csv
2026-10-25 05:25:27,875 INFO data_loader: Dataset validation passed: 36137 rows, 36 columns
2026-10-25 05:25:28,182 INFO data_loader: Saved dataset 43844 to /home/runner/work/llmXive/llmXive/projects/PROJ-436-assessing-the-validity-of-statistical-si/data/raw/43844.csv
2026-10-25 05:25:28,187 WARNING data_loader: Checksum mismatch for dataset 43844: expected 703c91d241b7fb8ca0e9f3677987836cec6d30e50b2224394b4c8db8b1dd5897, got 456ca677f93454b31a2353a4665a42cde97ebc2e58e0535b193b8f6c43be5e20. Updating manifest.
2026-10-25 05:25:28,187 INFO data_loader: Processing dataset 43845
2026-10-25 05:25:28,187 INFO data_loader: Fetching OpenML dataset 43845

[TIMEOUT after 120s]
- python code/main.py  --action run  --datasets rct_1 mcar_0 mar_0  --iterations 15000  --rates 0.05 0.10 0.15 0.20 0.25  --mechanisms MCAR MAR MNAR  --methods CC MI IPW -> rc=1

2026-10-25 05:27:13,322 INFO __main__: Running simulation with provided arguments.
2026-10-25 05:27:13,323 ERROR __main__: Config file not found: data/processed/simulation_config.json

- python -m pytest tests/ -v -> rc=2
thon/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
<frozen importlib._bootstrap>:1204: in _gcd_import
    ???
<frozen importlib._bootstrap>:1176: in _find_and_load
    ???
<frozen importlib._bootstrap>:1147: in _find_and_load_unlocked
    ???
<frozen importlib._bootstrap>:690: in _load_unlocked
    ???
/home/runner/.cache/llmxive/base-env/py311-6f1866971868/_pytest/assertion/rewrite.py:178: in exec_module
    exec(co, module.__dict__)
tests/integration/test_us2_sensitivity.py:29: in <module>
    from main import run_sensitivity_sweep, validate_condition_matrix, generate_tipping_point_report
E   ImportError: cannot import name 'run_sensitivity_sweep' from 'main' (/home/runner/work/llmXive/llmXive/projects/PROJ-436-assessing-the-validity-of-statistical-si/code/main.py)
=========================== short test summary info ============================
ERROR tests/integration/test_main_us1.py
ERROR tests/integration/test_us2_sensitivity.py
!!!!!!!!!!!!!!!!!!! Interrupted: 2 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 2 errors in 1.06s ===============================


