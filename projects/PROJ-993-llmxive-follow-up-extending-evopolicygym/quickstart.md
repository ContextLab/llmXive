# Quickstart: EvoPolicyGym Extension

## Prerequisites

1. **Install dependencies**
 ```bash
 pip install -r requirements.txt
 ```

2. **Discover environments (if not already present)**
 ```bash
 python -m code.main --check # will report missing files
 # If the check fails because files are missing, run the discovery step:
 python -m code.main --run-full-pipeline --seeds 42 --runs 1 --conditions baseline counterfactual
 ```

## Running the pipeline

The orchestrator provides three entry points:

### 1. Verify pre‑conditions
```bash
python -m code.main --check
```
Prints `All pre‑conditions satisfied` when `data/discovered_envs.json` and
`data/sensitivity_report.csv` exist.

### 2. Run only the evolutionary harness
```bash
python -m code.main --run-evolution --seeds 42 43 --runs 5 --conditions baseline counterfactual
```
Generates `data/evolution_results.csv`, `data/run_state.json`, and related
artefacts.

### 3. Run the full end‑to‑end study
```bash
python -m code.main --run-full-pipeline --seeds 42 --runs 5 --conditions baseline counterfactual
```
Executes, in order:
1. Dynamic‑shift environment generation
2. Shift sensitivity analysis (`data/sensitivity_report.csv`)
3. Shift validation (p‑values)
4. Evolutionary harness
5. Mixed‑effects statistical analysis (`data/stats_results.json`)

After completion, the following key files should be present:

- `data/discovered_envs.json`
- `data/sensitivity_report.csv`
- `data/evolution_results.csv`
- `data/stats_results.json`
- `data/final_results.csv` (created by later pipeline stages)

## Troubleshooting

- **Missing `discovered_envs.json`** – run the full pipeline or the
 discovery step first.
- **Missing `sensitivity_report.csv`** – ensure the shift analysis step
 completed successfully; the orchestrator will abort with a clear error
 if this file is absent.
- **Any step aborts** – the error message printed to stderr indicates the
 missing prerequisite. Fix the issue and re‑run the appropriate command.