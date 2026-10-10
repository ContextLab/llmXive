# Execution failures — fix these before the analysis can run

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- data/results/metrics.json: EVERY metric is null/NaN (world_score, sparse_consistency_score, fid, unified_geometric_error) — nothing was computed

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/main.py --phase evaluate`
  - script usage: `main.py [-h] [--thresholds THRESHOLDS [THRESHOLDS ...]]`
  - argparse error: `main.py: error: unrecognized arguments: --phase evaluate`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 hollow-result signal(s) — the analysis ran but computed nothing: data/results/metrics.json: EVERY metric is null/NaN (world_score, sparse_consistency_score, fid, unified_geometric_error) — nothing was computed; 4 command(s) failed: python code/main.py --phase data_prepare (rc=1); python code/main.py --phase compute_geometry (rc=1); python code/main.py --phase evaluate (rc=2); 1 declared deliverable(s) absent: data/raw/dense_baseline_frames.npy

## Failing / missing run-book commands

- python code/main.py --phase data_prepare -> rc=1
=== Phase: Data Preparation ===
Downloading dataset...

[download] Unable to reach https://huggingface.co/datasets/realestate10k. Check your internet connection.

- python code/main.py --phase compute_geometry -> rc=1
=== Phase: Compute Geometry ===
Running Solver...
No feature files found in /home/runner/work/llmXive/llmXive/projects/PROJ-843-llmxive-follow-up-extending-latent-spati/data/features

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-843-llmxive-follow-up-extending-latent-spati/code/main.py", line 188, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-843-llmxive-follow-up-extending-latent-spati/code/main.py", line 172, in main
    phase_compute_geometry()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-843-llmxive-follow-up-extending-latent-spati/code/main.py", line 75, in phase_compute_geometry
    solver_main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-843-llmxive-follow-up-extending-latent-spati/code/geometry/solver.py", line 259, in main
    print(f"Solver completed: {results['total_sequences']} sequences, "
                               ~~~~~~~^^^^^^^^^^^^^^^^^^^
KeyError: 'total_sequences'

- python code/main.py --phase evaluate -> rc=2
tency Score...
Solver output not found. Skipping Sparse-Consistency Score.
Calculating FID...
Computing Unified Geometric Error...
Metrics saved to /home/runner/work/llmXive/llmXive/projects/PROJ-843-llmxive-follow-up-extending-latent-spati/data/results/metrics.json
{
  "world_score": null,
  "sparse_consistency_score": null,
  "fid": null,
  "unified_geometric_error": null,
  "timestamp": "2026-10-10T00:58:59"
}
Running ANOVA...
Loaded 0 valid records for ANOVA

Running ANOVA for world_score...
  Error running ANOVA for world_score: Required column 'scenario' not found

Running ANOVA for sparse_consistency_score...
  Error running ANOVA for sparse_consistency_score: Required column 'scenario' not found

ANOVA results saved to /home/runner/work/llmXive/llmXive/projects/PROJ-843-llmxive-follow-up-extending-latent-spati/data/results/anova_results.json

--- ANOVA Summary ---
world_score: ERROR - Required column 'scenario' not found
sparse_consistency_score: ERROR - Required column 'scenario' not found
Running Sensitivity Analysis...

usage: main.py [-h] [--thresholds THRESHOLDS [THRESHOLDS ...]]
               [--output OUTPUT]
main.py: error: unrecognized arguments: --phase evaluate

- python -m pytest tests/ -v -> rc=2
t_validator.py - TypeError: can only concatena...
ERROR tests/test_aggregate_warps.py - TypeError: can only concatenate str (no...
ERROR tests/test_config_ensure_directories.py - TypeError: can only concatena...
ERROR tests/test_data_schemas.py
ERROR tests/test_download.py
ERROR tests/test_download_dense_baseline.py - TypeError: can only concatenate...
ERROR tests/test_ensure_directories.py - TypeError: can only concatenate str ...
ERROR tests/test_eval_sensitivity.py - TypeError: can only concatenate str (n...
ERROR tests/test_metrics.py - TypeError: can only concatenate str (not "NoneT...
ERROR tests/test_report_generation.py - TypeError: can only concatenate str (...
ERROR tests/test_schemas.py
ERROR tests/test_sensitivity.py - TypeError: can only concatenate str (not "N...
ERROR tests/test_stratify.py
ERROR tests/unit/test_feature_extraction.py - NameError: name 'Path' is not d...
ERROR tests/unit/test_metrics.py
ERROR tests/unit/test_solver.py - NameError: name 'Path' is not defined
ERROR tests/unit/test_stratify.py
!!!!!!!!!!!!!!!!!!! Interrupted: 18 errors during collection !!!!!!!!!!!!!!!!!!!
======================== 1 warning, 18 errors in 2.80s =========================



## Declared deliverables still missing

- data/raw/dense_baseline_frames.npy

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/raw/dense_baseline_frames.npy` is declared but was NOT written. Scripts referencing it:
    - `code/data/dense_baseline.py` — NOT invoked by the run-book
    - `code/eval/download_dense_baseline.py` — NOT invoked by the run-book
    - `code/eval/metrics.py` — NOT invoked by the run-book
    - `code/eval/quickstart_validator.py` — NOT invoked by the run-book
    - `code/eval/run_dense_baseline.py` — NOT invoked by the run-book
    - `code/eval/sensitivity.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/dense_baseline_frames.npy` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
