# Execution failures — fix these before the analysis can run

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python code/download.py`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 7 command(s) failed: python code/download.py (rc=1); python code/preprocess.py (rc=1); python code/residuals.py (rc=1); 1 declared deliverable(s) absent: data/processed/filtered_galaxies.csv

## Failing / missing run-book commands

- python code/download.py -> rc=1

2026-10-12 13:05:45 - __main__ - INFO - [T012] SPARC Data Download: Starting SPARC data download
2026-10-12 13:05:45 - __main__ - INFO - Downloading SPARC data from https://datadryad.org/stash/downloads/file_stream/270916
2026-10-12 13:05:45 - __main__ - ERROR - Invalid URL: https://datadryad.org/stash/downloads/file_stream/270916
2026-10-12 13:05:45 - __main__ - ERROR - [T012] SPARC Data Download: Failed to download SPARC data
2026-10-12 13:05:45 - __main__ - ERROR - SPARC data download failed

- python code/preprocess.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-076-assessing-the-validity-of-modified-newto/code/preprocess.py", line 231, in <module>
    exit(main())
         ^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-076-assessing-the-validity-of-modified-newto/code/preprocess.py", line 172, in main
    raw_dir = Path(cfg["data"]["source_dir"])
                   ~~~~~~~~~~~^^^^^^^^^^^^^^
KeyError: 'source_dir'

- python code/residuals.py -> rc=1

2026-10-12 13:05:46 - __main__ - INFO - Starting residual analysis pipeline
2026-10-12 13:05:46 - __main__ - ERROR - Filtered data not found: data/processed/filtered_galaxies.csv
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-076-assessing-the-validity-of-modified-newto/code/residuals.py", line 430, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-076-assessing-the-validity-of-modified-newto/code/residuals.py", line 324, in main
    raise FileNotFoundError(f"Required data file not found: {data_path}")
FileNotFoundError: Required data file not found: data/processed/filtered_galaxies.csv

- python code/sensitivity.py -> rc=1

2026-10-12 13:05:47 - __main__ - INFO - Running sensitivity analysis script.
2026-10-12 13:05:47 - __main__ - ERROR - Required input file missing: /home/runner/work/llmXive/llmXive/projects/PROJ-076-assessing-the-validity-of-modified-newto/results/fit_summary.csv
2026-10-12 13:05:47 - __main__ - ERROR - Please ensure T025 has been run to generate fit_summary.csv.

- python -m pytest tests/unit/ -> rc=2
ty-of-modified-newto
configfile: pyproject.toml
collecting ... collected 124 items / 1 error

==================================== ERRORS ====================================
___________________ ERROR collecting tests/unit/test_mond.py ___________________
ImportError while importing test module '/home/runner/work/llmXive/llmXive/projects/PROJ-076-assessing-the-validity-of-modified-newto/tests/unit/test_mond.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests/unit/test_mond.py:6: in <module>
    from code.models.mond import mond_simple, A0
E   ImportError: cannot import name 'A0' from 'code.models.mond' (/home/runner/work/llmXive/llmXive/projects/PROJ-076-assessing-the-validity-of-modified-newto/code/models/mond.py)
=========================== short test summary info ============================
ERROR tests/unit/test_mond.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
=============================== 1 error in 0.76s ===============================


- python -m pytest tests/contract/ -> rc=1
ader = parsers.TextReader(src, **kwds)
parsers.pyx:581: in pandas._libs.parsers.TextReader.__cinit__
    ???
E   pandas.errors.EmptyDataError: No columns to parse from file
__________________________ test_compute_summary_stats __________________________
tests/contract/test_sensitivity_summary.py:78: in test_compute_summary_stats
    assert stats['avg_mond_pass_rate'] == 0.67  # (0.5+0.6+0.7+0.75+0.8)/5
E   assert 0.6699999999999999 == 0.67
=========================== short test summary info ============================
FAILED tests/contract/test_dataset_schema.py::TestDatasetSchema::test_constraint_violation_fails_validation
FAILED tests/contract/test_schemas.py::test_dataset_schema_structure - Assert...
FAILED tests/contract/test_schemas.py::test_fit_results_schema_structure - As...
FAILED tests/contract/test_schemas.py::test_dataset_schema_with_sample_data
FAILED tests/contract/test_schemas.py::test_fit_results_schema_with_sample_data
FAILED tests/contract/test_sensitivity_summary.py::test_load_sensitivity_data_valid_file
FAILED tests/contract/test_sensitivity_summary.py::test_compute_summary_stats
=================== 7 failed, 38 passed, 2 skipped in 0.70s ====================


- python -m pytest tests/integration/ -> rc=2
ve/base-env/py311-6f1866971868/matplotlib/_fontconfig_pattern.py:92
../../../../../.cache/llmxive/base-env/py311-6f1866971868/matplotlib/_fontconfig_pattern.py:92
../../../../../.cache/llmxive/base-env/py311-6f1866971868/matplotlib/_fontconfig_pattern.py:92
  /home/runner/.cache/llmxive/base-env/py311-6f1866971868/matplotlib/_fontconfig_pattern.py:92: PyparsingDeprecationWarning: 'resetCache' deprecated - use 'reset_cache'
    parser.resetCache()

../../../../../.cache/llmxive/base-env/py311-6f1866971868/matplotlib/_mathtext.py:45
  /home/runner/.cache/llmxive/base-env/py311-6f1866971868/matplotlib/_mathtext.py:45: PyparsingDeprecationWarning: 'enablePackrat' deprecated - use 'enable_packrat'
    ParserElement.enablePackrat()

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
ERROR tests/integration/test_generate_fit_summary.py
ERROR tests/integration/test_statistics.py
ERROR tests/integration/test_verdict_generation.py
!!!!!!!!!!!!!!!!!!! Interrupted: 3 errors during collection !!!!!!!!!!!!!!!!!!!!
======================== 13 warnings, 3 errors in 0.89s ========================



## Declared deliverables still missing

- data/processed/filtered_galaxies.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/filtered_galaxies.csv` is declared but was NOT written. Scripts referencing it:
    - `code/aggregate.py` — NOT invoked by the run-book
    - `code/fit.py` — IS a run-book command
    - `code/generate_fit_summary.py` — NOT invoked by the run-book
    - `code/generate_residual_stats.py` — NOT invoked by the run-book
    - `code/preprocess.py` — IS a run-book command
    - `code/residuals.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/filtered_galaxies.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
