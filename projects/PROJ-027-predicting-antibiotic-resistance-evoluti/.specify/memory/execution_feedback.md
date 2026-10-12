# Execution failures — fix these before the analysis can run

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/processed/artifact_hashes.json, data/processed/pipeline_runtime.json, data/processed/verification_summary.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/main.py --stage viz --antibiotic ciprofloxacin`
  - script usage: `main.py [-h] [--stage {ingest,contract,train,validate,hash,full}]`
  - argparse error: `main.py: error: argument --stage: invalid choice: 'viz' (choose from 'ingest', 'contract', 'train', 'validate', 'hash', 'full')`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: every produced artifact is gitignored (data/processed/artifact_hashes.json, data/processed/pipeline_runtime.json, data/processed/verification_summary.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 6 command(s) failed: python code/main.py --stage ingest --n-isolates 1000 --bio_project PRJNA528852 (rc=1); python -m pytest tests/contract/ (rc=1); python code/main.py --stage train --antibiotic ciprofloxacin (rc=2)

## Failing / missing run-book commands

- python code/main.py --stage ingest --n-isolates 1000 --bio_project PRJNA528852 -> rc=1
2026-10-12 21:11:10 - root - INFO - Running stage: download_ncbi
2026-10-12 21:11:13 - root - INFO - Stage 'download_ncbi' completed successfully
2026-10-12 21:11:13 - root - INFO - Running stage: ingest_metadata
2026-10-12 21:11:13 - root - ERROR - Stage 'ingest_metadata' failed with exit code 1
2026-10-12 21:11:13 - root - INFO - Pipeline runtime written to /home/runner/work/llmXive/llmXive/projects/PROJ-027-predicting-antibiotic-resistance-evoluti/data/processed/pipeline_runtime.json


- python -m pytest tests/contract/ -> rc=1
xists()
tests/contract/test_phyl_permutation_schema.py:38: in check_file_exists
    assert PERMUTATION_RESULTS_PATH.exists(), \
E   AssertionError: Permutation results file not found at data/processed/permutation_results.json
E   assert False
E    +  where False = <bound method Path.exists of PosixPath('data/processed/permutation_results.json')>()
E    +    where <bound method Path.exists of PosixPath('data/processed/permutation_results.json')> = PosixPath('data/processed/permutation_results.json').exists
=========================== short test summary info ============================
FAILED tests/contract/test_model_output_schema.py::TestModelOutputSchema::test_model_pickle_loadable
FAILED tests/contract/test_phyl_permutation_schema.py::test_required_keys_present
FAILED tests/contract/test_phyl_permutation_schema.py::test_p_value_valid_range
FAILED tests/contract/test_phyl_permutation_schema.py::test_significance_flag_consistent
FAILED tests/contract/test_phyl_permutation_schema.py::test_permutation_count_positive
FAILED tests/contract/test_phyl_permutation_schema.py::test_observed_statistic_numeric
========================= 6 failed, 10 passed in 0.55s =========================


- python code/main.py --stage train --antibiotic ciprofloxacin -> rc=2
2026-10-12 21:11:14 - root - INFO - Running stage: train_models
2026-10-12 21:11:15 - root - ERROR - Stage 'train_models' failed with exit code 2
2026-10-12 21:11:15 - root - INFO - Pipeline runtime written to /home/runner/work/llmXive/llmXive/projects/PROJ-027-predicting-antibiotic-resistance-evoluti/data/processed/pipeline_runtime.json


- python code/main.py --stage validate --antibiotic ciprofloxacin --permutations [sufficient_permutations] -> rc=2
2026-10-12 21:11:15 - root - WARNING - Invalid permutations argument '[sufficient_permutations]'. Falling back to default 1000.
2026-10-12 21:11:15 - root - INFO - Running stage: phylo_permutation
2026-10-12 21:11:15 - root - ERROR - Stage 'phylo_permutation' failed with exit code 2
2026-10-12 21:11:15 - root - INFO - Pipeline runtime written to /home/runner/work/llmXive/llmXive/projects/PROJ-027-predicting-antibiotic-resistance-evoluti/data/processed/pipeline_runtime.json


- python code/main.py --stage viz --antibiotic ciprofloxacin -> rc=2

usage: main.py [-h] [--stage {ingest,contract,train,validate,hash,full}]
               [--n-isolates N_ISOLATES] [--bio_project BIO_PROJECT]
               [--antibiotic ANTIBIOTIC] [--permutations PERMUTATIONS]
main.py: error: argument --stage: invalid choice: 'viz' (choose from 'ingest', 'contract', 'train', 'validate', 'hash', 'full')

- python -m pytest tests/ -> rc=2
id_exclusion, verify_checksums
E   ModuleNotFoundError: No module named 'code.main_reproducible'
________________ ERROR collecting tests/unit/test_split_data.py ________________
ImportError while importing test module '/home/runner/work/llmXive/llmXive/projects/PROJ-027-predicting-antibiotic-resistance-evoluti/tests/unit/test_split_data.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests/unit/test_split_data.py:14: in <module>
    from code_03_model_split_data import load_filtered_matrix, validate_stratification, split_data
E   ModuleNotFoundError: No module named 'code_03_model_split_data'
=========================== short test summary info ============================
ERROR tests/test_setup_directories.py
ERROR tests/unit/test_hash_artifacts.py
ERROR tests/unit/test_main_reproducible.py
ERROR tests/unit/test_split_data.py
!!!!!!!!!!!!!!!!!!! Interrupted: 4 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 4 errors in 0.53s ===============================


## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
