# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 command(s) failed: python code/main.py --phase generate --config code/config.yaml (rc=1); python code/main.py --phase simulate --config code/config.yaml (rc=1); python code/main.py --phase sensitivity --config code/config.yaml (rc=1); 6 declared deliverable(s) absent: data/analysis/aggregated_results.json; data/analysis/final_results.json; data/analysis/sensitivity_sweep.json

## Failing / missing run-book commands

- python code/main.py --phase generate --config code/config.yaml -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-326-investigating-the-impact-of-network-stru/code/main.py", line 13, in <module>
    from code.src.generators.batch_runner import main as run_batch_generation
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-326-investigating-the-impact-of-network-stru/code/src/generators/batch_runner.py", line 25, in <module>
    from code.src.utils.logging import log_metric, log_run
ImportError: cannot import name 'log_run' from 'code.src.utils.logging' (/home/runner/work/llmXive/llmXive/projects/PROJ-326-investigating-the-impact-of-network-stru/code/src/utils/logging.py)
- python code/main.py --phase simulate --config code/config.yaml -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-326-investigating-the-impact-of-network-stru/code/main.py", line 13, in <module>
    from code.src.generators.batch_runner import main as run_batch_generation
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-326-investigating-the-impact-of-network-stru/code/src/generators/batch_runner.py", line 25, in <module>
    from code.src.utils.logging import log_metric, log_run
ImportError: cannot import name 'log_run' from 'code.src.utils.logging' (/home/runner/work/llmXive/llmXive/projects/PROJ-326-investigating-the-impact-of-network-stru/code/src/utils/logging.py)
- python code/main.py --phase sensitivity --config code/config.yaml -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-326-investigating-the-impact-of-network-stru/code/main.py", line 13, in <module>
    from code.src.generators.batch_runner import main as run_batch_generation
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-326-investigating-the-impact-of-network-stru/code/src/generators/batch_runner.py", line 25, in <module>
    from code.src.utils.logging import log_metric, log_run
ImportError: cannot import name 'log_run' from 'code.src.utils.logging' (/home/runner/work/llmXive/llmXive/projects/PROJ-326-investigating-the-impact-of-network-stru/code/src/utils/logging.py)
- python code/main.py --phase analyze --config code/config.yaml -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-326-investigating-the-impact-of-network-stru/code/main.py", line 13, in <module>
    from code.src.generators.batch_runner import main as run_batch_generation
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-326-investigating-the-impact-of-network-stru/code/src/generators/batch_runner.py", line 25, in <module>
    from code.src.utils.logging import log_metric, log_run
ImportError: cannot import name 'log_run' from 'code.src.utils.logging' (/home/runner/work/llmXive/llmXive/projects/PROJ-326-investigating-the-impact-of-network-stru/code/src/utils/logging.py)

## Declared deliverables still missing

- data/analysis/aggregated_results.json
- data/analysis/final_results.json
- data/analysis/sensitivity_sweep.json
- data/analysis/simulation_results.json
- data/raw/global_batch_manifest.json
- data/run_log.json

## ✅ VERIFIED REAL DATA SOURCE — use THIS in the data loader

Do NOT invent or guess a download URL/API (a hallucinated endpoint will 404). A real source was discovered AND verified by actually loading real data from it:

- **Install**: add `networkx` to the project's `requirements.txt` and `pip install networkx`.
- **Verified**: this loads **3** real records with fields: graph_id, node_list, edge_list, degree_distribution_type, parameter_values, clustering_coefficient, is_connected.
- **Working access recipe** (this EXACT code was executed and returned real data — base the loader on it):

```python
import networkx as nx

def make_record(g, gid, deg_type, params):
    return {
        "graph_id": gid,
        "node_list": list(g.nodes()),
        "edge_list": list(g.edges()),
        "degree_distribution_type": deg_type,
        "parameter_values": params,
        "clustering_coefficient": nx.average_clustering(g),
        "is_connected": nx.is_connected(g),
    }

records = []
generators = [
    ("erdos_renyi", lambda: nx.erdos_renyi_graph(30, 0.1), {"p": 0.1}),
    ("barabasi_albert", lambda: nx.barabasi_albert_graph(30, 2), {"m": 2}),
    ("watts_strogatz", lambda: nx.watts_strogatz_graph(30, 4, 0.3), {"k": 4, "p": 0.3}),
]

for i, (deg_type, gen_func, params) in enumerate(generators, start=1):
    g = gen_func()
    records.append(make_record(g, i, deg_type, params))

print(f"RECORDS={len(records)}")
print("FIELDS=" + ",".join(records[0].keys()))
```

Write the loader to use this source/recipe, persist the records to the declared raw/processed data files, and DELETE any old code that fetches from a guessed website endpoint.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/analysis/aggregated_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/analysis/aggregate_results.py` — NOT invoked by the run-book
    - `code/src/analysis/run_analysis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/analysis/aggregated_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/analysis/final_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/tests/test_run_analysis.py` — NOT invoked by the run-book
    - `code/tests/test_serialize_final.py` — NOT invoked by the run-book
    - `code/scripts/run_analysis.py` — NOT invoked by the run-book
    - `code/src/analysis/serialize_final.py` — NOT invoked by the run-book
    - `code/src/analysis/run_analysis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/analysis/final_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/analysis/sensitivity_sweep.json` is declared but was NOT written. Scripts referencing it:
    - `code/tests/test_run_analysis.py` — NOT invoked by the run-book
    - `code/tests/test_sensitivity.py` — NOT invoked by the run-book
    - `code/tests/test_validation.py` — NOT invoked by the run-book
    - `code/tests/test_serialize_final.py` — NOT invoked by the run-book
    - `code/scripts/run_sensitivity_sweep.py` — NOT invoked by the run-book
    - `code/src/analysis/report.py` — NOT invoked by the run-book
    - `code/src/analysis/sensitivity.py` — NOT invoked by the run-book
    - `code/src/analysis/serialize_final.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/analysis/sensitivity_sweep.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/analysis/simulation_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/tests/test_run_analysis.py` — NOT invoked by the run-book
    - `code/tests/test_sensitivity.py` — NOT invoked by the run-book
    - `code/tests/test_validation.py` — NOT invoked by the run-book
    - `code/tests/test_analysis.py` — NOT invoked by the run-book
    - `code/tests/test_serialization.py` — NOT invoked by the run-book
    - `code/tests/test_serialize_final.py` — NOT invoked by the run-book
    - `code/scripts/run_simulation_serialization.py` — NOT invoked by the run-book
    - `code/scripts/run_sensitivity_sweep.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/analysis/simulation_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/global_batch_manifest.json` is declared but was NOT written. Scripts referencing it:
    - `code/tests/test_integration.py` — NOT invoked by the run-book
    - `code/scripts/update_manifest.py` — NOT invoked by the run-book
    - `code/src/analysis/provenance.py` — NOT invoked by the run-book
    - `code/src/simulation/run_simulation.py` — NOT invoked by the run-book
    - `code/src/validation/validate_batch.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/global_batch_manifest.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/run_log.json` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/tests/test_simulation.py` — NOT invoked by the run-book
    - `code/tests/test_retry_logic.py` — NOT invoked by the run-book
    - `code/tests/test_integration.py` — NOT invoked by the run-book
    - `code/tests/test_logging.py` — NOT invoked by the run-book
    - `code/tests/test_inject_seed.py` — NOT invoked by the run-book
    - `code/tests/test_reproducibility.py` — NOT invoked by the run-book
    - `code/tests/test_generators.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/run_log.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
