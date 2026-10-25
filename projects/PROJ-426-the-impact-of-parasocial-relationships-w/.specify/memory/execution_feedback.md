# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 run-book script(s) missing (plan/impl path mismatch): python src/main.py --mode ingest_and_match; python src/main.py --mode fit_model; 1 command(s) failed: python -m pytest tests/contract/ (rc=1); 2 declared deliverable(s) absent: data/processed/matched_users.parquet; data/raw/loneliness_dataset.parquet

## Failing / missing run-book commands

- python src/main.py --mode ingest_and_match -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-426-the-impact-of-parasocial-relationships-w/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-426-the-impact-of-parasocial-relationships-w/src/main.py': [Errno 2] No such file or directory

- python src/main.py --mode fit_model -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-426-the-impact-of-parasocial-relationships-w/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-426-the-impact-of-parasocial-relationships-w/src/main.py': [Errno 2] No such file or directory

- python -m pytest tests/contract/ -> rc=1
um': -100.0, 'type': 'number'}, ...}, ...}

    def test_schema_constraints(schema):
        properties = schema.get("properties", {})
    
        # Check bounds for scores
        assert properties["loneliness_score"].get("minimum") is not None
        assert properties["loneliness_score"].get("maximum") is not None
    
        assert properties["usage_frequency"].get("minimum") == 0
>       assert properties["session_duration"].get("maximum") == 24.0
E       AssertionError: assert None == 24.0
E        +  where None = <built-in method get of dict object at 0x7f015b869780>('maximum')
E        +    where <built-in method get of dict object at 0x7f015b869780> = {'description': 'Total duration (in seconds) of consecutive activity sessions within the analysis window. Calculated as time difference between first and last activity in a 7-day window.\n', 'minimum': 0, 'type': 'number'}.get

tests/contract/test_unified_schema.py:56: AssertionError
=========================== short test summary info ============================
FAILED tests/contract/test_unified_schema.py::test_schema_constraints - Asser...
========================= 1 failed, 4 passed in 0.11s ==========================



## Declared deliverables still missing

- data/processed/matched_users.parquet
- data/raw/loneliness_dataset.parquet

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/matched_users.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/src/ingest/fetch_pushshift.py` — NOT invoked by the run-book
    - `code/src/match/user_match.py` — NOT invoked by the run-book
    - `code/src/validation/validate_match.py` — NOT invoked by the run-book
    - `code/tests/integration/test_pushshift_fetch.py` — NOT invoked by the run-book
    - `code/tests/unit/test_validate_match.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/matched_users.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/loneliness_dataset.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/src/match/user_match.py` — NOT invoked by the run-book
    - `code/src/validation/validate_match.py` — NOT invoked by the run-book
    - `code/tests/unit/test_validate_match.py` — NOT invoked by the run-book
    - `src/ingest/download_loneliness.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/loneliness_dataset.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
