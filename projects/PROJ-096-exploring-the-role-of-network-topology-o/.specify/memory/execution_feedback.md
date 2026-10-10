# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/generate_topology.py: synthetic/fake INPUT data not authorized by the spec — “…-> nx.Graph:     """     Generate a synthetic regular ring lattice.…”
- code/generate_topology.py: synthetic/fake INPUT data not authorized by the spec — “…corrected_requirement": "Generate synthetic regular ring lattice (N=…”

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- data/processed/simulation_results.csv: header only, ZERO data rows — the analysis produced no rows
- every produced artifact is gitignored (data/processed/simulation_results.csv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 fabricated/simulated-result signal(s) — results are not real measurements: code/generate_topology.py: synthetic/fake INPUT data not authorized by the spec — “…-> nx.Graph:     """     Generate a synthetic regular ring lattice.…”; code/generate_topology.py: synthetic/fake INPUT data not authorized by the spec — “…corrected_requirement": "Generate synthetic regular ring lattice (N=…”; 1 hollow-result signal(s) — the analysis ran but computed nothing: data/processed/simulation_results.csv: header only, ZERO data rows — the analysis produced no rows; every produced artifact is gitignored (data/processed/simulation_results.csv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 3 command(s) failed: python code/generate_topology.py (rc=1); python code/analyze_results.py (rc=2); python -m pytest tests/ -v (rc=1); 7 declared deliverable(s) absent: data/processed/config.json; data/processed/correlation_results.json; data/processed/graph_metadata.json

## Failing / missing run-book commands

- python code/generate_topology.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-096-exploring-the-role-of-network-topology-o/code/generate_topology.py", line 302, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-096-exploring-the-role-of-network-topology-o/code/generate_topology.py", line 290, in main
    sys.exit(1)
    ^^^
NameError: name 'sys' is not defined

- python code/analyze_results.py -> rc=2

2026-10-10 07:22:19,144 - __main__ - INFO - Loading simulation results from data/processed/simulation_results.csv
2026-10-10 07:22:19,144 - __main__ - ERROR - Value error: No valid data rows found in simulation results

- python -m pytest tests/ -v -> rc=1

/home/runner/work/llmXive/llmXive/projects/PROJ-096-exploring-the-role-of-network-topology-o/code/.venv/bin/python: No module named pytest


## Declared deliverables still missing

- data/processed/config.json
- data/processed/correlation_results.json
- data/processed/graph_metadata.json
- data/processed/invariance_verification.json
- data/processed/plot_kc_vs_p.png
- data/processed/sensitivity_analysis.json
- data/processed/stability_results.json

## ✅ VERIFIED REAL DATA SOURCE — use THIS in the data loader

Do NOT invent or guess a download URL/API (a hallucinated endpoint will 404). A real source was discovered AND verified by actually loading real data from it:

- **Install**: add `networkx` to the project's `requirements.txt` and `pip install networkx`.
- **Verified**: this loads **60** real records with fields: node_id, source, target.
- **Working access recipe** (this EXACT code was executed and returned real data — base the loader on it):

```python
import networkx as nx
# generate a regular ring lattice (Watts-Strogatz with rewiring prob 0)
G = nx.watts_strogatz_graph(n=30, k=4, p=0)
# build records: each edge as a dict with node_id, source, target (node_id = source)
records = [{'node_id': u, 'source': u, 'target': v} for u, v in G.edges()]
print(f'RECORDS={len(records)}')
print('FIELDS=node_id,source,target')
```

Write the loader to use this source/recipe, persist the records to the declared raw/processed data files, and DELETE any old code that fetches from a guessed website endpoint.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/config.json` is declared but was NOT written. Scripts referencing it:
    - `code/check_stability.py` — NOT invoked by the run-book
    - `code/feasibility_study.py` — NOT invoked by the run-book
    - `code/generate_report.py` — NOT invoked by the run-book
    - `code/generate_topology.py` — IS a run-book command
    - `code/review_physical_claims.py` — NOT invoked by the run-book
    - `code/setup_config.py` — NOT invoked by the run-book
    - `code/setup_linting.py` — NOT invoked by the run-book
    - `code/setup_venv.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/config.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/correlation_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/analyze_results.py` — IS a run-book command
    - `code/generate_report.py` — NOT invoked by the run-book
    - `code/validate_quickstart.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/correlation_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/graph_metadata.json` is declared but was NOT written. Scripts referencing it:
    - `code/generate_topology.py` — IS a run-book command
    - `code/setup_data_structure.py` — NOT invoked by the run-book
    - `code/validate_quickstart.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/graph_metadata.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/invariance_verification.json` is declared but was NOT written. Scripts referencing it:
    - `code/generate_report.py` — NOT invoked by the run-book
    - `code/review_physical_claims.py` — NOT invoked by the run-book
    - `code/validate_quickstart.py` — NOT invoked by the run-book
    - `code/verify_invariance.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/invariance_verification.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/plot_kc_vs_p.png` is declared but was NOT written. Scripts referencing it:
    - `code/validate_quickstart.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/plot_kc_vs_p.png` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/sensitivity_analysis.json` is declared but was NOT written. Scripts referencing it:
    - `code/generate_report.py` — NOT invoked by the run-book
    - `code/sensitivity_analysis.py` — NOT invoked by the run-book
    - `code/validate_quickstart.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/sensitivity_analysis.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/stability_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/check_stability.py` — NOT invoked by the run-book
    - `code/generate_report.py` — NOT invoked by the run-book
    - `code/validate_quickstart.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/stability_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
