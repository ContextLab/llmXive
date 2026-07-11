# Quickstart: llmXive Follow-up: Extending MulTaBench

## Prerequisites

*   Python 3.11+
*   Git
*   Access to the MulTaBench dataset (local copy required; see `data/README.md` for setup and checksum verification).
*   GB+ RAM available.

## Installation

1.  **Clone and Setup**:
    ```bash
    git checkout 001-llmxive-mulTabench-extension
    cd projects/PROJ-823-llmxive-follow-up-extending-multabench-b
    ```

2.  **Create Virtual Environment**:
    ```bash
    python -m venv .venv
    source .venv/bin/activate
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -e .
    ```
    *Note: This installs CPU-only versions of PyTorch and Transformers from `pyproject.toml`.*

## Data Setup

Ensure the MulTaBench raw data is present in `data/raw/`. The directory structure should match:
```text
data/raw/
├── dataset_001/
│   ├── images/
│   ├── text/
│   ├── tabular.csv
│   └── labels.csv
...
```
**Crucial**: Update `data/README.md` with the SHA-256 checksum of your MulTaBench archive. The pipeline will verify this checksum before running.

## Running the Pipeline

The pipeline is executed in three sequential phases.

### Phase 1: Generate Frozen Embeddings (FR-001)
Generates embeddings for images and text using CLIP and Sentence-BERT. Runs multiple seeds for sensitivity analysis.
```bash
python code/pipelines/run_baseline.py --seed 42 --additional-seeds 123,456,789,101 --batch-size 8
```
*Output*: `data/processed/embeddings/*.parquet` (with `run_id` and `seed` columns)

### Phase 2: Train Tabular-Conditioned Projection (FR-002)
Trains the lightweight projection module on the generated embeddings.
```bash
python code/pipelines/run_conditioned.py --seed --epochs 15
```
*Output*: `data/processed/models/*.pth`, `data/artifacts/cpu_conditioned_metrics.csv`

### Phase 3: Statistical Analysis (FR-003, FR-005, FR-006)
Computes metadata stats, recovery ratios (averaged), and correlation analysis.
```bash
python code/pipelines/run_analysis.py
```
*Output*: `data/artifacts/correlation_report.csv`, `data/artifacts/final_report.md`

### Phase 4: Update State
Updates the project state file with artifact hashes.
```bash
python code/pipelines/update_state.py
```
*Output*: `state/projects/PROJ-823-llmxive-follow-up-extending-multabench-b.yaml`

## Verification

To verify the results:
1.  Check `data/artifacts/final_report.md` for the "Data Availability Gap" section and "Known Limitations".
2.  Verify that the `recovery_ratio` is calculated for all datasets with valid baselines.
3.  Confirm that the `gradient_inspection.log` (generated during Phase 2) shows zero weight updates for the backbone.
4.  Check `data/artifacts/metrics.csv` for the `run_id` column to ensure traceability.

## Troubleshooting

*   **Checksum Mismatch**: Ensure the SHA-256 in `data/README.md` matches your local MulTaBench archive.
*   **OOM Error**: Reduce `--batch-size` in Phase 1 and 2.
*   **Missing Data**: Ensure `data/raw/` contains the MulTaBench files.
*   **CUDA Error**: Ensure you are using the CPU-only PyTorch wheel (check `pip show torch`).