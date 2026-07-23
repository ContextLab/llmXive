# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 6 command(s) failed: python code/run_pipeline.py (rc=1); python code/download_data.py (rc=1); python code/generate_code.py --model codegen-350M (rc=1); 1 declared deliverable(s) absent: data/analysis/metrics.json

## Failing / missing run-book commands

- python code/run_pipeline.py -> rc=1
    N] [INFO] - Created directory: /home/runner/work/llmXive/llmXive/projects/PROJ-294-evaluating-the-impact-of-code-generation/data/generated
2026-07-23 14:50:52 [PIPELINE-MAIN] [INFO] - Created directory: /home/runner/work/llmXive/llmXive/projects/PROJ-294-evaluating-the-impact-of-code-generation/data/analysis
2026-07-23 14:50:52 [PIPELINE-MAIN] [INFO] - Created directory: /home/runner/work/llmXive/llmXive/projects/PROJ-294-evaluating-the-impact-of-code-generation/results/figures
2026-07-23 14:50:52 [PIPELINE-MAIN] [INFO] - Executing Pipeline Gate: Citation Validation (T007a/T007b)...
2026-07-23 14:50:52 [PIPELINE-MAIN] [INFO] - Executing stage: /home/runner/work/llmXive/llmXive/projects/PROJ-294-evaluating-the-impact-of-code-generation/code/.venv/bin/python /home/runner/work/llmXive/llmXive/projects/PROJ-294-evaluating-the-impact-of-code-generation/code/validate_citations.py
Expected state/citations.yaml to contain a list of citations, got <class 'dict'>
2026-07-23 14:50:52 [PIPELINE-MAIN] [CRITICAL] - Pipeline Gate FAILED (Exit Code: 1). Aborting pipeline.
2026-07-23 14:50:52 [PIPELINE-MAIN] [CRITICAL] - Citation validation failed. Please check state/citations.yaml and fix issues.
- python code/download_data.py -> rc=1
    
- python code/generate_code.py --model codegen-350M -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-294-evaluating-the-impact-of-code-generation/code/generate_code.py", line 279, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-294-evaluating-the-impact-of-code-generation/code/generate_code.py", line 237, in main
    setup_logging(task_id=task_id)
TypeError: setup_logging() got an unexpected keyword argument 'task_id'
- python code/analyze_metrics.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-294-evaluating-the-impact-of-code-generation/code/analyze_metrics.py", line 9, in <module>
    from radon.halstead import halstead_visit
ModuleNotFoundError: No module named 'radon.halstead'
- python code/statistical_tests.py -> rc=1
    2026-07-23 14:50:55,476 - statistical_tests - INFO - Starting Statistical Analysis (T023)
2026-07-23 14:50:55,476 - statistical_tests - ERROR - Metrics file not found: data/analysis/metrics.json
2026-07-23 14:50:55,476 - statistical_tests - CRITICAL - Data file missing: Metrics file not found: data/analysis/metrics.json
- python code/report_generator.py -> rc=1
    Error during report generation: Metrics file not found: data/analysis/metrics.json
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-294-evaluating-the-impact-of-code-generation/code/report_generator.py", line 278, in main
    metrics_data = load_metrics_data()
                   ^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-294-evaluating-the-impact-of-code-generation/code/report_generator.py", line 32, in load_metrics_data
    raise FileNotFoundError(f"Metrics file not found: {metrics_path}")
FileNotFoundError: Metrics file not found: data/analysis/metrics.json

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
ds = load_dataset("openai/openai_humaneval", split="test")
records = len(ds)
print(f"RECORDS={records}")
required = ["task_id","prompt","canonical_solution","test","entry_point"]
fields = [f for f in required if f in ds.column_names]
print("FIELDS=" + ",".join(fields))
```

Write the loader to use this source/recipe, persist the records to the declared raw/processed data files, and DELETE any old code that fetches from a guessed website endpoint.

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### `setup_logging` — defined in `code/download_data.py`; called 14 way(s):

- code/create_results_dirs.py: setup_logging()
- code/run_pipeline_gate.py: setup_logging(task_id=TASK_ID)
- code/merge_sensitivity_metrics.py: setup_logging()
- code/append_sensitivity_comparison.py: logger = setup_logging()
- code/run_pipeline.py: logger = setup_logging()
- code/extract_citations.py: logger = setup_logging(task_id)
- code/download_data.py: logger = setup_logging()
- code/initialize_model_availability.py: setup_logging()
- code/generate_code.py: setup_logging(task_id=task_id)
- code/setup_data_dirs.py: setup_logging()
- code/analyze_metrics.py: logger = setup_logging()
- code/analyze_metrics.py: log_info(setup_logging(), f"Filtered {len(results) - len(filtered_results)} samples with null coverage")
- code/analyze_metrics.py: log_info(setup_logging(), f"Saved {len(filtered_results)} metrics to {output_path}")
- code/statistical_tests.py: logger = setup_logging()

Make `setup_logging` in `code/download_data.py` accept ALL of the above.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/analysis/metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/validate_quickstart.py` — NOT invoked by the run-book
    - `code/merge_sensitivity_metrics.py` — NOT invoked by the run-book
    - `code/append_sensitivity_comparison.py` — NOT invoked by the run-book
    - `code/run_pipeline.py` — IS a run-book command
    - `code/report_generator.py` — IS a run-book command
    - `code/analyze_metrics.py` — IS a run-book command
    - `code/statistical_tests.py` — IS a run-book command
  Make ONE of these WRITE `data/analysis/metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `data/analysis/metrics.json`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/merge_sensitivity_metrics.py`, `code/append_sensitivity_comparison.py`, `code/report_generator.py`, `code/analyze_metrics.py`, `code/statistical_tests.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/analysis/metrics.json`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/validate_quickstart.py`, `code/merge_sensitivity_metrics.py`, `code/append_sensitivity_comparison.py`, `code/report_generator.py`, `code/analyze_metrics.py`, `code/statistical_tests.py`.
