# Execution failures — fix these before the analysis can run

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/raw/checksums.json, data/raw/contract_hashes.json, data/raw/skills.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: every produced artifact is gitignored (data/raw/checksums.json, data/raw/contract_hashes.json, data/raw/skills.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 1 run-book script(s) missing (plan/impl path mismatch): python code/analysis.py --input data/results/metrics.csv; 4 command(s) failed: python -m pytest tests/contract/ (rc=1); python code/agent.py  --library-sizes 10 20 30 40 50 60 70 80 90 100  --overlap low medium high  --pruning {on,off}  --seed 42  --randomize-tasks (rc=1); python -m pytest tests/contract/ (rc=1); 2 declared deliverable(s) absent: data/results/analysis_report.json; data/results/experiment_log.csv

## Failing / missing run-book commands

- python -m pytest tests/contract/ -> rc=1
re unexpected)
E           Task 2 (ID: task_0002): Additional properties are not allowed ('edge_case', 'embedding_vector', 'ground_truth_path', 'id', 'num_steps' were unexpected)
E           Task 3 (ID: task_0003): Additional properties are not allowed ('edge_case', 'embedding_vector', 'ground_truth_path', 'id', 'num_steps' were unexpected)
E           Task 4 (ID: task_0004): Additional properties are not allowed ('edge_case', 'embedding_vector', 'ground_truth_path', 'id', 'num_steps' were unexpected)

tests/contract/test_task_schema.py:62: Failed
=========================== short test summary info ============================
FAILED tests/contract/test_schema_presence.py::test_dummy_instance_validation
FAILED tests/contract/test_schemas.py::test_real_tasks_schema_compliance - Fa...
FAILED tests/contract/test_schemas.py::test_real_skills_schema_compliance - F...
FAILED tests/contract/test_task_schema.py::test_schema_loads - AssertionError...
FAILED tests/contract/test_task_schema.py::test_sample_task_validates - Faile...
FAILED tests/contract/test_task_schema.py::test_all_tasks_validate - Failed: ...
========================= 6 failed, 17 passed in 5.18s =========================


- python code/agent.py  --library-sizes 10 20 30 40 50 60 70 80 90 100  --overlap low medium high  --pruning {on,off}  --seed 42  --randomize-tasks -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-975-llmxive-follow-up-extending-from-chatbot/code/agent.py", line 91, in <module>
    def execute_skill(skill: Dict[str, Any], inputs: Dict[str, Any]) -> Tuple[bool, Any, str]:
                                                                        ^^^^^
NameError: name 'Tuple' is not defined. Did you mean: 'tuple'?

- python -m pytest tests/contract/ -> rc=1
re unexpected)
E           Task 2 (ID: task_0002): Additional properties are not allowed ('edge_case', 'embedding_vector', 'ground_truth_path', 'id', 'num_steps' were unexpected)
E           Task 3 (ID: task_0003): Additional properties are not allowed ('edge_case', 'embedding_vector', 'ground_truth_path', 'id', 'num_steps' were unexpected)
E           Task 4 (ID: task_0004): Additional properties are not allowed ('edge_case', 'embedding_vector', 'ground_truth_path', 'id', 'num_steps' were unexpected)

tests/contract/test_task_schema.py:62: Failed
=========================== short test summary info ============================
FAILED tests/contract/test_schema_presence.py::test_dummy_instance_validation
FAILED tests/contract/test_schemas.py::test_real_tasks_schema_compliance - Fa...
FAILED tests/contract/test_schemas.py::test_real_skills_schema_compliance - F...
FAILED tests/contract/test_task_schema.py::test_schema_loads - AssertionError...
FAILED tests/contract/test_task_schema.py::test_sample_task_validates - Faile...
FAILED tests/contract/test_task_schema.py::test_all_tasks_validate - Failed: ...
========================= 6 failed, 17 passed in 5.19s =========================


- python code/analysis.py --input data/results/metrics.csv -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-975-llmxive-follow-up-extending-from-chatbot/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-975-llmxive-follow-up-extending-from-chatbot/code/analysis.py': [Errno 2] No such file or directory

- python -m pytest tests/contract/ -> rc=1
re unexpected)
E           Task 2 (ID: task_0002): Additional properties are not allowed ('edge_case', 'embedding_vector', 'ground_truth_path', 'id', 'num_steps' were unexpected)
E           Task 3 (ID: task_0003): Additional properties are not allowed ('edge_case', 'embedding_vector', 'ground_truth_path', 'id', 'num_steps' were unexpected)
E           Task 4 (ID: task_0004): Additional properties are not allowed ('edge_case', 'embedding_vector', 'ground_truth_path', 'id', 'num_steps' were unexpected)

tests/contract/test_task_schema.py:62: Failed
=========================== short test summary info ============================
FAILED tests/contract/test_schema_presence.py::test_dummy_instance_validation
FAILED tests/contract/test_schemas.py::test_real_tasks_schema_compliance - Fa...
FAILED tests/contract/test_schemas.py::test_real_skills_schema_compliance - F...
FAILED tests/contract/test_task_schema.py::test_schema_loads - AssertionError...
FAILED tests/contract/test_task_schema.py::test_sample_task_validates - Faile...
FAILED tests/contract/test_task_schema.py::test_all_tasks_validate - Failed: ...
========================= 6 failed, 17 passed in 5.20s =========================



## Declared deliverables still missing

- data/results/analysis_report.json
- data/results/experiment_log.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/results/analysis_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/analyze.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/analysis_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/experiment_log.csv` is declared but was NOT written. Scripts referencing it:
    - `code/agent.py` — IS a run-book command
    - `code/analyze.py` — NOT invoked by the run-book
    - `code/copy_contracts.py` — IS a run-book command
    - `code/logging_config.py` — NOT invoked by the run-book
    - `code/run_baseline.py` — NOT invoked by the run-book
    - `code/run_sensitivity.py` — NOT invoked by the run-book
    - `code/setup_contracts.py` — NOT invoked by the run-book
    - `code/smoke_logging.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/experiment_log.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
