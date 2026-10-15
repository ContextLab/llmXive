# Execution failures — fix these before the analysis can run

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/raw/metadata.csv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python -m code.main`
  - script usage: `main.py [-h] path`
  - argparse error: `main.py: error: the following arguments are required: path`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: every produced artifact is gitignored (data/raw/metadata.csv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 6 command(s) failed: python -m code.main (rc=2); python code/analyze_energies.py (rc=1); python code/derive_scaling.py (rc=1); 3 declared deliverable(s) absent: data/derived/correlation_results.csv; data/derived/raw_energies.csv; data/raw/experimental_bulk_properties.csv

## Failing / missing run-book commands

- python -m code.main -> rc=2
ty-of-dft-d3-dispersion-to-/data/raw/IL-Benchmark.zip
2026-10-15 06:18:23,175 INFO code.download_il_benchmark: Fallback zip created with metadata.csv (/home/runner/work/llmXive/llmXive/projects/PROJ-735-transferability-of-dft-d3-dispersion-to-/data/raw/IL-Benchmark.zip)
2026-10-15 06:18:23,175 INFO code.download_il_benchmark: No checksum manifest found – skipping verification.
2026-10-15 06:18:23,175 INFO code.download_il_benchmark: Extracting /home/runner/work/llmXive/llmXive/projects/PROJ-735-transferability-of-dft-d3-dispersion-to-/data/raw/IL-Benchmark.zip to /home/runner/work/llmXive/llmXive/projects/PROJ-735-transferability-of-dft-d3-dispersion-to-/data/raw
2026-10-15 06:18:23,176 INFO code.download_il_benchmark: Extraction complete.
2026-10-15 06:18:23,176 INFO code.download_il_benchmark: Dataset ready – metadata located at /home/runner/work/llmXive/llmXive/projects/PROJ-735-transferability-of-dft-d3-dispersion-to-/data/raw/metadata.csv
2026-10-15 06:18:23,176 INFO __main__: === Finished stage: download_il_benchmark ===
2026-10-15 06:18:23,176 INFO __main__: === Starting stage: load_data ===
usage: main.py [-h] path
main.py: error: the following arguments are required: path

- python code/analyze_energies.py -> rc=1
 found – generating placeholder data.
Energy analysis failed: Metadata file not found: /home/runner/work/llmXive/llmXive/projects/data/raw/metadata.csv
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-735-transferability-of-dft-d3-dispersion-to-/code/analyze_energies.py", line 390, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-735-transferability-of-dft-d3-dispersion-to-/code/analyze_energies.py", line 369, in main
    df, stats = analyze_and_export(
                ^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-735-transferability-of-dft-d3-dispersion-to-/code/analyze_energies.py", line 281, in analyze_and_export
    df = _generate_placeholder_raw_energies(input_path)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-735-transferability-of-dft-d3-dispersion-to-/code/analyze_energies.py", line 207, in _generate_placeholder_raw_energies
    raise FileNotFoundError(f"Metadata file not found: {raw_metadata_path}")
FileNotFoundError: Metadata file not found: /home/runner/work/llmXive/llmXive/projects/data/raw/metadata.csv

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
============================== 5 errors in 1.00s ===============================



## Declared deliverables still missing

- data/derived/correlation_results.csv
- data/derived/raw_energies.csv
- data/raw/experimental_bulk_properties.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/derived/correlation_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/correlate_bulk.py` — IS a run-book command
    - `code/generate_reports.py` — IS a run-book command
  Make ONE of these WRITE `data/derived/correlation_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/derived/raw_energies.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analyze_energies.py` — IS a run-book command
    - `code/correlate_bulk.py` — IS a run-book command
    - `code/derive_scaling.py` — IS a run-book command
    - `code/generate_reports.py` — IS a run-book command
    - `code/main.py` — IS a run-book command
    - `code/write_scaling_results.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/raw_energies.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/experimental_bulk_properties.csv` is declared but was NOT written. Scripts referencing it:
    - `code/correlate_bulk.py` — IS a run-book command
    - `code/generate_reports.py` — IS a run-book command
    - `code/generate_synthetic_data.py` — NOT invoked by the run-book
    - `code/retrieve_bulk_properties.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/experimental_bulk_properties.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
