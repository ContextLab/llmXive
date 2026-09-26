# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/analysis/diverge.py: synthetic/fake INPUT data not authorized by the spec — “…on batch JSON (optional, generates synthetic if missing)")     parser…”
- code/analysis/diverge.py: synthetic/fake INPUT data not authorized by the spec — “…transitions}. Generating synthetic sample for demonstration.")…”
- code/analysis/diverge.py: synthetic/fake INPUT data not authorized by the spec — “…monstration.")         # Generate a small synthetic sample for demonstration…”
- code/analysis/synthetic_trace_generator.py: synthetic/fake INPUT data not authorized by the spec — “…ceGenerator:     """     Generates synthetic control traces with dete…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 fabricated/simulated-result signal(s) — results are not real measurements: code/analysis/diverge.py: synthetic/fake INPUT data not authorized by the spec — “…on batch JSON (optional, generates synthetic if missing)")     parser…”; code/analysis/diverge.py: synthetic/fake INPUT data not authorized by the spec — “…transitions}. Generating synthetic sample for demonstration.")…”; code/analysis/diverge.py: synthetic/fake INPUT data not authorized by the spec — “…monstration.")         # Generate a small synthetic sample for demonstration…”; 1 command(s) failed: python -m code.main --seed 42 (rc=1); 6 declared deliverable(s) absent: data/processed/divergence_report.json; data/processed/extracted_rules.json; data/processed/oracle_graph.json

## Failing / missing run-book commands

- python -m code.main --seed 42 -> rc=1
    2026-09-26 06:16:40,308 - main - INFO - Starting llmXive pipeline execution...

Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-908-llmxive-follow-up-extending-qwen-agentwo/code/main.py", line 44, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-908-llmxive-follow-up-extending-qwen-agentwo/code/main.py", line 21, in main
    if not check_code_drift(code_dir):
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: check_code_drift() missing 1 required positional argument: 'reference_checksum'

## Declared deliverables still missing

- data/processed/divergence_report.json
- data/processed/extracted_rules.json
- data/processed/oracle_graph.json
- data/processed/rule_precision.json
- data/raw/cot_traces.json
- data/raw/synthetic_control_traces.json

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### `check_code_drift` — defined in `code/utils/checksums.py`; called 2 way(s):

- code/main.py: if not check_code_drift(code_dir):
- code/oracle/generator.py: drift_check = check_code_drift([output_file], manifest)

Make `check_code_drift` in `code/utils/checksums.py` accept ALL of the above.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/divergence_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/diverge.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/divergence_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/extracted_rules.json` is declared but was NOT written. Scripts referencing it:
    - `code/rules/validator.py` — NOT invoked by the run-book
    - `code/rules/metrics.py` — NOT invoked by the run-book
    - `code/rules/uncertainty_flagger.py` — NOT invoked by the run-book
    - `code/analysis/metrics.py` — NOT invoked by the run-book
    - `code/analysis/diverge.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/extracted_rules.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/oracle_graph.json` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — NOT invoked by the run-book
    - `code/rules/validator.py` — NOT invoked by the run-book
    - `code/rules/metrics.py` — NOT invoked by the run-book
    - `code/oracle/generator.py` — NOT invoked by the run-book
    - `code/analysis/diverge.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/oracle_graph.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/rule_precision.json` is declared but was NOT written. Scripts referencing it:
    - `code/rules/metrics.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/rule_precision.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/cot_traces.json` is declared but was NOT written. Scripts referencing it:
    - `code/utils/loaders.py` — NOT invoked by the run-book
    - `code/utils/__init__.py` — NOT invoked by the run-book
    - `code/rules/trace_loader.py` — NOT invoked by the run-book
    - `code/inference/runner.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/cot_traces.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/synthetic_control_traces.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/synthetic_trace_generator.py` — NOT invoked by the run-book
    - `code/analysis/metrics.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/synthetic_control_traces.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
