# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 command(s) failed: python code/run_all.py --seed 42 --window 45 --step 10 --permutations 1000 (rc=1); python code/run_all.py --stage download --stage extract --stage metrics (rc=1); python -m pytest -q tests (rc=2); 1 declared deliverable(s) absent: data/derived/pca_scores.csv

## Failing / missing run-book commands

- python code/run_all.py --seed 42 --window 45 --step 10 --permutations 1000 -> rc=1

2026-10-19 07:29:39,025 INFO __main__: Pipeline run: seed=42 window=45.0 step=10.0 permutations=1000 stages=['download', 'extract', 'fix_exclusion_log', 'metrics', 'pca', 'analysis', 'sensitivity', 'visualization', 'manifest']
2026-10-19 07:29:39,294 INFO __main__: === stage: download (download_openneuro) ===
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-414-investigating-the-relationship-between-b/code/run_all.py", line 130, in <module>
    raise SystemExit(main())
                     ^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-414-investigating-the-relationship-between-b/code/run_all.py", line 124, in main
    run_stage(stage, args)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-414-investigating-the-relationship-between-b/code/run_all.py", line 94, in run_stage
    exit_code = module.main([])
                ^^^^^^^^^^^^^^^
TypeError: main() takes 0 positional arguments but 1 was given

- python code/run_all.py --stage download --stage extract --stage metrics -> rc=1

2026-10-19 07:29:39,372 INFO __main__: Pipeline run: seed=42 window=45.0 step=10.0 permutations=1000 stages=['download', 'extract', 'metrics']
2026-10-19 07:29:39,642 INFO __main__: === stage: download (download_openneuro) ===
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-414-investigating-the-relationship-between-b/code/run_all.py", line 130, in <module>
    raise SystemExit(main())
                     ^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-414-investigating-the-relationship-between-b/code/run_all.py", line 124, in main
    run_stage(stage, args)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-414-investigating-the-relationship-between-b/code/run_all.py", line 94, in run_stage
    exit_code = module.main([])
                ^^^^^^^^^^^^^^^
TypeError: main() takes 0 positional arguments but 1 was given

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
2 errors in 1.16s


- python code/run_all.py --seed 123 --window 30 --step 5 --permutations 1000  --output_dir results/window30_step5 -> rc=1

2026-10-19 07:29:41,606 INFO __main__: Output directory overridden: results/window30_step5
2026-10-19 07:29:41,606 INFO __main__: Pipeline run: seed=123 window=30.0 step=5.0 permutations=1000 stages=['download', 'extract', 'fix_exclusion_log', 'metrics', 'pca', 'analysis', 'sensitivity', 'visualization', 'manifest']
2026-10-19 07:29:41,876 INFO __main__: === stage: download (download_openneuro) ===
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-414-investigating-the-relationship-between-b/code/run_all.py", line 130, in <module>
    raise SystemExit(main())
                     ^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-414-investigating-the-relationship-between-b/code/run_all.py", line 124, in main
    run_stage(stage, args)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-414-investigating-the-relationship-between-b/code/run_all.py", line 94, in run_stage
    exit_code = module.main([])
                ^^^^^^^^^^^^^^^
TypeError: main() takes 0 positional arguments but 1 was given


## Declared deliverables still missing

- data/derived/pca_scores.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/derived/pca_scores.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis.py` — NOT invoked by the run-book
    - `code/dimensionality.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/pca_scores.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
