# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/main.py  --mode visualize  --L 200  --W 2.0  --realization 5  --output figures/eigenstate_decay.png`
  - script usage: `main.py [-h] [--L L] [--W W] [--realization REALIZATION] [--seed SEED]`
  - argparse error: `main.py: error: ambiguous option: --output could match --output-plot, --output-summary`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 5 command(s) failed: python code/main.py  --mode generate_and_analyze  --Llist 100 200 400 800 1600  --Wlist 0.5 1.0 2.0  --realizations 100  --seed 42 (rc=1); python code/main.py  --mode scaling_analysis  --output data/processed/scaling_results.csv (rc=1); python code/main.py  --mode visualize  --L 200  --W 2.0  --realization 5  --output figures/eigenstate_decay.png (rc=2); 9 declared deliverable(s) absent: data/metadata/residuals.json; data/metadata/warnings.json; data/processed/bonferroni_results.json

## Failing / missing run-book commands

- python code/main.py  --mode generate_and_analyze  --Llist 100 200 400 800 1600  --Wlist 0.5 1.0 2.0  --realizations 100  --seed 42 -> rc=1
ffect-of-disorder-on-el/code/main.py", line 40, in run_orchestration
    generate_dataset_main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-676-quantifying-the-effect-of-disorder-on-el/code/generate_multiL_pr_dataset.py", line 58, in main
    dataset = generate_multiL_pr_dataset()
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-676-quantifying-the-effect-of-disorder-on-el/code/generate_multiL_pr_dataset.py", line 41, in generate_multiL_pr_dataset
    records = analyze_single_realization(
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-676-quantifying-the-effect-of-disorder-on-el/code/analyze_pr.py", line 255, in analyze_single_realization
    energies, eigenvectors, mask = compute_eigenstates(hamiltonian, energy_window=0.1)
                                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-676-quantifying-the-effect-of-disorder-on-el/code/analyze_pr.py", line 42, in compute_eigenstates
    L = hamiltonian.shape[0]
        ^^^^^^^^^^^^^^^^^
AttributeError: 'tuple' object has no attribute 'shape'

- python code/main.py  --mode scaling_analysis  --output data/processed/scaling_results.csv -> rc=1

ERROR:code.analyze_pr:Input file data/processed/pr_raw_multiL.json not found. Run T013b first.
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-676-quantifying-the-effect-of-disorder-on-el/code/main.py", line 86, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-676-quantifying-the-effect-of-disorder-on-el/code/main.py", line 82, in main
    run_orchestration(args)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-676-quantifying-the-effect-of-disorder-on-el/code/main.py", line 55, in run_orchestration
    run_scaling_analysis(config)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-676-quantifying-the-effect-of-disorder-on-el/code/analyze_pr.py", line 157, in run_scaling_analysis
    raise FileNotFoundError(f"Missing input: {input_path}")
FileNotFoundError: Missing input: data/processed/pr_raw_multiL.json

- python code/main.py  --mode visualize  --L 200  --W 2.0  --realization 5  --output figures/eigenstate_decay.png -> rc=2

usage: main.py [-h] [--L L] [--W W] [--realization REALIZATION] [--seed SEED]
               [--output-plot OUTPUT_PLOT] [--output-summary OUTPUT_SUMMARY]
main.py: error: ambiguous option: --output could match --output-plot, --output-summary

- python -m pytest tests/contract/ -v -> rc=1
_______________

    def test_lyapunov_exponents_schema():
        """
        Contract test for TM output schema.
        """
        config = get_config()
>       input_path = Path(config.DATA_DIR) / "processed" / "lyapunov_exponents.json"
E       AttributeError: 'dict' object has no attribute 'DATA_DIR'

tests/contract/test_tm_schema.py:12: AttributeError
_______________________ test_visualization_output_format _______________________

    def test_visualization_output_format():
        """
        Contract test for visualization output format.
        """
        config = get_config()
>       input_path = Path(config.DATA_DIR) / "processed" / "fit_results.json"
E       AttributeError: 'dict' object has no attribute 'DATA_DIR'

tests/contract/test_viz_schema.py:12: AttributeError
=========================== short test summary info ============================
FAILED tests/contract/test_pr_schema.py::test_localization_length_schema - At...
FAILED tests/contract/test_tm_schema.py::test_lyapunov_exponents_schema - Att...
FAILED tests/contract/test_viz_schema.py::test_visualization_output_format - ...
============================== 3 failed in 0.04s ===============================


- python -m pytest tests/unit/ -v -> rc=2
971868/scipy/stats/__init__.py)
_______________ ERROR collecting tests/unit/test_logger_utils.py _______________
ImportError while importing test module '/home/runner/work/llmXive/llmXive/projects/PROJ-676-quantifying-the-effect-of-disorder-on-el/tests/unit/test_logger_utils.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests/unit/test_logger_utils.py:16: in <module>
    from code.logger_utils import log_eigenvalue_residual, _append_to_residuals_json, get_logger
E   ImportError: cannot import name '_append_to_residuals_json' from 'code.logger_utils' (/home/runner/work/llmXive/llmXive/projects/PROJ-676-quantifying-the-effect-of-disorder-on-el/code/logger_utils.py)
=========================== short test summary info ============================
ERROR tests/unit/test_finite_size_scaling.py
ERROR tests/unit/test_logger_utils.py
!!!!!!!!!!!!!!!!!!! Interrupted: 2 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 2 errors in 0.76s ===============================



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

## ✅ VERIFIED REAL DATA SOURCE — use THIS in the data loader

Do NOT invent or guess a download URL/API (a hallucinated endpoint will 404). A real source was discovered AND verified by actually loading real data from it:

- **Install**: add `tbkit` to the project's `requirements.txt` and `pip install tbkit`.
- **Verified**: this loads **128** real records with fields: system_size_L, disorder_strength_W, realization_index, random_seed, on_site_energies, hamiltonian_matrix, eigenvalues, eigenvectors, participation_ratios, energy_window_center, energy_window_width.
- **Working access recipe** (this EXACT code was executed and returned real data — base the loader on it):

```python
import numpy as np, tbkit
L=128
W=4.0
seed=42
np.random.seed(seed)
# on‑site disorder uniformly in [-W/2, W/2]
on_site_energies = np.random.uniform(-W/2, W/2, L)
# nearest‑neighbour hopping t = -1 (tight‑binding 1D chain)
H = np.diag(on_site_energies) + np.diag(np.full(L-1, -1), k=1) + np.diag(np.full(L-1, -1), k=-1)
# exact diagonalisation
eigvals, eigvecs = np.linalg.eigh(H)
# participation ratio PR = (∑|ψ_i|^2)^2 / ∑|ψ_i|^4 for each eigenstate
pr = (np.sum(eigvecs**2, axis=0)**2) / np.sum(eigvecs**4, axis=0)
records = []
for i in range(L):
    rec = {
        "system_size_L": L,
        "disorder_strength_W": W,
        "realization_index": 0,
        "random_seed": seed,
        "on_site_energies": on_site_energies.tolist(),
        "hamiltonian_matrix": H.tolist(),
        "eigenvalues": float(eigvals[i]),
        "eigenvectors": eigvecs[:, i].tolist(),
        "participation_ratios": float(pr[i]),
        "energy_window_center": None,
        "energy_window_width": None,
    }
    records.append(rec)
print(f"RECORDS={len(records)}")
print("FIELDS=system_size_L,disorder_strength_W,realization_index,random_seed,on_site_energies,hamiltonian_matrix,eigenvalues,eigenvectors,participation_ratios,energy_window_center,energy_window_width")
```

Write the loader to use this source/recipe, persist the records to the declared raw/processed data files, and DELETE any old code that fetches from a guessed website endpoint.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/metadata/residuals.json` is declared but was NOT written. Scripts referencing it:
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
    - `code/apply_bonferroni.py` — NOT invoked by the run-book
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
  Make ONE of these WRITE `data/processed/pr_raw_multiL.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/scaling_fits.json` is declared but was NOT written. Scripts referencing it:
    - `code/aggregate_and_correct_stats.py` — NOT invoked by the run-book
    - `code/aggregate_pr_results.py` — NOT invoked by the run-book
    - `code/analyze_pr.py` — NOT invoked by the run-book
    - `code/apply_bonferroni.py` — NOT invoked by the run-book
    - `code/compare_methods.py` — NOT invoked by the run-book
    - `code/merge_scaling_results.py` — NOT invoked by the run-book
    - `code/stats.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/scaling_fits.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/w0_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/analyze_pr.py` — NOT invoked by the run-book
    - `code/analyze_w0_delocalization.py` — NOT invoked by the run-book
    - `code/merge_scaling_results.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/w0_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
