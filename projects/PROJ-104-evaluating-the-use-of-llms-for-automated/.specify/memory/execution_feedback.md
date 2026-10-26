# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/power_analysis.py: self-declared fabricated metric — “…les, 3))      # Construct the simulated scores matrix:     #   mean + sqrt(…”
- code/statistical_analysis.py: self-declared fabricated metric — “…rics CSV is empty – producing placeholder results.")     # Metrics we care abo…”

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python -m src.run_pipeline --full --samples 500`
  - script usage: `run_pipeline.py [-h] [--sample SAMPLE] [--full]`
  - argparse error: `run_pipeline.py: error: unrecognized arguments: --samples 500`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 fabricated/simulated-result signal(s) — results are not real measurements: code/power_analysis.py: self-declared fabricated metric — “…les, 3))      # Construct the simulated scores matrix:     #   mean + sqrt(…”; code/statistical_analysis.py: self-declared fabricated metric — “…rics CSV is empty – producing placeholder results.")     # Metrics we care abo…”; 3 command(s) failed: python -m pytest tests/contract/ (rc=1); python -m pytest tests/unit/ (rc=2); python -m src.run_pipeline --full --samples 500 (rc=2); 2 declared deliverable(s) absent: data/processed/fidelity_metrics.csv; data/raw/commit_pairs.csv

## Failing / missing run-book commands

- python -m pytest tests/contract/ -> rc=1
air`` schema."""
        csv_path = paths.data("raw", "commit_pairs.csv")
>       assert csv_path.exists(), f"{csv_path} does not exist"
E       AssertionError: /home/runner/work/llmXive/llmXive/projects/PROJ-104-evaluating-the-use-of-llms-for-automated/data/raw/commit_pairs.csv does not exist
E       assert False
E        +  where False = <bound method Path.exists of PosixPath('/home/runner/work/llmXive/llmXive/projects/PROJ-104-evaluating-the-use-of-llms-for-automated/data/raw/commit_pairs.csv')>()
E        +    where <bound method Path.exists of PosixPath('/home/runner/work/llmXive/llmXive/projects/PROJ-104-evaluating-the-use-of-llms-for-automated/data/raw/commit_pairs.csv')> = PosixPath('/home/runner/work/llmXive/llmXive/projects/PROJ-104-evaluating-the-use-of-llms-for-automated/data/raw/commit_pairs.csv').exists

tests/contract/test_schemas.py:56: AssertionError
=========================== short test summary info ============================
FAILED tests/contract/test_commitpair_schema.py::test_commitpair_csv_schema
FAILED tests/contract/test_schemas.py::test_commitpair_schema - AssertionErro...
========================= 2 failed, 5 passed in 0.25s ==========================


- python -m pytest tests/unit/ -> rc=2
-evaluating-the-use-of-llms-for-automated/tests/unit/test_entity_extraction_intent.py _
ImportError while importing test module '/home/runner/work/llmXive/llmXive/projects/PROJ-104-evaluating-the-use-of-llms-for-automated/tests/unit/test_entity_extraction_intent.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests/unit/test_entity_extraction_intent.py:21: in <module>
    from code.entity_extraction_intent import run_extraction, DEFAULT_OUTPUT_DIR, DEFAULT_CSV, DEFAULT_REPOS_ROOT
E   ImportError: cannot import name 'DEFAULT_OUTPUT_DIR' from 'code.entity_extraction_intent' (/home/runner/work/llmXive/llmXive/projects/PROJ-104-evaluating-the-use-of-llms-for-automated/code/entity_extraction_intent.py)
=========================== short test summary info ============================
ERROR tests/unit/test_entity_extraction_intent.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
=============================== 1 error in 0.52s ===============================


- python -m src.run_pipeline --full --samples 500 -> rc=2

usage: run_pipeline.py [-h] [--sample SAMPLE] [--full]
run_pipeline.py: error: unrecognized arguments: --samples 500


## Declared deliverables still missing

- data/processed/fidelity_metrics.csv
- data/raw/commit_pairs.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/fidelity_metrics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/fidelity_scoring.py` — NOT invoked by the run-book
    - `code/statistical_analysis.py` — NOT invoked by the run-book
    - `code/visualization.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/fidelity_metrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/commit_pairs.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data_extraction.py` — NOT invoked by the run-book
    - `code/entity_extraction_intent.py` — NOT invoked by the run-book
    - `code/entity_extraction_surface.py` — NOT invoked by the run-book
    - `code/fidelity_scoring.py` — NOT invoked by the run-book
    - `code/gold_annotation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/commit_pairs.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `.github/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
