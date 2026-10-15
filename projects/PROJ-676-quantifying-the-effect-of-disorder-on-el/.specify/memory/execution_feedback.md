# Execution failures — fix these before the analysis can run

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/raw/hamiltonians/H_W0.5_L100_idx0.h5) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/main.py  --mode visualize  --L 200  --W 2.0  --realization 5  --output figures/eigenstate_decay.png`
  - script usage: `main.py [-h] --L L --W W --realization REALIZATION --output OUTPUT`
  - argparse error: `main.py: error: unrecognized arguments: --mode visualize`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: every produced artifact is gitignored (data/raw/hamiltonians/H_W0.5_L100_idx0.h5) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 4 command(s) failed: python code/main.py  --mode generate_and_analyze  --Llist 100 200 400 800 1600  --Wlist 0.5 1.0 2.0  --realizations 100  --seed 42 (rc=1); python code/main.py  --mode scaling_analysis  --output data/processed/scaling_results.csv (rc=1); python code/main.py  --mode visualize  --L 200  --W 2.0  --realization 5  --output figures/eigenstate_decay.png (rc=2); 9 declared deliverable(s) absent: data/metadata/residuals.json; data/metadata/warnings.json; data/processed/bonferroni_results.json

## Failing / missing run-book commands

- python code/main.py  --mode generate_and_analyze  --Llist 100 200 400 800 1600  --Wlist 0.5 1.0 2.0  --realizations 100  --seed 42 -> rc=1
n-el/code/generate_multiL_pr_dataset.py", line 38, in generate_multiL_pr_dataset
    records = analyze_single_realization(
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-676-quantifying-the-effect-of-disorder-on-el/code/analyze_pr.py", line 327, in analyze_single_realization
    hamiltonian = generate_hamiltonian(L, W, seed=seed, realization_index=realization_index)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-676-quantifying-the-effect-of-disorder-on-el/code/generate_hamiltonian.py", line 56, in generate_hamiltonian
    save_hamiltonian_to_hdf5(
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-676-quantifying-the-effect-of-disorder-on-el/code/storage_utils.py", line 78, in save_hamiltonian_to_hdf5
    log_provenance_entry({
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-676-quantifying-the-effect-of-disorder-on-el/code/storage_utils.py", line 39, in log_provenance_entry
    raise ValueError(f"Provenance entry missing required field: {field}")
ValueError: Provenance entry missing required field: realization_index

- python code/main.py  --mode scaling_analysis  --output data/processed/scaling_results.csv -> rc=1

2026-10-15 05:34:51,349 - code.analyze_pr - ERROR - Input file data/processed/pr_raw_multiL.json not found. Run the dataset generator first.
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-676-quantifying-the-effect-of-disorder-on-el/code/main.py", line 86, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-676-quantifying-the-effect-of-disorder-on-el/code/main.py", line 82, in main
    run_orchestration(args)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-676-quantifying-the-effect-of-disorder-on-el/code/main.py", line 55, in run_orchestration
    run_scaling_analysis(config)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-676-quantifying-the-effect-of-disorder-on-el/code/analyze_pr.py", line 233, in run_scaling_analysis
    raise FileNotFoundError(f"Missing input: {input_path}")
FileNotFoundError: Missing input: data/processed/pr_raw_multiL.json

- python code/main.py  --mode visualize  --L 200  --W 2.0  --realization 5  --output figures/eigenstate_decay.png -> rc=2

usage: main.py [-h] --L L --W W --realization REALIZATION --output OUTPUT
main.py: error: unrecognized arguments: --mode visualize

- python -m pytest tests/unit/ -v -> rc=2
ffect-of-disorder-on-el/code/apply_bonferroni.py)
___________ ERROR collecting tests/unit/test_finite_size_scaling.py ____________
ImportError while importing test module '/home/runner/work/llmXive/llmXive/projects/PROJ-676-quantifying-the-effect-of-disorder-on-el/tests/unit/test_finite_size_scaling.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests/unit/test_finite_size_scaling.py:12: in <module>
    from code.finite_size_scaling import (
code/finite_size_scaling.py:17: in <module>
    from scipy.stats import r2_score
E   ImportError: cannot import name 'r2_score' from 'scipy.stats' (/home/runner/.cache/llmxive/base-env/py311-6f1866971868/scipy/stats/__init__.py)
=========================== short test summary info ============================
ERROR tests/unit/test_bonferroni.py
ERROR tests/unit/test_finite_size_scaling.py
!!!!!!!!!!!!!!!!!!! Interrupted: 2 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 2 errors in 0.56s ===============================



## Declared deliverables still missing

- data/metadata/residuals.json
- data/metadata/warnings.json
- data/processed/bonferroni_results.json
- data/processed/global_regression.json
- data/processed/lyapunov_exponents.json
- data/processed/method_agreement_report.json
- data/processed/pr_raw_multiL.json
- data/processed/scaling_fits.json
- data/processed/w0_results.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/metadata/residuals.json` is declared but was NOT written. Scripts referencing it:
    - `code/analyze_pr.py` — NOT invoked by the run-book
    - `code/generate_hamiltonian.py` — NOT invoked by the run-book
    - `code/logger.py` — NOT invoked by the run-book
    - `code/logger_utils.py` — NOT invoked by the run-book
    - `code/residual_logger.py` — NOT invoked by the run-book
    - `code/run_residual_logger.py` — NOT invoked by the run-book
    - `code/stats.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/metadata/residuals.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/metadata/warnings.json` is declared but was NOT written. Scripts referencing it:
    - `code/analyze_pr.py` — NOT invoked by the run-book
    - `code/finite_size_scaling.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/metadata/warnings.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/bonferroni_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/aggregate_and_correct_stats.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/bonferroni_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/global_regression.json` is declared but was NOT written. Scripts referencing it:
    - `code/aggregate_and_correct_stats.py` — NOT invoked by the run-book
    - `code/validate_slope_test.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/global_regression.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/lyapunov_exponents.json` is declared but was NOT written. Scripts referencing it:
    - `code/analyze_tm.py` — NOT invoked by the run-book
    - `code/compare_methods.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/lyapunov_exponents.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/method_agreement_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/compare_methods.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/method_agreement_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/pr_raw_multiL.json` is declared but was NOT written. Scripts referencing it:
    - `code/analyze_pr.py` — NOT invoked by the run-book
    - `code/finite_size_scaling.py` — NOT invoked by the run-book
    - `code/generate_multiL_pr_dataset.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
    - `code/visualize.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/pr_raw_multiL.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/scaling_fits.json` is declared but was NOT written. Scripts referencing it:
    - `code/aggregate_and_correct_stats.py` — NOT invoked by the run-book
    - `code/aggregate_pr_results.py` — NOT invoked by the run-book
    - `code/analyze_pr.py` — NOT invoked by the run-book
    - `code/compare_methods.py` — NOT invoked by the run-book
    - `code/merge_scaling_results.py` — NOT invoked by the run-book
    - `code/stats.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/scaling_fits.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/w0_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/analyze_pr.py` — NOT invoked by the run-book
    - `code/analyze_w0_delocalization.py` — NOT invoked by the run-book
    - `code/merge_scaling_results.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/w0_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
