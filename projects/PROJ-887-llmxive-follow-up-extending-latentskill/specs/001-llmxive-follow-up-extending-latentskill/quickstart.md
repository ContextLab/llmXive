# Quickstart: llmXive follow-up: extending "LatentSkill: From In-Context Textual Skills to In-Weight Latent Skills"

## Prerequisites

- **Python**: 3.11+
- **System**: Linux (Ubuntu 22.04 recommended for CI compatibility)
- **Memory**: 8 GB RAM (minimum 7 GB for GitHub Actions runner)
- **Disk**: 15 GB free space

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-887-llmxive-follow-up-extending-latentskill
    ```

2.  **Create Virtual Environment**:
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: `requirements.txt` pins `torch` to CPU-only version to ensure compatibility with the free-tier runner.*

4.  **Verify Data Availability**:
    Ensure the "Verified datasets" block contains a valid URL for the LoRA weights. If not, the pipeline will halt.

## Running the Pipeline

The entire pipeline can be executed via the CLI:

```bash
python src/cli.py --run full
```

This command executes the following stages in order:
1.  **Ingestion**: Downloads and verifies weights.
2.  **Flattening**: Creates `skill_index.npy`.
3.  **Retrieval**: Generates query embeddings and synthesizes adapters.
4.  **Evaluation**: Runs tasks against the environment (simulated or real).
5.  **Analysis**: Computes statistics and generates the report.

### Running Specific Stages

- **Only Ingestion**:
  ```bash
  python src/cli.py --run ingestion
  ```
- **Only Evaluation** (requires pre-existing index):
  ```bash
  python src/cli.py --run evaluation --k 5
  ```
- **Statistical Analysis Only**:
  ```bash
  python src/cli.py --run analysis
  ```

## Testing

Run the test suite to verify contract compliance and logic:

```bash
pytest tests/ -v --cov=src
```

### Contract Tests
Ensure output files match the YAML schemas:
```bash
pytest tests/contract/test_schemas.py -v
```

## Troubleshooting

- **Memory Error**: If `RuntimeError: Out of memory` occurs, reduce the number of tasks or use `--streaming` flag (if implemented) to process weights in chunks.
- **Missing Data**: If the pipeline halts with "Data Unavailable", check the "Verified datasets" block in `research.md`. No fallback URLs are permitted.
- **Statistical Failure**: If Benjamini-Hochberg correction fails due to empty comparisons, verify that `N >= 5` runs were completed per task.

## Expected Outputs

After a successful run, the following files will be generated:
- `data/processed/skill_index.npy`
- `data/results/success_log.csv`
- `data/results/stats_report.json` (Primary artifact for the paper)
