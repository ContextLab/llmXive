# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 command(s) failed: python -m src.cli.main --config config/settings.py --run all (rc=1); python -m pytest tests/unit/ (rc=2); python -m pytest tests/contract/ (rc=1); 6 declared deliverable(s) absent: data/annotations/raw_comments.json; data/derived/human_baseline.json; data/derived/human_confirmations.json

## Failing / missing run-book commands

- python -m src.cli.main --config config/settings.py --run all -> rc=1

Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-370-evaluating-the-impact-of-code-generation/src/cli/main.py", line 28, in <module>
    from src.utils.timeout_wrapper import (
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-370-evaluating-the-impact-of-code-generation/code/src/utils/__init__.py", line 10, in <module>
    from .timeout_wrapper import set_global_timeout, check_timeout
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-370-evaluating-the-impact-of-code-generation/code/src/utils/timeout_wrapper.py", line 30, in <module>
    from code.src.utils.logger import get_logger
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-370-evaluating-the-impact-of-code-generation/code/src/utils/__init__.py", line 10, in <module>
    from .timeout_wrapper import set_global_timeout, check_timeout
ImportError: cannot import name 'set_global_timeout' from 'code.src.utils.timeout_wrapper' (/home/runner/work/llmXive/llmXive/projects/PROJ-370-evaluating-the-impact-of-code-generation/code/src/utils/timeout_wrapper.py)

- python -m pytest tests/unit/ -> rc=2
le '/home/runner/work/llmXive/llmXive/projects/PROJ-370-evaluating-the-impact-of-code-generation/tests/unit/test_preprocess_and_ground_truth.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/unit/test_preprocess_and_ground_truth.py:5: in <module>
    from src.extraction.preprocess_and_ground_truth import main as preprocess_main
src/extraction/preprocess_and_ground_truth.py:39: in <module>
    from src.extraction.fetch_human_comments import main as fetch_comments_main
code/src/extraction/fetch_human_comments.py:17: in <module>
    import requests
E   ModuleNotFoundError: No module named 'requests'
=========================== short test summary info ============================
ERROR tests/unit/test_logger.py
ERROR tests/unit/test_preprocess_and_ground_truth.py
!!!!!!!!!!!!!!!!!!! Interrupted: 2 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 2 errors in 0.11s ===============================


- python -m pytest tests/contract/ -> rc=1
es"], f"Missing field {field} in alignment_result schema"
E           AssertionError: Missing field human_bug_index in alignment_result schema
E           assert 'human_bug_index' in {'pr_id': {'type': 'integer', 'description': 'GitHub Pull Request number'}, 'repo_name': {'type': 'string', 'descripti...': 'number', 'description': 'Cosine similarity threshold used for matching', 'minimum': 0.0, 'maximum': 1.0, ...}, ...}

tests/contract/test_yaml_schemas.py:89: AssertionError
=========================== short test summary info ============================
FAILED tests/contract/test_yaml_schemas.py::TestYAMLSchemas::test_bug_detection_schema_exists
FAILED tests/contract/test_yaml_schemas.py::TestYAMLSchemas::test_alignment_result_schema_exists
FAILED tests/contract/test_yaml_schemas.py::TestYAMLSchemas::test_pr_data_schema_valid_fields
FAILED tests/contract/test_yaml_schemas.py::TestYAMLSchemas::test_bug_detection_schema_valid_fields
FAILED tests/contract/test_yaml_schemas.py::TestYAMLSchemas::test_alignment_result_schema_valid_fields
ERROR tests/contract/test_yaml_schemas.py::test_yaml_syntax_validity
===================== 5 failed, 3 passed, 1 error in 0.08s =====================


- python -m src.cli.main --config config/settings.py --run all --seed 42 -> rc=1

Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-370-evaluating-the-impact-of-code-generation/src/cli/main.py", line 28, in <module>
    from src.utils.timeout_wrapper import (
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-370-evaluating-the-impact-of-code-generation/code/src/utils/__init__.py", line 10, in <module>
    from .timeout_wrapper import set_global_timeout, check_timeout
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-370-evaluating-the-impact-of-code-generation/code/src/utils/timeout_wrapper.py", line 30, in <module>
    from code.src.utils.logger import get_logger
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-370-evaluating-the-impact-of-code-generation/code/src/utils/__init__.py", line 10, in <module>
    from .timeout_wrapper import set_global_timeout, check_timeout
ImportError: cannot import name 'set_global_timeout' from 'code.src.utils.timeout_wrapper' (/home/runner/work/llmXive/llmXive/projects/PROJ-370-evaluating-the-impact-of-code-generation/code/src/utils/timeout_wrapper.py)


## Declared deliverables still missing

- data/annotations/raw_comments.json
- data/derived/human_baseline.json
- data/derived/human_confirmations.json
- data/derived/llm_detections.json
- data/raw/checksums.json
- data/raw/prs.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/annotations/raw_comments.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/extraction/fetch_human_comments.py` — NOT invoked by the run-book
    - `code/src/extraction/filter_human_confirmations.py` — NOT invoked by the run-book
    - `code/src/extraction/preprocess.py` — NOT invoked by the run-book
    - `code/tests/test_filter_human_confirmations.py` — NOT invoked by the run-book
    - `code/tests/test_preprocess.py` — NOT invoked by the run-book
    - `src/extraction/preprocess.py` — NOT invoked by the run-book
    - `src/extraction/preprocess_and_ground_truth.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/annotations/raw_comments.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/derived/human_baseline.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/extraction/generate_ground_truth.py` — NOT invoked by the run-book
    - `code/tests/test_generate_ground_truth.py` — NOT invoked by the run-book
    - `src/extraction/preprocess.py` — NOT invoked by the run-book
    - `src/extraction/preprocess_and_ground_truth.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/human_baseline.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/derived/human_confirmations.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/extraction/filter_human_confirmations.py` — NOT invoked by the run-book
    - `code/src/extraction/generate_ground_truth.py` — NOT invoked by the run-book
    - `code/src/extraction/preprocess.py` — NOT invoked by the run-book
    - `code/tests/test_filter_human_confirmations.py` — NOT invoked by the run-book
    - `code/tests/test_generate_ground_truth.py` — NOT invoked by the run-book
    - `src/extraction/preprocess_and_ground_truth.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/human_confirmations.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/derived/llm_detections.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/analysis/split_dataset.py` — NOT invoked by the run-book
    - `code/src/detection/detect_llm_code.py` — NOT invoked by the run-book
    - `code/src/inference/run_inference.py` — NOT invoked by the run-book
    - `code/tests/test_split_dataset.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/llm_detections.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/checksums.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/extraction/fetch_human_comments.py` — NOT invoked by the run-book
    - `code/src/extraction/fetch_prs.py` — NOT invoked by the run-book
    - `code/src/extraction/preprocess.py` — NOT invoked by the run-book
    - `code/tests/test_preprocess.py` — NOT invoked by the run-book
    - `src/extraction/fetch_prs.py` — NOT invoked by the run-book
    - `src/extraction/preprocess.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/checksums.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/prs.json` is declared but was NOT written. Scripts referencing it:
    - `code/config/settings.py` — NOT invoked by the run-book
    - `code/src/analysis/split_dataset.py` — NOT invoked by the run-book
    - `code/src/cli/main.py` — NOT invoked by the run-book
    - `code/src/extraction/fetch_human_comments.py` — NOT invoked by the run-book
    - `code/src/extraction/fetch_prs.py` — NOT invoked by the run-book
    - `code/src/extraction/filter_human_confirmations.py` — NOT invoked by the run-book
    - `code/src/extraction/preprocess.py` — NOT invoked by the run-book
    - `code/src/extraction/validate_linked_issues.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/prs.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
