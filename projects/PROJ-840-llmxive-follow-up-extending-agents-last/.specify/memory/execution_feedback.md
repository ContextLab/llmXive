# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/data/generator.py: synthetic/fake INPUT data not authorized by the spec — “…umentParser(description="Generate synthetic ALE execution traces")…”
- code/data/golden_set_generator.py: synthetic/fake INPUT data not authorized by the spec — “…er(         description="Generate automated synthetic ground truth subset (T01…”
- code/intervention/runner.py: synthetic/fake INPUT data not authorized by the spec — “…[ExecutionTrace]:     """Generate synthetic traces for execution whe…”
- code/intervention/runner.py: synthetic/fake INPUT data not authorized by the spec — “…ror:         # Fallback: generate synthetic traces         logger.wa…”

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/data/generator.py --seed 42 --num-tasks a sufficient batch size`
  - script usage: `generator.py [-h] --seed SEED [--num-tasks NUM_TASKS] [--output OUTPUT]`
  - argparse error: `generator.py: error: argument --num-tasks: invalid int value: 'a'`
- run-book command: `python code/utils/verify_checksums.py`
  - script usage: `verify_checksums.py [-h] --input INPUT [--seed SEED] [--output OUTPUT]`
  - argparse error: `verify_checksums.py: error: the following arguments are required: --input`
- run-book command: `python code/analysis/sensitivity.py --results data/processed/experiment_results.json --intervals,3,5 --output data/processed/sensitivity_analysis.json`
  - script usage: `sensitivity.py [-h] [--results RESULTS] [--intervals INTERVALS]`
  - argparse error: `sensitivity.py: error: unrecognized arguments: --intervals,3,5`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 fabricated/simulated-result signal(s) — results are not real measurements: code/data/generator.py: synthetic/fake INPUT data not authorized by the spec — “…umentParser(description="Generate synthetic ALE execution traces")…”; code/data/golden_set_generator.py: synthetic/fake INPUT data not authorized by the spec — “…er(         description="Generate automated synthetic ground truth subset (T01…”; code/intervention/runner.py: synthetic/fake INPUT data not authorized by the spec — “…[ExecutionTrace]:     """Generate synthetic traces for execution whe…”; 9 command(s) failed: python code/data/generator.py --seed 42 --num-tasks a sufficient batch size (rc=2); python code/utils/verify_checksums.py (rc=2); python code/classification/parser.py --input data/raw/synthetic_ale.jsonl --output data/processed/classified_traces.json (rc=1); 7 declared deliverable(s) absent: data/processed/classification_report.json; data/processed/sensitivity_N1.json; data/processed/sensitivity_N3.json

## Failing / missing run-book commands

- python code/data/generator.py --seed 42 --num-tasks a sufficient batch size -> rc=2
    usage: generator.py [-h] --seed SEED [--num-tasks NUM_TASKS] [--output OUTPUT]
generator.py: error: argument --num-tasks: invalid int value: 'a'
- python code/utils/verify_checksums.py -> rc=2
    usage: verify_checksums.py [-h] --input INPUT [--seed SEED] [--output OUTPUT]
verify_checksums.py: error: the following arguments are required: --input
- python code/classification/parser.py --input data/raw/synthetic_ale.jsonl --output data/processed/classified_traces.json -> rc=1
    Error parsing traces: Input file not found: data/raw/synthetic_ale.jsonl

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-840-llmxive-follow-up-extending-agents-last/code/classification/parser.py", line 135, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-840-llmxive-follow-up-extending-agents-last/code/classification/parser.py", line 123, in main
    parsed_data = parse_ale_trace(input_path)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-840-llmxive-follow-up-extending-agents-last/code/classification/parser.py", line 18, in parse_ale_trace
    raise FileNotFoundError(f"Input file not found: {input_path}")
FileNotFoundError: Input file not found: data/raw/synthetic_ale.jsonl
- python code/classification/validator.py --input data/processed/classified_traces.json --golden data/raw/golden_set.json -> rc=1
    Input file not found: data/processed/classified_traces.json
- python code/intervention/runner.py --condition baseline --model models/llama-3-8b-instruct.Q4_K_M.gguf --seed 42 --output data/processed/baseline_results.json -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-840-llmxive-follow-up-extending-agents-last/code/intervention/runner.py", line 15, in <module>
    from data.generator import ExecutionTrace, FailureType, generate_trace
ModuleNotFoundError: No module named 'data.generator'
- python code/intervention/runner.py --condition intervention --checkpoint-interval 3 --model models/llama-3-8b-instruct.Q4_K_M.gguf --seed 42 --output data/processed/intervention_results.json -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-840-llmxive-follow-up-extending-agents-last/code/intervention/runner.py", line 15, in <module>
    from data.generator import ExecutionTrace, FailureType, generate_trace
ModuleNotFoundError: No module named 'data.generator'
- python code/analysis/stats.py --baseline data/processed/baseline_results.json --intervention data/processed/intervention_results.json --output data/processed/stats_report.json -> rc=1
    Error running analysis: [Errno 2] No such file or directory: 'data/processed/baseline_results.json'
- python code/analysis/sensitivity.py --results data/processed/experiment_results.json --intervals,3,5 --output data/processed/sensitivity_analysis.json -> rc=2
    usage: sensitivity.py [-h] [--results RESULTS] [--intervals INTERVALS]
                      [--output OUTPUT]
sensitivity.py: error: unrecognized arguments: --intervals,3,5
- python code/utils/generate_report.py --stats data/processed/stats_report.json --sensitivity data/processed/sensitivity_analysis.json --output docs/report.md -> rc=1
    Stats file not found: data/processed/stats_report.json

## Declared deliverables still missing

- data/processed/classification_report.json
- data/processed/sensitivity_N1.json
- data/processed/sensitivity_N3.json
- data/processed/sensitivity_N5.json
- data/processed/sensitivity_analysis.json
- data/processed/static_constraints.json
- data/raw/golden_fixture.json

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### class `RunnerConfig` (in `code/utils/config.py`) — accessed via method/attribute names this round: `__init__`

`RunnerConfig` is used like a logger: different scripts call DIFFERENT method names on it, and the set grows every round. Adding only the name(s) above will fail next round on the NEXT name. Make the class tolerant of ANY method name **without removing the ones it already has**, by either:
  1. defining the full method set explicitly (keep existing methods like the ones already in `code/utils/config.py` AND add the missing ones), or
  2. adding a permissive fallback so unknown attributes resolve to a no-op callable, e.g.:

     ```python
     def __getattr__(self, name):
         # any logger-style call (.info/.debug/.warning/.error/...) becomes a tolerant no-op
         def _noop(*args, **kwargs):
             return None
         return _noop
     ```

Whichever you choose, every call site of `RunnerConfig` across the codebase must stop raising `AttributeError`/`TypeError`.

`RunnerConfig.__init__` call sites (1):
- code/utils/logging_config.py: super().__init__()

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/classification_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/classification/report_generator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/classification_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/sensitivity_N1.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/sensitivity_aggregator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/sensitivity_N1.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/sensitivity_N3.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/sensitivity_aggregator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/sensitivity_N3.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/sensitivity_N5.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/sensitivity_aggregator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/sensitivity_N5.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/sensitivity_analysis.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/sensitivity_aggregator.py` — NOT invoked by the run-book
    - `code/analysis/report_generator.py` — NOT invoked by the run-book
    - `code/analysis/sensitivity.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/sensitivity_analysis.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/static_constraints.json` is declared but was NOT written. Scripts referencing it:
    - `code/classification/goal_validator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/static_constraints.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/golden_fixture.json` is declared but was NOT written. Scripts referencing it:
    - `code/intervention/runner.py` — IS a run-book command
    - `code/classification/state_validator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/golden_fixture.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `data/processed/baseline_results.json`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/analysis/report_generator.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/processed/baseline_results.json`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/analysis/report_generator.py`.

### `data/processed/classified_traces.json`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/classification/parser.py`, `code/classification/report_generator.py`, `code/classification/state_validator.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/processed/classified_traces.json`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/classification/parser.py`, `code/classification/report_generator.py`, `code/classification/state_validator.py`.

### `data/raw/golden_subset.json`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/classification/parser.py`, `code/classification/goal_validator.py`, `code/data/generator.py`, `code/data/golden_set_generator.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/raw/golden_subset.json`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/classification/parser.py`, `code/classification/goal_validator.py`, `code/data/generator.py`, `code/data/golden_set_generator.py`.
