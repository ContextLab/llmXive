# Quickstart: llmXive Automation System (001-gene-regulation)

## Prerequisites

- Python 3.11+
- pip
- Git

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-556-llmxive-automation-system-fully-autonomo
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   *Note: `requirements.txt` pins all dependencies for reproducibility.*

3. **Download datasets**:
   Run the data loader script to fetch and checksum datasets:
   ```bash
   python src/utils/data_loader.py --fetch --verify
   ```
   This populates `data/raw/` with verified datasets from HuggingFace/UCI.

## Running the Pipeline

### 1. Smoke Test (Single Dataset)

Run the pipeline on a single UCI dataset to verify the mechanism:

```bash
python src/cli/main.py --dataset uci_har --hypotheses 10 --seed 42
```

**Expected Output**:
- `data/processed/hypotheses.csv`: Contains 10 hypotheses and novelty scores.
- `data/logs/execution_log.json`: Contains execution results.

### 2. Full Run (5 Datasets)

Run the full pipeline with multiple ArchConfigs:

```bash
python src/cli/main.py --full-run --arch-configs all
```

**Expected Output**:
- `data/processed/full_results.csv`: Aggregated results with p-values.
- `paper/summary.md`: Statistical analysis report.

### 3. Statistical Analysis

Run the statistical analysis module on existing results:

```bash
python src/core/stats.py --input data/processed/full_results.csv
```

**Expected Output**:
- Console output of p-values, correlation coefficients, and confidence intervals.

## Troubleshooting

- **MemoryError**: If the pipeline fails due to memory, it will automatically retry with a sampled dataset. Check `data/logs/execution_log.json` for `ResourceExceeded` entries.
- **Timeout**: If code execution times out, check `error_type` in the log. The system allows one retry for `MemoryError` only.
- **Novelty Score 0.5**: If the literature corpus is empty, novelty scores default to 0.5 and are flagged as 'non_novel'. Check `data/lit_search/` for the index.

## Contract Validation

To validate outputs against the schema:

```bash
pytest tests/contract/
```

This ensures all generated files match `contracts/*.schema.yaml`.