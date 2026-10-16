# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 command(s) failed: python src/cli/run_pipeline.py  --swe_gym_url https://huggingface.co/datasets/OpenHands/SWE-Gym-code-search/resolve/main/data/train-00000-of-00001.parquet  --multi_swe_rl_url https://huggingface.co/datasets/ByteDance-Seed/Multi-SWE-RL/resolve/main/data_20240601_20250331/c/OpenMathLib__OpenBLAS_dataset.jsonl  --output_dir $(pwd)/output  --seed 42 (rc=1); python -m pytest -q tests/contract (rc=1); python src/cli/run_pipeline.py  ...  --sample_fraction 0.1   # 10 % stratified sample, seed fixed (rc=1); 2 declared deliverable(s) absent: data/patches.csv; data/patches_sample.csv

## Failing / missing run-book commands

- python src/cli/run_pipeline.py  --swe_gym_url https://huggingface.co/datasets/OpenHands/SWE-Gym-code-search/resolve/main/data/train-00000-of-00001.parquet  --multi_swe_rl_url https://huggingface.co/datasets/ByteDance-Seed/Multi-SWE-RL/resolve/main/data_20240601_20250331/c/OpenMathLib__OpenBLAS_dataset.jsonl  --output_dir $(pwd)/output  --seed 42 -> rc=1
ngest: Reading SWE‑Gym parquet: /home/runner/work/llmXive/llmXive/projects/PROJ-955-llmxive-follow-up-extending-dockerless-e/data/raw_swe_gym.parquet
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-955-llmxive-follow-up-extending-dockerless-e/src/cli/run_pipeline.py", line 145, in <module>
    sys.exit(main())
             ^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-955-llmxive-follow-up-extending-dockerless-e/src/cli/run_pipeline.py", line 138, in main
    ingest(args.swe_gym_url, args.multi_swe_rl_url)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-955-llmxive-follow-up-extending-dockerless-e/src/pipeline/ingest.py", line 340, in ingest
    swe_patches, swe_logs = _process_swe_gym(raw_swe_gym_path)
                            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-955-llmxive-follow-up-extending-dockerless-e/src/pipeline/ingest.py", line 210, in _process_swe_gym
    raise RuntimeError(f"SWE‑Gym parquet missing columns (or equivalents): {missing}")
RuntimeError: SWE‑Gym parquet missing columns (or equivalents): {'language', 'label', 'source_code', 'patch_id'}

- python -m pytest -q tests/contract -> rc=1
_id", "id", "patchid"])
        lang_col = _select_column(df, ["language", "lang"])
        src_col = _select_column(df, ["source_code", "code", "patched_code", "original_code", "code_before", "code_after"])
        label_col = _select_column(df, ["exec_result", "test_result", "result", "label"])
    
        missing = set()
        if not pid_col:
            missing.add("patch_id")
        if not lang_col:
            missing.add("language")
        if not src_col:
            missing.add("source_code")
        if not label_col:
            missing.add("label")
    
        if missing:
>           raise RuntimeError(f"SWE‑Gym parquet missing columns (or equivalents): {missing}")
E           RuntimeError: SWE‑Gym parquet missing columns (or equivalents): {'label', 'source_code', 'language', 'patch_id'}

src/pipeline/ingest.py:210: RuntimeError
=========================== short test summary info ============================
ERROR tests/contract/test_contracts.py::test_raw_files_exist - RuntimeError: ...
ERROR tests/contract/test_contracts.py::test_patches_csv_structure - RuntimeE...
ERROR tests/contract/test_contracts.py::test_execution_logs_exist - RuntimeEr...
3 errors in 0.43s


- python src/cli/run_pipeline.py  ...  --sample_fraction 0.1   # 10 % stratified sample, seed fixed -> rc=1
usage: run_pipeline.py [-h] [--dry-run] [--swe_gym_url SWE_GYM_URL]
                       [--multi_swe_rl_url MULTI_SWE_RL_URL]
                       [--output_dir OUTPUT_DIR] [--seed SEED]
                       [--sample_fraction SAMPLE_FRACTION]

LLM-Xive static-dynamic gap analysis pipeline.

options:
  -h, --help            show this help message and exit
  --dry-run             Create project directories and a tiny sample CSV
                        result.
  --swe_gym_url SWE_GYM_URL
                        URL to the SWE-Gym parquet file.
  --multi_swe_rl_url MULTI_SWE_RL_URL
                        URL to the Multi-SWE-RL JSONL file.
  --output_dir OUTPUT_DIR
                        Directory where pipeline artefacts will be placed.
  --seed SEED           Random seed for reproducibility.
  --sample_fraction SAMPLE_FRACTION
                        Fraction of the dataset to sample (0‑1). Ignored in
                        this version.

2026-10-16 05:08:38,785 INFO __main__: Random seed set to 42
2026-10-16 05:08:38,789 ERROR __main__: Dataset URLs must be provided for full pipeline execution.


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
