# Execution failures — fix these before the analysis can run

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/raw/networks/ER/metadata_ER_0000.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: every produced artifact is gitignored (data/raw/networks/ER/metadata_ER_0000.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 2 run-book script(s) missing (plan/impl path mismatch): python code/simulate_hk.py  --networks data/raw/networks/  --epsilon-start 0.05  --epsilon-end 0.50  --epsilon-step 0.05  --seeds 50  --output data/raw/simulations/; python code/analyze_scaling.py  --simulations data/raw/simulations/  --networks data/raw/networks/  --output data/processed/; 3 command(s) failed: python code/generate_networks.py --output data/raw/networks/ --seeds 50 (rc=1); python -m pytest tests/unit/test_hk_update.py -v (rc=4); python -m pytest tests/integration/test_full_pipeline.py -v (rc=4)

## Failing / missing run-book commands

- python code/generate_networks.py --output data/raw/networks/ --seeds 50 -> rc=1

2026-10-13 00:26:02,128 INFO __main__: Generating 50 instance(s) for topology set: ['ER', 'BA', 'WS']
2026-10-13 00:26:02,138 INFO __main__: Wrote data/raw/networks/ER/ER_0000.edgelist and data/raw/networks/ER/metadata_ER_0000.json
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-672-the-impact-of-bounded-confidence-on-opin/code/generate_networks.py", line 237, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-672-the-impact-of-bounded-confidence-on-opin/code/generate_networks.py", line 200, in main
    raise RuntimeError(
RuntimeError: Generated graph has 499 nodes; expected 500.

- python code/simulate_hk.py  --networks data/raw/networks/  --epsilon-start 0.05  --epsilon-end 0.50  --epsilon-step 0.05  --seeds 50  --output data/raw/simulations/ -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-672-the-impact-of-bounded-confidence-on-opin/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-672-the-impact-of-bounded-confidence-on-opin/code/simulate_hk.py': [Errno 2] No such file or directory

- python code/analyze_scaling.py  --simulations data/raw/simulations/  --networks data/raw/networks/  --output data/processed/ -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-672-the-impact-of-bounded-confidence-on-opin/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-672-the-impact-of-bounded-confidence-on-opin/code/analyze_scaling.py': [Errno 2] No such file or directory

- python -m pytest tests/unit/test_hk_update.py -v -> rc=4
============================= test session starts ==============================
platform linux -- Python 3.11.17, pytest-8.2.0, pluggy-1.6.0 -- /home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-672-the-impact-of-bounded-confidence-on-opin/bin/python
cachedir: .pytest_cache
rootdir: /home/runner/work/llmXive/llmXive/projects/PROJ-672-the-impact-of-bounded-confidence-on-opin
configfile: pytest.ini
collecting ... collected 0 items

============================ no tests ran in 0.00s =============================

ERROR: file or directory not found: tests/unit/test_hk_update.py


- python -m pytest tests/integration/test_full_pipeline.py -v -> rc=4
============================= test session starts ==============================
platform linux -- Python 3.11.17, pytest-8.2.0, pluggy-1.6.0 -- /home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-672-the-impact-of-bounded-confidence-on-opin/bin/python
cachedir: .pytest_cache
rootdir: /home/runner/work/llmXive/llmXive/projects/PROJ-672-the-impact-of-bounded-confidence-on-opin
configfile: pytest.ini
collecting ... collected 0 items

============================ no tests ran in 0.00s =============================

ERROR: file or directory not found: tests/integration/test_full_pipeline.py



## ✅ VERIFIED REAL DATA SOURCE — use THIS in the data loader

Do NOT invent or guess a download URL/API (a hallucinated endpoint will 404). A real source was discovered AND verified by actually loading real data from it:

- **Install**: add `datasets` to the project's `requirements.txt` and `pip install datasets`.
- **Verified**: this loads **10000** real records with fields: algorithm, edge_list, node_count, edge_count, node_degree_node, node_degree, edge_existence_src, edge_existence_dst, edge_existence, cycle_check, triangle_count, connected_nodes_node, connected_nodes, reachability_src, reachability_dst, reachability, shortest_path_src, shortest_path_dst, shortest_path.
- **Working access recipe** (this EXACT code was executed and returned real data — base the loader on it):

```python
import datasets

ds = datasets.load_dataset("vstenby/random-graphs", split="train")
print(f"RECORDS={len(ds)}")
print("FIELDS=" + ",".join(ds.column_names))
```

Write the loader to use this source/recipe, persist the records to the declared raw/processed data files, and DELETE any old code that fetches from a guessed website endpoint.
## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
