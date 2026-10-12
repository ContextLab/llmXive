# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/loader.py: synthetic/fake INPUT data not authorized by the spec — “…etworkGraph:     """     Generates a synthetic random graph (Erdos-Reny…”
- code/loader.py: synthetic/fake INPUT data not authorized by the spec — “…3. If 10 <= real N < 30, generate synthetic data to reach N=30 and s…”
- code/loader.py: synthetic/fake INPUT data not authorized by the spec — “…en 10 and 30. Generating synthetic data to reach N=30.")…”
- code/loader.py: synthetic/fake INPUT data not authorized by the spec — “…= []                  # Generate synthetic graphs         for i in…”
- code/loader.py: synthetic/fake INPUT data not authorized by the spec — “…# Save synthetic data to CSV         synthetic…”
- code/loader.py: synthetic/fake INPUT data not authorized by the spec — “…# The task says "generate synthetic data to reach N=30".…”
- code/loader.py: synthetic/fake INPUT data not authorized by the spec — “…s "If 10 <= real N < 30, generate synthetic data to reach N=30".…”
- code/src/loader.py: synthetic/fake INPUT data not authorized by the spec — “…100) -> Any:     """     Generates a synthetic graph (Barabasi-Albert)…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 9 fabricated/simulated-result signal(s) — results are not real measurements: code/loader.py: synthetic/fake INPUT data not authorized by the spec — “…etworkGraph:     """     Generates a synthetic random graph (Erdos-Reny…”; code/loader.py: synthetic/fake INPUT data not authorized by the spec — “…3. If 10 <= real N < 30, generate synthetic data to reach N=30 and s…”; code/loader.py: synthetic/fake INPUT data not authorized by the spec — “…en 10 and 30. Generating synthetic data to reach N=30.")…”; 4 command(s) failed: python -m src.main --action download (rc=1); python -m src.main --action run (rc=1); python -m src.main --action viz (rc=1)

## Failing / missing run-book commands

- python -m src.main --action download -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-212-exploring-the-impact-of-network-structur/bin/python: No module named src.main

- python -m src.main --action run -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-212-exploring-the-impact-of-network-structur/bin/python: No module named src.main

- python -m src.main --action viz -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-212-exploring-the-impact-of-network-structur/bin/python: No module named src.main

- python -m pytest tests/ -v -> rc=2
mportlib.import_module(module_name)
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
<frozen importlib._bootstrap>:1204: in _gcd_import
    ???
<frozen importlib._bootstrap>:1176: in _find_and_load
    ???
<frozen importlib._bootstrap>:1147: in _find_and_load_unlocked
    ???
<frozen importlib._bootstrap>:690: in _load_unlocked
    ???
../../.llmxive-venvs/PROJ-212-exploring-the-impact-of-network-structur/lib/python3.11/site-packages/_pytest/assertion/rewrite.py:178: in exec_module
    exec(co, module.__dict__)
tests/test_utils.py:7: in <module>
    from src.utils import save_json, get_logger
E   ImportError: cannot import name 'save_json' from 'src.utils' (/home/runner/work/llmXive/llmXive/projects/PROJ-212-exploring-the-impact-of-network-structur/code/src/utils.py)
=========================== short test summary info ============================
ERROR tests/test_data_availability.py
ERROR tests/test_utils.py
!!!!!!!!!!!!!!!!!!! Interrupted: 2 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 2 errors in 1.21s ===============================



## ✅ VERIFIED REAL DATA SOURCE — use THIS in the data loader

Do NOT invent or guess a download URL/API (a hallucinated endpoint will 404). A real source was discovered AND verified by actually loading real data from it:

- **Install**: add `networkx` to the project's `requirements.txt` and `pip install networkx`.
- **Verified**: this loads **78** real records with fields: edge_list, node_count, edge_count, degree_distribution, clustering_coefficient, average_path_length, is_connected.
- **Working access recipe** (this EXACT code was executed and returned real data — base the loader on it):

```python
import networkx as nx
import urllib.request
import io

# Load a SNAP network dataset via NetworkX
# Using a standard SNAP dataset (Karate Club network as example)
try:
    # Load Karate Club dataset (classic SNAP network)
    url = 'https://snap.stanford.edu/data/karate.gml'
    G = nx.read_gml(urllib.request.urlopen(url))
except:
    # Fallback to built-in NetworkX example
    G = nx.karate_club_graph()

node_count = G.number_of_nodes()
edge_count = G.number_of_edges()
edge_list = list(G.edges())
degrees = [d for n, d in G.degree()]

# Calculate metrics
if nx.is_connected(G):
    avg_path_length = nx.average_shortest_path_length(G)
else:
    avg_path_length = None

clustering_coeff = nx.average_clustering(G)

RECORDS = edge_count
FIELDS = 'edge_list,node_count,edge_count,degree_distribution,clustering_coefficient,average_path_length,is_connected'
print(f'RECORDS={RECORDS}')
print(f'FIELDS={FIELDS}')
```

Write the loader to use this source/recipe, persist the records to the declared raw/processed data files, and DELETE any old code that fetches from a guessed website endpoint.
## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
