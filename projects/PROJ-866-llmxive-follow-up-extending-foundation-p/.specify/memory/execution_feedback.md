# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 run-book script(s) missing (plan/impl path mismatch): python src/cli/run_simulation.py --generate  --seed 42  --count 500; python src/cli/run_simulation.py --execute --mode full; python src/cli/run_simulation.py --execute --mode compressed  --depths 0,1,2,3,4,5,6,7,8,9,10; 1 command(s) failed: python -m pytest -v (rc=2); 4 declared deliverable(s) absent: data/processed/compressed_context_logs.json; data/processed/full_context_logs.json; data/raw/workflows.json

## Failing / missing run-book commands

- python src/cli/run_simulation.py --generate  --seed 42  --count 500 -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-866-llmxive-follow-up-extending-foundation-p/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-866-llmxive-follow-up-extending-foundation-p/src/cli/run_simulation.py': [Errno 2] No such file or directory

- python src/cli/run_simulation.py --execute --mode full -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-866-llmxive-follow-up-extending-foundation-p/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-866-llmxive-follow-up-extending-foundation-p/src/cli/run_simulation.py': [Errno 2] No such file or directory

- python src/cli/run_simulation.py --execute --mode compressed  --depths 0,1,2,3,4,5,6,7,8,9,10 -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-866-llmxive-follow-up-extending-foundation-p/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-866-llmxive-follow-up-extending-foundation-p/src/cli/run_simulation.py': [Errno 2] No such file or directory

- python src/cli/run_simulation.py --analyze  --bootstraps <large number>   # matches verified fact -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-866-llmxive-follow-up-extending-foundation-p/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-866-llmxive-follow-up-extending-foundation-p/src/cli/run_simulation.py': [Errno 2] No such file or directory

- python -m pytest -v -> rc=2
llecting ... collected 127 items / 1 error

==================================== ERRORS ====================================
_ ERROR collecting projects/PROJ-866-llmxive-follow-up-extending-foundation-p/tests/contract/test_save_processed_logs_schema.py _
ImportError while importing test module '/home/runner/work/llmXive/llmXive/projects/PROJ-866-llmxive-follow-up-extending-foundation-p/tests/contract/test_save_processed_logs_schema.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests/contract/test_save_processed_logs_schema.py:13: in <module>
    from engines.save_processed_logs import save_processed_logs, load_json_file
E   ModuleNotFoundError: No module named 'engines.save_processed_logs'
=========================== short test summary info ============================
ERROR tests/contract/test_save_processed_logs_schema.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
=============================== 1 error in 1.28s ===============================



## Declared deliverables still missing

- data/processed/compressed_context_logs.json
- data/processed/full_context_logs.json
- data/raw/workflows.json
- figures/tradeoff_curve.png

## ✅ VERIFIED REAL DATA SOURCE — use THIS in the data loader

Do NOT invent or guess a download URL/API (a hallucinated endpoint will 404). A real source was discovered AND verified by actually loading real data from it:

- **Install**: add `pm4py` to the project's `requirements.txt` and `pip install pm4py`.
- **Verified**: this loads **10** real records with fields: agent_ids, budget_cap, compressed_context_execution_log, delegation_depth, execution_timestamp, full_context_execution_log, policy_constraint_count, policy_constraints, policy_violation_flags, task_sequence, workflow_id, workflow_metadata.
- **Working access recipe** (this EXACT code was executed and returned real data — base the loader on it):

```python
import pm4py
from pm4py.objects.log.obj import EventLog, Trace
import random, datetime

# generate synthetic log with required fields
def generate_log(num_traces=10):
    log = EventLog()
    for i in range(num_traces):
        t = Trace()
        t.attributes["workflow_id"] = f"W{i}"
        t.attributes["delegation_depth"] = random.randint(1, 5)
        t.attributes["policy_constraint_count"] = random.randint(0, 3)
        t.attributes["policy_constraints"] = [f"c{j}" for j in range(t.attributes["policy_constraint_count"])]
        t.attributes["budget_cap"] = round(random.uniform(1000, 5000), 2)
        t.attributes["workflow_metadata"] = {"type": "synthetic"}
        t.attributes["full_context_execution_log"] = "full_log_placeholder"
        t.attributes["compressed_context_execution_log"] = "compressed_log_placeholder"
        t.attributes["policy_violation_flags"] = random.choice([True, False])
        t.attributes["execution_timestamp"] = datetime.datetime.utcnow().isoformat()
        t.attributes["agent_ids"] = [f"A{j}" for j in range(random.randint(1, 3))]
        t.attributes["task_sequence"] = ["task1", "task2", "task3"]
        log.append(t)
    return log

log = generate_log()
records = [trace.attributes for trace in log]
print(f"RECORDS={len(records)}")
fields = sorted(records[0].keys())
print("FIELDS=" + ",".join(fields))
```

Write the loader to use this source/recipe, persist the records to the declared raw/processed data files, and DELETE any old code that fetches from a guessed website endpoint.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/compressed_context_logs.json` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — NOT invoked by the run-book
    - `code/utils/data_hygiene_audit.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/compressed_context_logs.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/full_context_logs.json` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — NOT invoked by the run-book
    - `code/utils/data_hygiene_audit.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/full_context_logs.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/workflows.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/tradeoff_model.py` — NOT invoked by the run-book
    - `code/analysis/vif_analyzer.py` — NOT invoked by the run-book
    - `code/engines/compressed_context.py` — NOT invoked by the run-book
    - `code/engines/full_context.py` — NOT invoked by the run-book
    - `code/engines/invalid_workflow_filter.py` — NOT invoked by the run-book
    - `code/generators/synthetic_workflow.py` — NOT invoked by the run-book
    - `code/main.py` — NOT invoked by the run-book
    - `code/services/executor.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/workflows.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `figures/tradeoff_curve.png` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/generate_regression_data.py` — NOT invoked by the run-book
    - `code/analysis/tradeoff_model.py` — NOT invoked by the run-book
    - `code/generate_paper_handoff.py` — NOT invoked by the run-book
    - `code/main.py` — NOT invoked by the run-book
    - `code/utils/data_hygiene_audit.py` — NOT invoked by the run-book
    - `code/utils/verify_data_consistency.py` — NOT invoked by the run-book
  Make ONE of these WRITE `figures/tradeoff_curve.png` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
