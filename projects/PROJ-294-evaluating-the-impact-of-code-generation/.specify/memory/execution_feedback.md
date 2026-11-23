# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): python code/stats_analysis.py; 7 command(s) failed: python code/download_data.py (rc=1); python code/extract_human_reference.py (rc=1); python code/generate_code.py --model primary (rc=1); 5 declared deliverable(s) absent: data/analysis/metrics.json; data/analysis/statistical_results.json; data/generated/codegen_samples.json

## Failing / missing run-book commands

- python code/download_data.py -> rc=1

2026-10-16 17:32:04 [INFO] [T001] - Starting Data Acquisition (T001)
2026-10-16 17:32:04 [INFO] [T001] - Downloading HumanEval dataset...
2026-10-16 17:32:04 [ERROR] [T001] - Data acquisition failed: The 'datasets' library is required. Install it via `pip install datasets`.

- python code/extract_human_reference.py -> rc=1
/datasets/arrow_dataset.py", line 59, in <module>
    import pyarrow as pa
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-294-evaluating-the-impact-of-code-generation/lib/python3.11/site-packages/pyarrow/__init__.py", line 59, in <module>
    from pyarrow.lib import (BuildInfo, CppBuildInfo, RuntimeInfo, set_timezone_db_path,
  File "pyarrow/lib.pyx", line 42, in init pyarrow.lib
ImportError: pyarrow requires NumPy 2.0 or newer, found 1.26.4

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-294-evaluating-the-impact-of-code-generation/code/extract_human_reference.py", line 58, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-294-evaluating-the-impact-of-code-generation/code/extract_human_reference.py", line 54, in main
    extract_human_references()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-294-evaluating-the-impact-of-code-generation/code/extract_human_reference.py", line 29, in extract_human_references
    raise ImportError(
ImportError: The 'datasets' library is required. Install it via `pip install datasets`.

- python code/generate_code.py --model primary -> rc=1

2026-10-16 17:32:05 [INFO] [T012] - Starting Code Generation (T012)
2026-10-16 17:32:05 [ERROR] [T012] - Human samples not found: data/generated/human_samples.json

- python code/generate_code.py --model sensitivity -> rc=1

2026-10-16 17:32:05 [INFO] [T012] - Starting Code Generation (T012)
2026-10-16 17:32:05 [ERROR] [T012] - Human samples not found: data/generated/human_samples.json

- python code/analyze_metrics.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-294-evaluating-the-impact-of-code-generation/code/analyze_metrics.py", line 8, in <module>
    from utils import setup_logging, get_logger, set_task_id, get_task_id, get_timestamp, get_unique_id
ImportError: cannot import name 'get_timestamp' from 'utils' (/home/runner/work/llmXive/llmXive/projects/PROJ-294-evaluating-the-impact-of-code-generation/code/utils/__init__.py)

- python code/stats_analysis.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-294-evaluating-the-impact-of-code-generation/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-294-evaluating-the-impact-of-code-generation/code/stats_analysis.py': [Errno 2] No such file or directory

- python code/report_generator.py -> rc=1

2026-10-16 17:32:05 [INFO] [T030] - Starting Report Generation (T030)
2026-10-16 17:32:05 [ERROR] [T030] - Metrics file not found: data/analysis/metrics.json

- python -m pytest tests/ -> rc=2
/docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
ERROR tests/integration/test_aggregation.py
ERROR tests/integration/test_metrics.py
ERROR tests/integration/test_stats_pipeline.py
ERROR tests/unit/test_aggregation.py
ERROR tests/unit/test_analyze_metrics_filter.py
ERROR tests/unit/test_artifact_manager.py
ERROR tests/unit/test_edge_cases.py
ERROR tests/unit/test_extract_human_reference.py
ERROR tests/unit/test_generate_code_api.py
ERROR tests/unit/test_generate_code_t028a.py
ERROR tests/unit/test_initialize_model_availability.py
ERROR tests/unit/test_merge_sensitivity.py
ERROR tests/unit/test_setup_data_dirs.py - NameError: name 'sys' is not defined
ERROR tests/unit/test_setup_project_structure.py
ERROR tests/unit/test_setup_structure.py
ERROR tests/unit/test_statistics.py
ERROR tests/unit/test_t028a_local_fallback.py
ERROR tests/unit/test_utils_logging.py
ERROR tests/unit/test_validate_citations.py
ERROR tests/unit/test_validation.py
!!!!!!!!!!!!!!!!!!! Interrupted: 20 errors during collection !!!!!!!!!!!!!!!!!!!
======================= 13 warnings, 20 errors in 0.88s ========================



## Declared deliverables still missing

- data/analysis/metrics.json
- data/analysis/statistical_results.json
- data/generated/codegen_samples.json
- data/generated/human_samples.json
- data/raw/humaneval.parquet

## ✅ VERIFIED REAL DATA SOURCE — use THIS in the data loader

Do NOT invent or guess a download URL/API (a hallucinated endpoint will 404). A real source was discovered AND verified by actually loading real data from it:

- **Install**: add `datasets` to the project's `requirements.txt` and `pip install datasets`.
- **Verified**: this loads **164** real records with fields: task_id, prompt, canonical_solution, test, entry_point.
- **Working access recipe** (this EXACT code was executed and returned real data — base the loader on it):

```python
import datasets

# Load the dataset without specifying a split to get all available splits
dataset_dict = datasets.load_dataset("openai/openai_humaneval")

# Compute total number of records across all splits
total_records = sum(len(split) for split in dataset_dict.values())

# Use the first split to retrieve field names
first_split = next(iter(dataset_dict.values()))
field_names = first_split.column_names

print(f"RECORDS={total_records}")
print("FIELDS=" + ",".join(field_names))
```

Write the loader to use this source/recipe, persist the records to the declared raw/processed data files, and DELETE any old code that fetches from a guessed website endpoint.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/analysis/metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/analyze_metrics.py` — IS a run-book command
    - `code/append_sensitivity_comparison.py` — NOT invoked by the run-book
    - `code/merge_sensitivity_metrics.py` — NOT invoked by the run-book
    - `code/report_generator.py` — IS a run-book command
    - `code/run_pipeline.py` — NOT invoked by the run-book
    - `code/statistical_tests.py` — NOT invoked by the run-book
    - `code/utils/logger.py` — NOT invoked by the run-book
    - `code/validate_quickstart.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/analysis/metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/analysis/statistical_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/report_generator.py` — IS a run-book command
    - `code/statistical_tests.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/analysis/statistical_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/generated/codegen_samples.json` is declared but was NOT written. Scripts referencing it:
    - `code/analyze_metrics.py` — IS a run-book command
    - `code/generate_code.py` — IS a run-book command
    - `code/generate_code_gpu.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/generated/codegen_samples.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/generated/human_samples.json` is declared but was NOT written. Scripts referencing it:
    - `code/analyze_metrics.py` — IS a run-book command
    - `code/extract_human_reference.py` — IS a run-book command
    - `code/generate_code.py` — IS a run-book command
  Make ONE of these WRITE `data/generated/human_samples.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/humaneval.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/download_data.py` — IS a run-book command
    - `code/extract_human_reference.py` — IS a run-book command
    - `code/generate_code.py` — IS a run-book command
    - `code/generate_code_gpu.py` — NOT invoked by the run-book
    - `code/generate_code_llama.py` — NOT invoked by the run-book
    - `code/validate_quickstart.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/humaneval.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
