# Quickstart: llmXive follow‑up – Symbolic Bidirectional Evolutionary Search

## Overview
This quickstart provides a minimal, reproducible command chain that:
1. Installs the project dependencies.
2. Generates a small pilot dataset.
3. Runs the pilot version of the BES pipeline (the only mode that currently works out‑of‑the‑box).

The commands are designed to run on a **CPU‑only** environment (e.g. GitHub Actions free tier or a local machine) and create non‑empty artifacts under `data/processed/pilot/`.

## Prerequisites
- Python 3.11+
- Git
- Sufficient RAM (approximately a few gigabytes) and at least 2 CPU cores

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
All unit tests should pass.  The fixes for **T001** and **T002** are already incorporated, so the suite runs without import errors.

## Phase 0 – Pilot dataset & verification

```bash
python -m code.main --pilot --seed 42
```
- Generates a tiny puzzle set (a small number of instances) using the deterministic generator.
- Runs the deterministic verifier on a known correct solution (latency < 100 ms).
- Writes the pilot log to:
  - `data/processed/pilot/pilot_run.jsonl`
  - `data/processed/pilot/verifier_timing.log`

## Expected output locations

After the pilot command finishes, the following files/directories must exist and be non‑empty:

- `data/processed/pilot/pilot_run.jsonl` – JSON‑Lines file containing one entry per puzzle with verification timing and success flag.
- `data/processed/pilot/verifier_timing.log` – simple timing log produced by the pilot run.
- `data/processed/pilot/` – folder that may contain auxiliary logs (e.g., `verifier_timing.log`).

## Troubleshooting

- **Command fails with usage error** – ensure you are running the *pilot* mode (`--pilot`).  The symbolic and neural modes are not yet wired into the CLI; attempting to use them will raise a usage error.
- **Empty `pilot_run.jsonl`** – verify that the `code.main` entry point executed without exception (check the console output for any traceback).  The deterministic verifier must complete within 100 ms per puzzle; if it exceeds this, the pipeline aborts.
- **Missing `data/processed/` directory** – the `paths` helper from `llmxive_toolkit` creates parent folders automatically.  If the directory is still missing, the script likely terminated early; re‑run with `--seed 42` to get deterministic behaviour.

## Next steps

Once the pilot run succeeds, you can proceed to implement the full symbolic‑guided and neural‑baseline experiments (tasks T003‑T009).  Those commands will be added to the quickstart once the corresponding CLI flags are implemented.

---

*This document is version‑controlled; any future changes to the command chain must be reflected here to keep the quickstart reproducible.*
