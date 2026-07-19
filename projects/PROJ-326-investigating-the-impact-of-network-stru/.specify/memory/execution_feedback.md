# Execution failures — fix these before the analysis can run

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/run_log.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: every produced artifact is gitignored (data/run_log.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 1 command(s) failed: python code/main.py --config code/config.yaml --output data/ (rc=1); 5 declared deliverable(s) absent: data/analysis/final_results.json; data/analysis/power_analysis_report.json; data/analysis/sensitivity_sweep.json

## Failing / missing run-book commands

- python code/main.py --config code/config.yaml --output data/ -> rc=1
    2026-07-19 13:54:10,891 - matplotlib.font_manager - INFO - Failed to extract font properties from /usr/share/fonts/truetype/noto/NotoColorEmoji.ttf: Non-scalable fonts are not supported
2026-07-19 13:54:10,943 - matplotlib.font_manager - INFO - generated new fontManager
2026-07-19 13:54:11,233 - __main__ - INFO - Step 1: Injecting seeds into run log for reproducibility...
2026-07-19 13:54:11,236 - __main__ - ERROR - Pipeline failed: Config must contain 'random_seed' key for reproducibility.
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-326-investigating-the-impact-of-network-stru/code/main.py", line 49, in main
    inject_seed_to_log(str(config_path), f"{args.output}/run_log.json")
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-326-investigating-the-impact-of-network-stru/code/src/utils/reproducibility.py", line 74, in inject_seed_to_log
    raise ValueError("Config must contain 'random_seed' key for reproducibility.")
ValueError: Config must contain 'random_seed' key for reproducibility.

## Declared deliverables still missing

- data/analysis/final_results.json
- data/analysis/power_analysis_report.json
- data/analysis/sensitivity_sweep.json
- data/analysis/simulation_results.json
- data/raw/global_batch_manifest.json

## ✅ VERIFIED REAL DATA SOURCE — use THIS in the data loader

Do NOT invent or guess a download URL/API (a hallucinated endpoint will 404). A real source was discovered AND verified by actually loading real data from it:

- **Install**: add `networkx` to the project's `requirements.txt` and `pip install networkx`.
- **Verified**: this loads **1749** real records with fields: graph_id, node_id, edge_source, edge_target, degree_distribution_type, clustering_coefficient_target, clustering_coefficient_actual, rewiring_probability, scale_free_exponent_gamma, is_connected, num_nodes, num_edges.
- **Working access recipe** (this EXACT code was executed and returned real data — base the loader on it):

```python
import networkx as nx
import random

records = []
graph_id = 0

# Helper to add edge records with graph-level metadata
def add_graph_edges(G, model, **meta):
    global records, graph_id
    is_conn = nx.is_connected(G) if G.number_of_nodes() > 0 and nx.is_connected(G) else False
    avg_clust = nx.average_clustering(G)
    for u, v in G.edges():
        rec = {
            "graph_id": graph_id,
            "node_id": None,
            "edge_source": u,
            "edge_target": v,
            "degree_distribution_type": model,
            "clustering_coefficient_target": meta.get("clustering_target"),
            "clustering_coefficient_actual": avg_clust,
            "rewiring_probability": meta.get("rewiring_prob"),
            "scale_free_exponent_gamma": meta.get("scale_free_gamma"),
            "is_connected": is_conn,
            "num_nodes": G.number_of_nodes(),
            "num_edges": G.number_of_edges()
        }
        records.append(rec)
    graph_id += 1

# Erdős‑Rényi graphs
for p in [0.05, 0.1]:
    G = nx.erdos_renyi_graph(n=100, p=p, seed=random.randint(0, 10000))
    add_graph_edges(G, model="erdos_renyi")

# Watts‑Strogatz graphs
for k, p in [(4, 0.1), (6, 0.2)]:
    G = nx.watts_strogatz_graph(n=100, k=k, p=p, seed=random.randint(0, 10000))
    add_graph_edges(G, model="watts_strogatz", rewiring_prob=p, clustering_target=None)

# Barabási‑Albert graphs
for m in [2, 3]:
    G = nx.barabasi_albert_graph(n=100, m=m, seed=random.randint(0, 10000))
    # Approximate scale‑free exponent gamma ≈ 3 (theoretical) – use placeholder
    add_graph_edges(G, model="barabasi_albert", scale_free_gamma=3.0)

print(f"RECORDS={len(records)}")
print("FIELDS=" + ",".join(records[0].keys()))
```

Write the loader to use this source/recipe, persist the records to the declared raw/processed data files, and DELETE any old code that fetches from a guessed website endpoint.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/analysis/final_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/analysis/report.py` — NOT invoked by the run-book
    - `code/src/analysis/power.py` — NOT invoked by the run-book
    - `code/src/analysis/run_analysis.py` — NOT invoked by the run-book
    - `code/scripts/run_analysis.py` — NOT invoked by the run-book
    - `code/tests/test_run_analysis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/analysis/final_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/analysis/power_analysis_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/analysis/power.py` — NOT invoked by the run-book
    - `code/scripts/run_power_analysis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/analysis/power_analysis_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/analysis/sensitivity_sweep.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/validation/validate_batch.py` — NOT invoked by the run-book
    - `code/src/analysis/plotting.py` — NOT invoked by the run-book
    - `code/src/analysis/sensitivity.py` — NOT invoked by the run-book
    - `code/src/analysis/report.py` — NOT invoked by the run-book
    - `code/src/analysis/run_analysis.py` — NOT invoked by the run-book
    - `code/scripts/run_sensitivity_sweep.py` — NOT invoked by the run-book
    - `code/tests/test_analysis.py` — NOT invoked by the run-book
    - `code/tests/test_sensitivity.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/analysis/sensitivity_sweep.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/analysis/simulation_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/simulation/serialization.py` — NOT invoked by the run-book
    - `code/src/simulation/schema.py` — NOT invoked by the run-book
    - `code/src/simulation/run_simulation.py` — NOT invoked by the run-book
    - `code/src/analysis/plotting.py` — NOT invoked by the run-book
    - `code/src/analysis/sensitivity.py` — NOT invoked by the run-book
    - `code/src/analysis/anova.py` — NOT invoked by the run-book
    - `code/src/analysis/run_analysis.py` — NOT invoked by the run-book
    - `code/scripts/run_sensitivity_sweep.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/analysis/simulation_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/global_batch_manifest.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/validation/validate_batch.py` — NOT invoked by the run-book
    - `code/src/generators/aggregate_batch.py` — NOT invoked by the run-book
    - `code/tests/test_integration.py` — NOT invoked by the run-book
    - `code/tests/test_aggregate_batch.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/global_batch_manifest.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
