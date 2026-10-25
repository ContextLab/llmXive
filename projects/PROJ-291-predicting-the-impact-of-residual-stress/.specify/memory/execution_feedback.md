# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/src/data/gen_synthetic.py: synthetic/fake INPUT data not authorized by the spec — “…xports the deterministic synthetic dataset generator defined in the…”
- src/data/__init__.py: synthetic/fake INPUT data not authorized by the spec — “…generating deterministic synthetic datasets used for pipeline valida…”
- src/data/gen_synthetic.py: synthetic/fake INPUT data not authorized by the spec — “…---------- Deterministic synthetic dataset generator for pipeline v…”
- src/data/gen_synthetic.py: synthetic/fake INPUT data not authorized by the spec — “…Create a deterministic synthetic fatigue dataset.      Parameters     ---…”
- src/data/gen_synthetic.py: synthetic/fake INPUT data not authorized by the spec — “…dex=False)     log.info("Synthetic dataset written to %s (%d rows)"…”

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python -m src.ingest.ingest          # creates unified_fatigue.csv & missing_flags.json`
  - script usage: `ingest.py [-h] [--output OUTPUT] [--raw RAW [RAW ...]]`
  - argparse error: `ingest.py: error: unrecognized arguments: # creates unified_fatigue.csv & missing_flags.json`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 5 fabricated/simulated-result signal(s) — results are not real measurements: code/src/data/gen_synthetic.py: synthetic/fake INPUT data not authorized by the spec — “…xports the deterministic synthetic dataset generator defined in the…”; src/data/__init__.py: synthetic/fake INPUT data not authorized by the spec — “…generating deterministic synthetic datasets used for pipeline valida…”; src/data/gen_synthetic.py: synthetic/fake INPUT data not authorized by the spec — “…---------- Deterministic synthetic dataset generator for pipeline v…”; 11 command(s) failed: bash scripts/env_check.sh (rc=1); python -m src.ingest.ingest          # creates unified_fatigue.csv & missing_flags.json (rc=2); python -m src.preprocess.validate    # validates against contracts/dataset_schema.yaml (rc=1); 9 declared deliverable(s) absent: data/external/acquisition_log.json; data/processed/balanced_measured.csv; data/processed/missing_flags.json

## Failing / missing run-book commands

- bash scripts/env_check.sh -> rc=1

2026-10-25 04:10:29,273 INFO openml.config: Error opening file /home/runner/work/llmXive/llmXive/projects/PROJ-291-predicting-the-impact-of-residual-stress/.runtime-home/.config/openml/config: not readable
2026-10-25 04:10:29,273 WARNING openml: No permission to create OpenML directory at /home/runner/work/llmXive/llmXive/projects/PROJ-291-predicting-the-impact-of-residual-stress/.runtime-home/.config/openml! This can result in OpenML-Python not working properly.
2026-10-25 04:10:29,369 ERROR __main__: Missing required package ucimlrepo: No module named 'ucimlrepo'
2026-10-25 04:10:29,369 ERROR __main__: Environment validation failed: No module named 'ucimlrepo'

- python -m src.ingest.ingest          # creates unified_fatigue.csv & missing_flags.json -> rc=2

usage: ingest.py [-h] [--output OUTPUT] [--raw RAW [RAW ...]]
                 [--limit-rows LIMIT_ROWS]
ingest.py: error: unrecognized arguments: # creates unified_fatigue.csv & missing_flags.json

- python -m src.preprocess.validate    # validates against contracts/dataset_schema.yaml -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-291-predicting-the-impact-of-residual-stress/bin/python: Error while finding module specification for 'src.preprocess.validate' (ModuleNotFoundError: No module named 'src.preprocess')

- python -m src.features.build_sets -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-291-predicting-the-impact-of-residual-stress/bin/python: Error while finding module specification for 'src.features.build_sets' (ModuleNotFoundError: No module named 'src.features')

- python -m src.models.train --feature-set A -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-291-predicting-the-impact-of-residual-stress/bin/python: Error while finding module specification for 'src.models.train' (ModuleNotFoundError: No module named 'src.models')

- python -m src.models.train --feature-set B -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-291-predicting-the-impact-of-residual-stress/bin/python: Error while finding module specification for 'src.models.train' (ModuleNotFoundError: No module named 'src.models')

- python -m src.models.train --feature-set C -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-291-predicting-the-impact-of-residual-stress/bin/python: Error while finding module specification for 'src.models.train' (ModuleNotFoundError: No module named 'src.models')

- python -m src.models.evaluate --compare A B   # Wilcoxon test + Bonferroni‑corrected significance -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-291-predicting-the-impact-of-residual-stress/bin/python: Error while finding module specification for 'src.models.evaluate' (ModuleNotFoundError: No module named 'src.models')

- python -m src.models.evaluate --cross-material   # transfer ΔMAPE + permutation test -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-291-predicting-the-impact-of-residual-stress/bin/python: Error while finding module specification for 'src.models.evaluate' (ModuleNotFoundError: No module named 'src.models')

- python -m src.mediation.bootstrap_mediation --resamples 10000 -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-291-predicting-the-impact-of-residual-stress/bin/python: Error while finding module specification for 'src.mediation.bootstrap_mediation' (ModuleNotFoundError: No module named 'src.mediation')

- python -m pytest -q -> rc=2
 import_module
    return _bootstrap._gcd_import(name[level:], package, level)
code/tests/test_train.py:17: in <module>
    from src.train import main as train_main
E   ModuleNotFoundError: No module named 'src.train'
_ ERROR collecting projects/PROJ-291-predicting-the-impact-of-residual-stress/code/tests/test_wilcoxon.py _
ImportError while importing test module '/home/runner/work/llmXive/llmXive/projects/PROJ-291-predicting-the-impact-of-residual-stress/code/tests/test_wilcoxon.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
code/tests/test_wilcoxon.py:14: in <module>
    from src.wilcoxon_compare import _compute_group_stats, run_wilcoxon_analysis
E   ModuleNotFoundError: No module named 'src.wilcoxon_compare'
=========================== short test summary info ============================
ERROR code/tests/test_acquire.py
ERROR code/tests/test_train.py
ERROR code/tests/test_wilcoxon.py
!!!!!!!!!!!!!!!!!!! Interrupted: 3 errors during collection !!!!!!!!!!!!!!!!!!!!
3 errors in 1.01s



## Declared deliverables still missing

- data/external/acquisition_log.json
- data/processed/balanced_measured.csv
- data/processed/missing_flags.json
- data/processed/unified_fatigue.csv
- data/raw/synthetic_fatigue.csv
- data/results/model_performance.csv
- data/results/proxy_agreement.csv
- data/results/runtime_summary.csv
- data/results/wilcoxon_results.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/external/acquisition_log.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/acquire_external.py` — NOT invoked by the run-book
    - `code/tests/test_acquire.py` — NOT invoked by the run-book
    - `src/acquire_external.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/external/acquisition_log.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/balanced_measured.csv` is declared but was NOT written. Scripts referencing it:
    - `code/src/build_features.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/balanced_measured.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/missing_flags.json` is declared but was NOT written. Scripts referencing it:
    - `code/ingest/ingest.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/missing_flags.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/unified_fatigue.csv` is declared but was NOT written. Scripts referencing it:
    - `code/ingest/ingest.py` — NOT invoked by the run-book
    - `code/src/build_features.py` — NOT invoked by the run-book
    - `code/src/proxy_agreement.py` — NOT invoked by the run-book
    - `code/src/run_e2e.py` — NOT invoked by the run-book
    - `code/tests/test_e2e.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/unified_fatigue.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/synthetic_fatigue.csv` is declared but was NOT written. Scripts referencing it:
    - `code/ingest/ingest.py` — NOT invoked by the run-book
    - `code/tests/test_gen_synthetic.py` — NOT invoked by the run-book
    - `src/data/gen_synthetic.py` — IS a run-book command
  Make ONE of these WRITE `data/raw/synthetic_fatigue.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/model_performance.csv` is declared but was NOT written. Scripts referencing it:
    - `code/src/train.py` — NOT invoked by the run-book
    - `code/tests/test_train.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/model_performance.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/proxy_agreement.csv` is declared but was NOT written. Scripts referencing it:
    - `code/src/proxy_agreement.py` — NOT invoked by the run-book
    - `code/src/run_e2e.py` — NOT invoked by the run-book
    - `code/tests/test_e2e.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/proxy_agreement.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/runtime_summary.csv` is declared but was NOT written. Scripts referencing it:
    - `code/src/run_e2e.py` — NOT invoked by the run-book
    - `code/src/timing.py` — NOT invoked by the run-book
    - `code/tests/test_e2e.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/runtime_summary.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/wilcoxon_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/src/wilcoxon_compare.py` — NOT invoked by the run-book
    - `code/tests/test_wilcoxon.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/wilcoxon_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
