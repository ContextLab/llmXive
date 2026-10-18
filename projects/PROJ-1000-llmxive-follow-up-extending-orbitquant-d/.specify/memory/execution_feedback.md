# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/run_router_inference.py: self-declared fabricated metric — “…entropy, matrix index, and a placeholder metric structure.…”
- code/runners/router_inference_runner.py: self-declared fabricated metric — “…# For this runner, we simulate the metric collection structure.…”
- code/analysis/clustering.py: synthetic/fake INPUT data not authorized by the spec — “…cluster center values to generate synthetic activations         # th…”
- code/run_quantization_validation.py: synthetic/fake INPUT data not authorized by the spec — “…# We'll create a dummy input to the model's main bloc…”

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/raw/coco_captions/captions.csv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/main.py --phase correlation`
  - script usage: `main.py [-h] --phase {init,validate}`
  - argparse error: `main.py: error: argument --phase: invalid choice: 'correlation' (choose from 'init', 'validate')`
- run-book command: `python code/main.py --phase clustering`
  - script usage: `main.py [-h] --phase {init,validate}`
  - argparse error: `main.py: error: argument --phase: invalid choice: 'clustering' (choose from 'init', 'validate')`
- run-book command: `python code/main.py --phase router`
  - script usage: `main.py [-h] --phase {init,validate}`
  - argparse error: `main.py: error: argument --phase: invalid choice: 'router' (choose from 'init', 'validate')`
- run-book command: `python code/main.py --phase evaluation`
  - script usage: `main.py [-h] --phase {init,validate}`
  - argparse error: `main.py: error: argument --phase: invalid choice: 'evaluation' (choose from 'init', 'validate')`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 fabricated/simulated-result signal(s) — results are not real measurements: code/run_router_inference.py: self-declared fabricated metric — “…entropy, matrix index, and a placeholder metric structure.…”; code/runners/router_inference_runner.py: self-declared fabricated metric — “…# For this runner, we simulate the metric collection structure.…”; code/analysis/clustering.py: synthetic/fake INPUT data not authorized by the spec — “…cluster center values to generate synthetic activations         # th…”; every produced artifact is gitignored (data/raw/coco_captions/captions.csv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 7 command(s) failed: python code/data/preprocess.py (rc=1); python code/main.py --phase correlation (rc=2); python code/main.py --phase clustering (rc=2); 6 declared deliverable(s) absent: data/processed/clustering_report.json; data/processed/correlation_results.json; data/processed/diverse_prompts.csv

## Failing / missing run-book commands

- python code/data/preprocess.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1000-llmxive-follow-up-extending-orbitquant-d/code/data/preprocess.py", line 72, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1000-llmxive-follow-up-extending-orbitquant-d/code/data/preprocess.py", line 51, in main
    raise RuntimeError(f"Diverse prompts file missing at {diverse_path}. Run download_diverse_prompts.py first.")
RuntimeError: Diverse prompts file missing at data/processed/diverse_prompts.csv. Run download_diverse_prompts.py first.

- python code/main.py --phase correlation -> rc=2

usage: main.py [-h] --phase {init,validate}
main.py: error: argument --phase: invalid choice: 'correlation' (choose from 'init', 'validate')

- python code/main.py --phase clustering -> rc=2

usage: main.py [-h] --phase {init,validate}
main.py: error: argument --phase: invalid choice: 'clustering' (choose from 'init', 'validate')

- python code/main.py --phase router -> rc=2

usage: main.py [-h] --phase {init,validate}
main.py: error: argument --phase: invalid choice: 'router' (choose from 'init', 'validate')

- python code/main.py --phase evaluation -> rc=2

usage: main.py [-h] --phase {init,validate}
main.py: error: argument --phase: invalid choice: 'evaluation' (choose from 'init', 'validate')

- python -m pytest tests/unit/ -> rc=2
tquant-d/tests/unit/test_validate_clustering.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests/unit/test_validate_clustering.py:15: in <module>
    from validation.validate_clustering import (
E   ImportError: cannot import name 'REQUIRED_TOP_LEVEL_KEYS' from 'validation.validate_clustering' (/home/runner/work/llmXive/llmXive/projects/PROJ-1000-llmxive-follow-up-extending-orbitquant-d/code/validation/validate_clustering.py)
=========================== short test summary info ============================
ERROR tests/unit/test_clustering.py - FileNotFoundError: [Errno 2] No such fi...
ERROR tests/unit/test_download_diverse_prompts.py
ERROR tests/unit/test_load_matrices.py
ERROR tests/unit/test_preprocess.py
ERROR tests/unit/test_router_inference.py
ERROR tests/unit/test_timing.py
ERROR tests/unit/test_validate_clustering.py
!!!!!!!!!!!!!!!!!!! Interrupted: 7 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 7 errors in 5.43s ===============================


- python -m pytest tests/integration/ -> rc=2
ive/projects/PROJ-1000-llmxive-follow-up-extending-orbitquant-d/tests/integration/test_full_pipeline.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests/integration/test_full_pipeline.py:35: in <module>
    from evaluation.timing import measure_inference_time
code/evaluation/timing.py:36: in <module>
    from quantization.static_baseline import StaticRotationBaseline
E   ImportError: cannot import name 'StaticRotationBaseline' from 'quantization.static_baseline' (/home/runner/work/llmXive/llmXive/projects/PROJ-1000-llmxive-follow-up-extending-orbitquant-d/code/quantization/static_baseline.py)
=========================== short test summary info ============================
ERROR tests/integration/test_activation_variance.py
ERROR tests/integration/test_download_diverse_prompts.py
ERROR tests/integration/test_full_pipeline.py
!!!!!!!!!!!!!!!!!!! Interrupted: 3 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 3 errors in 5.12s ===============================



## Declared deliverables still missing

- data/processed/clustering_report.json
- data/processed/correlation_results.json
- data/processed/diverse_prompts.csv
- data/processed/entropy_scores.csv
- data/processed/final_evaluation_report.json
- data/processed/prompts.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/clustering_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/clustering.py` — NOT invoked by the run-book
    - `code/analysis/load_matrices.py` — NOT invoked by the run-book
    - `code/analysis/mse_validator.py` — NOT invoked by the run-book
    - `code/analysis/router.py` — NOT invoked by the run-book
    - `code/analysis/router_api_docs.py` — NOT invoked by the run-book
    - `code/config.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
    - `code/main_validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/clustering_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/correlation_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/clustering.py` — NOT invoked by the run-book
    - `code/analysis/generate_correlation_results.py` — NOT invoked by the run-book
    - `code/analysis/sensitivity.py` — NOT invoked by the run-book
    - `code/analysis/visualization.py` — NOT invoked by the run-book
    - `code/main_validation.py` — NOT invoked by the run-book
    - `code/run_correlation.py` — NOT invoked by the run-book
    - `code/validation/validate_correlation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/correlation_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/diverse_prompts.csv` is declared but was NOT written. Scripts referencing it:
    - `code/config.py` — NOT invoked by the run-book
    - `code/data/download_diverse_prompts.py` — NOT invoked by the run-book
    - `code/data/preprocess.py` — IS a run-book command
    - `code/evaluation/timing.py` — NOT invoked by the run-book
    - `code/run_correlation.py` — NOT invoked by the run-book
    - `code/run_evaluation.py` — NOT invoked by the run-book
    - `code/run_router_inference.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/diverse_prompts.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/entropy_scores.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/correlation.py` — NOT invoked by the run-book
    - `code/analysis/generate_correlation_results.py` — NOT invoked by the run-book
    - `code/analysis/sensitivity.py` — NOT invoked by the run-book
    - `code/analysis/visualization.py` — NOT invoked by the run-book
    - `code/run_router_inference_modular.py` — NOT invoked by the run-book
    - `code/runners/correlation_runner.py` — NOT invoked by the run-book
    - `code/runners/router_inference_runner.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/entropy_scores.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/final_evaluation_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/statistical_test.py` — NOT invoked by the run-book
    - `code/run_evaluation.py` — NOT invoked by the run-book
    - `code/run_evaluation_modular.py` — NOT invoked by the run-book
    - `code/utils/data_streaming.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/final_evaluation_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/prompts.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/correlation.py` — NOT invoked by the run-book
    - `code/analysis/sensitivity.py` — NOT invoked by the run-book
    - `code/config.py` — NOT invoked by the run-book
    - `code/data/download_diverse_prompts.py` — NOT invoked by the run-book
    - `code/data/preprocess.py` — IS a run-book command
    - `code/evaluation/metrics.py` — NOT invoked by the run-book
    - `code/evaluation/timing.py` — NOT invoked by the run-book
    - `code/run_correlation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/prompts.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
