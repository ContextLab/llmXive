# Execution failures — fix these before the analysis can run

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/processed/organophosphates_filtered.csv, data/processed/sample_size_status.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: every produced artifact is gitignored (data/processed/organophosphates_filtered.csv, data/processed/sample_size_status.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 3 command(s) failed: python code/split.py (rc=1); python code/train.py (rc=1); python -m pytest tests/ (rc=2)

## Failing / missing run-book commands

- python code/split.py -> rc=1

Fingerprint file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-678-comparative-analysis-of-molecular-finger/data/processed/fingerprints.pkl
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-678-comparative-analysis-of-molecular-finger/code/split.py", line 222, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-678-comparative-analysis-of-molecular-finger/code/split.py", line 189, in main
    raise FileNotFoundError(fingerprint_file)
FileNotFoundError: /home/runner/work/llmXive/llmXive/projects/PROJ-678-comparative-analysis-of-molecular-finger/data/processed/fingerprints.pkl

- python code/train.py -> rc=1

2026-10-13 06:57:00 - root - INFO - Starting K-Fold Cross-Validation Training (T019)
2026-10-13 06:57:00 - root - ERROR - Split indices file not found. Cannot proceed with training.
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-678-comparative-analysis-of-molecular-finger/code/train.py", line 240, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-678-comparative-analysis-of-molecular-finger/code/train.py", line 188, in main
    raise FileNotFoundError(f"Split file not found: {split_file}")
FileNotFoundError: Split file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-678-comparative-analysis-of-molecular-finger/data/processed/split_indices.json

- python -m pytest tests/ -> rc=2
11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests/integration/test_split.py:18: in <module>
    from split import (
E   ImportError: cannot import name 'verify_split_summary' from 'split' (/home/runner/work/llmXive/llmXive/projects/PROJ-678-comparative-analysis-of-molecular-finger/code/split.py)
=============================== warnings summary ===============================
tests/integration/test_download.py:48
  /home/runner/work/llmXive/llmXive/projects/PROJ-678-comparative-analysis-of-molecular-finger/tests/integration/test_download.py:48: PytestUnknownMarkWarning: Unknown pytest.mark.integration - is this a typo?  You can register custom marks to avoid this warning - for details, see https://docs.pytest.org/en/stable/how-to/mark.html
    @pytest.mark.integration

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
ERROR tests/integration/test_split.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
========================= 1 warning, 1 error in 1.93s ==========================


