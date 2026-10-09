# Execution failures — fix these before the analysis can run

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/raw/download_manifest.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/main.py --stage validate --antibiotic ciprofloxacin --permutations [sufficient_permutations]`
  - script usage: `main.py [-h] [--stage {ingest,contract,train,validate,viz,hash,full}]`
  - argparse error: `main.py: error: argument --permutations: invalid int value: '[sufficient_permutations]'`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: every produced artifact is gitignored (data/raw/download_manifest.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 7 command(s) failed: python code/main.py --stage ingest --n-isolates 1000 --bio_project PRJNA528852 (rc=1); python -m pytest tests/contract/ (rc=1); python code/main.py --stage train --antibiotic ciprofloxacin (rc=2)

## Failing / missing run-book commands

- python code/main.py --stage ingest --n-isolates 1000 --bio_project PRJNA528852 -> rc=1
2026-10-09 14:30:54 - root - INFO - Running stage: download_ncbi
2026-10-09 14:30:54 - root - INFO - Stage 'download_ncbi' completed successfully
2026-10-09 14:30:54 - root - INFO - Running stage: ingest_metadata
2026-10-09 14:30:55 - root - ERROR - Stage 'ingest_metadata' failed with exit code 1


- python -m pytest tests/contract/ -> rc=1

/home/runner/work/llmXive/llmXive/projects/PROJ-027-predicting-antibiotic-resistance-evoluti/code/.venv/bin/python: No module named pytest

- python code/main.py --stage train --antibiotic ciprofloxacin -> rc=2
2026-10-09 14:30:55 - root - INFO - Running stage: train_models
2026-10-09 14:30:56 - root - ERROR - Stage 'train_models' failed with exit code 2


- python code/main.py --stage validate --antibiotic ciprofloxacin --permutations [sufficient_permutations] -> rc=2

usage: main.py [-h] [--stage {ingest,contract,train,validate,viz,hash,full}]
               [--n-isolates N_ISOLATES] [--bio_project BIO_PROJECT]
               [--antibiotic ANTIBIOTIC] [--permutations PERMUTATIONS]
main.py: error: argument --permutations: invalid int value: '[sufficient_permutations]'

- python code/utils/hash_artifacts.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-027-predicting-antibiotic-resistance-evoluti/code/utils/hash_artifacts.py", line 9, in <module>
    from utils.logging import get_logger
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-027-predicting-antibiotic-resistance-evoluti/code/utils/logging.py", line 11, in <module>
    std_logging = importlib.import_module('logging')
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py", line 126, in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-027-predicting-antibiotic-resistance-evoluti/code/utils/logging.py", line 15, in <module>
    "DEBUG": std_logging.DEBUG,
             ^^^^^^^^^^^^^^^^^
AttributeError: partially initialized module 'logging' has no attribute 'DEBUG' (most likely due to a circular import)

- python code/main.py --stage viz --antibiotic ciprofloxacin -> rc=2
2026-10-09 14:30:56 - root - INFO - Running stage: generate_plots
2026-10-09 14:30:57 - root - ERROR - Stage 'generate_plots' failed with exit code 2


- python -m pytest tests/ -> rc=1

/home/runner/work/llmXive/llmXive/projects/PROJ-027-predicting-antibiotic-resistance-evoluti/code/.venv/bin/python: No module named pytest

