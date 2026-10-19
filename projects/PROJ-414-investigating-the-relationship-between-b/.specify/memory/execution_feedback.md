# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/run_all.py --seed 42 --window 45 --step 10 --permutations 1000`
  - script usage: `run_all.py [-h] [--shard SHARD] [--derived_dir DERIVED_DIR]`
  - argparse error: `run_all.py: error: unrecognized arguments: --seed 42 --window 45 --step 10 --permutations 1000`
- run-book command: `python code/run_all.py --stage download --stage extract --stage metrics`
  - script usage: `run_all.py [-h] [--shard SHARD] [--derived_dir DERIVED_DIR]`
  - argparse error: `run_all.py: error: unrecognized arguments: --stage download --stage extract --stage metrics`
- run-book command: `python code/run_all.py --seed 123 --window 30 --step 5 --permutations 1000  --output_dir results/window30_step5`
  - script usage: `run_all.py [-h] [--shard SHARD] [--derived_dir DERIVED_DIR]`
  - argparse error: `run_all.py: error: unrecognized arguments: --seed 123 --window 30 --step 5 --permutations 1000 --output_dir results/window30_step5`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 command(s) failed: python code/run_all.py --seed 42 --window 45 --step 10 --permutations 1000 (rc=2); python code/run_all.py --stage download --stage extract --stage metrics (rc=2); python -m pytest -q tests (rc=2); 1 declared deliverable(s) absent: data/derived/pca_scores.csv

## Failing / missing run-book commands

- python code/run_all.py --seed 42 --window 45 --step 10 --permutations 1000 -> rc=2
016.parquet
2026-10-19 07:32:50,823 INFO code.download_openneuro: /home/runner/work/llmXive/llmXive/projects/PROJ-414-investigating-the-relationship-between-b/data/raw/test-00000-of-00016.parquet already exists; skipping download.
2026-10-19 07:32:51,148 INFO code.download_openneuro: SHA-256 66c90ba52e1b8e11da9f152d4e0248b83606b99c64120091928be074a93359f7 written to /home/runner/work/llmXive/llmXive/projects/PROJ-414-investigating-the-relationship-between-b/data/checksums.json
2026-10-19 07:32:51,150 INFO code.download_openneuro: Column inventory written to /home/runner/work/llmXive/llmXive/projects/PROJ-414-investigating-the-relationship-between-b/data/raw/column_inventory.json (8 columns, available_subject_count=19)
2026-10-19 07:32:51,150 INFO code.download_openneuro: Expected fields ABSENT from shard (honest record): ['expert_rating', 'task_condition', 'years_of_training', 'age', 'fd', 'instrument', 'genre', 'practice_intensity', 'education']
2026-10-19 07:32:51,676 INFO __main__: === stage: extract (extract_rois) ===
usage: run_all.py [-h] [--shard SHARD] [--derived_dir DERIVED_DIR]
run_all.py: error: unrecognized arguments: --seed 42 --window 45 --step 10 --permutations 1000

- python code/run_all.py --stage download --stage extract --stage metrics -> rc=2
-00016.parquet
2026-10-19 07:32:52,166 INFO code.download_openneuro: /home/runner/work/llmXive/llmXive/projects/PROJ-414-investigating-the-relationship-between-b/data/raw/test-00000-of-00016.parquet already exists; skipping download.
2026-10-19 07:32:52,490 INFO code.download_openneuro: SHA-256 66c90ba52e1b8e11da9f152d4e0248b83606b99c64120091928be074a93359f7 written to /home/runner/work/llmXive/llmXive/projects/PROJ-414-investigating-the-relationship-between-b/data/checksums.json
2026-10-19 07:32:52,492 INFO code.download_openneuro: Column inventory written to /home/runner/work/llmXive/llmXive/projects/PROJ-414-investigating-the-relationship-between-b/data/raw/column_inventory.json (8 columns, available_subject_count=19)
2026-10-19 07:32:52,493 INFO code.download_openneuro: Expected fields ABSENT from shard (honest record): ['expert_rating', 'task_condition', 'years_of_training', 'age', 'fd', 'instrument', 'genre', 'practice_intensity', 'education']
2026-10-19 07:32:53,018 INFO __main__: === stage: extract (extract_rois) ===
usage: run_all.py [-h] [--shard SHARD] [--derived_dir DERIVED_DIR]
run_all.py: error: unrecognized arguments: --stage download --stage extract --stage metrics

- python -m pytest -q tests -> rc=2
els/tsa/stattools.py:395: in <module>
    @deprecate_kwarg("unbiased", "adjusted")
E   TypeError: deprecate_kwarg() missing 1 required positional argument: 'new_arg_name'
_ ERROR collecting projects/PROJ-414-investigating-the-relationship-between-b/tests/test_connectivity.py _
ImportError while importing test module '/home/runner/work/llmXive/llmXive/projects/PROJ-414-investigating-the-relationship-between-b/tests/test_connectivity.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests/test_connectivity.py:17: in <module>
    import connectivity  # noqa: E402
code/connectivity.py:26: in <module>
    from . import graph_metrics
E   ImportError: attempted relative import with no known parent package
=========================== short test summary info ============================
ERROR tests/test_analysis.py - TypeError: deprecate_kwarg() missing 1 require...
ERROR tests/test_connectivity.py
!!!!!!!!!!!!!!!!!!! Interrupted: 2 errors during collection !!!!!!!!!!!!!!!!!!!!
2 errors in 1.11s


- python code/run_all.py --seed 123 --window 30 --step 5 --permutations 1000  --output_dir results/window30_step5 -> rc=2
INFO code.download_openneuro: /home/runner/work/llmXive/llmXive/projects/PROJ-414-investigating-the-relationship-between-b/data/raw/test-00000-of-00016.parquet already exists; skipping download.
2026-10-19 07:32:55,633 INFO code.download_openneuro: SHA-256 66c90ba52e1b8e11da9f152d4e0248b83606b99c64120091928be074a93359f7 written to /home/runner/work/llmXive/llmXive/projects/PROJ-414-investigating-the-relationship-between-b/data/checksums.json
2026-10-19 07:32:55,635 INFO code.download_openneuro: Column inventory written to /home/runner/work/llmXive/llmXive/projects/PROJ-414-investigating-the-relationship-between-b/data/raw/column_inventory.json (8 columns, available_subject_count=19)
2026-10-19 07:32:55,635 INFO code.download_openneuro: Expected fields ABSENT from shard (honest record): ['expert_rating', 'task_condition', 'years_of_training', 'age', 'fd', 'instrument', 'genre', 'practice_intensity', 'education']
2026-10-19 07:32:56,166 INFO __main__: === stage: extract (extract_rois) ===
usage: run_all.py [-h] [--shard SHARD] [--derived_dir DERIVED_DIR]
run_all.py: error: unrecognized arguments: --seed 123 --window 30 --step 5 --permutations 1000 --output_dir results/window30_step5


## Declared deliverables still missing

- data/derived/pca_scores.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/derived/pca_scores.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis.py` — NOT invoked by the run-book
    - `code/dimensionality.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/pca_scores.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
