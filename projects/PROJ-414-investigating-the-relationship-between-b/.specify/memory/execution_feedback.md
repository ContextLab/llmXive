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

**Summary**: 4 command(s) failed: python code/run_all.py --seed 42 --window 45 --step 10 --permutations 1000 (rc=2); python code/run_all.py --stage download --stage extract --stage metrics (rc=2); python -m pytest -q tests (rc=1)

## Failing / missing run-book commands

- python code/run_all.py --seed 42 --window 45 --step 10 --permutations 1000 -> rc=2
016.parquet
2026-10-19 12:23:23,995 INFO code.download_openneuro: /home/runner/work/llmXive/llmXive/projects/PROJ-414-investigating-the-relationship-between-b/data/raw/test-00000-of-00016.parquet already exists; skipping download.
2026-10-19 12:23:24,281 INFO code.download_openneuro: SHA-256 66c90ba52e1b8e11da9f152d4e0248b83606b99c64120091928be074a93359f7 written to /home/runner/work/llmXive/llmXive/projects/PROJ-414-investigating-the-relationship-between-b/data/checksums.json
2026-10-19 12:23:24,284 INFO code.download_openneuro: Column inventory written to /home/runner/work/llmXive/llmXive/projects/PROJ-414-investigating-the-relationship-between-b/data/raw/column_inventory.json (8 columns, available_subject_count=19)
2026-10-19 12:23:24,284 INFO code.download_openneuro: Expected fields ABSENT from shard (honest record): ['expert_rating', 'task_condition', 'years_of_training', 'age', 'fd', 'instrument', 'genre', 'practice_intensity', 'education']
2026-10-19 12:23:24,655 INFO __main__: === stage: extract (extract_rois) ===
usage: run_all.py [-h] [--shard SHARD] [--derived_dir DERIVED_DIR]
run_all.py: error: unrecognized arguments: --seed 42 --window 45 --step 10 --permutations 1000

- python code/run_all.py --stage download --stage extract --stage metrics -> rc=2
-00016.parquet
2026-10-19 12:23:25,079 INFO code.download_openneuro: /home/runner/work/llmXive/llmXive/projects/PROJ-414-investigating-the-relationship-between-b/data/raw/test-00000-of-00016.parquet already exists; skipping download.
2026-10-19 12:23:25,372 INFO code.download_openneuro: SHA-256 66c90ba52e1b8e11da9f152d4e0248b83606b99c64120091928be074a93359f7 written to /home/runner/work/llmXive/llmXive/projects/PROJ-414-investigating-the-relationship-between-b/data/checksums.json
2026-10-19 12:23:25,376 INFO code.download_openneuro: Column inventory written to /home/runner/work/llmXive/llmXive/projects/PROJ-414-investigating-the-relationship-between-b/data/raw/column_inventory.json (8 columns, available_subject_count=19)
2026-10-19 12:23:25,376 INFO code.download_openneuro: Expected fields ABSENT from shard (honest record): ['expert_rating', 'task_condition', 'years_of_training', 'age', 'fd', 'instrument', 'genre', 'practice_intensity', 'education']
2026-10-19 12:23:25,753 INFO __main__: === stage: extract (extract_rois) ===
usage: run_all.py [-h] [--shard SHARD] [--derived_dir DERIVED_DIR]
run_all.py: error: unrecognized arguments: --stage download --stage extract --stage metrics

- python -m pytest -q tests -> rc=1
hs
        monkeypatch.setattr(paths, "data", lambda *parts: tmp_path / pathlib.Path(*parts))
    
        # Create a minimal parquet file with a single subject
        import pyarrow as pa
        import pyarrow.parquet as pq
    
        n_timepoints = 50
        n_vertices = 1000
>       bold = np.random.rand(n_timepoints * n_vertices).astype(np.float32)
E       NameError: name 'np' is not defined

tests/test_extract.py:61: NameError
=========================== short test summary info ============================
FAILED tests/test_analysis.py::test_association_halts_when_no_proxy - FileNot...
FAILED tests/test_connectivity.py::test_process_subject - AssertionError: ass...
FAILED tests/test_extract.py::test_block_assignment - NameError: name 'np' is...
FAILED tests/test_extract.py::test_compute_block_means - NameError: name 'np'...
FAILED tests/test_extract.py::test_bandpass_filter_applied - NameError: name ...
FAILED tests/test_extract.py::test_dvars_statistics - NameError: name 'np' is...
FAILED tests/test_extract.py::test_qc_exclusion - NameError: name 'np' is not...
FAILED tests/test_extract.py::test_full_extraction - NameError: name 'np' is ...
8 failed, 11 passed in 0.67s


- python code/run_all.py --seed 123 --window 30 --step 5 --permutations 1000  --output_dir results/window30_step5 -> rc=2
INFO code.download_openneuro: /home/runner/work/llmXive/llmXive/projects/PROJ-414-investigating-the-relationship-between-b/data/raw/test-00000-of-00016.parquet already exists; skipping download.
2026-10-19 12:23:27,734 INFO code.download_openneuro: SHA-256 66c90ba52e1b8e11da9f152d4e0248b83606b99c64120091928be074a93359f7 written to /home/runner/work/llmXive/llmXive/projects/PROJ-414-investigating-the-relationship-between-b/data/checksums.json
2026-10-19 12:23:27,738 INFO code.download_openneuro: Column inventory written to /home/runner/work/llmXive/llmXive/projects/PROJ-414-investigating-the-relationship-between-b/data/raw/column_inventory.json (8 columns, available_subject_count=19)
2026-10-19 12:23:27,738 INFO code.download_openneuro: Expected fields ABSENT from shard (honest record): ['expert_rating', 'task_condition', 'years_of_training', 'age', 'fd', 'instrument', 'genre', 'practice_intensity', 'education']
2026-10-19 12:23:28,126 INFO __main__: === stage: extract (extract_rois) ===
usage: run_all.py [-h] [--shard SHARD] [--derived_dir DERIVED_DIR]
run_all.py: error: unrecognized arguments: --seed 123 --window 30 --step 5 --permutations 1000 --output_dir results/window30_step5

