# Quickstart: llmXive follow‑up – Symbolic Bidirectional Evolutionary Search

## Overview
This quickstart provides a minimal, reproducible command chain that:
1. Installs the project dependencies.
2. Generates a small pilot dataset (in the required JSON format).
3. Runs the pilot version of the BES pipeline (the only mode that currently works out‑of‑the‑box).

All commands are CPU‑only and suitable for GitHub Actions free‑tier or a local machine.

## Prerequisites
- Python 3.11+  
- Git  
- At least 2 CPU cores and a few GB of RAM  

## Installation

```bash
# 1. Clone the repository
git clone <repo-url>
cd projects/PROJ-884-llmxive-follow-up-extending-self-improvi

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3. Install pinned dependencies
pip install -r requirements.txt
```

## Verify the test suite

```bash
pytest tests/unit/
```

All unit tests should pass. The fixes for **T001** (generator output format) and **T002** (planner exception handling) are incorporated.

## Phase 0 – Pilot dataset & verification

```bash
python -m code.main --mode pilot --seed 42
```

What this does:
- Generates a tiny puzzle set (default `N=10`, 5 puzzles) and writes **one JSON file** `data/raw/puzzles.json` containing a `"puzzles"` list (required by `test_generator.py`).  
- Creates deterministic verifier scripts under `data/raw/verifiers/`.  
- Runs a single generation of the BES loop using the symbolic planner and the CPU LLM.  
- Writes pilot logs to:
  - `data/processed/pilot/pilot_run.jsonl` – one line per puzzle with success flag, timing, and feasibility flag.  
  - `data/processed/pilot/summary.json` – aggregated success rate (conditional on feasibility), feasibility rate, and mean time.

## Expected output locations

After the pilot command finishes, the following files/directories must exist and be non‑empty:

- `data/raw/puzzles.json` – JSON object with `"puzzles"` list.  
- `data/raw/verifiers/` – deterministic verifier scripts (unchanged after creation).  
- `data/processed/pilot/pilot_run.jsonl` – per‑puzzle logs (includes feasibility flag).  
- `data/processed/pilot/summary.json` – high‑level metrics (conditional success rate, feasibility rate, mean time).  

## Troubleshooting

- **Command fails with usage error** – ensure you are using the `--mode pilot` flag; other modes are not yet wired.  
- **Empty `pilot_run.jsonl`** – check console output for tracebacks; the deterministic verifier must complete within 100 ms per puzzle.  
- **Missing `data/raw/puzzles.json`** – the generator may have aborted; re‑run with the same seed (`--seed 42`) for deterministic behaviour.

## Next steps

Once the pilot run succeeds, you can proceed to the full experiments:

```bash
python -m code.main --mode full --seed 42
```

This will:
- Generate the full synthetic dataset (N = 10 → 500).  
- Run **both** the symbolic‑guided BES and the neural‑verifier baseline on the *matched* set of puzzles (excluding only those where the symbolic planner fails).  
- Produce `data/processed/full/` with logs, `summary_symbolic.json`, `summary_neural.json`, and the final statistical result file `data/processed/full/statistical_result.json` (conforms to `contracts/output.schema.yaml`).  
- Record **CPU‑seconds** for each method and a placeholder `gpu_hours = 0` to satisfy Principle VII.

*Remember to keep the virtual environment activated and to use the same seed for reproducibility.*

---

