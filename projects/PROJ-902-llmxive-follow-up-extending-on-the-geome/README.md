# llmXive Geometry Extension

**Repository for extending the llmXive project with geometric‑mask experiments.**

## Quick‑Start

This guide walks you through setting up the environment, downloading the required data, and running the first user‑story pipelines.

### 1. Clone the repository

```bash
git clone
cd llmxive-geometry-extension
```

### 2. Install dependencies

The project uses **Python 3.11**. Install the required packages with `pip` (or `poetry` if you prefer):

```bash
pip install -r requirements.txt
```

The main dependencies include:

- `datasets` – for streaming the GSM8K dataset
- `torch` – PyTorch for model loading and training
- `bitsandbytes` – 8‑bit quantisation utilities
- `numpy`, `pandas`, `scipy` – numerical and statistical helpers
- `psutil`, `ruff`, `mypy` – tooling and linting

### 3. Verify the project layout

The repository must contain the following top‑level directories:

```
src/ # source code
tests/ # unit, integration and contract tests
data/ # downloaded datasets and generated splits
results/ # CSV and summary files produced by pipelines
contracts/ # JSON/YAML contracts for schema validation
```

A small contract test (`tests/contract/test_project_layout.py`) asserts their existence.

### 4. Download the GSM8K dataset

The dataset‑download script streams the data directly from the HuggingFace hub and caches it under `data/gsm8k/`:

```bash
python -m src.data.download_gsm8k
```

After the download finishes, a checksum file `data/checksums.txt` is generated for integrity verification.

### 5. Run the baseline and mask generation pipelines

**User Story 1 – Subspace Sufficiency (US1)**

```bash
python -m src.pipeline.run_us1
```

This orchestrates:

1. OPD baseline training (`src/train/opd_baseline.py`)
2. SVD computation (`src/data/svd_compute.py`)
3. Mask aggregation (`src/model/mask.py`)
4. Evaluation and statistical analysis (`src/eval/*`)

The resulting summary CSV is written to `results/us1_summary.csv`.

**User Story 2 – Comparative Geometric Distinctness (US2)**

```bash
python -m src.pipeline.run_us2
```

This runs the same pipeline for both the OPD mask and a random mask, evaluates accuracy, and records statistical tests in `results/us2_summary.csv`.

### 6. Run the full experiment suite

To execute both user stories sequentially and produce a unified summary:

```bash
python -m src.pipeline.run_all
```

The unified CSV (`results/experiment_summary.csv`) conforms to `contracts/experiment.schema.yaml`.

### 7. Run the test suite

```bash
pytest -q
```

All unit, integration, and contract tests should pass. The CI workflow (`.github/workflows/ci.yml`) runs the same checks (Wikipedia: Qodo, https://en.wikipedia.org/wiki/Qodo) automatically.

## Project Structure Overview

- `src/` – core modules (data handling, utilities, models, training, evaluation, pipelines)
- `tests/` – **contract** tests (schema validation), **unit** tests (functionality), **integration** tests (end‑to‑end scripts)
- `data/` – cached dataset files and generated splits/checksums
- `results/` – CSV files produced by pipelines and the final unified summary
- `contracts/` – JSON/YAML schemas used by contract tests

## Contributing

1. Fork the repository.
2. Create a feature branch.
3. Ensure all tests pass locally.
4. Open a pull request.

## License

This project is licensed under the MIT License. See `LICENSE` for details.