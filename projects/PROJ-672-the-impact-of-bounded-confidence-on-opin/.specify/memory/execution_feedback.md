# Execution failures — fix these before the analysis can run

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/raw/networks/BA_metadata.csv, data/raw/networks/ER_metadata.csv, data/raw/networks/WS_metadata.csv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: every produced artifact is gitignored (data/raw/networks/BA_metadata.csv, data/raw/networks/ER_metadata.csv, data/raw/networks/WS_metadata.csv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 1 run-book script(s) missing (plan/impl path mismatch): python code/analyze_scaling.py  --simulations data/raw/simulations/  --networks data/raw/networks/  --output data/processed/; 2 command(s) failed: python code/simulate_hk.py  --networks data/raw/networks/  --epsilon-start 0.05  --epsilon-end 0.50  --epsilon-step 0.05  --seeds 50  --output data/raw/simulations/ (rc=-1); python -m pytest tests/integration/test_full_pipeline.py -v (rc=4); 1 declared deliverable(s) absent: data/raw/simulations/summary.csv

## Failing / missing run-book commands

- python code/simulate_hk.py  --networks data/raw/networks/  --epsilon-start 0.05  --epsilon-end 0.50  --epsilon-step 0.05  --seeds 50  --output data/raw/simulations/ -> rc=-1

2026-10-31 15:16:02,066 INFO __main__: Running HK simulation on 150 networks, 10 epsilons, 50 seeds

[TIMEOUT after 120s]
- python code/analyze_scaling.py  --simulations data/raw/simulations/  --networks data/raw/networks/  --output data/processed/ -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-672-the-impact-of-bounded-confidence-on-opin/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-672-the-impact-of-bounded-confidence-on-opin/code/analyze_scaling.py': [Errno 2] No such file or directory

- python -m pytest tests/integration/test_full_pipeline.py -v -> rc=4
============================= test session starts ==============================
platform linux -- Python 3.11.17, pytest-8.2.0, pluggy-1.7.0 -- /home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-672-the-impact-of-bounded-confidence-on-opin/bin/python
cachedir: .pytest_cache
rootdir: /home/runner/work/llmXive/llmXive/projects/PROJ-672-the-impact-of-bounded-confidence-on-opin
configfile: pytest.ini
collecting ... collected 0 items

============================ no tests ran in 0.00s =============================

ERROR: file or directory not found: tests/integration/test_full_pipeline.py



## Declared deliverables still missing

- data/raw/simulations/summary.csv

## ✅ VERIFIED REAL DATA SOURCE — use THIS in the data loader

Do NOT invent or guess a download URL/API (a hallucinated endpoint will 404). A real source was discovered AND verified by actually loading real data from it:

- **Install**: add `networkx` to the project's `requirements.txt` and `pip install networkx`.
- **Verified**: this loads **5** real records with fields: graph_id, topology_type, seed, num_nodes, parameters, edge_list, adjacency_matrix, degree_distribution, average_degree, clustering_coefficient, average_path_length.
- **Working access recipe** (this EXACT code was executed and returned real data — base the loader on it):

```python
import networkx as nx

def make_record(gid, topo, seed, n, params, G):
    edge_list = list(G.edges())
    # build adjacency matrix without numpy
    matrix = [[1 if j in G[i] else 0 for j in range(n)] for i in range(n)]
    degrees = [d for _, d in G.degree()]
    avg_deg = sum(degrees) / n
    clustering = nx.average_clustering(G)
    try:
        apl = nx.average_shortest_path_length(G)
    except nx.NetworkXError:
        apl = None
    return {
        "graph_id": gid,
        "topology_type": topo,
        "seed": seed,
        "num_nodes": n,
        "parameters": params,
        "edge_list": edge_list,
        "adjacency_matrix": matrix,
        "degree_distribution": degrees,
        "average_degree": avg_deg,
        "clustering_coefficient": clustering,
        "average_path_length": apl,
    }

def generate():
    records = []
    seeds = [42, 43, 44, 45, 46]
    # Erdos‑Renyi graphs
    for i, seed in enumerate(seeds[:2], start=1):
        n = 100
        p = 0.05
        G = nx.erdos_renyi_graph(n, p, seed=seed)
        records.append(make_record(i, "erdos_renyi", seed, n, {"p": p}, G))
    # Barabási‑Albert graphs
    for i, seed in enumerate(seeds[2:4], start=3):
        n = 100
        m = 3
        G = nx.barabasi_albert_graph(n, m, seed=seed)
        records.append(make_record(i, "barabasi_albert", seed, n, {"m": m}, G))
    # Watts‑Strogatz graph
    seed = seeds[4]
    n = 100
    k = 4
    p = 0.1
    G = nx.watts_strogatz_graph(n, k, p, seed=seed)
    records.append(make_record(5, "watts_strogatz", seed, n, {"k": k, "p": p}, G))
    return records

records = generate()
print(f"RECORDS={len(records)}")
print("FIELDS=graph_id,topology_type,seed,num_nodes,parameters,edge_list,adjacency_matrix,degree_distribution,average_degree,clustering_coefficient,average_path_length")
```

Write the loader to use this source/recipe, persist the records to the declared raw/processed data files, and DELETE any old code that fetches from a guessed website endpoint.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/raw/simulations/summary.csv` is declared but was NOT written. Scripts referencing it:
    - `code/calculate_network_metrics.py` — NOT invoked by the run-book
    - `code/generate_networks.py` — IS a run-book command
    - `code/run_batch.py` — NOT invoked by the run-book
    - `code/simulate_hk.py` — IS a run-book command
  Make ONE of these WRITE `data/raw/simulations/summary.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
