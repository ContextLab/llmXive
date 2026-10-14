# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 6 command(s) failed: python -m code.main (rc=1); python code/analyze_energies.py (rc=1); python code/derive_scaling.py (rc=1); 2 declared deliverable(s) absent: data/derived/correlation_results.csv; data/derived/raw_energies.csv

## Failing / missing run-book commands

- python -m code.main -> rc=1

2026-10-14 07:41:26,051 INFO __main__: Running pipeline with time wrapper: /usr/bin/time -v bash -c python code/load_data.py && python code/run_psi4.py && python code/analyze_energies.py && python code/derive_scaling.py && python code/correlate_bulk.py --scaling data/derived/scaling_stats.json --include-energy-error && python code/generate_reports.py
2026-10-14 07:41:26,843 INFO __main__: Runtime report written to data/derived/runtime_report.txt
2026-10-14 07:41:26,847 INFO __main__: Appended reproducibility section to benchmark_report.md
2026-10-14 07:41:26,918 INFO __main__: No contracts directory found – skipping validation.
2026-10-14 07:41:26,918 ERROR __main__: Pipeline failed with exit code 1

- python code/analyze_energies.py -> rc=1
ft-d3-dispersion-to-/code/analyze_energies.py", line 342, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-735-transferability-of-dft-d3-dispersion-to-/code/analyze_energies.py", line 321, in main
    df, stats = analyze_and_export(
                ^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-735-transferability-of-dft-d3-dispersion-to-/code/analyze_energies.py", line 233, in analyze_and_export
    df = _generate_placeholder_raw_energies(input_path)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-735-transferability-of-dft-d3-dispersion-to-/code/analyze_energies.py", line 201, in _generate_placeholder_raw_energies
    pairs, _ = load_synthetic_dataset(synthetic_zip)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-735-transferability-of-dft-d3-dispersion-to-/code/load_data.py", line 89, in load_synthetic_dataset
    raise FileNotFoundError(f"Synthetic dataset not found: {zip_path}")
FileNotFoundError: Synthetic dataset not found: /home/runner/work/llmXive/llmXive/projects/data/IL-Benchmark-local.zip

- python code/derive_scaling.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-735-transferability-of-dft-d3-dispersion-to-/code/derive_scaling.py", line 189, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-735-transferability-of-dft-d3-dispersion-to-/code/derive_scaling.py", line 159, in main
    df = load_raw_energies(input_csv)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-735-transferability-of-dft-d3-dispersion-to-/code/derive_scaling.py", line 21, in load_raw_energies
    raise FileNotFoundError(f"Raw energies file not found: {csv_path}")
FileNotFoundError: Raw energies file not found: data/derived/raw_energies.csv

- python code/correlate_bulk.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-735-transferability-of-dft-d3-dispersion-to-/code/correlate_bulk.py", line 434, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-735-transferability-of-dft-d3-dispersion-to-/code/correlate_bulk.py", line 423, in main
    analyze_and_export(
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-735-transferability-of-dft-d3-dispersion-to-/code/correlate_bulk.py", line 350, in analyze_and_export
    energies_df = load_energies_csv(energies_path)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-735-transferability-of-dft-d3-dispersion-to-/code/correlate_bulk.py", line 16, in load_energies_csv
    raise FileNotFoundError(f"Energy CSV not found: {filepath}")
FileNotFoundError: Energy CSV not found: /home/runner/work/llmXive/llmXive/projects/PROJ-735-transferability-of-dft-d3-dispersion-to-/data/derived/raw_energies.csv

- python code/generate_reports.py -> rc=1
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/io/parsers/readers.py", line 1620, in __init__
    self._engine = self._make_engine(f, self.engine)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/io/parsers/readers.py", line 1880, in _make_engine
    self.handles = get_handle(
                   ^^^^^^^^^^^
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/io/common.py", line 794, in get_handle
    handle = _BytesZipFile(
             ^^^^^^^^^^^^^^
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/io/common.py", line 1037, in __init__
    self.buffer: zipfile.ZipFile = zipfile.ZipFile(  # type: ignore[assignment]
                                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/zipfile.py", line 1355, in __init__
    self._RealGetContents()
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/zipfile.py", line 1422, in _RealGetContents
    raise BadZipFile("File is not a zip file")
zipfile.BadZipFile: File is not a zip file

- python -m pytest -v tests/ -> rc=2
le
    return _bootstrap._gcd_import(name[level:], package, level)
<frozen importlib._bootstrap>:1204: in _gcd_import
    ???
<frozen importlib._bootstrap>:1176: in _find_and_load
    ???
<frozen importlib._bootstrap>:1147: in _find_and_load_unlocked
    ???
<frozen importlib._bootstrap>:690: in _load_unlocked
    ???
/home/runner/.cache/llmxive/base-env/py311-6f1866971868/_pytest/assertion/rewrite.py:178: in exec_module
    exec(co, module.__dict__)
tests/unit/test_scaling.py:18: in <module>
    from code.derive_scaling import optimize_scaling_factor, compute_scaled_metrics
E   ImportError: cannot import name 'optimize_scaling_factor' from 'code.derive_scaling' (/home/runner/work/llmXive/llmXive/projects/PROJ-735-transferability-of-dft-d3-dispersion-to-/code/derive_scaling.py)
=========================== short test summary info ============================
ERROR tests/test_config.py
ERROR tests/unit/test_bonferroni.py
ERROR tests/unit/test_load_data.py
ERROR tests/unit/test_parse_psi4.py
ERROR tests/unit/test_scaling.py
!!!!!!!!!!!!!!!!!!! Interrupted: 5 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 5 errors in 1.05s ===============================



## Declared deliverables still missing

- data/derived/correlation_results.csv
- data/derived/raw_energies.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/derived/correlation_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/correlate_bulk.py` — IS a run-book command
    - `code/generate_reports.py` — IS a run-book command
    - `code/main.py` — IS a run-book command
  Make ONE of these WRITE `data/derived/correlation_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/derived/raw_energies.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analyze_energies.py` — IS a run-book command
    - `code/correlate_bulk.py` — IS a run-book command
    - `code/derive_scaling.py` — IS a run-book command
    - `code/generate_reports.py` — IS a run-book command
    - `code/main.py` — IS a run-book command
    - `code/write_scaling_results.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/raw_energies.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
