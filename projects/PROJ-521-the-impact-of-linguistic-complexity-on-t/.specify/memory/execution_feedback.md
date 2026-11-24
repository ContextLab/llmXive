# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 6 command(s) failed: python code/generate_text.py --num-samples 200 --seed 42 (rc=1); python code/collect_trust.py --simulate --num-participants 100 --seed 42 (rc=1); python code/analyze.py --input data/processed/analysis_inputs.csv --output data/outputs/ (rc=1); 3 declared deliverable(s) absent: data/outputs/validation_report.json; data/processed/cleaned_responses.csv; data/raw/generated_text.csv

## Failing / missing run-book commands

- python code/generate_text.py --num-samples 200 --seed 42 -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-521-the-impact-of-linguistic-complexity-on-t/code/generate_text.py", line 21, in <module>
    from datasets import load_dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-521-the-impact-of-linguistic-complexity-on-t/lib/python3.11/site-packages/datasets/__init__.py", line 17, in <module>
    from .arrow_dataset import Column, Dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-521-the-impact-of-linguistic-complexity-on-t/lib/python3.11/site-packages/datasets/arrow_dataset.py", line 59, in <module>
    import pyarrow as pa
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-521-the-impact-of-linguistic-complexity-on-t/lib/python3.11/site-packages/pyarrow/__init__.py", line 59, in <module>
    from pyarrow.lib import (BuildInfo, CppBuildInfo, RuntimeInfo, set_timezone_db_path,
  File "pyarrow/lib.pyx", line 42, in init pyarrow.lib
ImportError: pyarrow requires NumPy 2.0 or newer, found 1.26.4

- python code/collect_trust.py --simulate --num-participants 100 --seed 42 -> rc=1

2026-10-16 18:43:01,185 - ERROR - Raw responses file not found: data/raw/trust_responses.csv
2026-10-16 18:43:01,185 - ERROR - Data cleaning failed: Raw responses file not found: data/raw/trust_responses.csv

- python code/analyze.py --input data/processed/analysis_inputs.csv --output data/outputs/ -> rc=1
2026-10-16 18:43:02,076 - INFO - Starting Analysis Pipeline (T030: Save Regression Results)
2026-10-16 18:43:02,076 - ERROR - Cleaned responses file not found: data/processed/cleaned_responses.csv


- python -m pytest tests/unit/ -> rc=1
est_analysis.py::test_univariate_regression_coefficients
FAILED tests/unit/test_analysis.py::test_bonferroni_correction - AttributeErr...
FAILED tests/unit/test_analysis.py::test_power_analysis_logic - TypeError: ru...
FAILED tests/unit/test_analysis.py::test_ordinal_regression - KeyError: 'conv...
FAILED tests/unit/test_collect_trust.py::TestDataCleaning::test_attention_check_filtering
FAILED tests/unit/test_collect_trust.py::TestDataCleaning::test_invalid_ratings_removed
FAILED tests/unit/test_metrics.py::test_pin_random_seed - assert 6 == 34
FAILED tests/unit/test_metrics.py::test_mtld_forward_vs_bidirectional - TypeE...
FAILED tests/unit/test_metrics.py::test_avg_sentence_length_basic - assert 4....
FAILED tests/unit/test_metrics.py::test_avg_sentence_length_single - assert 0...
FAILED tests/unit/test_metrics.py::test_get_all_metrics - AssertionError: ass...
FAILED tests/unit/test_metrics.py::test_metrics_consistency - TypeError: tupl...
FAILED tests/unit/test_metrics.py::test_mtld_invalid_measure - TypeError: cal...
FAILED tests/unit/test_setup_structure.py::test_nested_directory_structure - ...
================== 14 failed, 14 passed, 2 warnings in 1.88s ===================


- python -m pytest tests/contract/ -> rc=1
s/contract/test_schemas.py:177: PytestUnknownMarkWarning: Unknown pytest.mark.contract - is this a typo?  You can register custom marks to avoid this warning - for details, see https://docs.pytest.org/en/stable/how-to/mark.html
    @pytest.mark.contract

tests/contract/test_schemas.py:185
  /home/runner/work/llmXive/llmXive/projects/PROJ-521-the-impact-of-linguistic-complexity-on-t/tests/contract/test_schemas.py:185: PytestUnknownMarkWarning: Unknown pytest.mark.contract - is this a typo?  You can register custom marks to avoid this warning - for details, see https://docs.pytest.org/en/stable/how-to/mark.html
    @pytest.mark.contract

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
FAILED tests/contract/test_schemas.py::test_text_sample_schema_structure - Fi...
FAILED tests/contract/test_schemas.py::test_participant_response_schema_structure
FAILED tests/contract/test_schemas.py::test_analysis_result_schema_structure
FAILED tests/contract/test_schemas.py::test_all_schemas_load_valid - Failed: ...
=================== 4 failed, 1 skipped, 5 warnings in 0.07s ===================


- python -m pytest tests/integration/test_pipeline.py -> rc=2
ap._gcd_import(name[level:], package, level)
tests/integration/test_pipeline.py:27: in <module>
    from generate_text import main as generate_main
code/generate_text.py:21: in <module>
    from datasets import load_dataset
../../.llmxive-venvs/PROJ-521-the-impact-of-linguistic-complexity-on-t/lib/python3.11/site-packages/datasets/__init__.py:17: in <module>
    from .arrow_dataset import Column, Dataset
../../.llmxive-venvs/PROJ-521-the-impact-of-linguistic-complexity-on-t/lib/python3.11/site-packages/datasets/arrow_dataset.py:59: in <module>
    import pyarrow as pa
../../.llmxive-venvs/PROJ-521-the-impact-of-linguistic-complexity-on-t/lib/python3.11/site-packages/pyarrow/__init__.py:59: in <module>
    from pyarrow.lib import (BuildInfo, CppBuildInfo, RuntimeInfo, set_timezone_db_path,
pyarrow/lib.pyx:42: in init pyarrow.lib
    ???
E   ImportError: pyarrow requires NumPy 2.0 or newer, found 1.26.4
=========================== short test summary info ============================
ERROR tests/integration/test_pipeline.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
=============================== 1 error in 0.38s ===============================



## Declared deliverables still missing

- data/outputs/validation_report.json
- data/processed/cleaned_responses.csv
- data/raw/generated_text.csv

## ✅ VERIFIED REAL DATA SOURCE — use THIS in the data loader

Do NOT invent or guess a download URL/API (a hallucinated endpoint will 404). A real source was discovered AND verified by actually loading real data from it:

- **Install**: add `lexicalrichness` to the project's `requirements.txt` and `pip install lexicalrichness`.
- **Verified**: this loads **2** real records with fields: sample_id, source_paragraph_id, text, mtld_score, ttr_score.
- **Working access recipe** (this EXACT code was executed and returned real data — base the loader on it):

```python
from lexicalrichness import LexicalRichness

texts = [
    "This is a simple sentence.",
    "Another example of a longer piece of text, which contains multiple words and varied vocabulary."
]

records = []
for i, txt in enumerate(texts):
    lr = LexicalRichness(txt)
    records.append({
        "sample_id": i,
        "source_paragraph_id": i,
        "text": txt,
        "mtld_score": lr.mtld,
        "ttr_score": lr.ttr,
    })

print(f"RECORDS={len(records)}")
print("FIELDS=sample_id,source_paragraph_id,text,mtld_score,ttr_score")
```

Write the loader to use this source/recipe, persist the records to the declared raw/processed data files, and DELETE any old code that fetches from a guessed website endpoint.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/outputs/validation_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/validate_sample_size.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/outputs/validation_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/cleaned_responses.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analyze.py` — IS a run-book command
    - `code/collect_trust.py` — IS a run-book command
    - `code/validate_sample_size.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/cleaned_responses.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/generated_text.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analyze.py` — IS a run-book command
    - `code/checksum_generated_text.py` — NOT invoked by the run-book
    - `code/collect_trust.py` — IS a run-book command
    - `code/generate_text.py` — IS a run-book command
    - `code/update_state.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/generated_text.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
