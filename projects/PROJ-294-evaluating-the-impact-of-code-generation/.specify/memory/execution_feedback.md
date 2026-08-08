# Execution failures — fix these before the analysis can run

## ⚠ REGRESSIONS — your last fix BROKE these (they passed before)

These commands were NOT failing in the previous round and ARE failing now — your last edit broke previously-working code. REVERT or correct whatever change broke each one BEFORE touching anything else; do not trade one passing script for another (that oscillation is what burns the fix-round budget toward escalation):

- `python code/generate_code.py --model salesforce/codegen-mono-350M`
- `python code/validate_citations.py`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 6 command(s) failed: python code/download_data.py (rc=1); python code/generate_code.py --model salesforce/codegen-mono-350M (rc=1); python code/analyze_metrics.py (rc=1); 1 declared deliverable(s) absent: data/analysis/metrics.json

## Failing / missing run-book commands

- python code/download_data.py -> rc=1
    JT7X5E0fdyiuRQIgNQYODFAlmZxxax6q8J4XeJadMZ2xj28rJv-drucatkw_&Key-Pair-Id=01KXEF4KZ1B6FV465MAWR4M21F "HTTP/1.1 206 Partial Content"
2026-08-08 05:57:28,832 [INFO] Downloaded 164 records to /home/runner/work/llmXive/llmXive/projects/PROJ-294-evaluating-the-impact-of-code-generation/data/raw/humaneval_test.jsonl
2026-08-08 05:57:28,832 [INFO] Loading downloaded data for sampling...

Warning: You are sending unauthenticated requests to the HF Hub. Please set a HF_TOKEN to enable higher rate limits and faster downloads.
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-294-evaluating-the-impact-of-code-generation/code/download_data.py", line 368, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-294-evaluating-the-impact-of-code-generation/code/download_data.py", line 363, in main
    perform_stratified_sampling(data, config, sample_output)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-294-evaluating-the-impact-of-code-generation/code/download_data.py", line 244, in perform_stratified_sampling
    q1 = config['quartile_boundaries']['Q1']
         ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
KeyError: 'quartile_boundaries'
- python code/generate_code.py --model salesforce/codegen-mono-350M -> rc=1
    2026-08-08 05:57:29,105 - GEN-CODE - INFO - Starting T028: Sensitivity Generation (7B)
2026-08-08 05:57:29,106 - GEN-CODE - ERROR - Raw HumanEval data not found. Run T010 first.
- python code/analyze_metrics.py -> rc=1
    2026-08-08 05:57:29 [T017] [INFO] - Starting Metric Aggregation (T017)
2026-08-08 05:57:29 [T017] [ERROR] - Intermediate metrics file not found: data/analysis/intermediate_metrics.json
2026-08-08 05:57:29 [T017] [ERROR] - Cannot proceed without intermediate metrics.
- python code/statistical_tests.py -> rc=1
    2026-08-08 05:57:29,225 [T046] - INFO - Starting Success Criteria Validation (T046)
2026-08-08 05:57:29,225 [T046] - ERROR - Metrics file not found: data/analysis/metrics.json
2026-08-08 05:57:29,225 [T046] - ERROR - T046 failed: Metrics file not found: data/analysis/metrics.json
- python code/validate_citations.py -> rc=1
    2026-08-08 05:57:29 [INFO] Validating citations from: state/citations.yaml
2026-08-08 05:57:29 [INFO] Detected nested 'citations' key in YAML.
2026-08-08 05:57:29 [ERROR] Item 0 missing required keys: {'id'}
2026-08-08 05:57:29 [CRITICAL] Citation validation failed. Pipeline must abort.
- python code/report_generator.py -> rc=1
    2026-08-08 05:57:30 [T030] [INFO] - Starting Report Generation (T030)
2026-08-08 05:57:30 [T030] [INFO] - Loading metrics from data/analysis/metrics.json
2026-08-08 05:57:30 [T030] [ERROR] - Metrics file not found: data/analysis/metrics.json

## Declared deliverables still missing

- data/analysis/metrics.json

## ✅ VERIFIED REAL DATA SOURCE — use THIS in the data loader

Do NOT invent or guess a download URL/API (a hallucinated endpoint will 404). A real source was discovered AND verified by actually loading real data from it:

- **Install**: add `datasets` to the project's `requirements.txt` and `pip install datasets`.
- **Verified**: this loads **164** real records with fields: task_id, prompt, canonical_solution, test, entry_point.
- **Working access recipe** (this EXACT code was executed and returned real data — base the loader on it):

```python
import sys
from datasets import load_dataset

# Load the full dataset (default split is the only available one)
ds = load_dataset("openai/openai_humaneval", split="test")
# Ensure we actually have records
record_count = len(ds)
if record_count == 0:
    raise RuntimeError("Loaded dataset contains zero records")
print(f"RECORDS={record_count}")

# Print field names from a sample record
fields = ds.column_names
print("FIELDS=" + ",".join(fields))
```

Write the loader to use this source/recipe, persist the records to the declared raw/processed data files, and DELETE any old code that fetches from a guessed website endpoint.

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### `setup_logging` — defined in `code/generate_code.py`; called 25 way(s):

- code/append_sensitivity_comparison.py: logger = setup_logging()
- code/create_results_dirs.py: setup_logging()
- code/generate_code.py: - setup_logging()
- code/generate_code.py: - setup_logging(task_id="T028")
- code/generate_code.py: - setup_logging(task_id)
- code/generate_code.py: # If positional arg passed (e.g., setup_logging(task_id)), assume it's the task_id
- code/generate_code.py: return setup_logging()
- code/generate_code.py: logger = setup_logging(task_id="T028")
- code/report_generator.py: logger = setup_logging()
- code/analyze_metrics.py: logger = setup_logging(task_id="T017")
- code/merge_sensitivity_metrics.py: setup_logging()
- code/extract_citations.py: logger = setup_logging(task_id)
- code/setup_data_dirs.py: setup_logging()
- code/statistical_tests.py: return setup_logging()
- code/statistical_tests.py: logger = setup_logging(task_id="T046")
- code/statistical_tests.py: logger = setup_logging()
- code/initialize_model_availability.py: setup_logging()
- code/run_pipeline_gate.py: setup_logging(task_id=TASK_ID)
- code/run_pipeline.py: logger = setup_logging()
- code/download_data.py: # setup_logging(), setup_logging(task_id="..."), setup_logging(task_id=TASK_ID)
- code/download_data.py: return setup_logging()
- code/download_data.py: logger = setup_logging()
- code/utils.py: - setup_logging()
- code/utils.py: - setup_logging(task_id="T007")
- code/utils.py: - setup_logging(level=logging.INFO)

Make `setup_logging` in `code/generate_code.py` accept ALL of the above.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/analysis/metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/append_sensitivity_comparison.py` — NOT invoked by the run-book
    - `code/report_generator.py` — IS a run-book command
    - `code/analyze_metrics.py` — IS a run-book command
    - `code/merge_sensitivity_metrics.py` — NOT invoked by the run-book
    - `code/validate_quickstart.py` — NOT invoked by the run-book
    - `code/statistical_tests.py` — IS a run-book command
    - `code/run_pipeline.py` — NOT invoked by the run-book
    - `code/download_data.py` — IS a run-book command
  Make ONE of these WRITE `data/analysis/metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `home/runner/work/llmXive/llmXive/projects/PROJ-294-evaluating-the-impact-of-code-generation/data/raw/humaneval_test.json`

- ACTUAL columns/keys the producer wrote: `(file not on disk this run)`
- REQUIRED by the consumer(s): `[quartile_boundaries]`
- PRODUCER(s) to edit: `code/download_data.py`
- CONSUMER(s) that read it: `code/download_data.py`
  → Edit the producer so every required name [quartile_boundaries] is in `home/runner/work/llmXive/llmXive/projects/PROJ-294-evaluating-the-impact-of-code-generation/data/raw/humaneval_test.json`'s header (renaming, not dropping, the columns it already writes); do not change the consumers (they already agree).

### `data/analysis/intermediate_metrics.json`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/analyze_metrics.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/analysis/intermediate_metrics.json`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/analyze_metrics.py`.

### `data/analysis/metrics.json`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/append_sensitivity_comparison.py`, `code/report_generator.py`, `code/analyze_metrics.py`, `code/merge_sensitivity_metrics.py`, `code/statistical_tests.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/analysis/metrics.json`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/append_sensitivity_comparison.py`, `code/report_generator.py`, `code/analyze_metrics.py`, `code/merge_sensitivity_metrics.py`, `code/validate_quickstart.py`, `code/statistical_tests.py`.
