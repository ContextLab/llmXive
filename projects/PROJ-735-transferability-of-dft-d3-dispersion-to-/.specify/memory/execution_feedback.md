# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 command(s) failed: python code/main.py (rc=1); 2 declared deliverable(s) absent: data/derived/correlation_results.csv; data/derived/raw_energies.csv

## Failing / missing run-book commands

- python code/main.py -> rc=1

2026-10-14 04:16:41,324 INFO __main__: Running pipeline with time wrapper: /usr/bin/time -v bash -c python code/load_data.py && python code/run_psi4.py && python code/analyze_energies.py && python code/derive_scaling.py && python code/correlate_bulk.py --scaling data/derived/scaling_stats.json --include-energy-error && python code/generate_reports.py
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-735-transferability-of-dft-d3-dispersion-to-/code/main.py", line 234, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-735-transferability-of-dft-d3-dispersion-to-/code/main.py", line 180, in main
    write_runtime_report(
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-735-transferability-of-dft-d3-dispersion-to-/code/main.py", line 70, in write_runtime_report
    report_path.parent.mkdir(parents=True, exist_ok=True)
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/pathlib.py", line 1116, in mkdir
    os.mkdir(self, mode)
FileExistsError: [Errno 17] File exists: 'data/derived'


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
