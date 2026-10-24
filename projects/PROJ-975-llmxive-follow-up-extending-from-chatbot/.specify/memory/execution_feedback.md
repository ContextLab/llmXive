# Execution failures — fix these before the analysis can run

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/raw/checksums.json, data/raw/skills.json, data/raw/tasks.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: every produced artifact is gitignored (data/raw/checksums.json, data/raw/skills.json, data/raw/tasks.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 1 run-book script(s) missing (plan/impl path mismatch): python code/analysis.py --input data/results/metrics.csv; 1 command(s) failed: python -m pytest tests/contract/ (rc=1); 1 declared deliverable(s) absent: data/results/experiment_log.csv

## Failing / missing run-book commands

- python code/analysis.py --input data/results/metrics.csv -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-975-llmxive-follow-up-extending-from-chatbot/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-975-llmxive-follow-up-extending-from-chatbot/code/analysis.py': [Errno 2] No such file or directory

- python -m pytest tests/contract/ -> rc=1
_______

schema = {'$schema': 'http://json-schema.org/draft-07/schema#', 'properties': {'description': {'description': 'Textual descript...he task', 'type': 'string'}}, 'required': ['task_id', 'description', 'ground_truth_path'], 'title': 'Task Schema', ...}

    def test_schema_loads(schema):
        """Ensure the YAML schema is valid and loads correctly."""
        assert 'properties' in schema
        assert 'task_id' in schema['properties']
        assert 'description' in schema['properties']
        assert 'ground_truth_path' in schema['properties']
>       assert 'complexity' in schema['properties']
E       AssertionError: assert 'complexity' in {'description': {'description': 'Textual description of the task to be solved', 'type': 'string'}, 'ground_truth_path'...: {'type': 'string'}, 'type': 'array'}, 'task_id': {'description': 'Unique identifier for the task', 'type': 'string'}}

tests/contract/test_task_schema.py:35: AssertionError
=========================== short test summary info ============================
FAILED tests/contract/test_task_schema.py::test_schema_loads - AssertionError...
========================= 1 failed, 19 passed in 3.27s =========================



## Declared deliverables still missing

- data/results/experiment_log.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/results/experiment_log.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analyze.py` — NOT invoked by the run-book
    - `code/logging_config.py` — NOT invoked by the run-book
    - `code/run_baseline.py` — NOT invoked by the run-book
    - `code/run_sensitivity.py` — NOT invoked by the run-book
    - `code/setup_contracts.py` — NOT invoked by the run-book
    - `code/smoke_logging.py` — NOT invoked by the run-book
    - `code/verify_logging.py` — NOT invoked by the run-book
    - `code/verify_schema_t009c.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/experiment_log.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
