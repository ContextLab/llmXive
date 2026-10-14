# Quickstart: llmXive Follow-up: Structural Mismatch Cost in Heterogeneous Retrieval

## Prerequisites
- Python 3.11+
- Linux environment (GitHub Actions runner or equivalent)
- ≥ 7 GB RAM, ≥ 2 CPU cores

## Installation
```bash
git clone <repo-url>
cd projects/PROJ-883-llmxive-follow-up-extending-omniretrieva
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## End‑to‑End Run
```bash
python -m code.main
```
The command performs the full pipeline:
1. Downloads verified datasets (`data_loader.py`).
2. Generates queries (`query_generator.py`).
3. Builds ground‑truth plans (`ground_truth_engine.py`).
4. Executes under **cgroups** CPU throttling; **if cgroups cannot be applied the run aborts** (`ERR_THROTTLE_UNAVAILABLE`). No fallback to time‑only throttling.
5. Runs ANCOVA, Tukey, chi‑square (translation‑error stability), and sensitivity analysis (`stats.py`).
6. Produces the interaction plot (`visualize.py`).

All intermediate files are version‑controlled and checksummed; re‑running any step yields identical results (random seeds are fixed in `code/config.py`).

## Step‑by‑Step (for debugging)

| Step | Command | Description |
|------|---------|-------------|
| Data preparation | `python code/data_loader.py --prepare` | Downloads DBpedia, MS MARCO, and Spider; verifies checksums. |
| Query generation | `python code/query_generator.py --levels 1 2 3 4 --count 125` | Creates a large number of queries., writes `generation_log.json`. |
| Schema validation | `python -c "import json, jsonschema, pathlib; schema=json.load(open('specs/001-llmxive-follow-up-extending-omniretrieva/contracts/query_instance.schema.yaml')); data=json.load(open('data/processed/generation_log.json')); jsonschema.validate(data, schema)"` | Validates `generation_log.json` against its schema (plan consistency). |
| Ground‑truth | `python code/ground_truth_engine.py --input data/processed/generation_log.json --output data/processed/generation_log.json` | Populates `ground_truth_plan` using an independent cost table. |
| Benchmark | `python code/benchmark_runner.py --throttle cgroups` | Executes queries, writes `execution_logs.csv`. |
| Statistics | `python code/stats.py --input data/processed/execution_logs.csv` | Generates `anova_results.json`, `sensitivity_analysis.json`. |
| Visualization | `python code/visualize.py --input data/processed/execution_logs.csv --output data/results/interaction_plot.png` | Saves the interaction plot. |

## Notes

* If the runner lacks permission to create cgroups, the pipeline will exit with `ERR_THROTTLE_UNAVAILABLE` – this prevents mixing throttling modes.  
* Synthetic topology fallback (`synthetic_flag=1`) is **excluded** from all statistical tests.  
