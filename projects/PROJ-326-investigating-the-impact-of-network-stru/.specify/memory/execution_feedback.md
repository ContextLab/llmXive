# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 command(s) failed: python code/main.py --config code/config.yaml --output data/ (rc=1); 5 declared deliverable(s) absent: data/analysis/final_results.json; data/analysis/power_analysis_report.json; data/analysis/sensitivity_sweep.json

## Failing / missing run-book commands

- python code/main.py --config code/config.yaml --output data/ -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-326-investigating-the-impact-of-network-stru/code/main.py", line 15, in <module>
    from code.src.analysis.run_analysis import main as run_analysis
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-326-investigating-the-impact-of-network-stru/code/src/analysis/__init__.py", line 6, in <module>
    from .sensitivity import run_sensitivity_sweep
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-326-investigating-the-impact-of-network-stru/code/src/analysis/sensitivity.py", line 14, in <module>
    from code.src.simulation.serialization import load_results
ImportError: cannot import name 'load_results' from 'code.src.simulation.serialization' (/home/runner/work/llmXive/llmXive/projects/PROJ-326-investigating-the-impact-of-network-stru/code/src/simulation/serialization.py)

## Declared deliverables still missing

- data/analysis/final_results.json
- data/analysis/power_analysis_report.json
- data/analysis/sensitivity_sweep.json
- data/analysis/simulation_results.json
- data/analysis/validation_report.json

## ✅ VERIFIED REAL DATA SOURCE — use THIS in the data loader

Do NOT invent or guess a download URL/API (a hallucinated endpoint will 404). A real source was discovered AND verified by actually loading real data from it:

- **Install**: add `networkx` to the project's `requirements.txt` and `pip install networkx`.
- **Verified**: this loads **5** real records with fields: graph_id, graph_name, node_count, edge_count, adjacency, is_connected.
- **Working access recipe** (this EXACT code was executed and returned real data — base the loader on it):

```python
import networkx as nx

def load_graphs():
    graphs = [
        ("karate_club", nx.karate_club_graph()),
        ("les_miserables", nx.les_miserables_graph()),
        ("davis_southern_women", nx.davis_southern_women_graph()),
        ("florentine_families", nx.florentine_families_graph()),
        ("caveman", nx.caveman_graph(2, 3)),
    ]
    records = []
    for i, (name, G) in enumerate(graphs):
        rec = {
            "graph_id": i,
            "graph_name": name,
            "node_count": G.number_of_nodes(),
            "edge_count": G.number_of_edges(),
            "adjacency": nx.to_dict_of_dicts(G),
            "is_connected": nx.is_connected(G) if G.number_of_nodes() > 0 else False,
        }
        records.append(rec)
    return records

records = load_graphs()
print(f"RECORDS={len(records)}")
print("FIELDS=" + ",".join(records[0].keys()))
```

Write the loader to use this source/recipe, persist the records to the declared raw/processed data files, and DELETE any old code that fetches from a guessed website endpoint.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/analysis/final_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/analysis/report.py` — NOT invoked by the run-book
    - `code/src/analysis/run_analysis.py` — NOT invoked by the run-book
    - `code/scripts/run_power_analysis.py` — NOT invoked by the run-book
    - `code/tests/test_run_analysis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/analysis/final_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/analysis/power_analysis_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/analysis/power.py` — NOT invoked by the run-book
    - `code/scripts/run_power_analysis.py` — NOT invoked by the run-book
    - `code/scripts/validate_batch.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/analysis/power_analysis_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/analysis/sensitivity_sweep.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/analysis/plotting.py` — NOT invoked by the run-book
    - `code/src/analysis/sensitivity.py` — NOT invoked by the run-book
    - `code/src/analysis/report.py` — NOT invoked by the run-book
    - `code/src/analysis/run_analysis.py` — NOT invoked by the run-book
    - `code/src/analysis/__init__.py` — NOT invoked by the run-book
    - `code/scripts/validate_batch.py` — NOT invoked by the run-book
    - `code/tests/test_analysis.py` — NOT invoked by the run-book
    - `code/tests/test_sensitivity.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/analysis/sensitivity_sweep.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/analysis/simulation_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/simulation/serialization.py` — NOT invoked by the run-book
    - `code/src/simulation/run_simulation.py` — NOT invoked by the run-book
    - `code/src/analysis/plotting.py` — NOT invoked by the run-book
    - `code/src/analysis/sensitivity.py` — NOT invoked by the run-book
    - `code/src/analysis/anova.py` — NOT invoked by the run-book
    - `code/src/analysis/run_analysis.py` — NOT invoked by the run-book
    - `code/tests/test_analysis.py` — NOT invoked by the run-book
    - `code/tests/test_serialization.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/analysis/simulation_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/analysis/validation_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/scripts/validate_batch.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/analysis/validation_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
