# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/main.py --mode simulation --config-id "test-config-1" --iterations 100`
  - script usage: `main.py [-h] [--mode {simulation,real_world,analyze,visualize}]`
  - argparse error: `main.py: error: argument subcommand: invalid choice: 'test-config-1' (choose from 'simulation', 'real_world', 'analyze', 'visualize')`
- run-book command: `python code/main.py --mode verify-checksums`
  - script usage: `main.py [-h] [--mode {simulation,real_world,analyze,visualize}]`
  - argparse error: `main.py: error: argument --mode: invalid choice: 'verify-checksums' (choose from 'simulation', 'real_world', 'analyze', 'visualize')`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 command(s) failed: python code/main.py --mode simulation (rc=1); python code/main.py --mode simulation --config-id "test-config-1" --iterations 100 (rc=2); python code/main.py --mode verify-checksums (rc=2)

## Failing / missing run-book commands

- python code/main.py --mode simulation -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-541-evaluating-the-impact-of-data-scaling-on/code/main.py", line 333, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-541-evaluating-the-impact-of-data-scaling-on/code/main.py", line 320, in main
    run_simulation_loop(target_iterations=args.iterations, output_path=args.output)
                                          ^^^^^^^^^^^^^^^
AttributeError: 'Namespace' object has no attribute 'iterations'

- python code/main.py --mode simulation --config-id "test-config-1" --iterations 100 -> rc=2

usage: main.py [-h] [--mode {simulation,real_world,analyze,visualize}]
               {simulation,real_world,analyze,visualize} ...
main.py: error: argument subcommand: invalid choice: 'test-config-1' (choose from 'simulation', 'real_world', 'analyze', 'visualize')

- python code/main.py --mode verify-checksums -> rc=2

usage: main.py [-h] [--mode {simulation,real_world,analyze,visualize}]
               {simulation,real_world,analyze,visualize} ...
main.py: error: argument --mode: invalid choice: 'verify-checksums' (choose from 'simulation', 'real_world', 'analyze', 'visualize')

- python -m pytest tests/unit/ -> rc=2
imezone_db_path,
pyarrow/lib.pyx:42: in init pyarrow.lib
    ???
E   ImportError: pyarrow requires NumPy 2.0 or newer, found 1.24.0
_____ ERROR collecting tests/unit/validation/test_quickstart_validation.py _____
ImportError while importing test module '/home/runner/work/llmXive/llmXive/projects/PROJ-541-evaluating-the-impact-of-data-scaling-on/tests/unit/validation/test_quickstart_validation.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests/unit/validation/test_quickstart_validation.py:16: in <module>
    from validation.quickstart_validation import check_directories, run_aggregation
E   ModuleNotFoundError: No module named 'validation'
=========================== short test summary info ============================
ERROR tests/unit/preprocessing/test_ingestion.py
ERROR tests/unit/validation/test_quickstart_validation.py
!!!!!!!!!!!!!!!!!!! Interrupted: 2 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 2 errors in 1.04s ===============================


