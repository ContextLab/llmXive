# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python src/cli/run_pipeline.py  ...  --sample_fraction 0.1   # 10 % stratified sample, seed fixed`
  - script usage: `run_pipeline.py [-h] [--dry-run] [--swe_gym_url SWE_GYM_URL]`
  - argparse error: `run_pipeline.py: error: unrecognized arguments: ... # 10 % stratified sample, seed fixed`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 command(s) failed: python src/cli/run_pipeline.py  --swe_gym_url https://huggingface.co/datasets/OpenHands/SWE-Gym-code-search/resolve/main/data/train-00000-of-00001.parquet  --multi_swe_rl_url https://huggingface.co/datasets/ByteDance-Seed/Multi-SWE-RL/resolve/main/data_20240601_20250331/c/OpenMathLib__OpenBLAS_dataset.jsonl  --output_dir $(pwd)/output  --seed 42 (rc=1); python -m pytest -q tests/contract (rc=1); python src/cli/run_pipeline.py  ...  --sample_fraction 0.1   # 10 % stratified sample, seed fixed (rc=2); 2 declared deliverable(s) absent: data/patches.csv; data/patches_sample.csv

## Failing / missing run-book commands

- python src/cli/run_pipeline.py  --swe_gym_url https://huggingface.co/datasets/OpenHands/SWE-Gym-code-search/resolve/main/data/train-00000-of-00001.parquet  --multi_swe_rl_url https://huggingface.co/datasets/ByteDance-Seed/Multi-SWE-RL/resolve/main/data_20240601_20250331/c/OpenMathLib__OpenBLAS_dataset.jsonl  --output_dir $(pwd)/output  --seed 42 -> rc=1
4:06,475 INFO src.pipeline.ingest: Reading SWE‑Gym parquet: /home/runner/work/llmXive/llmXive/projects/PROJ-955-llmxive-follow-up-extending-dockerless-e/data/raw_swe_gym.parquet
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-955-llmxive-follow-up-extending-dockerless-e/src/cli/run_pipeline.py", line 142, in <module>
    sys.exit(main())
             ^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-955-llmxive-follow-up-extending-dockerless-e/src/cli/run_pipeline.py", line 135, in main
    ingest(args.swe_gym_url, args.multi_swe_rl_url)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-955-llmxive-follow-up-extending-dockerless-e/src/pipeline/ingest.py", line 292, in ingest
    swe_patches, swe_logs = _process_swe_gym(raw_swe_gym_path)
                            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-955-llmxive-follow-up-extending-dockerless-e/src/pipeline/ingest.py", line 181, in _process_swe_gym
    raise RuntimeError(f"SWE‑Gym parquet missing columns: {missing}")
RuntimeError: SWE‑Gym parquet missing columns: {'language', 'source_code', 'exec_result', 'patch_id'}

- python -m pytest -q tests/contract -> rc=1
columns.
    
        Returns
        -------
        patches_df : pd.DataFrame
            Columns: ``patch_id, language, source_code, label``.
        logs : list of (patch_id, log_text)
            The raw execution log for each patch (may be empty).
        """
        log.info(f"Reading SWE‑Gym parquet: {parquet_path}")
        # Use fastparquet engine to avoid pulling in pyarrow (which requires NumPy 2).
        df = pd.read_parquet(parquet_path, engine="fastparquet")
    
        required = {"patch_id", "language", "source_code", "exec_result"}
        missing = required - set(df.columns)
        if missing:
>           raise RuntimeError(f"SWE‑Gym parquet missing columns: {missing}")
E           RuntimeError: SWE‑Gym parquet missing columns: {'exec_result', 'language', 'source_code', 'patch_id'}

src/pipeline/ingest.py:181: RuntimeError
=========================== short test summary info ============================
ERROR tests/contract/test_contracts.py::test_raw_files_exist - RuntimeError: ...
ERROR tests/contract/test_contracts.py::test_patches_csv_structure - RuntimeE...
ERROR tests/contract/test_contracts.py::test_execution_logs_exist - RuntimeEr...
3 errors in 0.41s


- python src/cli/run_pipeline.py  ...  --sample_fraction 0.1   # 10 % stratified sample, seed fixed -> rc=2

2026-10-16 00:14:07,413 INFO __main__: Random seed set to 42
usage: run_pipeline.py [-h] [--dry-run] [--swe_gym_url SWE_GYM_URL]
                       [--multi_swe_rl_url MULTI_SWE_RL_URL]
                       [--output_dir OUTPUT_DIR] [--seed SEED]
                       [--sample_fraction SAMPLE_FRACTION]
run_pipeline.py: error: unrecognized arguments: ... # 10 % stratified sample, seed fixed


## Declared deliverables still missing

- data/patches.csv
- data/patches_sample.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/patches.csv` is declared but was NOT written. Scripts referencing it:
    - `src/pipeline/graph_extractor.py` — NOT invoked by the run-book
    - `src/pipeline/ingest.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/patches.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/patches_sample.csv` is declared but was NOT written. Scripts referencing it:
    - `src/pipeline/graph_extractor.py` — NOT invoked by the run-book
    - `src/pipeline/ingest.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/patches_sample.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
