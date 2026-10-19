# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 command(s) failed: python code/run_all.py --seed 42 --window 45 --step 10 --permutations 1000 (rc=1); python code/run_all.py --stage download --stage extract --stage metrics (rc=1); python -m pytest -q tests (rc=1)

## Failing / missing run-book commands

- python code/run_all.py --seed 42 --window 45 --step 10 --permutations 1000 -> rc=1

2026-10-19 04:41:39,888 INFO __main__: Pipeline run: seed=42 window=45.0s step=10.0s permutations=1000 tr=1.0s stages=['download', 'extract', 'metrics', 'pca', 'analysis', 'sensitivity', 'visualization', 'manifest']
2026-10-19 04:41:40,155 INFO __main__: === stage: download (download_openneuro.main) ===
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-414-investigating-the-relationship-between-b/code/run_all.py", line 137, in <module>
    raise SystemExit(main())
                     ^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-414-investigating-the-relationship-between-b/code/run_all.py", line 131, in main
    run_stage(stage, args)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-414-investigating-the-relationship-between-b/code/run_all.py", line 111, in run_stage
    entry(args)
TypeError: main() takes 0 positional arguments but 1 was given

- python code/run_all.py --stage download --stage extract --stage metrics -> rc=1

2026-10-19 04:41:40,229 INFO __main__: Pipeline run: seed=42 window=45.0s step=10.0s permutations=1000 tr=1.0s stages=['download', 'extract', 'metrics']
2026-10-19 04:41:40,494 INFO __main__: === stage: download (download_openneuro.main) ===
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-414-investigating-the-relationship-between-b/code/run_all.py", line 137, in <module>
    raise SystemExit(main())
                     ^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-414-investigating-the-relationship-between-b/code/run_all.py", line 131, in main
    run_stage(stage, args)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-414-investigating-the-relationship-between-b/code/run_all.py", line 111, in run_stage
    entry(args)
TypeError: main() takes 0 positional arguments but 1 was given

- python -m pytest -q tests -> rc=1
validators.py:1332: ValidationError
____________________ test_exclusion_log_covers_all_subjects ____________________

    def test_exclusion_log_covers_all_subjects():
        files = _derived_files()
        log_path = paths.data("derived", "exclusion_log.csv")
        if not files or not log_path.is_file():
            pytest.skip("no derived outputs yet")
        log_df = pd.read_csv(log_path)
>       assert set(log_df["subject_id"]) == {
            f.stem.replace("roi_timeseries_", "") for f in files
        }
E       AssertionError: assert {1, 2, 3, 4, 5, 6, ...} == {'01', '02', ...5', '06', ...}
E         
E         Extra items in the left set:
E         1
E         2
E         3
E         4
E         5...
E         
E         ...Full output truncated (35 lines hidden), use '-vv' to show

tests/test_extract.py:181: AssertionError
=========================== short test summary info ============================
FAILED tests/test_extract.py::test_dvars_exclusion_fires_on_known_bad_volumes
FAILED tests/test_extract.py::test_real_outputs_conform_to_schema - jsonschem...
FAILED tests/test_extract.py::test_exclusion_log_covers_all_subjects - Assert...
3 failed, 14 passed in 1.01s


- python code/run_all.py --seed 123 --window 30 --step 5 --permutations 1000  --output_dir results/window30_step5 -> rc=1

2026-10-19 04:41:41,919 INFO __main__: Output directory override: results/window30_step5
2026-10-19 04:41:41,919 INFO __main__: Pipeline run: seed=123 window=30.0s step=5.0s permutations=1000 tr=1.0s stages=['download', 'extract', 'metrics', 'pca', 'analysis', 'sensitivity', 'visualization', 'manifest']
2026-10-19 04:41:42,185 INFO __main__: === stage: download (download_openneuro.main) ===
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-414-investigating-the-relationship-between-b/code/run_all.py", line 137, in <module>
    raise SystemExit(main())
                     ^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-414-investigating-the-relationship-between-b/code/run_all.py", line 131, in main
    run_stage(stage, args)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-414-investigating-the-relationship-between-b/code/run_all.py", line 111, in run_stage
    entry(args)
TypeError: main() takes 0 positional arguments but 1 was given

