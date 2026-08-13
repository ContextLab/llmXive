# llmXive Geometry Extension

## Overview
This repository implements the **llmXive Geometry Extension** project, providing data
download, preprocessing, model training, evaluation, statistical analysis, and a
unified experiment aggregation pipeline. All scripts are written for Python 3.11
and can be run on a standard Linux workstation or CI runner.

## Quickstart
Follow these steps to get the project up and running from a fresh clone:

```bash
# 1. Install the required Python packages
pip install -r requirements.txt

# 2. Download the GSM8K dataset (the script validates SHA‑256 checksums)
python -m src.data.download_gsm8k

# 3. Run the full end‑to‑end experiment pipeline
python -m src.pipeline.run_all
```

The commands above will:
* fetch and verify the GSM8K data,
* execute the US‑1, US‑2, and US‑3 pipelines,
* generate per‑seed results, `state.yaml`, and a unified
 `results/experiment_summary.csv`,
* produce `ci_metrics.json` containing peak RAM and total wall‑clock time.

## Running the Full Pipeline
The primary entry point for the experiment is **`src/pipeline/run_all.py`**.
It orchestrates the three user‑story pipelines (`run_us1.py`, `run_us2.py`,
`run_us3.py`), aggregates their CSV outputs, and writes the final summary.

You can invoke it in either of the following ways:

```bash
# Preferred module‑style execution (ensures the package is on the import path)
python -m src.pipeline.run_all

# Direct script execution (also works)
python src/pipeline/run_all.py
```

## Additional Documentation
* **`quickstart.md`** – step‑by‑step reproduction instructions, including
 environment setup and troubleshooting tips.
* **`data-model.md`** – description of dataset schemas, splits, and checksum
 handling.
* **`contracts/`** – JSON/YAML schemas used by the contract tests under
 `tests/contract/`.
* **`src/`** – core source code (data utilities, model masks, training,
 evaluation, statistical analysis, and pipeline orchestration).

## Testing
The repository ships a comprehensive test suite:

```bash
# Run all unit, integration, and contract tests
pytest -q
```

The CI workflow (`.github/workflows/ci.yml`) executes the same command,
validates `ci_metrics.json`, and enforces the pass‑rate threshold.

---

*For any questions or contributions, please open an issue or submit a pull
request.*