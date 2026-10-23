# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/agent.py  --library-sizes 10 20 30 40 50 60 70 80 90 100  --overlap high  --pruning`
  - script usage: `agent.py [-h] [--library-size LIBRARY_SIZE] [--pruning {on,off}]`
  - argparse error: `agent.py: error: argument --overlap: invalid choice: 'high' (choose from 'LOW', 'MEDIUM', 'HIGH')`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): python code/analysis.py --input data/results/metrics.csv; 2 command(s) failed: python code/agent.py  --library-sizes 10 20 30 40 50 60 70 80 90 100  --overlap high  --pruning (rc=2); python -m pytest tests/contract/ (rc=1)

## Failing / missing run-book commands

- python code/agent.py  --library-sizes 10 20 30 40 50 60 70 80 90 100  --overlap high  --pruning -> rc=2

usage: agent.py [-h] [--library-size LIBRARY_SIZE] [--pruning {on,off}]
                [--overlap {LOW,MEDIUM,HIGH}] [--task-sample TASK_SAMPLE]
agent.py: error: argument --overlap: invalid choice: 'high' (choose from 'LOW', 'MEDIUM', 'HIGH')

- python code/analysis.py --input data/results/metrics.csv -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-975-llmxive-follow-up-extending-from-chatbot/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-975-llmxive-follow-up-extending-from-chatbot/code/analysis.py': [Errno 2] No such file or directory

- python -m pytest tests/contract/ -> rc=1
ueError
----------------------------- Captured stderr call -----------------------------
2026-10-23 18:24:54,508 INFO llmXive_experiment: {"run_id": "run_001", "task_id": "task_001", "library_size": 50, "pruning_enabled": true, "success": true, "latency_ms": 120.5, "tokens_used": 450, "retrieval_precision": 0.8, "retrieval_diversity": 0.6, "edge_case": "none"}
------------------------------ Captured log call -------------------------------
INFO     llmXive_experiment:logging_config.py:99 {"run_id": "run_001", "task_id": "task_001", "library_size": 50, "pruning_enabled": true, "success": true, "latency_ms": 120.5, "tokens_used": 450, "retrieval_precision": 0.8, "retrieval_diversity": 0.6, "edge_case": "none"}
=========================== short test summary info ============================
FAILED tests/contract/test_experiment_log_schema.py::test_valid_log_entry - j...
FAILED tests/contract/test_experiment_log_schema.py::test_edge_case_entry - j...
FAILED tests/contract/test_logging_schema.py::test_logging_csv_header_order
FAILED tests/contract/test_logging_schema.py::test_logging_csv_schema_compliance
========================= 4 failed, 19 passed in 6.63s =========================


## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
