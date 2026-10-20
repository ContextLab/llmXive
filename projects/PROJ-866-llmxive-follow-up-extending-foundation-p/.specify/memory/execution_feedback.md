# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/generators/synthetic_workflow.py: self-declared fabricated metric — “…lates them with deterministic placeholder values based on the field type. Thi…”
- code/generators/synthetic_workflow.py: self-declared fabricated metric — “…"""Create a deterministic dummy value for a given field based on it…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 fabricated/simulated-result signal(s) — results are not real measurements: code/generators/synthetic_workflow.py: self-declared fabricated metric — “…lates them with deterministic placeholder values based on the field type. Thi…”; code/generators/synthetic_workflow.py: self-declared fabricated metric — “…"""Create a deterministic dummy value for a given field based on it…”; 4 run-book script(s) missing (plan/impl path mismatch): python src/cli/run_simulation.py --generate  --seed 42  --count 500; python src/cli/run_simulation.py --execute --mode full; python src/cli/run_simulation.py --execute --mode compressed  --depths 0,1,2,3,4,5,6,7,8,9,10; 1 command(s) failed: python -m pytest -v (rc=2); 4 declared deliverable(s) absent: data/processed/compressed_context_logs.json; data/processed/full_context_logs.json; data/raw/workflows.json

## Failing / missing run-book commands

- python src/cli/run_simulation.py --generate  --seed 42  --count 500 -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-866-llmxive-follow-up-extending-foundation-p/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-866-llmxive-follow-up-extending-foundation-p/src/cli/run_simulation.py': [Errno 2] No such file or directory

- python src/cli/run_simulation.py --execute --mode full -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-866-llmxive-follow-up-extending-foundation-p/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-866-llmxive-follow-up-extending-foundation-p/src/cli/run_simulation.py': [Errno 2] No such file or directory

- python src/cli/run_simulation.py --execute --mode compressed  --depths 0,1,2,3,4,5,6,7,8,9,10 -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-866-llmxive-follow-up-extending-foundation-p/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-866-llmxive-follow-up-extending-foundation-p/src/cli/run_simulation.py': [Errno 2] No such file or directory

- python src/cli/run_simulation.py --analyze  --bootstraps <large number>   # matches verified fact -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-866-llmxive-follow-up-extending-foundation-p/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-866-llmxive-follow-up-extending-foundation-p/src/cli/run_simulation.py': [Errno 2] No such file or directory

- python -m pytest -v -> rc=2
e/projects/PROJ-866-llmxive-follow-up-extending-foundation-p/tests/unit/test_generator.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests/unit/test_generator.py:7: in <module>
    from generators.synthetic_workflow import SyntheticWorkflowGenerator
generators/__init__.py:9: in <module>
    from code.generators.synthetic_workflow import SyntheticWorkflowGenerator  # noqa: F401
E   ImportError: cannot import name 'SyntheticWorkflowGenerator' from 'code.generators.synthetic_workflow' (/home/runner/work/llmXive/llmXive/projects/PROJ-866-llmxive-follow-up-extending-foundation-p/code/generators/synthetic_workflow.py)
=========================== short test summary info ============================
ERROR tests/contract/test_save_processed_logs_schema.py
ERROR tests/integration/test_compression.py
ERROR tests/unit/test_generator.py
!!!!!!!!!!!!!!!!!!! Interrupted: 3 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 3 errors in 1.39s ===============================



## Declared deliverables still missing

- data/processed/compressed_context_logs.json
- data/processed/full_context_logs.json
- data/raw/workflows.json
- figures/tradeoff_curve.png

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/compressed_context_logs.json` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — NOT invoked by the run-book
    - `code/utils/data_hygiene_audit.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/compressed_context_logs.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/full_context_logs.json` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — NOT invoked by the run-book
    - `code/utils/data_hygiene_audit.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/full_context_logs.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/workflows.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/tradeoff_model.py` — NOT invoked by the run-book
    - `code/analysis/vif_analyzer.py` — NOT invoked by the run-book
    - `code/engines/compressed_context.py` — NOT invoked by the run-book
    - `code/engines/full_context.py` — NOT invoked by the run-book
    - `code/engines/invalid_workflow_filter.py` — NOT invoked by the run-book
    - `code/generators/synthetic_workflow.py` — NOT invoked by the run-book
    - `code/main.py` — NOT invoked by the run-book
    - `code/services/executor.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/workflows.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `figures/tradeoff_curve.png` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/generate_regression_data.py` — NOT invoked by the run-book
    - `code/analysis/tradeoff_model.py` — NOT invoked by the run-book
    - `code/generate_paper_handoff.py` — NOT invoked by the run-book
    - `code/main.py` — NOT invoked by the run-book
    - `code/utils/data_hygiene_audit.py` — NOT invoked by the run-book
    - `code/utils/verify_data_consistency.py` — NOT invoked by the run-book
  Make ONE of these WRITE `figures/tradeoff_curve.png` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
